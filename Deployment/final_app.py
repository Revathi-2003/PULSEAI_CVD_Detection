import streamlit as st
from Ecg import ECG
from auth import get_db, create_user, verify_user
import os
import uuid
from datetime import datetime
import base64
import traceback
import hashlib
import logging

logging.basicConfig(level=logging.DEBUG)

# -------------------- Helpers --------------------------

def get_ecg_model():
    return ECG()

@st.cache_resource
def get_database():
    return get_db()

def get_base64_of_bin_file(png_file):
    with open(png_file, "rb") as f:
        return base64.b64encode(f.read()).decode()

# -------------------------------------------------------
#  UI COMPONENTS (UNMODIFIED FROM YOUR ORIGINAL)
# -------------------------------------------------------

def add_logo():
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #e74c3c; font-size: 3.5em; margin: 0; font-weight: bold;">
            ❤️ PulseAI
        </h1>
        <p style="color: #7f8c8d; font-size: 1.2em; margin: 5px 0;">
            AI-Powered Cardiovascular Detection
        </p>
        <p style="color: #95a5a6; font-size: 1em; margin: 0;">
            Advanced ECG Analysis for Early Heart Disease Detection
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
        <p style="font-size: 1.1em; margin: 0; opacity: 0.8;">
            - T.E. Kalem
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
            <h3 style="color: #2c3e50;">AI-Powered Analysis</h3>
            <p style="color: #7f8c8d;">Advanced algorithms for accurate ECG interpretation</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #f8f9fa; 
                    border-radius: 10px; margin: 10px 0;">
            <div style="font-size: 3em; margin-bottom: 15px;">⚡</div>
            <h3 style="color: #2c3e50;">Instant Results</h3>
            <p style="color: #7f8c8d;">Get analysis in seconds</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #f8f9fa;
                    border-radius: 10px; margin: 10px 0;">
            <div style="font-size: 3em; margin-bottom: 15px;">🛡️</div>
            <h3 style="color: #2c3e50;">Secure</h3>
            <p style="color: #7f8c8d;">Your health data is protected</p>
        </div>
        """, unsafe_allow_html=True)

def add_doctor_quote():
    st.markdown("""
    <div style="background: #ecf0f1; padding: 30px; border-radius: 15px;
                margin: 30px 0; border-left: 5px solid #e74c3c;">
        <p style="font-size: 1.2em; font-style: italic;">
            "Early detection of cardiovascular diseases saves lives."
        </p>
        <p style="color: #7f8c8d; font-weight: bold;">
            - Dr. Sarah Johnson
        </p>
    </div>
    """, unsafe_allow_html=True)

def create_auth_tabs():
    st.markdown("""
    <style>
    .stTabs [aria-selected="true"] {
        background-color: #e74c3c; color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    return st.tabs(["🔐 Login", "📝 Register"])

def login_ui(db):
    tab1, tab2 = create_auth_tabs()

    with tab1:
        email = st.text_input('📧 Email', key='login_email')
        password = st.text_input('🔒 Password', type='password', key='login_password')
        if st.button("🚀 Login"):
            if verify_user(db, email, password):
                st.session_state['logged_in'] = True
                st.session_state['email'] = email
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_email = st.text_input('📧 Email')
        new_username = st.text_input('👤 Username')
        new_password = st.text_input('🔒 Password', type='password')
        if st.button("✨ Register"):
            if create_user(db, new_email, new_username, new_password):
                st.success("Account created. Please login.")
            else:
                st.error("Account already exists")


# -------------------- File save helper --------------------

def _save_uploaded_file_to_disk(uploaded_file):
    file_bytes = uploaded_file.getbuffer()
    filename = getattr(uploaded_file, 'name', f'upload_{uuid.uuid4().hex}.png')
    filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.'))
    if not filename:
        filename = f'upload_{uuid.uuid4().hex}.png'
    uploads_dir = os.path.join(os.getcwd(), 'uploaded_files')
    os.makedirs(uploads_dir, exist_ok=True)
    saved_path = os.path.join(uploads_dir, filename)
    with open(saved_path, 'wb') as f:
        f.write(file_bytes)
    return saved_path, file_bytes

# ----------------------------------------------------------
#                     MAIN APP
# ----------------------------------------------------------

def main():
    st.set_page_config(page_title="PulseAI", page_icon="❤️", layout="wide")
    add_logo()

    db = get_database()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        add_hero_section()
        add_features_section()
        add_doctor_quote()
        login_ui(db)
        return

    # Logged-in section
    st.markdown(f"<h2>👋 Welcome {st.session_state['email']}</h2>", unsafe_allow_html=True)

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    ecg = get_ecg_model()

    st.markdown("### 📤 Upload Your ECG Image")
    uploaded_file = st.file_uploader("Choose file", type=['png','jpg','jpeg'])

    # State keys
    if 'last_upload_hash' not in st.session_state:
        st.session_state['last_upload_hash'] = None
    if 'last_upload_result' not in st.session_state:
        st.session_state['last_upload_result'] = None

    if uploaded_file:
        # hash for dedupe
        file_bytes = uploaded_file.getbuffer()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        if st.session_state['last_upload_hash'] == file_hash:
            st.info("This file is already analysed.")
            st.success(st.session_state['last_upload_result'])
            return

        # process new file
        progress = st.progress(0)
        status = st.empty()

        try:
            status.text("Saving file...")
            saved_path, _ = _save_uploaded_file_to_disk(uploaded_file)
            progress.progress(10)

            # CLEANUP FIX ✔✔✔
            deployment_dir = os.path.join(os.getcwd(), "Deployment")
            for f in os.listdir(deployment_dir):
                if f.startswith("Scaled_1DLead_") and f.endswith(".csv"):
                    try:
                        os.remove(os.path.join(deployment_dir, f))
                    except:
                        pass

            progress.progress(20)
            status.text("Loading image...")
            img = ecg.getImage(saved_path)

            progress.progress(40)
            status.text("Gray scaling...")
            gray = ecg.GrayImgae(img)

            progress.progress(55)
            status.text("Dividing leads...")
            leads = ecg.DividingLeads(img)

            progress.progress(65)
            status.text("Preprocessing leads...")
            ecg.PreprocessingLeads(leads)

            progress.progress(75)
            status.text("Signal extraction...")
            ecg.SignalExtraction_Scaling(leads)

            progress.progress(82)
            status.text("Combining signals...")
            df1d = ecg.CombineConvert1Dsignal()

            progress.progress(90)
            status.text("Dimensionality reduction...")
            final_df = ecg.DimensionalReduciton(df1d)

            progress.progress(97)
            status.text("Predicting...")
            result = ecg.ModelLoad_predict(final_df)

            progress.progress(100)
            status.text("Done ✔")

            st.session_state['last_upload_hash'] = file_hash
            st.session_state['last_upload_result'] = result

            st.success(result)

            preds = db['predictions']
            preds.insert_one({
                "prediction_id": str(uuid.uuid4()),
                "user_email": st.session_state['email'],
                "prediction": result,
                "file_name": os.path.basename(saved_path),
                "timestamp": datetime.utcnow()
            })

        except Exception as e:
            tb = traceback.format_exc()
            st.error("Processing failed ❌")
            st.code(tb, language="python")

    else:
        st.info("Upload an ECG image to begin.")

if __name__ == "__main__":
    main()
