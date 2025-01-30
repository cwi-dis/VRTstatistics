import os
import sys
import time
import subprocess
import shutil
from typing import Dict, Optional, List
import datetime
from flask import Flask, request, Response, jsonify, send_file
import platform
import psutil
import argparse

RunnerServerPort = 5002

if platform.system() == "Windows":
    import WinTmp

app = Flask(__name__)

class Settings:
    def __init__(self):
        self.executable = "/Users/jack/src/VRTogether/VRTApp-Develop-built.app/Contents/MacOS/VR2Gather"
        self.topworkdir = "/Users/jack/tmp/VRTrunserver"
        self.workdir : Optional[str] = None

    def init_defaults(self):
        my_path = os.path.join(os.getcwd(), sys.argv[0])
        my_topdir = os.path.dirname(my_path)
        if sys.platform == "darwin":
            # On MacOS the VRTrunserver lives in the bundle where the VR2Gather executable is.
            # We create a temporary workdir in the same directory as the VR2Gather app.
            self.executable = os.path.join(my_topdir, "VR2Gather")
            app_dir = os.path.dirname(my_topdir) # Contents
            app_dir = os.path.dirname(app_dir) # VRTApp-Develop-built.app
            app_dir = os.path.dirname(app_dir) # Where the .app lives
            self.topworkdir = os.path.join(app_dir, "VRTrunserver-workdir")
        elif sys.platform == "win32":
            # On other platforms the VRTrunserver lives in the same directory as the VR2Gather executable.
            # We create a temporary workdir in the same directory as the VR2Gather executable.
            self.executable = os.path.join(my_topdir, "VR2Gather.exe")
            self.topworkdir = os.path.join(my_topdir, "VRTrunserver-workdir")
        else:
            raise Exception(f"Unsupported platform {sys.platform}")
        
    def check_defaults(self):
        if not os.path.exists(self.executable):
            raise Exception(f"Executable {self.executable} does not exist")
        if not os.path.exists(self.topworkdir):
            os.makedirs(self.topworkdir)
        print(f"VRTrunserver: executable={self.executable}")
        print(f"VRTRunserver: topworkdir={self.topworkdir}")

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
    args : Dict[str, str] = request.json
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
    logfile = os.path.join(SETTINGS.workdir, 'unity.log')
    command = [
        SETTINGS.executable,
        "-logFile", logfile
        ]
    configfile = os.path.join(SETTINGS.workdir, 'config.json')
    if os.path.exists(configfile):
        command += ["-vrt-config", configfile]    
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
    #
    # Find the statsfilename and copy that file to the workdir
    #
    copy_stats_file(logfile, SETTINGS.workdir)
    if stderr_data:
        stdout_data += b"\n" + stderr_data
    return Response(stdout_data, mimetype="text/plain")

def copy_stats_file(logfile : str, workdir : str):
    # See if we can find the stats file
    stats_filename = None
    for line in open(logfile):
        if line.startswith("stats:"):
            fields = line.split(",")
            for field in fields:
                field = field.strip()
                key, value = field.split("=")
                if key == "statsFilename":
                    stats_filename = value
                    break
    if stats_filename:
        shutil.copy(stats_filename, workdir)

@app.route("/putfile", methods=["POST"])
def putfile():
    if SETTINGS.workdir == None:
        print("putfile: start not called")
        return Response("400: putfile: start not called", status=400)
    file = request.files['file']
    filename = file.filename
    if not filename:
        return Response("400: putfile: no filename", status=400)
    filename = os.path.join(SETTINGS.workdir, filename)
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    file.save(filename)
    full_filename = os.path.abspath(filename)
    print(f"put: return fullpath {full_filename}")
    rv = {"fullpath" : full_filename}
    return jsonify(rv)

@app.route("/get/<path:filename>")
def getfile(filename : str):
    if SETTINGS.workdir == None:
        print("getfile: start not called")
        return Response("400: getfile: start not called", status=400)
    
    print(f"get: {filename}")
    try:
        file = open(os.path.join(SETTINGS.topworkdir, filename), 'rb')
    except FileNotFoundError:
        print("failed")
        return Response(status=404)
    return send_file(file, mimetype="application/binary", download_name=filename, as_attachment=True)

@app.route("/listdir")
def listdir():
    if SETTINGS.workdir == None:
        print("listdir: start not called")
        return Response("400: listdir: start not called", status=400)
    files = []
    try:
        for dirpath, _, filenames in os.walk(SETTINGS.workdir):
            files : List[str] = []
            for filename in filenames:
                relpath = os.path.relpath(os.path.join(dirpath, filename), SETTINGS.topworkdir)
                relpath.replace("\\", "/")
                files.append(relpath)
    except FileNotFoundError:
        print("listdir: failed")
        return Response(status=404)
    print(f"listdir: {len(files)} files: {files}")
    return jsonify(files)

def main():
    print("WARNING: this is a dangerous server that allows executing anything on this machine.")
    SETTINGS.init_defaults()
    parser = argparse.ArgumentParser(description="Run a VR2Gather player server")
    parser.add_argument("--executable", metavar="EXE", default=SETTINGS.executable, help="Executable to run (default: %(default)s)")
    parser.add_argument("--topworkdir", metavar="DIR", default=SETTINGS.topworkdir, help="Top work directory (default: %(default)s)")
    args = parser.parse_args()
    SETTINGS.executable = args.executable
    SETTINGS.topworkdir = args.topworkdir
    SETTINGS.check_defaults()
    app.run(host='0.0.0.0', port=RunnerServerPort)

if __name__ == '__main__':
    main()