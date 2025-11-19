"""Quick MongoDB connection tester for the PulseAI Deployment folder.

Usage (PowerShell):
  cd Deployment
  .\.venv\Scripts\Activate.ps1   # if you use the venv
  python test_mongo.py

This script loads Deployment/.env (if present), prints a redacted URI, and attempts to connect and show basic info.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ConfigurationError
import urllib.parse

# Load .env from this folder
load_dotenv(Path(__file__).with_name('.env'))

uri = os.environ.get('MONGO_URI')
if not uri:
    print('MONGO_URI not found in environment or .env. Please set MONGO_URI and retry.')
    raise SystemExit(1)

# Redact password for display (attempt to hide between : and @ in the URI)
redacted = uri
try:
    # naive redact: replace between : and @ after scheme
    if '@' in uri and '//' in uri:
        prefix, rest = uri.split('//', 1)
        userinfo, hostpart = rest.split('@', 1)
        if ':' in userinfo:
            user, pwd = userinfo.split(':', 1)
            redacted = f"{prefix}//{user}:<REDACTED>@{hostpart}"
except Exception:
    redacted = '<unable to redact>'

print('Using MONGO_URI:', redacted)

print('\nAttempting connection...')
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # Force connection / server selection
    info = client.server_info()
    print('Connected to MongoDB server version:', info.get('version'))
    dbname = None
    # try to get default db from URI (path component)
    if '@' in uri:
        # URI has authentication, extract path after @
        path = uri.split('@')[-1]
        if '/' in path:
            dbname = path.split('/', 1)[1].split('?')[0]
    elif 'mongodb://' in uri or 'mongodb+srv://' in uri:
        # URI without auth, extract path after hostname
        if 'mongodb+srv://' in uri:
            path = uri.split('mongodb+srv://')[1]
        else:
            path = uri.split('mongodb://')[1]
        if '/' in path:
            dbname = path.split('/', 1)[1].split('?')[0]
    if not dbname:
        dbname = 'CVD_Project'
    db = client[dbname]
    print('Using database:', dbname)
    print('Collections:', db.list_collection_names())
    # If users collection exists, show count
    if 'users' in db.list_collection_names():
        print('users count:', db['users'].count_documents({}))
    else:
        print('users collection not found (expected if no registrations yet)')
except OperationFailure as e:
    print('\nOperationFailure: authentication failed or insufficient privileges.')
    print('Full error:', e)
    print('\nCommon causes and fixes:')
    print('- Wrong username or password. Reset the user password in Atlas and retry.')
    print('- Password contains special characters (e.g. @, :, /). URL-encode the password:')
    print("  Example Python encoding: from urllib.parse import quote_plus; quote_plus('p@ssw:rd')")
    print("  Then use: mongodb+srv://user:encoded_password@cluster.../dbname?options")
    print('- Ensure the Atlas database user has the correct role (readWrite) on the target database.')
    print('- Ensure your cluster allows connections from your IP (Network Access in Atlas). For testing you can allow 0.0.0.0/0 but be careful.')
except ConfigurationError as e:
    print('\nConfigurationError:', e)
except Exception as e:
    print('\nUnexpected error while connecting:', repr(e))
    print('If it is an authentication error, check user/password, URL-encoding, and Atlas user roles.')
