Python 3.13.5 (tags/v3.13.5:6cb20a2, Jun 11 2025, 16:15:46) [MSC v.1943 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
from cryptography.fernet import Fernet
import os, json, datetime

KEY_FILE = "luna_data/secret.key"
ACCESS_FILE = "luna_data/access_codes.json"

def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    with open(KEY_FILE, "rb") as f:
        return f.read()

FERNET = Fernet(load_key())

def encrypt_json(obj, path):
    data = json.dumps(obj).encode()
    encrypted = FERNET.encrypt(data)
    with open(path, "wb") as f:
        f.write(encrypted)

... def decrypt_json(path):
...     with open(path, "rb") as f:
...         decrypted = FERNET.decrypt(f.read())
...     return json.loads(decrypted)
... 
... def load_usage(path):
...     if os.path.exists(path):
...         return decrypt_json(path)
...     return {"date": None, "count": 0, "code": "", "activated": ""}
... 
... def save_usage(usage, path):
...     encrypt_json(usage, path)
... 
... def load_access_codes():
...     if not os.path.exists(ACCESS_FILE):
...         return {}
...     with open(ACCESS_FILE, "r") as f:
...         return json.load(f)
... 
... def save_access_codes(data):
...     with open(ACCESS_FILE, "w") as f:
...         json.dump(data, f, indent=2)
... 
... def validate_and_use_code(code, user):
...     DURATION_DAYS = 30
...     codes = load_access_codes()
...     if code not in codes:
...         return False, "❌ Invalid code."
...     info = codes[code]
...     if user in info.get("used_by", []):
...         return True, "✅ Code already redeemed."
...     if int(info.get("uses_left", 0)) <= 0:
...         return False, "🚫 Code has been fully used."
...     if datetime.date.today() > datetime.date.fromisoformat(info["expires"]):
...         return False, "⌛ Code expired."
...     info["used_by"].append(user)
...     info["uses_left"] -= 1
...     save_access_codes(codes)
...     return True, "✅ Code applied!"
