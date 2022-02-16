from .datastore import DataStore

class Symbolicate:
    def __init__(self, datastore : DataStore) -> None:
        self.datastore = datastore

    def run(self) -> None:
        #
        # Find names of sender side PC components
        #
        r = self.datastore.find_first_record('role == "sender" and "PointCloudPipeline" in component and self == 1', "sender pc pipeline")
        send_pc_pipeline = r['component']

        r = self.datastore.find_first_record(f'role == "sender" and component == "{send_pc_pipeline}" and "writer" in record', "sender pc writer umbrella")
        send_pc_writer_umbrella = r["writer"]

        rr = self.datastore.find_all_records(f'role == "sender" and component == "{send_pc_writer_umbrella}" and "pusher" in record', "sender pc writer")
        send_pc_writers = {}
        for r in rr:
            stream = r["stream"]
            pusher = r["pusher"]
            send_pc_writers[pusher] = stream
        send_pc_reader = "PrerecordedLineReader#0.0" # xxxx cannot find pointcloud reader
        send_pc_encoder = "NULLEncoder#0" # xxxx cannot find encoder
        #
        # Find names of sender side voice components
        #
        r = self.datastore.find_first_record('role == "sender" and "VoiceSender" in component', "sender voice pipeline")
        send_voice_pipeline = r['component']
        send_voice_writer = r['writer']

        send_voice_reader = "VoiceReader" # xxxx cannot find voice reader
        send_voice_encoder = None # xxxx cannot find voice encoder

        #
        # Find names of receiver side pc components
        #
        r = self.datastore.find_first_record('role == "receiver" and "PointCloudPipeline" in component and self == 0', "receiver pc pipeline")
        recv_pc_pipeline = r['component']
        r = self.datastore.find_first_record(f'role == "receiver" and component == "{recv_pc_pipeline}" and "reader" in record', "receiver pc reader umbrella")
        recv_pc_reader_umbrella = r["reader"]
        recv_pc_readers = {}
        rr = self.datastore.find_all_records(f'role == "receiver" and component == "{recv_pc_reader_umbrella}" and "pull_thread" in record', "receiver pc readers")
        for r in rr:
            tile = r["tile"]
            pull_thread = r["pull_thread"]
            recv_pc_readers[pull_thread] = tile
        recv_pc_preparers = {}
        recv_pc_renderers = {}
        rr = self.datastore.find_all_records(f'role == "receiver" and component == "{recv_pc_pipeline}" and "tile" in record', "receiver pc preparers and renderers")
        for r in rr:
            tile = r["tile"]
            preparer = r["preparer"]
            renderer = r["renderer"]
            recv_pc_preparers[preparer] = tile
            recv_pc_renderers[renderer] = tile
        recv_pc_synchronizer = "Synchronizer#1" # xxxx cannot find synchronizer
        recv_pc_decoders = {"NULLDecoder#0" : 0} # xxxx cannot find decoder
        #
        # Find names of receiver side voice components
        # 
        # xxxjack to be done
        #
        # Add symbolic names to all relevant records
        #
        for record in self.datastore.data:
            # sender pc
            if record["role"] == "sender" and record["component"] == send_pc_reader:
                record["fullrole"] = "sender.reader"
            if record["role"] == "sender" and record["component"] == send_pc_encoder:
                record["fullrole"] = "sender.encoder"
            if record["role"] == "sender" and record["component"] in send_pc_writers:
                record["fullrole"] = f"sender.writer.{tile}"
            # receiver pc
            if record["role"] == "receiver" and record["component"] in recv_pc_readers:
                tile = recv_pc_readers[record["component"]]
                record["fullrole"] = f"receiver.reader.{tile}"
            if record["role"] == "receiver" and record["component"] in recv_pc_decoders:
                tile = recv_pc_decoders[record["component"]]
                record["fullrole"] = f"receiver.decoder.{tile}"
            if record["role"] == "receiver" and record["component"] in recv_pc_preparers:
                tile = recv_pc_preparers[record["component"]]
                record["fullrole"] = f"receiver.preparer.{tile}"
            if record["role"] == "receiver" and record["component"] == recv_pc_synchronizer:
                record["fullrole"] = f"receiver.synchronizer"
            if record["role"] == "receiver" and record["component"] in recv_pc_renderers:
                tile = recv_pc_renderers[record["component"]]
                record["fullrole"] = f"receiver.renderer.{tile}"

