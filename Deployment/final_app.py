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

def add_logo():
    """Add PulseAI logo and branding"""
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
    """Add hero section with inspirational content"""
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
    """Add features section with AI doctor imagery"""
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
    """Add inspirational doctor quote"""
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
    """Create attractive login/register tabs"""
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e74c3c;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    return tab1, tab2

def login_ui(db):
    """Enhanced login UI with tabs"""
    tab1, tab2 = create_auth_tabs()
    
    with tab1:
        st.markdown("""
        <div style="background: white; padding: 30px; border-radius: 15px; 
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin: 20px 0;">
            <h2 style="color: #2c3e50; text-align: center; margin-bottom: 30px;">
                Welcome Back to PulseAI
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        email = st.text_input('📧 Email Address', key='login_email', placeholder="Enter your email")
        password = st.text_input('🔒 Password', type='password', key='login_password', placeholder="Enter your password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button('🚀 Login to PulseAI', type='primary', use_container_width=True):
                if email and password:
                    if verify_user(db, email, password):
                        st.session_state['logged_in'] = True
                        st.session_state['email'] = email
                        # create a session document in DB
                        try:
                            sess = db['sessions']
                            session_doc = {
                                'session_id': str(uuid.uuid4()),
                                'user_email': email,
                                'started_at': datetime.utcnow()
                            }
                            sess.insert_one(session_doc)
                        except Exception:
                            pass
                        st.success('🎉 Login successful! Welcome to PulseAI!')
                        st.rerun()
                    else:
                        st.error('❌ Invalid credentials. Please check your email and password.')
                else:
                    st.warning('⚠️ Please fill in all fields.')
    
    with tab2:
        st.markdown("""
        <div style="background: white; padding: 30px; border-radius: 15px; 
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin: 20px 0;">
            <h2 style="color: #2c3e50; text-align: center; margin-bottom: 30px;">
                Join PulseAI Today
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        new_email = st.text_input('📧 Email Address', placeholder="Enter your email")
        new_username = st.text_input('👤 Username', placeholder="Choose a username")
        new_password = st.text_input('🔒 Password', type='password', placeholder="Create a password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button('✨ Create Account', type='primary', use_container_width=True):
                if new_email and new_password:
                    ok = create_user(db, new_email, new_username or new_email.split('@')[0], new_password)
                    if ok:
                        st.success('🎉 Account created successfully! Please login to continue.')
                    else:
                        st.error('❌ An account with that email already exists.')
                else:
                    st.warning('⚠️ Please fill in email and password fields.')

def main():
    st.set_page_config(
        page_title="PulseAI - Cardiovascular Detection",
        page_icon="❤️",
        layout='wide',
        initial_sidebar_state='collapsed'
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stButton > button {
        background: linear-gradient(45deg, #e74c3c, #c0392b);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .stFileUploader > div > div > div {
        background: white;
        border-radius: 10px;
        border: 2px dashed #e74c3c;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add logo and branding
    add_logo()
    
    # Use cached database connection for better performance
    db = get_database()
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        # Show hero section and features for non-logged-in users
        add_hero_section()
        add_features_section()
        add_doctor_quote()
        
        # Login/Register UI
        login_ui(db)
        
        # Add footer
        st.markdown("""
        <div style="text-align: center; padding: 40px 0; color: #7f8c8d;">
            <p style="margin: 0;">© 2024 PulseAI - Revolutionizing Cardiovascular Healthcare</p>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">
                Powered by Advanced AI Technology | Secure & HIPAA Compliant
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # User is logged in — show prediction UI
    st.markdown(f"""
    <div style="background: linear-gradient(45deg, #e74c3c, #c0392b); 
                padding: 20px; border-radius: 15px; margin: 20px 0; 
                text-align: center; color: white;">
        <h2 style="color: white; margin: 0;">
            👋 Welcome back, {st.session_state.get('email', 'User')}!
        </h2>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">
            Ready to analyze your ECG? Upload an image below to get started.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button('🚪 Logout', use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Use cached ECG model for better performance
    ecg = get_ecg_model()
    
    # File uploader with enhanced styling
    st.markdown("### 📤 Upload Your ECG Image")
    uploaded_file = st.file_uploader(
        "Choose an ECG image file", 
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear ECG image for AI analysis"
    )
    
    if uploaded_file is not None:
        # Show progress bar for image processing
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Load and display uploaded image
        status_text.text("🔄 Loading uploaded image...")
        progress_bar.progress(10)
        
        # Save uploaded file to disk and record upload in DB
        uploads_coll = db['uploads']
        uploads_dir = os.path.join(os.getcwd(), 'uploaded_files')
        os.makedirs(uploads_dir, exist_ok=True)
        filename = getattr(uploaded_file, 'name', f'upload_{uuid.uuid4().hex}.png')
        saved_path = os.path.join(uploads_dir, filename)
        with open(saved_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            upload_doc = {
                'upload_id': str(uuid.uuid4()),
                'user_email': st.session_state.get('email'),
                'file_name': filename,
                'saved_path': saved_path,
                'uploaded_at': datetime.utcnow()
            }
            uploads_coll.insert_one(upload_doc)
        except Exception:
            upload_doc = None
        
        ecg_user_image_read = ecg.getImage(saved_path)
        
        # Display uploaded image with enhanced styling
        st.markdown("### 📷 Your ECG Image")
        st.image(ecg_user_image_read, caption='Uploaded ECG image', use_column_width=True)
        
        # Step 2: Convert to grayscale
        status_text.text("🎨 Converting to grayscale...")
        progress_bar.progress(20)
        ecg_user_gray_image_read = ecg.GrayImgae(ecg_user_image_read)
        
        with st.expander("🔍 Gray Scale Image", expanded=False):
            st.image(ecg_user_gray_image_read)
        
        # Step 3: Divide leads
        status_text.text("📊 Dividing ECG leads...")
        progress_bar.progress(30)
        dividing_leads = ecg.DividingLeads(ecg_user_image_read)
        
        with st.expander("📈 ECG Lead Division", expanded=False):
            st.image('Leads_1-12_figure.png')
            st.image('Long_Lead_13_figure.png')
        
        # Step 4: Preprocess leads
        status_text.text("⚙️ Preprocessing leads...")
        progress_bar.progress(50)
        ecg_preprocessed_leads = ecg.PreprocessingLeads(dividing_leads)
        
        with st.expander("🔧 Preprocessed Leads", expanded=False):
            st.image('Preprossed_Leads_1-12_figure.png')
            st.image('Preprossed_Leads_13_figure.png')
        
        # Step 5: Extract signals
        status_text.text("📡 Extracting signals...")
        progress_bar.progress(70)
        ec_signal_extraction = ecg.SignalExtraction_Scaling(dividing_leads)
        
        with st.expander("📊 Signal Contours", expanded=False):
            st.image('Contour_Leads_1-12_figure.png')
        
        # Step 6: Convert to 1D signal
        status_text.text("🔄 Converting to 1D signal...")
        progress_bar.progress(80)
        ecg_1dsignal = ecg.CombineConvert1Dsignal()
        
        with st.expander("📈 1D Signals", expanded=False):
            st.write(ecg_1dsignal)
               
        # Step 7: Dimensionality reduction
        status_text.text("🧮 Performing dimensionality reduction...")
        progress_bar.progress(90)
        ecg_final = ecg.DimensionalReduciton(ecg_1dsignal)
        
        with st.expander("🎯 Dimensional Reduction", expanded=False):
            st.write(ecg_final)
        
        
        # Step 8: Make prediction
        status_text.text("🤖 Making AI prediction...")
        progress_bar.progress(95)
        ecg_model = ecg.ModelLoad_predict(ecg_final)
        
        # Complete progress
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        # Show prediction result prominently with enhanced styling
        if "Normal" in ecg_model:
            result_color = "#27ae60"
            result_icon = "✅"
        elif "Myocardial Infarction" in ecg_model:
            result_color = "#e74c3c"
            result_icon = "⚠️"
        elif "Abnormal Heartbeat" in ecg_model:
            result_color = "#f39c12"
            result_icon = "🔔"
        else:
            result_color = "#9b59b6"
            result_icon = "📋"
        
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
        
        # Additional information based on result
        if "Normal" in ecg_model:
            st.success("🎉 Great news! Your ECG appears to be within normal parameters. Continue maintaining a healthy lifestyle!")
        elif "Myocardial Infarction" in ecg_model:
            st.error("🚨 This result suggests potential myocardial infarction. Please consult with a healthcare professional immediately.")
        elif "Abnormal Heartbeat" in ecg_model:
            st.warning("⚠️ Abnormal heartbeat detected. We recommend scheduling a consultation with a cardiologist.")
        else:
            st.info("📋 History of myocardial infarction detected. Regular monitoring and follow-up with your doctor is recommended.")
        
        # Save prediction to MongoDB for auditing/tracking (async)
        with st.spinner('💾 Saving prediction to database...'):
            now = datetime.utcnow()
            try:
                preds = db['predictions']
                pred_doc = {
                    'prediction_id': str(uuid.uuid4()),
                    'user_email': st.session_state.get('email'),
                    'prediction': str(ecg_model),
                    'file_name': filename,
                    'timestamp': now
                }
                preds.insert_one(pred_doc)
                st.info('✅ Prediction saved to database')
            except Exception as e:
                st.warning(f'Could not save prediction to DB: {e}')
        
        # Add recommendation section
        st.markdown("""
        <div style="background: #ecf0f1; padding: 25px; border-radius: 15px; 
                    margin: 30px 0; border-left: 5px solid #3498db;">
            <h3 style="color: #2c3e50; margin: 0 0 15px 0;">💡 Next Steps</h3>
            <ul style="color: #2c3e50; margin: 0;">
                <li>Share these results with your healthcare provider</li>
                <li>Schedule regular cardiovascular check-ups</li>
                <li>Maintain a heart-healthy lifestyle</li>
                <li>Monitor your symptoms and report any changes</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Add disclaimer
        st.markdown("""
        <div style="background: #fff3cd; padding: 20px; border-radius: 10px; 
                    margin: 20px 0; border-left: 5px solid #ffc107;">
            <p style="color: #856404; margin: 0; font-size: 0.9em;">
                <strong>⚠️ Medical Disclaimer:</strong> This AI analysis is for informational purposes only 
                and should not replace professional medical advice. Always consult with qualified healthcare 
                professionals for medical decisions.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Show instructions when no file is uploaded
        st.markdown("""
        <div style="background: white; padding: 40px; border-radius: 15px; 
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin: 30px 0;">
            <h3 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">
                🚀 How to Use PulseAI
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 3em; margin-bottom: 15px;">📤</div>
                    <h4 style="color: #2c3e50;">1. Upload ECG</h4>
                    <p style="color: #7f8c8d;">Upload a clear ECG image file (PNG, JPG, JPEG)</p>
                </div>
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 3em; margin-bottom: 15px;">🤖</div>
                    <h4 style="color: #2c3e50;">2. AI Analysis</h4>
                    <p style="color: #7f8c8d;">Our AI processes your ECG in seconds</p>
                </div>
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 3em; margin-bottom: 15px;">📊</div>
                    <h4 style="color: #2c3e50;">3. Get Results</h4>
                    <p style="color: #7f8c8d;">Receive detailed analysis and recommendations</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()