import sys
import time
import datetime
from typing import Mapping, Optional, Tuple, Type, Union, Dict, Any

from .datastore import DataStore, DataStoreError, DataStoreRecord

__all__ = ["Annotator", "combine", "deserialize"]

class Annotator:
    verbose = True
    datastore : DataStore
    role : str
    session_id : str
    session_start_time : float
    desync : float
    desync_uncertainty : float
    user_name : Optional[str]

    def __init__(self, datastore : DataStore, role : str) -> None:
        self.datastore = datastore
        self.datastore.annotator = self
        self.role = role
    
    def to_dict(self) -> DataStoreRecord:
        rv = dict(
            type=type(self).__name__,
            role=self.role,
            session_id=self.session_id,
            session_start_time=self.session_start_time,
            desync=self.desync,
            desync_uncertainty=self.desync_uncertainty,
            user_name=self.user_name
        )
        return rv

    def collect(self) -> None:
        r = self.datastore.find_first_record('"starting" in record and component == "OrchestratorController"', f"{self.role} session start")
        self.session_id = r["sessionId"]
        if self.verbose:
            print(f"{self.role}: session_id={self.session_id} (from seq={r['seq']})")
        
        r = self.datastore.find_first_record('component == "SessionPlayerManager"', f"{self.role} session start time")
        self.session_start_time = r["orchtime"]
        if self.verbose:
            print(f"{self.role}: session_start_time={self.session_start_time} (from seq={r['seq']})")
        r = self.datastore.find_first_record('"localtime_behind_ms" in record and component == "OrchestratorController"', f"{self.role} session time synchronization")
        self.desync = r["localtime_behind_ms"] / 1000.0
        self.desync_uncertainty = r["uncertainty_interval_ms"] / 1000.0
        r = self.datastore.find_first_record('component == "SessionPlayerManager" and "userName" in record and self == "True"', f"{self.role} user name")
        self.user_name = r["userName"]
        if self.verbose:
            print(f"{self.role}: user_name={self.user_name} (from seq={r['seq']})")
        
    def annotate(self) -> None:
        self._adjust_time_and_role(self.session_start_time, self.role)
        
    def _adjust_time_and_role(self, starttime: float, role: str) -> None:
        self.session_start_time = starttime
        rv : list[DataStoreRecord] = []
        for r in self.datastore.data:
            newrecord = dict(r)
            if "orchtime" in r:
                newrecord["sessiontime"] = r["orchtime"] - starttime
            else:
                continue  # Delete records before start-of-session
            newrecord["role"] = role
            rv.append(newrecord)
        self.datastore.data = rv

    def description(self) -> str:
        return f"captured: {time.ctime(self.session_start_time)}\nrole: {self.role}\nsession_id: {self.session_id}\nusername: {self.user_name}"

class CombinedAnnotator(Annotator):
    sender : Optional[str]
    receiver : Optional[str]

    def collect(self) -> None:
        super().collect()

    def from_sources(self, sender_annotator : Annotator, receiver_annotator : Annotator) -> None:
        self.desync = 0
        self.desync = sender_annotator.desync - receiver_annotator.desync
        self.desync_uncertainty = max(sender_annotator.desync_uncertainty, receiver_annotator.desync_uncertainty)/2
        self.sender = sender_annotator.user_name
        self.receiver = receiver_annotator.user_name
        self.user_name = None

    def to_dict(self):
        rv = super().to_dict()
        rv["sender"] = self.sender
        rv["receiver"] = self.receiver
        return rv

    def annotate(self) -> None:
        pass # Nothing to change in the data, has all been done in the sender and receiver annotator

    def description(self) -> str:
        return f"captured: {time.ctime(self.session_start_time)}\nsender: {self.sender}\nreceiver: {self.receiver}\ndesync: {self.desync:.3f} ± {self.desync_uncertainty:.3f}"

