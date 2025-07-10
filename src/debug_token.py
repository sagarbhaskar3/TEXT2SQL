# debug_token.py
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_huggingface_token():
    """Test if your Hugging Face token is working"""
    
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    
    if not token:
        print("❌ No token found in .env file")
        return False
    
    print(f"🔑 Testing token: {token[:10]}...")
    
    # Test with a simple model first
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try a simpler model first
    test_url = "https://api-inference.huggingface.co/models/gpt2"
    test_payload = {"inputs": "Hello world"}
    
    try:
        response = requests.post(test_url, headers=headers, json=test_payload, timeout=10)
        print(f"Test response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Token is working with basic models")
            
            # Now test with defog model
            defog_url = "https://api-inference.huggingface.co/models/defog/sqlcoder-7b"
            defog_payload = {"inputs": "SELECT * FROM users;"}
            
            defog_response = requests.post(defog_url, headers=headers, json=defog_payload, timeout=30)
            print(f"Defog model status: {defog_response.status_code}")
            
            if defog_response.status_code == 200:
                print("✅ Token works with defog/sqlcoder-7b")
                return True
            elif defog_response.status_code == 403:
                print("❌ 403 Forbidden for defog model - this model might require special access")
                print("💡 Let's try an alternative approach...")
                return False
            elif defog_response.status_code == 503:
                print("⏳ Model is loading, try again in a few minutes")
                return False
            else:
                print(f"❌ Defog model error: {defog_response.text}")
                return False
        
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - Token is invalid")
            return False
        elif response.status_code == 403:
            print("❌ 403 Forbidden - Token doesn't have required permissions")
            return False
        else:
            print(f"❌ Unexpected error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def get_new_token_instructions():
    """Instructions for getting a new token"""
    print("\n" + "="*50)
    print("🔧 How to fix the token issue:")
    print("="*50)
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Click 'New token'")
    print("3. Name: 'Text2SQL Project'")
    print("4. Type: Select 'Read' (or 'Write' if available)")
    print("5. Copy the token that starts with 'hf_'")
    print("6. Update your .env file:")
    print("   HUGGINGFACE_API_TOKEN=hf_your_new_token_here")
    print("="*50)

def try_alternative_models():
    """Try alternative SQL models that might work better"""
    
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    
    alternative_models = [
        "microsoft/DialoGPT-medium",  # General purpose, should work
        "codellama/CodeLlama-7b-hf",   # Code-focused
        "Salesforce/codegen-350M-mono" # Smaller code model
    ]
    
    print("\n🔄 Trying alternative models...")
    
    for model in alternative_models:
        url = f"https://api-inference.huggingface.co/models/{model}"
        payload = {"inputs": "CREATE TABLE users (id INT, name VARCHAR(50));"}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            print(f"Model {model}: Status {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ {model} is working!")
                return model
                
        except Exception as e:
            print(f"❌ {model} failed: {e}")
    
    return None

if __name__ == "__main__":
    print("🏥 Healthcare Text2SQL - Token Debug")
    print("="*40)
    
    token_works = test_huggingface_token()
    
    if not token_works:
        get_new_token_instructions()
        alternative_model = try_alternative_models()
        
        if alternative_model:
            print(f"\n💡 Use this working model: {alternative_model}")
        else:
            print("\n❌ No working models found. Please get a new token.")