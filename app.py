from flask import Flask
import subprocess

app = Flask(__name__)


def start_another_process():
    subprocess.Popen(["python", "TgBot.py"])


start_another_process()


@app.route("/")
def index():
    return "zxc"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)