class LatencySenderAnnotator(Annotator):
    send_pc_pipeline : str
    send_pc_grabber : str
    send_pc_encoder : str
    send_pc_writers : Mapping[str, int]
    protocol : str
    compressed : bool
    nTiles : int
    nQualities : int

    send_voice_pipeline : Optional[str]
    send_voice_grabber : Optional[str]
    send_voice_encoder : Optional[str]
    send_voice_writer : Optional[str]

    def _check(self):
        assert self.send_pc_pipeline
        assert self.send_pc_grabber
        assert self.send_pc_encoder
        assert len(self.send_pc_writers) >= 1
        assert self.protocol
        assert self.nTiles >= 1
        assert self.nQualities >= 1

    def collect(self) -> None:
        super().collect()
        #
        # Find protocol used
        #
        recs = self.datastore.find_all_records('"proto" in record', f"{self.role} protocol used")
        self.protocol = recs[0]["proto"]
        for r in recs:
            assert r["proto"] == self.protocol
        #
        # Find names of sender side PC components
        #
        r = self.datastore.find_first_record('"PointCloudPipelineSelf" in component and "self" in record and self == 1', f"{self.role} pc pipeline")
        self.send_pc_pipeline = r['component']
        if self.verbose:
            print(f"{self.role}: send_pc_pipeline={self.send_pc_pipeline} (from seq={r['seq']})")

        r = self.datastore.find_first_record(f'component == "{self.send_pc_pipeline}" and "writer" in record', f"{self.role} pc writer umbrella")
        self.send_pc_grabber = r["reader"]
        self.send_pc_encoder = r["encoder"]
        send_pc_writer_umbrella = r["writer"]
        if self.verbose:
            print(f"{self.role}: send_pc_grabber={self.send_pc_grabber} (from seq={r['seq']})")
            print(f"{self.role}: send_pc_encoder={self.send_pc_encoder} (from seq={r['seq']})")
            print(f"{self.role}: send_pc_writer_umbrella={send_pc_writer_umbrella} (from seq={r['seq']})")
        self.compressed = "PCEncoder" in self.send_pc_encoder
        self.nTiles = r["ntile"]
        self.nQualities = r["nquality"]

        # Hack: SocketIO uses a single writer to push all streams.
        if self.protocol == "socketio" or self.protocol == "tcpreflector":
            self.send_pc_writers = {send_pc_writer_umbrella : "all" } # type: ignore
        else:
            rr = self.datastore.find_all_records(f'component == "{send_pc_writer_umbrella}" and "pusher" in record', f"{self.role} pc writer")
            self.send_pc_writers = {}
            for r in rr:
                pusher = r["pusher"]
                if "tile" in r:
                    # B2DWriter uses tile field. Need to check what happens with multiple qualities.
                    tile = r["tile"]
                    # And B2DWriter uses tile numbers (1-based) not indices.
                    tile = tile-1
                    self.send_pc_writers[pusher] = tile
                else:
                    stream = r["stream"]
                    self.send_pc_writers[pusher] = stream
        #
        # Find names of sender side voice components
        #
        self.send_voice_pipeline = None
        self.send_voice_grabber = None
        self.send_voice_encoder = None
        self.send_voice_writer = None
        try:
            r = self.datastore.find_first_record('"VoicePipelineSelf" in component and "writer" in record', f"{self.role} sender voice pipeline")
            self.send_voice_pipeline = r['component']
            self.send_voice_writer = r['writer']
            self.send_voice_grabber = r["reader"]
            self.send_voice_encoder = r["encoder"]
            if self.verbose:
                print(f"{self.role}: send_voice_pipeline={self.send_voice_pipeline} (from seq={r['seq']})")
                print(f"{self.role}: send_voice_writer={self.send_voice_writer} (from seq={r['seq']})")
                print(f"{self.role}: send_voice_grabber={self.send_voice_grabber} (from seq={r['seq']})")
                print(f"{self.role}: send_voice_encoder={self.send_voice_encoder} (from seq={r['seq']})")
        except DataStoreError:
            print("Warning: no voice VoicePipelineSelf record found, no sender voice pipeline")
        self._check()

    def annotate(self) -> None:
        super().annotate()
        for record in self.datastore.data:
            # sender pc
            if record["component"] == self.send_pc_grabber:
                record["component_role"] = "sender.pc.grabber"
            elif record["component"] == self.send_pc_encoder:
                record["component_role"] = "sender.pc.encoder"
            elif record["component"] in self.send_pc_writers:
                tile = self.send_pc_writers[record["component"]]
                record["component_role"] = f"sender.pc.writer.{tile}"
            elif record["component"] == self.send_voice_grabber:
                record["component_role"] = "sender.voice.grabber"
            elif record["component"] == self.send_voice_encoder:
                record["component_role"] = "sender.voice.encoder"
            elif record["component"] == self.send_voice_writer:
                record["component_role"] = "sender.voice.writer"
            else:
                record["component_role"] = ""
          
