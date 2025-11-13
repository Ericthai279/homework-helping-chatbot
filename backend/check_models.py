import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("Attempting to load Google API Key...")
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("\nError: GOOGLE_API_KEY not found in .env file.")
    print("Please make sure your .env file is in the same folder and has your key.")
else:
    try:
        # We must add this check, as your 'langchain-google-genai'
        # might not have installed 'google-generativeai'
        if genai is None:
            print("\nError: 'google-generativeai' package not found.")
            print("Please run: pip install google-generativeai")
        else:
            print("Key loaded. Configuring API...")
            genai.configure(api_key=API_KEY)
            
            print("\nFetching available models for your key...")
            print("=========================================")
            
            # List the models
            found_models = False
            for m in genai.list_models():
                # We only care about models that can be used for chat
                if 'generateContent' in m.supported_generation_methods:
                    print(f"Model Name: {m.name}")
                    found_models = True
                    
            if not found_models:
                print("No models found for your API key that support 'generateContent'.")
                
            print("=========================================")
            print("\nProcess complete.")
            print("Please copy one of the 'Model Name's listed above (e.g., 'models/gemini-1.0-pro')")
            print("and paste it into the 'model=...' line in your core/tutor_service.py file.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")