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

# --- logging for debugging ---
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

# ---------- UI helpers ----------
def add_logo():
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #e74c3c; font-size: 3.2em; margin: 0; font-weight: 800;">
            ❤️ PulseAI
        </h1>
        <p style="color: #7f8c8d; font-size: 1.05em; margin: 5px 0;">
            AI-Powered Cardiovascular Detection
        </p>
    </div>
    """, unsafe_allow_html=True)

def add_hero_section():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 36px 20px; border-radius: 14px; margin: 18px 0;
                text-align: center; color: white;">
        <h2 style="color: white; font-size: 2.2em; margin: 0 0 10px 0;">
            🩺 Your Heart Health Matters
        </h2>
        <p style="font-size: 1.05em; margin: 0;">
            Early ECG analysis with AI to help flag potential cardiac issues.
        </p>
    </div>
    """, unsafe_allow_html=True)

def add_features_section():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 18px; background: #f8f9fa;
                    border-radius: 8px; margin: 8px 0;">
            <div style="font-size: 2.4em; margin-bottom: 8px;">🤖</div>
            <h4 style="margin: 0 0 6px 0;">AI-Powered Analysis</h4>
            <p style="color:#7f8c8d; margin: 0;">Uses ML to interpret ECGs quickly</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 18px; background: #f8f9fa;
                    border-radius: 8px; margin: 8px 0;">
            <div style="font-size: 2.4em; margin-bottom: 8px;">⚡</div>
            <h4 style="margin: 0 0 6px 0;">Instant Results</h4>
            <p style="color:#7f8c8d; margin: 0;">Fast pipeline — one upload and get a result</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 18px; background: #f8f9fa;
                    border-radius: 8px; margin: 8px 0;">
            <div style="font-size: 2.4em; margin-bottom: 8px;">🛡️</div>
            <h4 style="margin: 0 0 6px 0;">Secure & Private</h4>
            <p style="color:#7f8c8d; margin: 0;">Your files and results are handled privately</p>
        </div>
        """, unsafe_allow_html=True)

def add_doctor_quote():
    st.markdown("""
    <div style="background: #ecf0f1; padding: 18px; border-radius: 10px;
                margin: 20px 0; border-left: 5px solid #e74c3c;">
        <div style="display:flex;align-items:center;">
            <div style="font-size: 2.6em; margin-right: 12px;">👨‍⚕️</div>
            <div>
                <p style="margin:0 0 6px 0; font-style:italic;">
                    "Prevention is better than cure. Early detection of cardiovascular issues can save lives."
                </p>
                <p style="margin:0; font-weight:bold; color:#7f8c8d;">- Dr. Sarah Johnson</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_auth_tabs():
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { height: 44px; background: #f0f2f6; border-radius: 8px; }
    .stTabs [aria-selected="true"] { background: #e74c3c; color: white; }
    </style>
    """, unsafe_allow_html=True)
    return st.tabs(["🔐 Login", "📝 Register"])

def login_ui(db):
    tab1, tab2 = create_auth_tabs()
    with tab1:
        st.markdown("<div style='background:white;padding:18px;border-radius:10px;margin-bottom:10px;'><h3 style='text-align:center'>Welcome Back</h3></div>", unsafe_allow_html=True)
        email = st.text_input('📧 Email Address', key='login_email')
        password = st.text_input('🔒 Password', type='password', key='login_password')
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button('🚀 Login to PulseAI', use_container_width=True):
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
                        st.success('🎉 Login successful!')
                        st.rerun()
                    else:
                        st.error('❌ Invalid credentials.')
                else:
                    st.warning('⚠️ Fill both fields.')

    with tab2:
        st.markdown("<div style='background:white;padding:18px;border-radius:10px;margin-bottom:10px;'><h3 style='text-align:center'>Create Account</h3></div>", unsafe_allow_html=True)
        new_email = st.text_input('📧 Email Address', key='reg_email')
        new_username = st.text_input('👤 Username', key='reg_username')
        new_password = st.text_input('🔒 Password', type='password', key='reg_password')
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button('✨ Create Account', use_container_width=True):
                if new_email and new_password:
                    ok = create_user(db, new_email, new_username or new_email.split('@')[0], new_password)
                    if ok:
                        st.success('🎉 Account created successfully! Please login.')
                    else:
                        st.error('❌ Account already exists.')
                else:
                    st.warning('⚠️ Provide email and password.')

# ---------- helpers to save uploaded file ----------
def _sanitize_filename(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in ('-', '_', '.')).strip()
    if not safe or safe.startswith('.'):
        safe = f"upload_{uuid.uuid4().hex}.jpg"
    return safe

def _save_uploaded_file(uploaded_file) -> tuple[str, str, bytes]:
    try:
        b = uploaded_file.getbuffer()
    except Exception:
        b = uploaded_file.read()
    safe_name = _sanitize_filename(getattr(uploaded_file, "name", f"upload_{uuid.uuid4().hex}.jpg"))
    uploads_dir = os.path.join(os.getcwd(), 'uploaded_files')
    os.makedirs(uploads_dir, exist_ok=True)
    saved_path = os.path.join(uploads_dir, safe_name)
    with open(saved_path, 'wb') as f:
        f.write(b)
    return saved_path, safe_name, b

# ---------- Main ----------
def main():
    st.set_page_config(page_title="PulseAI - Cardiovascular Detection", page_icon="❤️", layout='wide', initial_sidebar_state='collapsed')
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .stButton > button { background: linear-gradient(45deg, #e74c3c, #c0392b); color: white; border-radius: 20px; }
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
        st.markdown("<div style='text-align:center;padding:36px 0;color:#7f8c8d;'>© 2024 PulseAI</div>", unsafe_allow_html=True)
        return

    # Logged-in UI
    st.markdown(f"""<div style="background: linear-gradient(45deg,#e74c3c,#c0392b); padding:18px;border-radius:12px;color:white;">
                   <h3 style="margin:0">👋 Welcome, {st.session_state.get('email','User')}!</h3></div>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col3:
        if st.button('🚪 Logout', use_container_width=True):
            st.session_state.clear()
            st.rerun()

    ecg = get_ecg_model()

    st.markdown("### 📤 Upload Your ECG Image")
    # accept_multiple_files True helps avoid client-side 400 in some cloud environments
    uploaded_files = st.file_uploader("Choose an ECG image file", type=['png','jpg','jpeg'], accept_multiple_files=True)

    # session caches
    if 'last_upload_hash' not in st.session_state:
        st.session_state['last_upload_hash'] = None
    if 'last_upload_result' not in st.session_state:
        st.session_state['last_upload_result'] = None
    if 'upload_error' not in st.session_state:
        st.session_state['upload_error'] = None

    if uploaded_files:
        uploaded_file = uploaded_files[0]  # process only the first
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
                status.text("🔄 Saving uploaded file...")
                progress.progress(5)
                saved_path, safe_name, _ = _save_uploaded_file(uploaded_file)
                logger.info("Saved upload to %s", saved_path)
                progress.progress(15)

                # delete stale CSVs from ecg.base_dir (if present)
                base_dir = getattr(ecg, "base_dir", os.getcwd())
                for f in os.listdir(base_dir):
                    if f.startswith("Scaled_1DLead_") and f.endswith(".csv"):
                        try:
                            os.remove(os.path.join(base_dir, f))
                        except Exception:
                            pass

                progress.progress(25)
                status.text("🔄 Running pipeline...")

                ecg_user_image = ecg.getImage(saved_path)
                progress.progress(35)
                status.text("🎨 Converting to grayscale...")
                ecg_user_gray = ecg.GrayImgae(ecg_user_image)
                progress.progress(45)
                status.text("📊 Dividing leads...")
                dividing_leads = ecg.DividingLeads(ecg_user_image)

                # show preview images if they were created by pipeline
                lead12_path = os.path.join(ecg.base_dir, "Leads_1-12_figure.png")
                lead13_path = os.path.join(ecg.base_dir, "Long_Lead_13_figure.png")
                if os.path.isfile(lead12_path) and os.path.isfile(lead13_path):
                    with st.expander("📈 ECG Lead Division (previews)", expanded=False):
                        st.image(lead12_path)
                        st.image(lead13_path)

                progress.progress(60)
                status.text("⚙️ Preprocessing leads...")
                ecg.PreprocessingLeads(dividing_leads)

                pre12_path = os.path.join(ecg.base_dir, "Preprossed_Leads_1-12_figure.png")
                pre13_path = os.path.join(ecg.base_dir, "Preprossed_Leads_13_figure.png")
                if os.path.isfile(pre12_path) and os.path.isfile(pre13_path):
                    with st.expander("🔧 Preprocessed Leads", expanded=False):
                        st.image(pre12_path)
                        st.image(pre13_path)

                progress.progress(75)
                status.text("📡 Extracting & scaling signals...")
                ecg.SignalExtraction_Scaling(dividing_leads)

                contour_path = os.path.join(ecg.base_dir, "Contour_Leads_1-12_figure.png")
                if os.path.isfile(contour_path):
                    with st.expander("📊 Signal Contours", expanded=False):
                        st.image(contour_path)

                progress.progress(85)
                status.text("🔄 Combining 1D signals...")
                ecg_1d = ecg.CombineConvert1Dsignal()
                with st.expander("📈 1D Signals", expanded=False):
                    st.write(ecg_1d)

                progress.progress(90)
                status.text("🧮 Dimensionality reduction...")
                ecg_final = ecg.DimensionalReduciton(ecg_1d)
                with st.expander("🎯 Reduced features", expanded=False):
                    st.write(ecg_final.head())

                progress.progress(95)
                status.text("🤖 Predicting...")
                prediction_text = ecg.ModelLoad_predict(ecg_final)
                progress.progress(100)
                status.text("✅ Analysis complete!")

                # cache result
                st.session_state['last_upload_hash'] = file_hash
                st.session_state['last_upload_result'] = prediction_text
                st.session_state['upload_error'] = None

                # show result block
                if "Normal" in prediction_text:
                    color, icon = "#27ae60", "✅"
                elif "Myocardial Infarction" in prediction_text:
                    color, icon = "#e74c3c", "⚠️"
                elif "Abnormal Heartbeat" in prediction_text:
                    color, icon = "#f39c12", "🔔"
                else:
                    color, icon = "#9b59b6", "📋"

                st.markdown(f"""
                <div style="background:{color}; padding:20px; border-radius:12px; margin:18px 0; color:white;">
                    <h3 style="margin:0;">{icon} AI DIAGNOSIS RESULT</h3>
                    <p style="font-weight:bold; margin:8px 0 0 0;">{prediction_text}</p>
                </div>
                """, unsafe_allow_html=True)

                # save prediction record to DB
                try:
                    preds = db['predictions']
                    pred_doc = {'prediction_id': str(uuid.uuid4()), 'user_email': st.session_state.get('email'), 'prediction': str(prediction_text), 'file_name': safe_name, 'timestamp': datetime.utcnow()}
                    preds.insert_one(pred_doc)
                    st.info("✅ Prediction saved to database")
                except Exception as e:
                    logger.warning("DB save failed: %s", e)

            except Exception as e:
                tb = traceback.format_exc()
                logger.error("Processing error: %s", tb)
                st.error("❌ An error occurred during processing. See details below.")
                st.code(tb, language="python")
                st.session_state['last_upload_hash'] = None
                st.session_state['last_upload_result'] = None
                st.session_state['upload_error'] = str(e)
            finally:
                try:
                    progress.empty()
                    status.empty()
                except Exception:
                    pass

    else:
        st.markdown("""
        <div style="background:white;padding:20px;border-radius:10px;">
            <h4 style="text-align:center;">How to use PulseAI</h4>
            <ol>
                <li>Login or create an account.</li>
                <li>Upload a clear ECG image (PNG/JPG/JPEG).</li>
                <li>Wait for the pipeline to run — the app shows progress and previews.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
