import os
import hashlib
import binascii
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Load project .env (Deployment/.env) if present so MONGO_URI is available via os.environ
load_dotenv(Path(__file__).with_name('.env'))


def get_db(uri: str = None):
    """Return a pymongo database object for the PulseAI app.

    Reads the connection string from the MONGO_URI environment variable if
    not provided. Defaults to a local MongoDB instance.
    """
    uri = uri or os.environ.get('MONGO_URI') or 'mongodb://localhost:27017'
    client = MongoClient(uri)

    # Determine which database name to use:
    # 1) MONGO_DB env var (explicit)
    # 2) database path component from the MONGO_URI if present (e.g. /mydb)
    # 3) fallback to 'pulseai' for backward compatibility
    db_name = os.environ.get('MONGO_DB')
    if not db_name:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(uri)
            path = (parsed.path or '').lstrip('/')
            if path:
                # path may include query params; split on '?' just in case
                db_name = path.split('?', 1)[0]
        except Exception:
            db_name = None

    if not db_name:
        db_name = 'CVD_Project'

    db = client[db_name]
    return db


def _hash_password(password: str) -> str:
    """Hash a password with a random 16-byte salt and return salt:hash hex string."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return binascii.hexlify(salt).decode('utf-8') + ':' + binascii.hexlify(dk).decode('utf-8')


def _verify_password(stored: str, provided_password: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split(':')
        salt = binascii.unhexlify(salt_hex)
        dk = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return binascii.hexlify(dk).decode('utf-8') == hash_hex
    except Exception:
        return False


def create_user(db, email: str, username: str, password: str) -> bool:
    """Create a user document in the users collection.

    Returns True if created, False if user already exists.
    """
    users = db['users']
    if users.find_one({'email': email}):
        return False
    password_hash = _hash_password(password)
    users.insert_one({'email': email, 'username': username, 'password': password_hash})
    return True


def get_user(db, email: str):
    users = db['users']
    return users.find_one({'email': email})


def verify_user(db, email: str, password: str) -> bool:
    user = get_user(db, email)
    if not user:
        return False
    return _verify_password(user.get('password', ''), password)