class LatencyReceiverAnnotator(Annotator):
    recv_synchronizer : str

    recv_pc_pipeline : str
    recv_pc_readers : Mapping[str, Union[int, str]]
    recv_pc_decoders : Mapping[str, int]
    recv_pc_preparers : Mapping[str, int]
    recv_pc_renderers : Mapping[str, int]

    recv_voice_pipeline : Optional[str]
    recv_voice_reader : Optional[str]
    recv_voice_decoder : Optional[str]
    recv_voice_preparer : Optional[str]
    recv_voice_renderer : Optional[str]

    def _check(self):
        assert self.recv_pc_pipeline
        assert self.recv_synchronizer
        assert len(self.recv_pc_readers) >= 1
        assert len(self.recv_pc_decoders) == len(self.recv_pc_readers) or list(self.recv_pc_readers.values())[0] == 'all'
        assert len(self.recv_pc_preparers) == len(self.recv_pc_decoders)
        assert len(self.recv_pc_renderers) == len(self.recv_pc_preparers)

    def collect(self) -> None:
        super().collect()
        assert self.datastore
        #
        # Find names of receiver side pc components
        #
        r = self.datastore.find_first_record('"PointCloudPipelineOther" in component and "self" in record and self == 0', f"{self.role} pc pipeline")
        self.recv_pc_pipeline = r['component']
        if self.verbose:
            print(f"{self.role}: recv_pc_pipeline={self.recv_pc_pipeline} (from seq={r['seq']})")
        r = self.datastore.find_first_record(f'component == "{self.recv_pc_pipeline}" and "reader" in record', f"{self.role} pc reader umbrella")
        recv_pc_reader_umbrella = r["reader"]
        self.recv_synchronizer = r["synchronizer"]
        if self.verbose:
            print(f"{self.role}: recv_pc_reader_umbrella={recv_pc_reader_umbrella} (from seq={r['seq']})")
            print(f"{self.role}: recv_synchronizer={self.recv_synchronizer} (from seq={r['seq']})")
        # Hack - SocketIO uses a single reader to read all streams.
        if "SocketIOReader" in recv_pc_reader_umbrella or "TCPReflectorReader" in recv_pc_reader_umbrella:
            self.recv_pc_readers = { recv_pc_reader_umbrella : "all"}
        else:
            self.recv_pc_readers = {}
            rr = self.datastore.find_all_records(f'component == "{recv_pc_reader_umbrella}" and "pull_thread" in record', f"{self.role} pc readers")
            for r in rr:
                tile = r["tile"]
                # Grrr, need to subtract one, at least for PCSubReader
                if 'Sub' in recv_pc_reader_umbrella:
                    tile = tile-1
                pull_thread = r["pull_thread"]
                self.recv_pc_readers[pull_thread] = tile
        self.recv_pc_preparers = {}
        self.recv_pc_renderers = {}
        self.recv_pc_decoders = {}
        rr = self.datastore.find_all_records(f'component == "{self.recv_pc_pipeline}" and "decoder" in record', f"{self.role} pc preparers and renderers")
        for r in rr:
            tile = r["tile"]
            decoder = r["decoder"]
            self.recv_pc_decoders[decoder] = tile
        rr = self.datastore.find_all_records(f'component == "{self.recv_pc_pipeline}" and "renderer" in record', f"{self.role} pc preparers and renderers")
        for r in rr:
            tile = r["tile"]
            preparer = r["preparer"]
            renderer = r["renderer"]
            self.recv_pc_preparers[preparer] = tile
            self.recv_pc_renderers[renderer] = tile
        #
        # Find names of receiver side voice components
        # 
        self.recv_voice_reader = None
        self.recv_voice_decoder = None
        self.recv_voice_preparer = None
        self.recv_voice_renderer = None
        try:
            r = self.datastore.find_first_record('"VoicePipelineOther" in component and "reader" in record', f"{self.role} voice reader umbrella")
            self.recv_voice_pipeline = r["component"]
            self.recv_voice_renderer = r["component"] # same
            self.recv_voice_preparer = r["preparer"]
            synchronizer = r["synchronizer"]
            if self.verbose:
                print(f"{self.role}: recv_voice_pipeline={self.recv_voice_pipeline} (from seq={r['seq']})")
                print(f"{self.role}: recv_voice_renderer={self.recv_voice_renderer} (from seq={r['seq']})")
                print(f"{self.role}: recv_voice_preparer={self.recv_voice_preparer} (from seq={r['seq']})")
                print(f"{self.role}: synchronizer={synchronizer} (from seq={r['seq']})")
            if synchronizer != "none" and synchronizer != self.recv_synchronizer:
                print("Warning: mismatched synchronizer, was {self.recv_synchronizer} record {r}")
