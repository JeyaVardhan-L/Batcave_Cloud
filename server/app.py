from pathlib import Path

from flask import Flask, jsonify, send_from_directory


app = Flask(__name__)

# Real Batcave storage on the Android device
BATCAVE_ROOT = Path.home() / "storage" / "shared" / "BatCave"
BATCAVE_FILES = BATCAVE_ROOT / "files"

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


@app.route("/")
def home():
    return send_from_directory(WEB_ROOT, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(WEB_ROOT, path)


@app.route("/api/files")
def list_files():
    files = []

    if BATCAVE_FILES.exists():
        for file in BATCAVE_FILES.iterdir():
            if file.is_file():
                files.append(
                    {
                        "name": file.name,
                        "url": f"/files/{file.name}",
                    }
                )

    files.sort(key=lambda item: item["name"].lower())

    return jsonify({"files": files})


@app.route("/files/<path:filename>")
def serve_file(filename):
    return send_from_directory(BATCAVE_FILES, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)