from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Yes! It's working."

app.run(host="0.0.0.0", port=8080)
