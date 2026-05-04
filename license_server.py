
from flask import Flask, request, jsonify
import sqlite3, datetime
import license_core

DB = "license_server.db"
app = Flask(__name__)

def init():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS activations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        customer_name TEXT,
        license_type TEXT,
        expiry TEXT,
        created_at TEXT
    )""")
    con.commit()
    con.close()

@app.route("/activate", methods=["POST"])
def activate():
    data = request.get_json(force=True)
    device_id = data.get("device_id", "").strip()
    customer_name = data.get("customer_name", "Customer").strip()
    if not device_id:
        return jsonify({"ok": False, "message": "Missing device_id"}), 400

    # Default: one-year license from activation date.
    expiry = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    payload = {
        "device_id": device_id,
        "customer_name": customer_name,
        "license_type": "ONLINE-1YEAR",
        "expiry": expiry,
        "brand": license_core.APP_BRAND,
    }
    token = license_core.sign_payload(payload)

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("INSERT INTO activations(device_id,customer_name,license_type,expiry,created_at) VALUES(?,?,?,?,?)",
                (device_id, customer_name, "ONLINE-1YEAR", expiry, datetime.datetime.now().isoformat()))
    con.commit()
    con.close()

    return jsonify({"ok": True, "license_token": token, "expiry": expiry})

@app.route("/", methods=["GET"])
def home():
    return "Dentaflix License Server is running."

if __name__ == "__main__":
    init()
    print("Dentaflix License Server running on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000)
