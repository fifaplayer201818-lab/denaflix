
from flask import Flask, request, jsonify
import datetime, hashlib, hmac, base64, json

app = Flask(__name__)
SECRET = "DENTAFLIX_PRIVATE_SECRET_CHANGE_ME_2026"
APP_BRAND = "Dentaflix"
LICENSE_DAYS = 730

def sign_payload(payload):
    clean = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(SECRET.encode(), clean.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(json.dumps({"payload": payload, "sig": sig}).encode()).decode()

@app.route("/", methods=["GET"])
def home():
    return "Dentaflix License Server is running. Plan: 14000 EGP / 2 years."

@app.route("/activate", methods=["POST"])
def activate():
    data = request.get_json(force=True)
    device_id = data.get("device_id", "").strip()
    customer_name = data.get("customer_name", "Customer").strip()

    if not device_id:
        return jsonify({"ok": False, "message": "Missing device_id"}), 400

    expiry = (datetime.date.today() + datetime.timedelta(days=LICENSE_DAYS)).isoformat()
    payload = {
        "device_id": device_id,
        "customer_name": customer_name,
        "license_type": "ONLINE-2YEARS",
        "expiry": expiry,
        "brand": APP_BRAND,
        "price": "14000 EGP"
    }
    return jsonify({"ok": True, "license_token": sign_payload(payload), "expiry": expiry, "plan": "2 Years", "price": "14000 EGP"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