#            recv_voice_reader_umbrella = r["reader"]
#            r = self.datastore.find_first_record(f'component == "{recv_voice_reader_umbrella}" and "pull_thread" in record', f"{self.role} voice reader umbrella")
#            self.recv_voice_reader = r["pull_thread"]
        except DataStoreError:
            print("Warning: no voice VoicePipelineOther record found, no receiver voice pipeline")
        self._check()
      
    def annotate(self) -> None:
        super().annotate()
        for record in self.datastore.data:
            if record["component"] == self.recv_synchronizer:
                record["component_role"] = f"receiver.synchronizer"
            # receiver pc
            elif record["component"] in self.recv_pc_readers:
                tile = self.recv_pc_readers[record["component"]]
                record["component_role"] = f"receiver.pc.reader.{tile}"
            elif record["component"] in self.recv_pc_decoders:
                tile = self.recv_pc_decoders[record["component"]]
                record["component_role"] = f"receiver.pc.decoder.{tile}"
            elif record["component"] in self.recv_pc_preparers:
                tile = self.recv_pc_preparers[record["component"]]
                record["component_role"] = f"receiver.pc.preparer.{tile}"
            elif record["component"] in self.recv_pc_renderers:
                tile = self.recv_pc_renderers[record["component"]]
                record["component_role"] = f"receiver.pc.renderer.{tile}"
            # receiver voice
            elif record["component"] == self.recv_voice_reader:
                record["component_role"] = f"receiver.voice.reader"
            elif record["component"] == self.recv_voice_decoder:
                record["component_role"] = f"receiver.voice.decoder"
            elif record["component"] == self.recv_voice_preparer:
                record["component_role"] = f"receiver.voice.preparer"
            elif record["component"] == self.recv_voice_renderer:
                record["component_role"] = f"receiver.voice.renderer"
            else:
                record["component_role"] = ""

class LatencyCombinedAnnotator(CombinedAnnotator):
    protocol : str
    nTiles : int
    nQualities : int
    compressed : bool

    def from_sources(self, sender_annotator : Annotator, receiver_annotator : Annotator) -> None:
        super().from_sources(sender_annotator, receiver_annotator)
        self.protocol = sender_annotator.protocol
        self.nTiles = sender_annotator.nTiles
        self.nQualities = sender_annotator.nQualities
        self.compressed = sender_annotator.compressed

    def to_dict(self) -> DataStoreRecord:
        rv = super().to_dict()
        rv["protocol"] = self.protocol
        rv["nTiles"] = self.nTiles
        rv["nQualities"] = self.nQualities
        rv["compressed"] = self.compressed
        return rv

    def collect(self) -> None:
        super().collect()
        self.protocol = "unknown"
        self.nTiles = -1
        self.nQualities = -1
        self.compressed = False

    def description(self) -> str:
        dt = datetime.datetime.fromtimestamp(self.session_start_time)
        dt = dt.strftime("%d-%b-%Y %H:%M")
        rv = f"{dt}\n{self.sender} to {self.receiver}\n{self.protocol}"
        if self.compressed:
            rv += ", compressed"
            if self.nQualities > 1:
                rv += f" ({self.nQualities} levels)"
        if self.nTiles > 1:
            rv += f", {self.nTiles} tiles"
        rv += f"\ndesync: {int(self.desync*1000)} ms ± {int(self.desync_uncertainty*1000)}"
        return rv
    def annotate(self) -> None:
        pass # Nothing to change in the data, has all been done in the sender and receiver annotator

