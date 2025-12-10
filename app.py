from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "SmartBusFlow Backend Running!"

@app.route("/api/bus")
def bus_info():
    return jsonify({
        "status": "online",
        "message": "Bus tracking API coming soon"
    })

if __name__ == "__main__":
    app.run(debug=True)
