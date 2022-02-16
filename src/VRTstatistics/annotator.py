import sys
from typing import Mapping, Optional
from .datastore import DataStore, DataStoreError

__all__ = ["Annotator", "combine"]

class Annotator:
    datastore : DataStore
    role : str
    session_id : str
    session_start_time : float
    desync : float

    def __init__(self, datastore : DataStore, role : str) -> None:
        self.datastore = datastore
        self.role = role
    
    def collect(self) -> None:
        r = self.datastore.find_first_record('"starting" in record and component == "OrchestratorController"', "session start")
        self.session_id = r["sessionId"]

        r = self.datastore.find_first_record('component == "SessionPlayerManager"', "session start time")
        self.session_start_time = r["orchtime"]
        r = self.datastore.find_first_record('"localtime_behind_ms" in record and component == "OrchestratorController"', "session time synchronization")
        self.desync = r["localtime_behind_ms"]

    def annotate(self) -> None:
        self._adjust_time_and_role(self.session_start_time, self.role)
        
    def _adjust_time_and_role(self, starttime: float, role: str) -> None:
        self.session_start_time = starttime
        rv = []
        for r in self.datastore.data:
            newrecord = dict(r)
            if "orchtime" in r:
                newrecord["sessiontime"] = r["orchtime"] - starttime
            else:
                continue  # Delete records before start-of-session
            newrecord["role"] = role
            rv.append(newrecord)
        self.datastore.data = rv

class LatencySenderAnnotator(Annotator):
    send_pc_pipeline : str
    send_pc_grabber : str
    send_pc_encoder : str
    send_pc_writers : Mapping[str, int]

    send_voice_pipeline : Optional[str]
    send_voice_grabber : Optional[str]
    send_voice_encoder : Optional[str]
    send_voice_writer : Optional[str]

    def collect(self) -> None:
        super().collect()
        #
        # Find names of sender side PC components
        #
        r = self.datastore.find_first_record('"PointCloudPipeline" in component and self == 1', "sender pc pipeline")
        self.send_pc_pipeline = r['component']

        self.send_pc_grabber = "PrerecordedLiveReader#0.0" # xxxx cannot find pointcloud reader

        self.send_pc_encoder = "NULLEncoder#0" # xxxx cannot find encoder

        r = self.datastore.find_first_record(f'component == "{self.send_pc_pipeline}" and "writer" in record', "sender pc writer umbrella")
        send_pc_writer_umbrella = r["writer"]

        rr = self.datastore.find_all_records(f'component == "{send_pc_writer_umbrella}" and "pusher" in record', "sender pc writer")
        self.send_pc_writers = {}
        for r in rr:
            stream = r["stream"]
            pusher = r["pusher"]
            self.send_pc_writers[pusher] = stream
        #
        # Find names of sender side voice components
        #
        r = self.datastore.find_first_record('"VoiceSender" in component', "sender voice pipeline")
        self.send_voice_pipeline = r['component']
        send_voice_writer_umbrella = r['writer']
        self.send_voice_grabber = r["reader"]
        self.send_voice_encoder = r["encoder"]
        r = self.datastore.find_first_record(f'component == "{send_voice_writer_umbrella}" and "pusher" in record', "sender voice writer")
        self.send_voice_writer = r['pusher']


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
    recv_pc_readers : Mapping[str, int]
    recv_pc_decoders : Mapping[str, int]
    recv_pc_preparers : Mapping[str, int]
    recv_pc_renderers : Mapping[str, int]

    recv_voice_pipeline : Optional[str]
    recv_voice_reader : Optional[str]
    recv_voice_decoder : Optional[str]
    recv_voice_preparer : Optional[str]
    recv_voice_renderer : Optional[str]


    def collect(self) -> None:
        super().collect()
        #
        # Find names of receiver side pc components
        #
        r = self.datastore.find_first_record('"PointCloudPipeline" in component and self == 0', "receiver pc pipeline")
        self.recv_pc_pipeline = r['component']
        r = self.datastore.find_first_record(f'component == "{self.recv_pc_pipeline}" and "reader" in record', "receiver pc reader umbrella")
        recv_pc_reader_umbrella = r["reader"]
        self.recv_synchronizer = r["synchronizer"]
        self.recv_pc_readers = {}
        rr = self.datastore.find_all_records(f'component == "{recv_pc_reader_umbrella}" and "pull_thread" in record', "receiver pc readers")
        for r in rr:
            tile = r["tile"]
            pull_thread = r["pull_thread"]
            self.recv_pc_readers[pull_thread] = tile
        self.recv_pc_preparers = {}
        self.recv_pc_renderers = {}
        self.recv_pc_decoders = {}
        rr = self.datastore.find_all_records(f'component == "{self.recv_pc_pipeline}" and "decoder" in record', "receiver pc preparers and renderers")
        for r in rr:
            tile = r["tile"]
            decoder = r["decoder"]
            self.recv_pc_decoders[decoder] = tile
        rr = self.datastore.find_all_records(f'component == "{self.recv_pc_pipeline}" and "renderer" in record', "receiver pc preparers and renderers")
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
        r = self.datastore.find_first_record('"VoiceReceiver" in component and "reader" in record', "receiver voice reader umbrella")
        self.recv_voice_pipeline = r["component"]
        self.recv_voice_renderer = r["component"] # same
        self.recv_voice_preparer = r["preparer"]
        synchronizer = r["synchronizer"]
        if synchronizer != "none" and synchronizer != self.recv_synchronizer:
            print("Warning: mismatched synchronizer, was {self.recv_synchronizer} record {r}")
        recv_voice_reader_umbrella = r["reader"]
        r = self.datastore.find_first_record(f'component == "{recv_voice_reader_umbrella}" and "pull_thread" in record', "receiver voice reader umbrella")
        self.recv_voice_reader = r["pull_thread"]
      
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

