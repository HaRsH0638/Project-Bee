import streamlit as st
import cv2
import tempfile
import sys
import os
import time

# --- 1. SYSTEM INITIALIZATION ---
# Using raw strings to prevent Windows path escape sequence errors.
root_path = r"E:\Projects\Project Bee" 

if root_path not in sys.path:
    sys.path.insert(0, root_path)

try:
    from core.processor import VideoProcessor
except ImportError as e:
    st.error(f"TELEMETRY_FAILURE: {e}")
    st.stop()

# --- 2. THEME & INTERFACE CONFIGURATION ---
st.set_page_config(
    page_title="PROJECT BEE | ANALYTICS",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. CUSTOM CSS: ORBITRON & GLASSMORPHIC REFINEMENT ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@400;600&display=swap');

    /* Global Background & Base Font */
    .stApp {
        background: #0b0b0b;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }

    /* Subtle GitHub Link (Top Right) */
    .github-link {
        position: absolute;
        top: 0px;
        right: 0px;
        padding: 10px;
        z-index: 1000;
        text-decoration: none;
        color: rgba(255, 255, 255, 0.4);
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        transition: 0.3s;
    }
    .github-link:hover {
        color: #FF8700;
    }

    /* Main Header with Orange Bar */
    .main-header-container {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .orange-bar {
        width: 6px;
        height: 60px;
        background-color: #FF8700;
        margin-right: 20px;
    }
    .main-header {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 38px;
        font-weight: 900;
        letter-spacing: 2px;
        color: #FFFFFF;
    }

    /* Status Badges */
    .badge-row {
        margin-bottom: 25px;
    }
    .status-badge {
        font-family: 'Orbitron', sans-serif;
        font-size: 10px;
        padding: 2px 10px;
        border: 1px solid #FF8700;
        color: #FF8700;
        margin-right: 10px;
        background: rgba(255, 135, 0, 0.05);
    }

    /* Sidebar Cockpit Logic */
    section[data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-right: 1px solid rgba(255, 135, 0, 0.3);
    }
    
    /* Control Expanders Styling */
    .stExpander {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        margin-bottom: 10px;
    }

    /* Metric Card Glassmorphism */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #FF8700 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 12px !important;
    }

    /* Input Styling */
    .stSlider [data-baseweb="slider"] {
        color: #FF8700;
    }
    
    /* Reset Button Styling */
    .stButton>button {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        width: 100%;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 14px !important;
        border-radius: 8px !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #FF8700 !important;
        color: #FF8700 !important;
    }

    /* Blue Awaiting Status Bar */
    .awaiting-bar {
        background: rgba(0, 100, 255, 0.1);
        border: 1px solid rgba(0, 100, 255, 0.3);
        color: #4da6ff;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TOP NAVIGATION (GITHUB LINK) ---
st.markdown('<a href="https://github.com/HaRsH0638" class="github-link" target="_blank">VIEW_ON_GITHUB / 🔗</a>', unsafe_allow_html=True)

# --- 5. SIDEBAR: SYSTEM CONTROLS ---
with st.sidebar:
    st.markdown("### SYSTEM CONTROLS")
    
    with st.expander("DETECTION PARAMETERS", expanded=True):
        conf_level = st.slider("CONFIDENCE", 0.0, 1.0, 0.45)
        iou_level = st.slider("IOU THRESHOLD", 0.0, 1.0, 0.50)
        
    with st.expander("VISUAL SETTINGS", expanded=True):
        privacy_mode = st.toggle("PRIVACY BLUR", value=True)
        show_labels = st.toggle("SHOW LABELS", value=True)
        blur_strength = st.slider("BLUR STRENGTH", 31, 91, 51, step=2)

    st.markdown("<br>" * 2, unsafe_allow_html=True)
    if st.button("RESET SESSION DATA"):
        st.session_state.processor = VideoProcessor()
        st.rerun()

# --- 6. MAIN PANEL: PROJECT BEE ---
st.markdown("""
    <div class="main-header-container">
        <div class="orange-bar"></div>
        <div class="main-header">PROJECT BEE / VISION ANALYTICS</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="badge-row">
        <span class="status-badge">STATUS: ACTIVE</span>
        <span class="status-badge">LOGGED AS: HARSH_SINHA</span>
    </div>
    """, unsafe_allow_html=True)

if 'processor' not in st.session_state:
    st.session_state.processor = VideoProcessor()

# Initializing Empty Metrics
m1, m2, m3 = st.columns(3)
metric_count = m1.empty()
metric_fps = m2.empty()
metric_latency = m3.empty()

st.markdown("##### SELECT VIDEO DATA SOURCE")
uploaded_file = st.file_uploader("", type=['mp4', 'mov', 'avi'])

if uploaded_file:
    # Processing Engine
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    
    cap = cv2.VideoCapture(tfile.name)
    viewport = st.empty()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        start = time.time()
        
        # Inference Logic (Update your Processor with the new sliders!)
        processed_frame, count = st.session_state.processor.process_frame(
            frame, 
            enable_blur=privacy_mode
        )

        end = time.time()
        fps = 1 / (end - start)
        latency = (end - start) * 1000

        # Updating Real-time Telemetry
        metric_count.metric("TOTAL UNIQUE TARGETS", count)
        metric_fps.metric("INFERENCE SPEED", f"{fps:.1f} FPS")
        metric_latency.metric("SYSTEM LATENCY", f"{latency:.1f} MS")

        viewport.image(processed_frame, channels="BGR", use_container_width=True)

    cap.release()
else:
    # Awaiting Status Bar matching your reference image
    st.markdown('<div class="awaiting-bar">AWAITING INPUT... SELECT VIDEO SOURCE TO INITIALIZE TRACKING.</div>', unsafe_allow_html=True)