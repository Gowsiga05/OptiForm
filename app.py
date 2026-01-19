from flask import Flask, request, jsonify, render_template
import cv2
import numpy as np
import base64
import mediapipe as mp
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from core.coach_llm import get_llm_coaching # Add at top of app.py


app = Flask(__name__)

# --- INITIALIZE MEDIAPIPE ---
MODEL_PATH = 'data/pose_landmarker_lite.task'
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE
)
detector = vision.PoseLandmarker.create_from_options(options)

# --- ENHANCED STATE MANAGEMENT ---
# Using 'down' and 'up' stages with wider thresholds for "smooth" detection
session = {
    "stage": "down", 
    "reps": 0, 
    "feedback": "Ready! Start your curl.",
    "last_angle": 0
}

def calculate_angle(a, b, c):
    """Calculates angle between shoulder(a), elbow(b), and wrist(c)."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180.0 else angle

@app.route('/')
def index():
    return render_template('index.html')

# Ensure you import your modules at the top of app.py
from exercises.bicep_curl import get_bicep_curl_data
from exercises.squat import get_squat_data

@app.route('/detect', methods=['POST'])
def detect():
    global session
    try:
        # 1. Decode Frame and Get Exercise Type
        data = request.json
        ex_type = data.get('exercise', 'bicep_curl')
        img_data = base64.b64decode(data['image'].split(',')[1])
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # 2. MediaPipe Detection
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = detector.detect(mp_image)
        
        filtered_landmarks = []
        angle = 0

        if result.pose_landmarks:
            points = result.pose_landmarks[0]
            
            # 3. CALL EXTERNAL MODULES
            # Each module returns (p1, p2, p3, visibility, up_thresh, down_thresh, error_msg)
            if ex_type == 'bicep_curl':
                p1, p2, p3, visible, up_t, down_t, error_msg = get_bicep_curl_data(points)
            elif ex_type == 'squat':
                p1, p2, p3, visible, up_t, down_t, error_msg = get_squat_data(points)
            else:
                return jsonify({'error': 'Exercise not supported'}), 400

            # 4. Visibility Guard
            if not visible:
                return jsonify({
                    'landmarks': [], 
                    'reps': session["reps"], 
                    'angle': 0, 
                    'feedback': error_msg
                })

            # 5. Calculate Angle
            angle = calculate_angle(p1, p2, p3)

            # 6. Repetition Logic using module-specific thresholds
            if angle > down_t:
                if session["stage"] == "up":
                    session["feedback"] = "Fully extended! Ready for next."
                session["stage"] = "down"
            
            elif angle < up_t and session["stage"] == "down":
                session["stage"] = "up"
                session["reps"] += 1
                
                # 7. AI Coaching Trigger (Updated to pass ex_type)
                if session["reps"] % 5 == 0:
                    session["feedback"] = get_llm_coaching(session["reps"], int(angle), "up", ex_type)
                else:
                    session["feedback"] = f"Rep {session['reps']} complete!"

            # 8. Prepare Landmarks for drawing
            filtered_landmarks = [{'x': p1[0], 'y': p1[1]}, 
                                 {'x': p2[0], 'y': p2[1]}, 
                                 {'x': p3[0], 'y': p3[1]}]

        return jsonify({
            'landmarks': filtered_landmarks,
            'reps': session["reps"],
            'angle': int(angle),
            'feedback': session["feedback"]
        })

    except Exception as e:
        print(f"Error in detect: {e}")
        return jsonify({'error': str(e)}), 500
    
    
from utils.db import save_workout_session

@app.route('/finish', methods=['POST'])
def finish():
    global session
    message = save_workout_session(session["reps"])
    # Reset local session after saving
    session["reps"] = 0
    session["stage"] = "down"
    return jsonify({"status": "success", "message": message})

from utils.db import get_workout_history

@app.route('/get_history')
def history():
    data = get_workout_history()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)