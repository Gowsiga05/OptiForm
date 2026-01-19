import firebase_admin
from firebase_admin import credentials, firestore
import pytz

# Initialize Firebase with your local key
cred = credentials.Certificate("data/serviceAccountKey.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

def save_workout_session(reps):
    """Saves the workout data to Firestore."""
    data = {
        "exercise": "Bicep Curl",
        "reps_completed": reps,
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    # Add a new document to the 'workouts' collection
    db.collection("workouts").add(data)
    return "Session Saved Successfully!"

# Add this to your utils/db.py
import pytz # Add this import at the top

def get_workout_history(limit=5):
    docs = db.collection("workouts").order_by(
        "timestamp", direction=firestore.Query.DESCENDING
    ).limit(limit).stream()
    
    # Define your local timezone
    local_tz = pytz.timezone('Asia/Kolkata') 
    
    history = []
    for doc in docs:
        data = doc.to_dict()
        # Convert UTC to Local Time
        utc_dt = data['timestamp'].replace(tzinfo=pytz.utc)
        local_dt = utc_dt.astimezone(local_tz)
        
        date_str = local_dt.strftime("%Y-%m-%d %H:%M")
        history.append({
            "reps": data['reps_completed'],
            "date": date_str
        })
    return history