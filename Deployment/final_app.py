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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pulseai")

APP_TITLE = "PulseAI"
APP_SUBTITLE = "AI-Powered Cardiovascular Detection"

def get_ecg_model():
    return ECG()

@st.cache_resource
def get_database():
    return get_db()

def add_logo():
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #e74c3c; font-size: 3.2em; margin: 0; font-weight: bold;">❤️ PulseAI</h1>
        <p style="color: #7f8c8d; font-size: 1.1em; margin: 5px 0;">AI-Powered Cardiovascular Detection</p>
    </div>
    """, unsafe_allow_html=True)

def add_hero_section():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px; border-radius: 12px; margin: 20px 0; color: white; text-align:center;">
        <h2 style="margin:0">🩺 Your Heart Health Matters</h2>
        <p style="opacity:0.9">"The heart is the only broken instrument that works perfectly."</p>
    </div>
    """, unsafe_allow_html=True)

def add_features_section():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div style='text-align:center; padding:10px;'><div style='font-size:2em'>🤖</div><b>AI-Powered Analysis</b></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align:center; padding:10px;'><div style='font-size:2em'>⚡</div><b>Instant Results</b></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='text-align:center; padding:10px;'><div style='font-size:2em'>🛡️</div><b>Secure & Private</b></div>", unsafe_allow_html=True)

def add_doctor_quote():
    st.markdown("""
    <div style="background:#ecf0f1; padding:20px; border-radius:10px; margin:20px 0;">
      <strong>👨‍⚕️ Dr. Sarah Johnson:</strong>
      <em> Prevention is better than cure. Early detection of cardiovascular diseases can save lives.</em>
    </div>
    """, unsafe_allow_html=True)

