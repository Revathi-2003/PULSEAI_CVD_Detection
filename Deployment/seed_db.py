"""Seed script to create common collections for the PulseAI project and insert sample documents.

Run from Deployment/ with your venv active:
  .\.venv\Scripts\Activate.ps1
  python seed_db.py

The script uses the same get_db() from auth.py and will use MONGO_URI / MONGO_DB from your .env.
It is safe to run multiple times; documents inserted include a "seeded_at" timestamp.
"""
from datetime import datetime
from auth import get_db


def seed():
    db = get_db()
    print('Using database:', db.name)

    # Collections to create with a single sample document each
    samples = {
        # Collections requested by the user (PulseAI schema)
        'features_1d': {
            'feature_id': 'F1D_0001',
            'record_id': 'R0001',
            'values': [0.1, 0.2, 0.3],
            'created_at': datetime.utcnow()
        },
        'features_pca': {
            'feature_id': 'FPCA_0001',
            'record_id': 'R0001',
            'pca_values': [1.2, -0.3],
            'created_at': datetime.utcnow()
        },
        'models': {
            'model_name': 'Heart_Disease_Prediction_using_ECG',
            'version': '1.0',
            'file_ref': 'Heart_Disease_Prediction_using_ECG (4).pkl',
            'created_at': datetime.utcnow()
        },
        'predictions': {
            'prediction_id': 'PRED_0001',
            'user_email': 'alice@example.com',
            'prediction': 'Normal',
            'score': 0.87,
            'timestamp': datetime.utcnow()
        },
        'processing_runs': {
            'run_id': 'RUN_0001',
            'status': 'completed',
            'started_at': datetime.utcnow(),
            'finished_at': datetime.utcnow()
        },
        'sessions': {
            'session_id': 'S0001',
            'user_email': 'alice@example.com',
            'started_at': datetime.utcnow()
        },
        'uploads': {
            'upload_id': 'U0001',
            'user_email': 'alice@example.com',
            'file_name': 'example_ecg.png',
            'uploaded_at': datetime.utcnow()
        },
        # existing examples (kept)
        'patients': {
            'patient_id': 'P0001',
            'name': 'John Doe',
            'age': 58,
            'sex': 'M',
            'medical_history': ['hypertension'],
            'created_at': datetime.utcnow()
        },
        'ecg_records': {
            'record_id': 'R0001',
            'patient_id': 'P0001',
            'lead_count': 12,
            'recorded_at': datetime.utcnow(),
            'file_ref': 'example_ecg_1.png'
        },
        'leads': {
            'lead_name': 'Lead I',
            'lead_index': 1,
            'created_at': datetime.utcnow()
        },
        'model_metadata': {
            'model_name': 'Heart_Disease_Prediction_using_ECG',
            'version': '1.0',
            'created_at': datetime.utcnow()
        },
        'audit_logs': {
            'action': 'seed_db',
            'detail': 'Created sample collections and documents',
            'seeded_at': datetime.utcnow()
        }
    }

    for coll_name, doc in samples.items():
        coll = db[coll_name]
        # insert a doc only if collection is empty to avoid duplicates on repeated runs
        count = coll.count_documents({})
        if count == 0:
            res = coll.insert_one(doc)
            print(f'Inserted sample into {coll_name} with _id={res.inserted_id}')
        else:
            print(f'Collection {coll_name} already has {count} documents; skipping insert')

    print('\nSeeding complete. Check Atlas Data Explorer or run test_mongo.py to list collections.')


if __name__ == '__main__':
    seed()
