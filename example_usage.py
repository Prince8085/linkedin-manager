from linkedin_manager import LinkedInAutomation
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize LinkedIn Automation
linkedin = LinkedInAutomation(
    linkedin_username=os.getenv('LINKEDIN_USERNAME'),
    linkedin_password=os.getenv('LINKEDIN_PASSWORD')
)

# Optional: Set Company ID
linkedin.set_company_id(os.getenv('COMPANY_ID'))

# Generate and post content
def main():
    # Example topics
    topics = [
        "AI and Machine Learning",
        "Future of Technology",
        "Innovation in Software Development"
    ]

    for topic in topics:
        try:
            # Generate and post content
            result = linkedin.generate_and_post(topic, include_hashtags=True)
            print(f"Successfully posted about {topic}")
        except Exception as e:
            print(f"Error posting about {topic}: {str(e)}")

if __name__ == "__main__":
    main()