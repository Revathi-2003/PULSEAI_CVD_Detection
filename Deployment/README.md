# PulseAI Deployment

This folder contains a Streamlit app that wraps the existing ECG model and adds simple authentication and tracking.

What I changed/added

- `auth.py` - simple MongoDB-based user helpers (register, verify). Passwords are salted+hashed.
- `final_app.py` - updated Streamlit app to add Login/Register UI, require login to run predictions, and store prediction records in MongoDB.
- `requirements.txt` - added `pymongo`.

Quick setup (Windows PowerShell)

1. Create and activate a virtual environment inside `Deployment` (optional but recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install requirements:

```powershell
pip install -r requirements.txt
```

3. Run MongoDB locally (or provide a connection string):
- For local development, install and start MongoDB.
- Or set the `MONGO_URI` environment variable to a MongoDB connection string (e.g. MongoDB Atlas).

4. Run the Streamlit app:

```powershell
streamlit run final_app.py
```

Schema notes

- `users` collection documents: { email, username, password }
- `predictions` collection documents: { user_email, prediction, file_name, timestamp }

No changes were made to the model or prediction logic.