def create_auth_tabs():
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background:#e74c3c; color:white; }
    </style>
    """, unsafe_allow_html=True)
    return st.tabs(["🔐 Login", "📝 Register"])

def login_ui(db):
    tab1, tab2 = create_auth_tabs()
    with tab1:
        email = st.text_input('📧 Email Address', key='login_email')
        password = st.text_input('🔒 Password', type='password', key='login_password')
        if st.button('🚀 Login to PulseAI'):
            if email and password:
                if verify_user(db, email, password):
                    st.session_state['logged_in'] = True
                    st.session_state['email'] = email
                    try:
                        sess = db['sessions']
                        sess.insert_one({'session_id': str(uuid.uuid4()), 'user_email': email, 'started_at': datetime.utcnow()})
                    except Exception:
                        pass
                    st.success('Logged in')
                    st.experimental_rerun()
                else:
                    st.error('Invalid credentials')
            else:
                st.warning('Fill email and password')
    with tab2:
        new_email = st.text_input('📧 Email Address', key='reg_email')
        new_username = st.text_input('👤 Username', key='reg_username')
        new_password = st.text_input('🔒 Password', type='password', key='reg_password')
        if st.button('✨ Create Account'):
            if new_email and new_password:
                ok = create_user(db, new_email, new_username or new_email.split('@')[0], new_password)
                if ok:
                    st.success('Account created, please login')
                else:
                    st.error('Account exists')
            else:
                st.warning('Fill email and password')

def _sanitize_filename(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in ('-', '_', '.'))
    if not safe or safe.startswith('.'):
        safe = f"upload_{uuid.uuid4().hex}.jpg"
    return safe

def _save_uploaded_file(uploaded_file) -> tuple:
    try:
        b = uploaded_file.getbuffer()
    except Exception:
        b = uploaded_file.read()
    safe_name = _sanitize_filename(uploaded_file.name or f"upload_{uuid.uuid4().hex}.jpg")
    uploads_dir = os.path.join(os.getcwd(), 'uploaded_files')
    os.makedirs(uploads_dir, exist_ok=True)
    saved_path = os.path.join(uploads_dir, safe_name)
    with open(saved_path, 'wb') as f:
        f.write(b)
    return saved_path, safe_name, b

def main():
    st.set_page_config(page_title="PulseAI - Cardiovascular Detection", page_icon="❤️", layout='wide')
    st.markdown("<style>.stApp{background:linear-gradient(135deg,#f5f7fa,#c3cfe2)}</style>", unsafe_allow_html=True)
    add_logo()
    db = get_database()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if not st.session_state['logged_in']:
        add_hero_section(); add_features_section(); add_doctor_quote(); login_ui(db)
        st.markdown("<div style='text-align:center; color:#7f8c8d; padding:20px'>© 2024 PulseAI</div>", unsafe_allow_html=True)
        return

    st.markdown(f"<div style='background:linear-gradient(45deg,#e74c3c,#c0392b); padding:15px; border-radius:12px; color:white;'>👋 Welcome back, {st.session_state.get('email','User')}!</div>", unsafe_allow_html=True)
    if st.button('🚪 Logout'):
        st.session_state.clear()
        st.experimental_rerun()

    ecg = get_ecg_model()

    st.markdown("### 📤 Upload Your ECG Image")
    # accept multiple files to avoid axios 400 on some Streamlit deployments
    uploaded_files = st.file_uploader("Choose ECG image(s)", type=['png','jpg','jpeg'], accept_multiple_files=True)

    # session caching keys
    st.session_state.setdefault('last_upload_hash', None)
    st.session_state.setdefault('last_upload_result', None)
    st.session_state.setdefault('upload_error', None)

    if uploaded_files:
        uploaded_file = uploaded_files[0]  # currently process first file
        try:
            buf = uploaded_file.getbuffer()
        except Exception:
            buf = uploaded_file.read()
        file_hash = hashlib.sha256(buf).hexdigest()

        if st.session_state['last_upload_hash'] == file_hash and st.session_state['last_upload_result'] is not None:
            st.success("✅ This file has already been analyzed.")
            st.info(st.session_state['last_upload_result'])
        else:
            progress = st.progress(0)
            status = st.empty()
            try:
                status.text("🔄 Saving uploaded image...")
                progress.progress(5)
                saved_path, safe_name, _ = _save_uploaded_file(uploaded_file)
                logger.info("saved upload: %s", saved_path)
                progress.progress(15)

                # clean any previous scaled CSVs in ecg.base_dir
                try:
                    base_dir = ecg.base_dir
                except Exception:
                    base_dir = os.getcwd()
                for f in os.listdir(base_dir):
                    if f.startswith("Scaled_1DLead_") and f.endswith(".csv"):
                        try:
                            os.remove(os.path.join(base_dir, f))
                        except Exception:
                            pass

                progress.progress(25)
                status.text("🔄 Loading image into pipeline...")
                ecg_img = ecg.getImage(saved_path)
                progress.progress(35)
                status.text("🎨 Converting to grayscale...")
                ecg_gray = ecg.GrayImgae(ecg_img)
                with st.expander("🔍 Gray Scale Image", expanded=False):
                    st.image(ecg_gray, use_column_width=True)
                progress.progress(45)
                status.text("📊 Dividing ECG leads...")
                dividing_leads = ecg.DividingLeads(ecg_img)

                # display lead previews safely
                with st.expander("📈 ECG Lead Division", expanded=False):
                    leads12 = ecg._path("Leads_1-12_figure.png")
                    longlead = ecg._path("Long_Lead_13_figure.png")
                    if os.path.isfile(leads12):
                        st.image(leads12, caption='Leads 1-12 preview', use_column_width=True)
                    else:
                        st.info("Leads preview not available.")
                    if os.path.isfile(longlead):
                        st.image(longlead, caption='Long Lead preview', use_column_width=True)

                progress.progress(60)
                status.text("⚙️ Preprocessing leads...")
                ecg.PreprocessingLeads(dividing_leads)
                with st.expander("🔧 Preprocessed Leads", expanded=False):
                    pre12 = ecg._path("Preprocessed_Leads_1-12_figure.png")
                    pre13 = ecg._path("Preprocessed_Leads_13_figure.png")
                    if os.path.isfile(pre12):
                        st.image(pre12, caption='Preprocessed leads 1-12', use_column_width=True)
                    else:
                        st.info("Preprocessed 12-lead preview not available.")
                    if os.path.isfile(pre13):
                        st.image(pre13, caption='Preprocessed long lead', use_column_width=True)

                progress.progress(70)
                status.text("📡 Extracting signals & scaling...")
                ecg.SignalExtraction_Scaling(dividing_leads)
                with st.expander("📊 Signal Contours", expanded=False):
                    contour_img = ecg._path("Contour_Leads_1-12_figure.png")
                    if os.path.isfile(contour_img):
                        st.image(contour_img, caption='Extracted contours', use_column_width=True)
                    else:
                        st.info("Contour preview not available.")

                progress.progress(80)
                status.text("🔄 Combining 1D signals...")
                try:
                    ecg_1dsignal = ecg.CombineConvert1Dsignal()
                except FileNotFoundError as e:
                    st.error("Could not generate 1D signals — signal extraction may have failed.")
                    st.code(str(e))
                    progress.empty(); status.empty()
                    st.session_state['upload_error'] = str(e)
                    return

                with st.expander("📈 1D Signals (first rows)", expanded=False):
                    st.write(ecg_1dsignal.head())

                progress.progress(90)
                status.text("🧮 Dimensionality reduction...")
                try:
                    ecg_final = ecg.DimensionalReduciton(ecg_1dsignal)
                except FileNotFoundError as e:
                    st.error("Missing PCA model on server.")
                    st.code(str(e))
                    progress.empty(); status.empty()
                    st.session_state['upload_error'] = str(e)
                    return

                with st.expander("🎯 Dimensional Reduction", expanded=False):
                    st.write(ecg_final.head())

                progress.progress(95)
                status.text("🤖 Predicting...")
                try:
                    ecg_model = ecg.ModelLoad_predict(ecg_final)
                except FileNotFoundError as e:
                    st.error("Classifier model missing on server.")
                    st.code(str(e))
                    progress.empty(); status.empty()
                    st.session_state['upload_error'] = str(e)
                    return

                progress.progress(100)
                status.text("✅ Analysis complete!")

                # cache result
                st.session_state['last_upload_hash'] = file_hash
                st.session_state['last_upload_result'] = ecg_model
                st.session_state['upload_error'] = None

                # styled result
                if "Normal" in ecg_model:
                    result_color = "#27ae60"; result_icon = "✅"
                elif "Myocardial Infarction" in ecg_model:
                    result_color = "#e74c3c"; result_icon = "⚠️"
                elif "Abnormal Heartbeat" in ecg_model:
                    result_color = "#f39c12"; result_icon = "🔔"
                else:
                    result_color = "#9b59b6"; result_icon = "📋"

                st.markdown(f"""
                <div style="background:{result_color}; padding:20px; border-radius:10px; color:white;">
                    <h3 style="margin:0">{result_icon} AI DIAGNOSIS RESULT</h3>
                    <p style="font-weight:bold; margin:8px 0 0 0;">{ecg_model}</p>
                </div>
                """, unsafe_allow_html=True)

                # follow-ups / recommendation
                if "Normal" in ecg_model:
                    st.success("🎉 Great news! Your ECG appears normal.")
                elif "Myocardial Infarction" in ecg_model:
                    st.error("🚨 Possible myocardial infarction. Seek medical attention.")
                elif "Abnormal Heartbeat" in ecg_model:
                    st.warning("⚠️ Abnormal heartbeat detected. Consult a cardiologist.")
                else:
                    st.info("📋 History of MI flagged. Follow-up recommended.")

                try:
                    preds = db['predictions']
                    preds.insert_one({
                        'prediction_id': str(uuid.uuid4()),
                        'user_email': st.session_state.get('email'),
                        'prediction': str(ecg_model),
                        'file_name': safe_name,
                        'timestamp': datetime.utcnow()
                    })
                    st.info("Saved prediction to DB")
                except Exception as e:
                    logger.warning("DB save failed: %s", e)

            except Exception as e:
                tb = traceback.format_exc()
                logger.error("Processing error: %s", tb)
                st.error("❌ An error occurred during processing. See traceback below.")
                st.code(tb, language="python")
                st.session_state['last_upload_hash'] = None
                st.session_state['last_upload_result'] = None
                st.session_state['upload_error'] = str(e)
            finally:
                try:
                    progress.empty(); status.empty()
                except Exception:
                    pass

    else:
        st.markdown("""
        <div style="background:white; padding:20px; border-radius:8px;">
          <h3 style="text-align:center">🚀 How to Use PulseAI</h3>
          <ol>
            <li>Upload a clear ECG image (PNG/JPG/JPEG)</li>
            <li>Wait for the pipeline to run (you'll see progress)</li>
            <li>Read the result and consult a clinician for action</li>
          </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
