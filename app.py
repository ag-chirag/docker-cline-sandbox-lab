from flask import Flask

app = Flask(__name__)


@app.get("/")
def index():
    return {"message": "Hello from the sandbox lab"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
