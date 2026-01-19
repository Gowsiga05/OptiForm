import firebase_admin
from firebase_admin import credentials, auth

# 1. Point to your key
cred = credentials.Certificate("data/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# 2. Try to create a user manually
try:
    user = auth.create_user(
        email="testuser1@fitnessapp.com",
        password="password123"
    )
    print(f"Successfully created user: {user.uid}")
except Exception as e:
    print(f"Error: {e}")