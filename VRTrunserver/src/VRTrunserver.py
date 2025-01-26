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

@app.route("/runold", methods=["POST"])
def run():
    command = request.json
    print(f"run: command={command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout_data, stderr_data = process.communicate()
    process.wait()
    return Response(stdout_data, mimetype="text/plain")

@app.route("/run", methods=["POST"])
def runwithusage():
    command = request.json
    print(f"run: command={command}")
    process = psutil.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    usage_collector = RUsageCollector('rusage.log', process)
    while process.poll() == None:
        time.sleep(0.1)
        usage_collector.step()
    usage_collector.close()
    stdout_data, stderr_data = process.communicate()
    process.wait()
    return Response(stdout_data, mimetype="text/plain")

@app.route("/putfile", methods=["POST"])
def putfile():
    args = request.json
    filename = args['filename']
    data = args['data']
    print(f"put: {filename}, {len(data)} bytes")
    open(filename, 'w').write(data)
    full_filename = os.path.abspath(filename)
    print(f"put: return fullpath {full_filename}")
    rv = {"fullpath" : full_filename}
    return jsonify(rv)

@app.route("/getfile")
def getfile():
    args = request.json
    filename = args["fullpath"]
    if not os.path.isabs(filename):
        # Not an absolute path. If it contains directories it is relative to HOME else in working directory.
        if os.path.dirname(filename):
            filename = os.path.join(os.path.expanduser("~"), filename)
    
    print(f"get: {filename}")
    try:
        file_data = open(filename, 'r').read()
    except FileNotFoundError:
        print("failed")
        return Response(status=404)
    return Response(file_data, mimetype="text/plain")

def main():
    print("WARNING: this is a dangerous server that allows executing anything on this machine.")
    app.run(host='0.0.0.0', port=RunnerServerPort)

if __name__ == '__main__':
    main()