_Annotators = {
    None: (Annotator, Annotator),
    "latency" : (LatencySenderAnnotator, LatencyReceiverAnnotator)
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
    annotate_sender = _Annotators[annotator][0](senderdata, "sender")
    annotate_receiver = _Annotators[annotator][1](receiverdata, "receiver")
    annotate_sender.collect()
    annotate_receiver.collect()
    
    if annotate_sender.session_id != annotate_receiver.session_id:
        raise DataStoreError(
            f"sender has session {annotate_sender.session_id} and receiver has {annotate_receiver.session_id}"
        )
    if abs(annotate_sender.session_start_time - annotate_receiver.session_start_time) > 1:
        print(
            f"Warning: different session start times, {abs(annotate_sender.session_start_time-annotate_receiver.session_start_time)} seconds apart: receiver {annotate_receiver.session_start_time} sender {annotate_sender.session_start_time}",
            file=sys.stderr,
        )
    if abs(annotate_sender.desync) > 30 or abs(annotate_receiver.desync > 30):
        print(
            f"Warning: synchronization: sender {annotate_sender.desync}ms behind orchestrator",
            file=sys.stderr,
        )
        print(
            f"Warning: synchronization: receiver {annotate_receiver.desync}ms behind orchestrator",
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
    return True

class Symbolicate:
    def __init__(self, datastore : DataStore) -> None:
        self.datastore = datastore

    def run(self) -> None:
 

        # Add symbolic names to all relevant records
        #
        for record in self.datastore.data:
            # sender pc
            if record["role"] == "sender" and record["component"] == self.send_pc_reader:
                record["component_role"] = "sender.reader"
            if record["role"] == "sender" and record["component"] == self.send_pc_encoder:
                record["component_role"] = "sender.encoder"
            if record["role"] == "sender" and record["component"] in self.send_pc_writers:
                record["component_role"] = f"sender.writer.{tile}"
            # receiver pc
            if record["role"] == "receiver" and record["component"] in self.recv_pc_readers:
                tile = self.recv_pc_readers[record["component"]]
                record["component_role"] = f"receiver.reader.{tile}"
            if record["role"] == "receiver" and record["component"] in self.recv_pc_decoders:
                tile = self.recv_pc_decoders[record["component"]]
                record["component_role"] = f"receiver.decoder.{tile}"
            if record["role"] == "receiver" and record["component"] in self.recv_pc_preparers:
                tile = self.recv_pc_preparers[record["component"]]
                record["component_role"] = f"receiver.preparer.{tile}"
            if record["role"] == "receiver" and record["component"] == self.recv_pc_synchronizer:
                record["component_role"] = f"receiver.synchronizer"
            if record["role"] == "receiver" and record["component"] in self.recv_pc_renderers:
                tile = self.recv_pc_renderers[record["component"]]
                record["component_role"] = f"receiver.renderer.{tile}"

