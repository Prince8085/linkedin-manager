import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LinkedIn credentials
LINKEDIN_USERNAME = os.getenv('LINKEDIN_USERNAME')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
COMPANY_ID = os.getenv('COMPANY_ID')
OPENAI_API_KEY = os.getenv('GROQ_API_KEY')  # Using GROQ API key for OpenAI compatibility

# Validate required environment variables
if not all([LINKEDIN_USERNAME, LINKEDIN_PASSWORD, COMPANY_ID]):
    raise ValueError("Missing required environment variables. Please check your .env file.")