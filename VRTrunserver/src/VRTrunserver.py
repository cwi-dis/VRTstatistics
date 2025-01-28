import os
import time
import subprocess
import datetime
from flask import Flask, request, Response, jsonify
import platform
import psutil

RunnerServerPort = 5002

if platform.system() == "Windows":
    import WinTmp

app = Flask(__name__)

class Settings:
    def __init__(self):
        self.executable = "/Users/jack/src/VRTogether/VRTApp-Develop-built.app/Contents/MacOS/VR2Gather"
        self.topworkdir = "/Users/jack/tmp/VRTrunserver"
        self.workdir = None

SETTINGS = Settings()

class RUsageCollector:
    def __init__(self, filename : str, proc : psutil.Process) -> None:
        self.fp = open(filename, 'w')
        self.proc = proc
        self.net_last_time = 0
        self.net_bytes_recv = 0
        self.net_bytes_sent = 0
        self._get_bandwidth()
        self.plt = platform.system()

    def close(self):
        self.fp.close()

    def step(self):
        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        ts = (now-midnight).total_seconds()
        try:
            cpu = self.proc.cpu_percent()
            mem = self.proc.memory_info()
        except psutil.ZombieProcess:
            return
        except psutil.NoSuchProcess:
            return
        allcpu = psutil.cpu_percent(percpu=True)
        maxcpu = max(allcpu)
        rss = mem.rss
        vms = mem.vms
        net = psutil.net_io_counters()
        recv, sent = self._get_bandwidth()
        stats_log = f'stats: component=ResourceConsumption, ts={ts:.3f}, cpu={cpu}, cpu_max={maxcpu}, mem={vms}, recv_bandwidth={recv:.0f}, sent_bandwidth={sent:.0f}'
        if self.plt == "Windows":
            temperature = WinTmp.CPU_Temp()
            stats_log += f', temperature={temperature}'
        print(stats_log, file=self.fp)

    def _get_bandwidth(self):
        net = psutil.net_io_counters()
        now = time.time()
        interval = now - self.net_last_time
        recv_bandwidth = (net.bytes_recv - self.net_bytes_recv) / interval
        sent_bandwidth = (net.bytes_sent - self.net_bytes_sent) / interval
        self.net_last_time = now
        self.net_bytes_recv = net.bytes_recv
        self.net_bytes_sent = net.bytes_sent
        return recv_bandwidth, sent_bandwidth

@app.route("/about")
def about():
    return "<p>Hello world!</p>"

@app.route("/start", methods=["POST"])
def start():
    args = request.json
    print(f"start: {args}")
    SETTINGS.workdir = os.path.join(SETTINGS.topworkdir, args["workdir"])
    os.makedirs(SETTINGS.workdir, exist_ok=True)
    return Response("OK", mimetype="text/plain")

@app.route("/stop", methods=["GET", "POST"])
def stop():
    if SETTINGS.workdir == None:
        print("stop: start not called")
        return Response("400: stop: start not called", status=400)
    print("stop")
    SETTINGS.workdir = None
    return Response("OK", mimetype="text/plain")

@app.route("/run", methods=["GET", "POST"])
def run():
    if SETTINGS.workdir == None:
        print("run: start not called")
        return Response("400: run: start not called", status=400)
    command = [SETTINGS.executable]
    
    print(f"run: command={' '.join(command)}")
    
    process = psutil.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    usage_file = os.path.join(SETTINGS.workdir, 'rusage.log')
    usage_collector = RUsageCollector(usage_file, process)
    while process.poll() == None:
        time.sleep(0.1)
        usage_collector.step()
    usage_collector.close()
    stdout_data, stderr_data = process.communicate()
    process.wait()
    return Response(stdout_data, mimetype="text/plain")

@app.route("/putfile", methods=["POST"])
def putfile():
    if SETTINGS.workdir == None:
        print("putfile: start not called")
        return Response("400: putfile: start not called", status=400)
    args = request.json
    filename = os.path.join(SETTINGS.workdir, args['filename'])
    data = args['data']
    print(f"put: {filename}, {len(data)} bytes")
    open(filename, 'wb').write(data)
    full_filename = os.path.abspath(filename)
    print(f"put: return fullpath {full_filename}")
    rv = {"fullpath" : full_filename}
    return jsonify(rv)

@app.route("/getfile")
def getfile():
    if SETTINGS.workdir == None:
        print("getfile: start not called")
        return Response("400: getfile: start not called", status=400)
    args = request.json
    filename = os.path.join(SETTINGS.workdir, args['filename'])
    
    print(f"get: {filename}")
    try:
        file_data = open(filename, 'rb').read()
    except FileNotFoundError:
        print("failed")
        return Response(status=404)
    return Response(file_data, mimetype="text/plain")

@app.route("/listdir")
def listdir():
    if SETTINGS.workdir == None:
        print("listdir: start not called")
        return Response("400: listdir: start not called", status=400)
    files = []
    try:
        for dirpath, dirnames, filenames in os.walk(SETTINGS.workdir):
            files = []
            for filename in filenames:
                files.append(os.path.join(dirpath, filename))
    except FileNotFoundError:
        print("listdir: failed")
        return Response(status=404)
    print(f"listdir: {len(files)} files")
    return jsonify(files)

def main():
    print("WARNING: this is a dangerous server that allows executing anything on this machine.")
    app.run(host='0.0.0.0', port=RunnerServerPort)

if __name__ == '__main__':
    main()