from flask import Flask, request, Response, jsonify
import subprocess
import os
from ..runner import RunnerServerPort

app = Flask(__name__)

@app.route("/about")
def about():
    return "<p>Hello world!</p>"

@app.route("/run", methods=["POST"])
def run():
    command = request.json
    print(f"run: command={command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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