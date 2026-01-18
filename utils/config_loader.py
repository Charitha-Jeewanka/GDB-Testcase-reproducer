import os
import yaml
from dotenv import load_dotenv

def load_config(config_path="config.yaml"):
    load_dotenv()
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    # Validation/Defaults could go here
    return config

def get_groq_api_key():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    return key
