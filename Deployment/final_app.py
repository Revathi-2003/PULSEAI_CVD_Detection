# final_app.py
import streamlit as st
from Ecg import ECG
from auth import get_db, create_user, verify_user
import os
import uuid
from datetime import datetime
import base64
from io import BytesIO
import hashlib
import traceback
import logging

# --- logging for debugging on Streamlit Cloud ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pulseai")

# --- Branding / constants ---
APP_TITLE = "PulseAI"
APP_SUBTITLE = "AI-Powered Cardiovascular Detection"

# ECG model function (no caching to avoid sklearn version issues)
def get_ecg_model():
    return ECG()

# Cache database connection
@st.cache_resource
def get_database():
    return get_db()

def get_base64_of_bin_file(png_file):
    with open(png_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ---------- UI helper functions (kept from your version) ----------
def add_logo():
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #e74c3c; font-size: 3.5em; margin: 0; font-weight: bold;">
            ❤️ PulseAI
        </h1>
        <p style="color: #7f8c8d; font-size: 1.2em; margin: 5px 0;">
            AI-Powered Cardiovascular Detection
        </p>
    </div>
    """, unsafe_allow_html=True)

def add_hero_section():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 20px; border-radius: 15px; margin: 20px 0;
                text-align: center; color: white;">
        <h2 style="color: white; font-size: 2.5em; margin: 0 0 20px 0;">
            🩺 Your Heart Health Matters
        </h2>
        <p style="font-size: 1.3em; margin: 0 0 20px 0; opacity: 0.9;">
            "The heart is the only broken instrument that works perfectly."
        </p>
    </div>
    """, unsafe_allow_html=True)

