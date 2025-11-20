# final_app.py
import streamlit as st
from Ecg import ECG
from auth import get_db, create_user, verify_user
import os
import uuid
from datetime import datetime
import base64
import hashlib
import traceback
import logging

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pulseai")

# ECG factory
def get_ecg_model():
    return ECG()

@st.cache_resource
def get_database():
    return get_db()

def _sanitize_filename(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in ('-', '_', '.'))
    if not safe or safe.startswith('.'):
        safe = f"upload_{uuid.uuid4().hex}.jpg"
    return safe

def _save_uploaded_file(uploaded_file) -> tuple[str,str,bytes]:
    try:
        b = uploaded_file.getbuffer()
    except Exception:
        b = uploaded_file.read()
    safe_name = _sanitize_filename(getattr(uploaded_file, 'name', f"upload_{uuid.uuid4().hex}.jpg"))
    uploads_dir = os.path.join(os.getcwd(), 'uploaded_files')
    os.makedirs(uploads_dir, exist_ok=True)
    saved_path = os.path.join(uploads_dir, safe_name)
    with open(saved_path, 'wb') as f:
        f.write(b)
    return saved_path, safe_name, b

# UI helpers (kept condensed)
def add_logo():
    st.markdown("""<div style="text-align:center;padding:20px 0;"><h1 style="color:#e74c3c">❤️ PulseAI</h1>
                   <p style="color:#7f8c8d;">AI-Powered Cardiovascular Detection</p></div>""", unsafe_allow_html=True)

