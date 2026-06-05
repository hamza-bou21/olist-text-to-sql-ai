import os
from google import genai
from dotenv import load_dotenv

# This line finds your .env file and loads your key into Python's memory automatically
load_dotenv()

def test_connection():
    print("⏳ Checking for API key...")
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in .env file!")
        return
        
    print("🚀 Connecting to Gemini...")
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Hello! Reply with exactly: "Gemini is online and ready for SQL!"',
        )
        print(f"\n🤖 Response from AI: {response.text}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()