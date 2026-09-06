from flask import Flask, send_from_directory
from pathlib import Path

app = Flask(__name__)

BATCAVE_FILES = Path.home() / "storage" / "shared" / "BatCave" / "files"

@app.route("/")
def home():
    return send_from_directory("../web", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("../web", path)

@app.route("/api/files")
def files():
    return {
        "files": [
            {
                "name": file.name,
                "url": f"/files/{file.name}"
            }
            for file in BATCAVE_FILES.iterdir()
            if file.is_file()
        ]
    }

@app.route("/files/<path:filename>")
def download_file(filename):
    return send_from_directory(BATCAVE_FILES, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)