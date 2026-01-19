import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env
load_dotenv()

# NEW SDK SYNTAX: Pass the API key directly to the Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_llm_coaching(reps, angle, stage,exercise_name):
    """Generates 5-word supportive feedback using the new SDK."""
    prompt = (f"User is performing {exercise_name}. Reps: {reps}, Angle: {angle}. "
              f"The user is in the {stage} phase. Give 5-word supportive advice.")
    # ... (Keep your client.models.generate_content call) ...    
    try:
        # Correct method call for the new SDK
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return "Keep going, great form!"