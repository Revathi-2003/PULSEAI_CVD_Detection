# auth.py
import os
import hashlib
import binascii
from pathlib import Path

# Keep dotenv support for local development (optional)
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# Load a .env sitting next to this file if present
load_dotenv(Path(__file__).with_name('.env'))


def _resolve_uri_and_db_from_streamlit_secrets():
    """
    Helper to read Streamlit secrets if the app is running under Streamlit.
    Supports both styles:
      - Top-level keys: MONGO_URI and MONGO_DB
      - Section-style: [MONGO] URI = "..."
    Returns (uri_or_none, db_name_or_none)
    """
    try:
        import streamlit as st  # local import so module can be used outside Streamlit too
    except Exception:
        return None, None

    # Try section style first: st.secrets["MONGO"]["URI"]
    try:
        mongo_section = st.secrets.get("MONGO")
        if mongo_section:
            uri = mongo_section.get("URI") or mongo_section.get("uri")
            dbname = mongo_section.get("DB") or mongo_section.get("db") or mongo_section.get("NAME") or mongo_section.get("name")
            return uri, dbname
    except Exception:
        pass

    # Try top-level keys
    try:
        uri = st.secrets.get("MONGO_URI") or st.secrets.get("MONGOURI") or st.secrets.get("MONGO")
        dbname = st.secrets.get("MONGO_DB") or st.secrets.get("MONGO_DBNAME") or st.secrets.get("MONGO_DB_NAME")
        return uri, dbname
    except Exception:
        return None, None


def get_db(uri: str = None):
    """
    Return a pymongo Database object.

    Resolution order for connection info:
      1. Explicit `uri` argument
      2. Streamlit secrets (MONGO section or MONGO_URI / MONGO_DB)
      3. Environment variables MONGO_URI and MONGO_DB
      4. Parse DB name out of the URI if present
      5. Fallback to localhost and 'CVD_Project' database

    This function attempts a quick ping to verify connection and will raise
    RuntimeError if it cannot connect to the resolved MongoDB URI.
    """
    # 1) explicit arg
    resolved_uri = uri

    # 2) try streamlit secrets
    if not resolved_uri:
        st_uri, st_db = _resolve_uri_and_db_from_streamlit_secrets()
        if st_uri:
            resolved_uri = st_uri

    # 3) try environment variables
    if not resolved_uri:
        resolved_uri = os.environ.get("MONGO_URI") or os.environ.get("MONGODB_URI")

    # 4) default to localhost if nothing found
    if not resolved_uri:
        resolved_uri = "mongodb://localhost:27017"

    # Determine DB name
    db_name = None

    # streamlit secret db name if present
    try:
        _, st_db = _resolve_uri_and_db_from_streamlit_secrets()
        if st_db:
            db_name = st_db
    except Exception:
        pass

    # env var
    if not db_name:
        db_name = os.environ.get("MONGO_DB") or os.environ.get("MONGO_DBNAME") or os.environ.get("MONGODB_DATABASE")

    # try to parse DB from URI path component if still missing
    if not db_name:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(resolved_uri)
            path = (parsed.path or "").lstrip("/")
            if path:
                db_name = path.split("?", 1)[0]
        except Exception:
            db_name = None

    # final fallback
    if not db_name:
        db_name = "CVD_Project"

    # Create client and ping to validate
    client = MongoClient(resolved_uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError as e:
        # Provide a clear error — this will appear in Streamlit logs
        raise RuntimeError(
            f"Could not connect to MongoDB at '{resolved_uri}'. "
            "Check your Streamlit secrets, environment variables, and Atlas IP whitelist."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error when connecting to MongoDB: {e}") from e

    return client[db_name]


def _hash_password(password: str) -> str:
    """Hash a password with a random 16-byte salt and return salt:hash hex string."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return binascii.hexlify(salt).decode("utf-8") + ":" + binascii.hexlify(dk).decode("utf-8")


def _verify_password(stored: str, provided_password: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split(":")
        salt = binascii.unhexlify(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100000)
        return binascii.hexlify(dk).decode("utf-8") == hash_hex
    except Exception:
        return False


def create_user(db, email: str, username: str, password: str) -> bool:
    """Create a user document in the users collection.

    Returns True if created, False if user already exists.
    """
    users = db["users"]
    if users.find_one({"email": email}):
        return False
    password_hash = _hash_password(password)
    users.insert_one({"email": email, "username": username, "password": password_hash})
    return True


def get_user(db, email: str):
    users = db["users"]
    return users.find_one({"email": email})


def verify_user(db, email: str, password: str) -> bool:
    user = get_user(db, email)
    if not user:
        return False
    return _verify_password(user.get("password", ""), password)