def add_features_section():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #f8f9fa;
                    border-radius: 10px; margin: 10px 0;">
            <div style="font-size: 3em; margin-bottom: 15px;">🤖</div>
            <h3 style="color: #2c3e50; margin: 0 0 10px 0;">AI-Powered Analysis</h3>
            <p style="color: #7f8c8d; margin: 0;">Advanced machine learning algorithms for accurate ECG interpretation</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #f8f9fa;
                    border-radius: 10px; margin: 10px 0;">
            <div style="font-size: 3em; margin-bottom: 15px;">⚡</div>
            <h3 style="color: #2c3e50; margin: 0 0 10px 0;">Instant Results</h3>
            <p style="color: #7f8c8d; margin: 0;">Get your cardiovascular analysis in seconds, not days</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #f8f9fa;
                    border-radius: 10px; margin: 10px 0;">
            <div style="font-size: 3em; margin-bottom: 15px;">🛡️</div>
            <h3 style="color: #2c3e50; margin: 0 0 10px 0;">Secure & Private</h3>
            <p style="color: #7f8c8d; margin: 0;">Your health data is encrypted and protected</p>
        </div>
        """, unsafe_allow_html=True)

def add_doctor_quote():
    st.markdown("""
    <div style="background: #ecf0f1; padding: 30px; border-radius: 15px;
                margin: 30px 0; border-left: 5px solid #e74c3c;">
        <div style="display: flex; align-items: center;">
            <div style="font-size: 4em; margin-right: 20px;">👨‍⚕️</div>
            <div>
                <p style="font-size: 1.2em; color: #2c3e50; margin: 0 0 10px 0; font-style: italic;">
                    "Prevention is better than cure. Early detection of cardiovascular diseases
                    can save lives and improve quality of life significantly."
                </p>
                <p style="color: #7f8c8d; margin: 0; font-weight: bold;">
                    - Dr. Sarah Johnson, Cardiologist
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_auth_tabs():
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #f0f2f6;
        border-radius: 10px 10px 0px 0px; padding-top: 10px; padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #e74c3c; color: white; }
    </style>
    """, unsafe_allow_html=True)
    return st.tabs(["🔐 Login", "📝 Register"])

def login_ui(db):
    tab1, tab2 = create_auth_tabs()
    with tab1:
        st.markdown("""<div style="background: white; padding: 30px; border-radius: 15px;">
            <h2 style="text-align:center;">Welcome Back to PulseAI</h2></div>""", unsafe_allow_html=True)
        email = st.text_input('📧 Email Address', key='login_email', placeholder="Enter your email")
        password = st.text_input('🔒 Password', type='password', key='login_password', placeholder="Enter your password")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button('🚀 Login to PulseAI', type='primary', use_container_width=True):
                if email and password:
                    if verify_user(db, email, password):
                        st.session_state['logged_in'] = True
                        st.session_state['email'] = email
                        try:
                            sess = db['sessions']
                            session_doc = {'session_id': str(uuid.uuid4()), 'user_email': email, 'started_at': datetime.utcnow()}
                            sess.insert_one(session_doc)
                        except Exception:
                            pass
                        st.success('🎉 Login successful! Welcome to PulseAI!')
                        st.rerun()
                    else:
                        st.error('❌ Invalid credentials.')
                else:
                    st.warning('⚠️ Please fill in all fields.')

    with tab2:
        st.markdown("""<div style="background: white; padding: 30px; border-radius: 15px;">
            <h2 style="text-align:center;">Join PulseAI Today</h2></div>""", unsafe_allow_html=True)
        new_email = st.text_input('📧 Email Address', key='reg_email', placeholder="Enter your email")
        new_username = st.text_input('👤 Username', key='reg_username', placeholder="Choose a username")
        new_password = st.text_input('🔒 Password', type='password', key='reg_password', placeholder="Create a password")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button('✨ Create Account', type='primary', use_container_width=True):
                if new_email and new_password:
                    ok = create_user(db, new_email, new_username or new_email.split('@')[0], new_password)
                    if ok:
                        st.success('🎉 Account created successfully! Please login to continue.')
                    else:
                        st.error('❌ Account already exists.')
                else:
                    st.warning('⚠️ Fill in email and password.')

# ---------- helper to sanitize and save uploaded files ----------
def _sanitize_filename(name: str) -> str:
    # keep letters, numbers, dash, underscore, dot
    safe = "".join(c for c in name if c.isalnum() or c in ('-', '_', '.'))
    if not safe or safe.startswith('.'):
        safe = f"upload_{uuid.uuid4().hex}.jpg"
    return safe

def _save_uploaded_file(uploaded_file) -> str:
    # uploaded_file is a streamlit UploadedFile-like object
    # read bytes
    try:
        b = uploaded_file.getbuffer()
    except Exception:
        b = uploaded_file.read()
    # make safe filename (do NOT trust client filename)
    safe_name = _sanitize_filename(uploaded_file.name or f"upload_{uuid.uuid4().hex}.jpg")
    uploads_dir = os.path.join(os.getcwd(), 'uploaded_files')
    os.makedirs(uploads_dir, exist_ok=True)
    saved_path = os.path.join(uploads_dir, safe_name)
    with open(saved_path, 'wb') as f:
        f.write(b)
    return saved_path, safe_name, b

# ---------- Main app ----------
def main():
    st.set_page_config(page_title="PulseAI - Cardiovascular Detection", page_icon="❤️", layout='wide', initial_sidebar_state='collapsed')
    # Minimal CSS
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .stButton > button { background: linear-gradient(45deg, #e74c3c, #c0392b); color: white; border: none; border-radius: 25px; }
    </style>
    """, unsafe_allow_html=True)

    add_logo()
    db = get_database()

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        add_hero_section()
        add_features_section()
        add_doctor_quote()
        login_ui(db)
        st.markdown("<div style='text-align:center;padding:40px 0;color:#7f8c8d'>© 2024 PulseAI</div>", unsafe_allow_html=True)
        return

    # logged in UI
    st.markdown(f"""<div style="background: linear-gradient(45deg,#e74c3c,#c0392b); padding:20px;border-radius:15px;color:white;">
                   <h2>👋 Welcome back, {st.session_state.get('email','User')}!</h2></div>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col3:
        if st.button('🚪 Logout', use_container_width=True):
            st.session_state.clear()
            st.rerun()

    ecg = get_ecg_model()

    st.markdown("### 📤 Upload Your ECG Image")

    # ---------- IMPORTANT: accept_multiple_files=True to avoid axios 400 ----------
    uploaded_files = st.file_uploader("Choose an ECG image file", type=['png','jpg','jpeg'], accept_multiple_files=True)

    # session_state keys
    if 'last_upload_hash' not in st.session_state:
        st.session_state['last_upload_hash'] = None
    if 'last_upload_result' not in st.session_state:
        st.session_state['last_upload_result'] = None
    if 'upload_error' not in st.session_state:
        st.session_state['upload_error'] = None

    if uploaded_files:
        # pick first file (you can change to allow batch processing)
        uploaded_file = uploaded_files[0]

        # compute hash for dedup
        try:
            buf = uploaded_file.getbuffer()
        except Exception:
            buf = uploaded_file.read()
        file_hash = hashlib.sha256(buf).hexdigest()

        # if same file processed, show cached result
        if st.session_state['last_upload_hash'] == file_hash and st.session_state['last_upload_result'] is not None:
            st.success("✅ This file was already analyzed in this session.")
            st.info(st.session_state['last_upload_result'])
        else:
            # new file -> run pipeline once
            progress_bar = st.progress(0)
            status = st.empty()
            try:
                status.text("🔄 Saving uploaded image...")
                progress_bar.progress(5)
                saved_path, safe_name, _ = _save_uploaded_file(uploaded_file)
                logger.info("Saved upload to %s", saved_path)
                progress_bar.progress(15)

                # cleanup old scaled CSVs in deployment folder to avoid stale/collision
                # (these CSVs are created by your Ecg.SignalExtraction_Scaling)
                deployment_dir = os.path.dirname(ecg.__module__.__file__) if hasattr(ecg, '__module__') else os.getcwd()
                # But safer: use ecg.base_dir if provided
                try:
                    base_dir = ecg.base_dir
                except Exception:
                    base_dir = deployment_dir
                for f in os.listdir(base_dir):
                    if f.startswith("Scaled_1DLead_") and f.endswith(".csv"):
                        try:
                            os.remove(os.path.join(base_dir, f))
                        except Exception:
                            pass

                progress_bar.progress(25)
                status.text("🔄 Loading image into pipeline...")
                ecg_user_image_read = ecg.getImage(saved_path)
                progress_bar.progress(35)
                status.text("🎨 Converting to grayscale...")
                ecg_user_gray_image_read = ecg.GrayImgae(ecg_user_image_read)
                progress_bar.progress(45)
                status.text("📊 Dividing ECG leads...")
                dividing_leads = ecg.DividingLeads(ecg_user_image_read)
                progress_bar.progress(60)
                status.text("⚙️ Preprocessing leads...")
                ecg.PreprocessingLeads(dividing_leads)
                progress_bar.progress(70)
                status.text("📡 Extracting signals & scaling...")
                ecg.SignalExtraction_Scaling(dividing_leads)
                progress_bar.progress(80)
                status.text("🔄 Combining 1D signals...")
                ecg_1dsignal = ecg.CombineConvert1Dsignal()
                progress_bar.progress(85)
                status.text("🧮 Dimensionality reduction...")
                ecg_final = ecg.DimensionalReduciton(ecg_1dsignal)
                progress_bar.progress(95)
                status.text("🤖 Predicting...")
                ecg_model = ecg.ModelLoad_predict(ecg_final)
                progress_bar.progress(100)
                status.text("✅ Analysis complete!")

                # cache result in session
                st.session_state['last_upload_hash'] = file_hash
                st.session_state['last_upload_result'] = ecg_model
                st.session_state['upload_error'] = None

                # display styled result (same as before)
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
                    <h2 style="color: white; margin: 0 0 15px 0;">{result_icon} AI DIAGNOSIS RESULT</h2>
                    <p style="font-size: 1.3em; margin: 0; font-weight: bold;">{ecg_model}</p>
                </div>
                """, unsafe_allow_html=True)

                # save to DB (optional)
                try:
                    preds = db['predictions']
                    pred_doc = {'prediction_id': str(uuid.uuid4()), 'user_email': st.session_state.get('email'),
                                'prediction': str(ecg_model), 'file_name': safe_name, 'timestamp': datetime.utcnow()}
                    preds.insert_one(pred_doc)
                    st.info('✅ Prediction saved to database')
                except Exception as e:
                    logger.warning("Could not save to DB: %s", e)

            except Exception as e:
                tb = traceback.format_exc()
                logger.error("Processing error: %s", tb)
                st.error("❌ An error occurred during processing. See traceback below.")
                st.code(tb, language="python")
                # reset session cached result for this bad upload
                st.session_state['last_upload_hash'] = None
                st.session_state['last_upload_result'] = None
                st.session_state['upload_error'] = str(e)
            finally:
                try:
                    progress_bar.empty()
                    status.empty()
                except Exception:
                    pass

    else:
        # instructions when no upload
        st.markdown("""
        <div style="background: white; padding: 40px; border-radius: 15px;">
            <h3 style="text-align:center;">🚀 How to Use PulseAI</h3>
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(250px,1fr)); gap:20px;">
                <div style="text-align:center;">
                    <div style="font-size:3em;">📤</div><h4>1. Upload ECG</h4><p>Upload a clear ECG image</p>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:3em;">🤖</div><h4>2. AI Analysis</h4><p>We process your ECG</p>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:3em;">📊</div><h4>3. Get Results</h4><p>Receive analysis & recommendations</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()
