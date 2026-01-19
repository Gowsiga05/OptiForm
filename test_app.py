import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Correct imports based on your folder structure
from utils.auth import db, auth
from core.coach_llm import get_coaching_feedback
from core.pose_engine import calculate_angle

# --- PAGE CONFIG ---
st.set_page_config(page_title="OptiForm AI", layout="wide")
st.title("OptiForm AI Coach [cite: 10]")

# --- AUTHENTICATION STATE ---
if 'user_uid' not in st.session_state:
    st.session_state.user_uid = None

# Sidebar Login/Signup UI
if not st.session_state.user_uid:
    st.sidebar.header("Login to Track Progress")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        try:
            # Note: auth.get_user_by_email is part of firebase-admin
            user = auth.get_user_by_email(email)
            st.session_state.user_uid = user.uid
            st.rerun()
        except Exception as e:
            st.sidebar.error("User not found. Please check credentials.")
    st.stop()

# --- VISION ENGINE SETUP ---
# Path points to your 'data' folder
MODEL_PATH = 'data/pose_landmarker_lite.task'
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE
)
detector = vision.PoseLandmarker.create_from_options(options)

# --- WORKOUT INTERFACE ---
col1, col2 = st.columns([3, 1])
FRAME_WINDOW = col1.image([])
stats_area = col2.empty()

# Progress Tracking Variables
if 'counter' not in st.session_state:
    st.session_state.counter = 0
stage = None
feedback = "Stand in frame to begin..."

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    
    # Process with MediaPipe [cite: 12, 101]
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    result = detector.detect(mp_image)
    
    if result.pose_landmarks:
        landmarks = result.pose_landmarks[0]
        
        # Landmarks for Bicep Curl (11, 13, 15) [cite: 85, 89, 92]
        sh = [landmarks[11].x, landmarks[11].y]
        el = [landmarks[13].x, landmarks[13].y]
        wr = [landmarks[15].x, landmarks[15].y]
        
        # Use imported calculate_angle from core/pose_engine.py [cite: 60, 98]
        angle = calculate_angle(sh, el, wr)
        
        # Rep Counting Logic [cite: 103, 108]
        if angle > 160: 
            stage = "down"
        if angle < 35 and stage == "down":
            stage = "up"
            st.session_state.counter += 1
            
            # Sync Reps to Firestore [cite: 175, 176]
            db.collection('users').document(st.session_state.user_uid).set({
                'reps': st.session_state.counter,
                'last_workout': time.strftime("%Y-%m-%d %H:%M:%S")
            }, merge=True)
            
        # Get AI Feedback from core/coach_llm.py [cite: 13, 118]
        if 60 < angle < 120:
            advice = get_coaching_feedback("Bicep Curl", int(angle), "Form correction needed")
            if advice: feedback = advice

        # Drawing Skeleton overlay [cite: 115]
        p_sh = (int(sh[0]*w), int(sh[1]*h))
        p_el = (int(el[0]*w), int(el[1]*h))
        p_wr = (int(wr[0]*w), int(wr[1]*h))
        cv2.line(frame, p_sh, p_el, (255, 255, 255), 3)
        cv2.line(frame, p_el, p_wr, (255, 255, 255), 3)
        cv2.circle(frame, p_el, 8, (0, 255, 0), -1)

    # UI Updates
    stats_area.markdown(f"""
    ### 📈 Session Stats [cite: 215]
    - **Exercise:** Bicep Curl
    - **Total Reps:** {st.session_state.counter} [cite: 47, 105]
    - **Current Angle:** {int(angle) if 'angle' in locals() else 0}° [cite: 95]
    
    **AI Coach Advice:** [cite: 111]
    > "{feedback}"
    """)
    
    FRAME_WINDOW.image(frame, channels="BGR")

cap.release()