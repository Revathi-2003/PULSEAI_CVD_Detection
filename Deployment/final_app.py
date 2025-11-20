import streamlit as st
from Ecg import ECG
from auth import get_db, create_user, verify_user
import os
import uuid
from datetime import datetime
import time
import base64
from PIL import Image
import requests
from io import BytesIO
import logging
import traceback
import hashlib

# --- DEBUG logging ---
logging.basicConfig(level=logging.DEBUG)

# --- Branding / constants ---
APP_TITLE = "PulseAI"
APP_SUBTITLE = "AI-Powered Cardiovascular Detection"

# ECG model function (no caching to avoid sklearn version issues)
def get_ecg_model():
    """Get ECG model instance"""
    return ECG()

# Cache database connection
@st.cache_resource
def get_database():
    """Cache database connection for better performance"""
    return get_db()

def get_base64_of_bin_file(png_file):
    """Convert image to base64 for embedding in HTML"""
    with open(png_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# (KEEP all your existing UI helper functions unchanged)
# ... (add_logo, add_hero_section, add_features_section, add_doctor_quote,
# create_auth_tabs, login_ui) ...
# Paste your previous implementations of those functions here unchanged.
# For brevity in this response I assume you will reuse the same UI helpers.

# ---------- REPLACE upload handling with robust logic ----------
def _save_uploaded_file_to_disk(uploaded_file):
    file_bytes = uploaded_file.getbuffer()
    # sanitize filename
    filename = getattr(uploaded_file, 'name', f'upload_{uuid.uuid4().hex}.png')
    filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.')).strip()
    if not filename:
        filename = f'upload_{uuid.uuid4().hex}.png'
    uploads_dir = os.path.join(os.getcwd(), 'uploaded_files')
    os.makedirs(uploads_dir, exist_ok=True)
    saved_path = os.path.join(uploads_dir, filename)
    with open(saved_path, 'wb') as f:
        f.write(file_bytes)
    return saved_path, file_bytes

def main():
    st.set_page_config(
        page_title="PulseAI - Cardiovascular Detection",
        page_icon="❤️",
        layout='wide',
        initial_sidebar_state='collapsed'
    )

    # Custom CSS + UI helpers
    st.markdown("""<style> ... </style>""", unsafe_allow_html=True)  # keep original CSS block
    add_logo()

    db = get_database()

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        add_hero_section()
        add_features_section()
        add_doctor_quote()
        login_ui(db)
        st.markdown("""<div style="text-align:center;...">...</div>""", unsafe_allow_html=True)  # your footer
        return

    # Logged in UI (identical to your previous code up to uploader)
    st.markdown(f"""<div style="background: linear-gradient(45deg, #e74c3c, #c0392b); ...">
        <h2>👋 Welcome back, {st.session_state.get('email', 'User')}!</h2></div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1])
    with col3:
        if st.button('🚪 Logout', use_container_width=True):
            st.session_state.clear()
            st.rerun()

    ecg = get_ecg_model()

    st.markdown("### 📤 Upload Your ECG Image")
    uploaded_file = st.file_uploader(
        "Choose an ECG image file",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear ECG image for AI analysis"
    )

    # INITIALIZE session_state keys for upload deduping
    if 'last_upload_hash' not in st.session_state:
        st.session_state['last_upload_hash'] = None
    if 'last_upload_result' not in st.session_state:
        st.session_state['last_upload_result'] = None
    if 'upload_error' not in st.session_state:
        st.session_state['upload_error'] = None

    if uploaded_file is not None:
        # compute stable hash for dedup
        try:
            file_bytes = uploaded_file.getbuffer()
        except Exception:
            file_bytes = uploaded_file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # If same file already processed, show cached result
        if st.session_state['last_upload_hash'] == file_hash and st.session_state['last_upload_result'] is not None:
            st.success("✅ This file has already been analyzed.")
            st.markdown("### Result")
            st.info(st.session_state['last_upload_result'])
        else:
            # New file: process it once
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                status_text.text("🔄 Saving uploaded image...")
                progress_bar.progress(5)
                saved_path, _ = _save_uploaded_file_to_disk(uploaded_file)
                progress_bar.progress(15)
                status_text.text("🧹 Cleaning old temporary files...")
                # remove leftover Scaled_1DLead CSVs from previous runs (prevents accumulation)
                for f in os.listdir(os.getcwd()):
                    if f.startswith("Scaled_1DLead_") and f.endswith(".csv"):
                        try:
                            os.remove(os.path.join(os.getcwd(), f))
                        except Exception as e:
                            print("Could not remove old CSV:", f, e)

                progress_bar.progress(25)
                status_text.text("🔄 Loading into ECG pipeline...")

                # pipeline steps (each may raise; traceback shown at top-level)
                ecg_user_image_read = ecg.getImage(saved_path)
                progress_bar.progress(35)
                status_text.text("🎨 Converting to grayscale...")
                ecg_user_gray_image_read = ecg.GrayImgae(ecg_user_image_read)
                progress_bar.progress(45)
                status_text.text("📊 Dividing ECG leads...")
                dividing_leads = ecg.DividingLeads(ecg_user_image_read)
                progress_bar.progress(60)
                status_text.text("⚙️ Preprocessing leads...")
                ecg.PreprocessingLeads(dividing_leads)
                progress_bar.progress(70)
                status_text.text("📡 Extracting signals & scaling...")
                ecg.SignalExtraction_Scaling(dividing_leads)
                progress_bar.progress(80)
                status_text.text("🔄 Converting to 1D signal...")
                ecg_1dsignal = ecg.CombineConvert1Dsignal()
                progress_bar.progress(85)
                status_text.text("🧮 Dimensionality reduction...")
                ecg_final = ecg.DimensionalReduciton(ecg_1dsignal)
                progress_bar.progress(95)
                status_text.text("🤖 Prediction...")
                ecg_model = ecg.ModelLoad_predict(ecg_final)
                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")

                # store result in session
                st.session_state['last_upload_hash'] = file_hash
                st.session_state['last_upload_result'] = ecg_model
                st.session_state['upload_error'] = None

                # show result (same styling as before)
                if "Normal" in ecg_model:
                    result_color = "#27ae60"; result_icon = "✅"
                elif "Myocardial Infarction" in ecg_model:
                    result_color = "#e74c3c"; result_icon = "⚠️"
                elif "Abnormal Heartbeat" in ecg_model:
                    result_color = "#f39c12"; result_icon = "🔔"
                else:
                    result_color = "#9b59b6"; result_icon = "📋"

                st.markdown(f"""
                <div style="background: {result_color}; padding: 30px; border-radius: 15px; 
                            margin: 30px 0; text-align: center; color: white;">
                    <h2 style="color: white; margin: 0 0 15px 0;">
                        {result_icon} AI DIAGNOSIS RESULT
                    </h2>
                    <p style="font-size: 1.3em; margin: 0; font-weight: bold;">
                        {ecg_model}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Save prediction to DB (optional)
                try:
                    preds = db['predictions']
                    pred_doc = {
                        'prediction_id': str(uuid.uuid4()),
                        'user_email': st.session_state.get('email'),
                        'prediction': str(ecg_model),
                        'file_name': os.path.basename(saved_path),
                        'timestamp': datetime.utcnow()
                    }
                    preds.insert_one(pred_doc)
                    st.info('✅ Prediction saved to database')
                except Exception as e:
                    print("DB save failed:", e)

            except Exception as e:
                tb = traceback.format_exc()
                print("Processing error:\n", tb)
                st.error("❌ An error occurred during processing. Full traceback below:")
                st.code(tb, language="python")
                st.session_state['upload_error'] = str(e)
                st.session_state['last_upload_hash'] = None
                st.session_state['last_upload_result'] = None
            finally:
                progress_bar.empty()
                status_text.empty()

    else:
        # your existing "how to use" block unchanged
        st.markdown("""<div style="background: white; ...">...</div>""", unsafe_allow_html=True)

if __name__ == '__main__':
    main()