class VqegCombinedAnnotator(CombinedAnnotator):
    pass

class VqegSenderAnnotator(Annotator):
    pass

class VqegReceiverAnnotator(Annotator):
    pass

_Annotators : dict[Optional[str], Tuple[Type[Annotator], Type[Annotator], Type[CombinedAnnotator]]]= {
    None: (Annotator, Annotator, CombinedAnnotator),
    "latency" : (LatencySenderAnnotator, LatencyReceiverAnnotator, LatencyCombinedAnnotator),
    "vqeg" : (VqegSenderAnnotator, VqegReceiverAnnotator, VqegCombinedAnnotator)
}

def combine(
    annotator : str, senderdata: DataStore, receiverdata: DataStore, outputdata: DataStore
) -> bool:
    """
    Senderdata and receiverdata are lists of dictionaries, they are combined and sorted and the result is returned.
    Session timestamps (relative to start of session), sender/receiver role are added to each record.
    Records are sorted by timstamp.
    """
    if not annotator in _Annotators:
        raise RuntimeError(f"Unknown annotator {annotator}, only know {list(_Annotators.keys())}")
    AnnoClassSender, AnnoClassReceiver, AnnoClassCombined = _Annotators[annotator]
    assert AnnoClassSender
    assert AnnoClassReceiver

    annotate_sender = AnnoClassSender(senderdata, "sender")
    annotate_receiver = AnnoClassReceiver(receiverdata, "receiver")
    annotate_sender.collect()
    annotate_receiver.collect()

    print(f"Sender:\n{annotate_sender.description()}\n\nReceiver:\n{annotate_receiver.description()}\n\n")
    
    if annotate_sender.session_id != annotate_receiver.session_id:
        raise DataStoreError(
            f"sender has session {annotate_sender.session_id} and receiver has {annotate_receiver.session_id}"
        )
    if abs(annotate_sender.session_start_time - annotate_receiver.session_start_time) > 1:
        print(
            f"Warning: different session start times, {abs(annotate_sender.session_start_time-annotate_receiver.session_start_time)} seconds apart: receiver {annotate_receiver.session_start_time} sender {annotate_sender.session_start_time}",
            file=sys.stderr,
        )
    if abs(annotate_sender.desync) > 0.030 or abs(annotate_receiver.desync > 0.030):
        print(
            f"Warning: synchronization: sender {annotate_sender.desync:.3f}s (+/- {annotate_sender.desync_uncertainty/2:.3f}s) behind orchestrator",
            file=sys.stderr,
        )
        print(
            f"Warning: synchronization: receiver {annotate_receiver.desync:.3f}s (+/- {annotate_receiver.desync_uncertainty/2:.3f}s) behind orchestrator",
            file=sys.stderr,
        )

    session_start_time = min(annotate_receiver.session_start_time, annotate_sender.session_start_time)
    annotate_receiver.session_start_time = session_start_time
    annotate_sender.session_start_time = session_start_time
    #
    # Adjust data lists with session timestamps and roles
    #
    annotate_sender.annotate()
    annotate_receiver.annotate()

    #
    # Combine and sort
    #
    outputdata.load_data(senderdata.data + receiverdata.data)
    outputdata.sort(key=lambda r: r["sessiontime"])
    # And annotate, if wanted
    if AnnoClassCombined:
        annotate_combined = AnnoClassCombined(outputdata, "combined")
        annotate_combined.collect()
        annotate_combined.from_sources(annotate_sender, annotate_receiver)
        annotate_combined.annotate()
        print(f"Session:\n{annotate_combined.description()}\n\n")
    return True

def deserialize(datastore : DataStore, d : Dict[Any, Any]) -> Annotator:
    klass = globals()[d["type"]]
    ann = klass(datastore, d["role"])
    for k, v in d.items():
        if k == "type": continue
        setattr(ann, k, v)
    print(f"deserialize:\n{ann.description()}")
    return ann