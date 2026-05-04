
import os, json, uuid, hashlib, hmac, base64, datetime, subprocess, platform
from pathlib import Path

APP_BRAND = "Dentaflix"
TRIAL_DAYS = 7
SECRET = "DENTAFLIX_PRIVATE_SECRET_CHANGE_ME_2026"
LICENSE_FILE = Path(__file__).parent / "license.dat"
TRIAL_FILE = Path(__file__).parent / ".trial.dat"
SERVER_URL_FILE = Path(__file__).parent / "activation_server.txt"


def _run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode(errors="ignore").strip()
    except Exception:
        return ""


def get_device_id():
    parts = [
        platform.node(),
        platform.system(),
        platform.machine(),
        str(uuid.getnode()),
    ]
    if platform.system() == "Windows":
        parts.append(_run("wmic csproduct get uuid"))
        parts.append(_run("wmic diskdrive get serialnumber"))
    raw = "|".join(parts)
    digest = hashlib.sha256(raw.encode()).hexdigest().upper()
    return "-".join([digest[i:i+4] for i in range(0, 24, 4)])


def sign_payload(payload):
    clean = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(SECRET.encode(), clean.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(json.dumps({"payload": payload, "sig": sig}).encode()).decode()
    return token


def verify_token(token):
    try:
        data = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        payload = data["payload"]
        expected = hmac.new(
            SECRET.encode(),
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, data["sig"]):
            return False, "Invalid license signature", None
        if payload.get("device_id") != get_device_id():
            return False, "License is not valid for this device", payload
        expiry = payload.get("expiry")
        if expiry != "LIFETIME":
            exp = datetime.date.fromisoformat(expiry)
            if datetime.date.today() > exp:
                return False, "License expired", payload
        return True, "OK", payload
    except Exception as e:
        return False, f"Invalid license: {e}", None


def save_license(token):
    LICENSE_FILE.write_text(token, encoding="utf-8")


def load_license():
    if LICENSE_FILE.exists():
        return LICENSE_FILE.read_text(encoding="utf-8").strip()
    return ""


def get_trial_status():
    today = datetime.date.today()
    if not TRIAL_FILE.exists():
        TRIAL_FILE.write_text(today.isoformat(), encoding="utf-8")
        return True, TRIAL_DAYS
    try:
        start = datetime.date.fromisoformat(TRIAL_FILE.read_text().strip())
    except Exception:
        start = today
        TRIAL_FILE.write_text(today.isoformat(), encoding="utf-8")
    days_used = (today - start).days
    remaining = TRIAL_DAYS - days_used
    return remaining >= 0, max(0, remaining)


def is_activated():
    token = load_license()
    if token:
        ok, msg, payload = verify_token(token)
        if ok:
            return True, f"Licensed to: {payload.get('customer_name','Customer')} | Expiry: {payload.get('expiry')}", payload
    trial_ok, remain = get_trial_status()
    if trial_ok:
        return True, f"Trial Version - {remain} days remaining", None
    return False, "Trial expired. Please activate.", None


def default_server_url():
    if SERVER_URL_FILE.exists():
        return SERVER_URL_FILE.read_text(encoding="utf-8").strip()
    return "http://127.0.0.1:5000/activate"


def set_server_url(url):
    SERVER_URL_FILE.write_text(url.strip(), encoding="utf-8")
