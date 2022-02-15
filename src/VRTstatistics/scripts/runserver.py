from flask import Flask, request, Response
import subprocess
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

def main():
    print("WARNING: this is a dangerous server that allows executing anything on this machine.")
    app.run(host='0.0.0.0', port=RunnerServerPort)

if __name__ == '__main__':
    main()