def create_auth_tabs():
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { height:50px; background:#f0f2f6; border-radius:10px 10px 0 0; }
    .stTabs [aria-selected="true"] { background:#e74c3c; color:white; }
    </style>
    """, unsafe_allow_html=True)
    return st.tabs(["🔐 Login","📝 Register"])

# simplified login/register UI (use your implementations if desired)
def login_ui(db):
    tab1, tab2 = create_auth_tabs()
    with tab1:
        email = st.text_input('📧 Email Address', key='login_email')
        password = st.text_input('🔒 Password', type='password', key='login_password')
        if st.button('🚀 Login to PulseAI', key='login_btn'):
            if email and password and verify_user(db, email, password):
                st.session_state['logged_in'] = True
                st.session_state['email'] = email
                try:
                    sess = db['sessions']; sess.insert_one({'session_id':str(uuid.uuid4()), 'user_email':email, 'started_at':datetime.utcnow()})
                except Exception:
                    pass
                st.success('✅ Logged in'); st.rerun()
            else:
                st.error('Invalid credentials')

    with tab2:
        new_email = st.text_input('📧 Email', key='reg_email')
        new_username = st.text_input('👤 Username', key='reg_username')
        new_password = st.text_input('🔒 Password', type='password', key='reg_password')
        if st.button('✨ Create Account', key='reg_btn'):
            if new_email and new_password:
                ok = create_user(db, new_email, new_username or new_email.split('@')[0], new_password)
                if ok: st.success('Account created! Please login.')
                else: st.error('Account already exists')
            else:
                st.warning('Fill email and password')

def main():
    st.set_page_config(page_title="PulseAI - Cardiovascular Detection", page_icon="❤️", layout='wide')
    add_logo()
    db = get_database()

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        st.markdown("<h3>Welcome — please login to continue</h3>", unsafe_allow_html=True)
        login_ui(db)
        return

    st.markdown(f"<div style='background:linear-gradient(45deg,#e74c3c,#c0392b);padding:12px;border-radius:12px;color:white;'><b>👋 Welcome {st.session_state.get('email')}</b></div>", unsafe_allow_html=True)
    if st.button('🚪 Logout'):
        st.session_state.clear(); st.rerun()

    ecg = get_ecg_model()

    st.markdown("### 📤 Upload Your ECG Image")
    uploaded_files = st.file_uploader("Choose an ECG image file", type=['png','jpg','jpeg'], accept_multiple_files=True)

    # session caching
    st.session_state.setdefault('last_upload_hash', None)
    st.session_state.setdefault('last_upload_result', None)
    st.session_state.setdefault('upload_error', None)

    if uploaded_files:
        uploaded_file = uploaded_files[0]
        try:
            buf = uploaded_file.getbuffer()
        except Exception:
            buf = uploaded_file.read()
        file_hash = hashlib.sha256(buf).hexdigest()

        if st.session_state['last_upload_hash'] == file_hash and st.session_state['last_upload_result'] is not None:
            st.success("✅ This file was already analyzed in this session.")
            st.info(st.session_state['last_upload_result'])
        else:
            progress = st.progress(0)
            status = st.empty()
            try:
                status.text("Saving uploaded file...")
                progress.progress(5)
                saved_path, safe_name, _ = _save_uploaded_file(uploaded_file)
                logger.info("Saved upload to %s", saved_path)
                progress.progress(15)

                # remove stale Scaled CSVs in ecg.base_dir
                base_dir = getattr(ecg, 'base_dir', os.getcwd())
                for f in os.listdir(base_dir):
                    if f.startswith("Scaled_1DLead_") and f.endswith(".csv"):
                        try: os.remove(os.path.join(base_dir, f))
                        except Exception: pass

                progress.progress(25); status.text("Loading into ECG pipeline...")
                ecg_image = ecg.getImage(saved_path); progress.progress(35)
                status.text("Converting to grayscale..."); ecg_gray = ecg.GrayImgae(ecg_image); progress.progress(45)
                status.text("Dividing leads..."); dividing_leads = ecg.DividingLeads(ecg_image); progress.progress(60)

                # show previews safely if available
                leads12_file = os.path.join(ecg.base_dir, 'Leads_1-12_figure.png')
                longlead_file = os.path.join(ecg.base_dir, 'Long_Lead_13_figure.png')
                with st.expander("📈 Lead previews (optional)"):
                    if os.path.isfile(leads12_file): st.image(leads12_file, caption='Leads 1-12', use_column_width=True)
                    else: st.warning("Leads_1-12_figure.png not found.")
                    if os.path.isfile(longlead_file): st.image(longlead_file, caption='Long lead', use_column_width=True)
                    else: st.warning("Long_Lead_13_figure.png not found.")

                status.text("Preprocessing leads..."); ecg.PreprocessingLeads(dividing_leads); progress.progress(70)
                status.text("Extracting signals & scaling..."); ecg.SignalExtraction_Scaling(dividing_leads); progress.progress(80)
                status.text("Combining 1D signals..."); ecg_1d = ecg.CombineConvert1Dsignal(); progress.progress(85)
                status.text("Dimensionality reduction..."); ecg_final = ecg.DimensionalReduciton(ecg_1d); progress.progress(95)
                status.text("Predicting..."); result_text = ecg.ModelLoad_predict(ecg_final); progress.progress(100)
                status.text("Complete ✅")

                # cache
                st.session_state['last_upload_hash'] = file_hash
                st.session_state['last_upload_result'] = result_text
                st.session_state['upload_error'] = None

                # styled output
                if "Normal" in result_text: color="#27ae60"; icon="✅"
                elif "Myocardial Infarction" in result_text: color="#e74c3c"; icon="⚠️"
                elif "Abnormal Heartbeat" in result_text: color="#f39c12"; icon="🔔"
                else: color="#9b59b6"; icon="📋"

                st.markdown(f"""
                    <div style="background:{color};padding:20px;border-radius:12px;color:white;text-align:center;">
                    <h3>{icon} AI DIAGNOSIS</h3><p style="font-weight:bold">{result_text}</p></div>
                """, unsafe_allow_html=True)

                # save to DB (optional)
                try:
                    preds = db['predictions']
                    preds.insert_one({'prediction_id':str(uuid.uuid4()), 'user_email':st.session_state.get('email'),
                                      'prediction':result_text, 'file_name':safe_name, 'timestamp':datetime.utcnow()})
                    st.info('Saved prediction to DB')
                except Exception as e:
                    logger.warning("DB save failed: %s", e)

            except Exception as e:
                tb = traceback.format_exc()
                logger.error("Processing error: %s", tb)
                st.error("An error occurred during processing. See traceback below.")
                st.code(tb, language='python')
                st.session_state['last_upload_hash'] = None
                st.session_state['last_upload_result'] = None
                st.session_state['upload_error'] = str(e)
            finally:
                try: progress.empty(); status.empty()
                except Exception: pass

    else:
        st.markdown("<i>No file uploaded — upload a PNG/JPG ECG image to analyze.</i>", unsafe_allow_html=True)

if __name__ == '__main__':
    main()
