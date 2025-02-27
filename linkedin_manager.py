import os
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Check for required environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

# Groq API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

class LinkedInAutomation:
    def __init__(self, linkedin_username: str, linkedin_password: str):
        """
        Initialize LinkedIn Automation with credentials
        
        Args:
            linkedin_username: LinkedIn account username/email
            linkedin_password: LinkedIn account password
        """
        self.username = linkedin_username
        self.password = linkedin_password
        self.company_id = None
        self.driver = None
        
    def _setup_driver(self):
        """Setup Selenium WebDriver with comprehensive options to mitigate GPU and rendering issues"""
        try:
            # Comprehensive Chrome options
            options = webdriver.ChromeOptions()
            
            # Disable GPU and enable software rendering
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-software-rasterizer')
            
            # Headless mode with window size
            options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
            
            # Performance and stability options
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-sync')
            options.add_argument('--metrics-recording-only')
            options.add_argument('--mute-audio')
            
            # Specific WebDriver stability arguments
            options.add_argument('--remote-debugging-port=9222')
            options.add_argument('--no-first-run')
            options.add_argument('--no-service-autorun')
            options.add_argument('--disable-features=VizDisplayCompositor')
            
            # User agent to mimic browser
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Additional experimental options
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Create WebDriver service with logging
            service = webdriver.chrome.service.Service()
            service.creationflags = 0x08000000  # No-window flag
            
            # Initialize WebDriver with enhanced options
            self.driver = webdriver.Chrome(
                options=options,
                service=service
            )
            
            # Set page load and script timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(30)
            
            # Additional configuration
            self.driver.implicitly_wait(10)
            
            return True
        except Exception as e:
            print(f"Critical error setting up WebDriver: {str(e)}")
            # Log the full traceback for debugging
            import traceback
            traceback.print_exc()
            return False
            
    def login(self) -> bool:
        """Enhanced LinkedIn login method with multiple retry mechanisms"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Ensure driver is set up
                if not self.driver:
                    if not self._setup_driver():
                        print(f"Failed to setup WebDriver (Attempt {attempt + 1})")
                        continue
                
                # Navigate to LinkedIn login
                self.driver.get('https://www.linkedin.com/login')
                
                # Wait for username field with explicit wait
                username_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                
                # Clear and input username
                username_field.clear()
                username_field.send_keys(self.username)
                
                # Find and fill password field
                password_field = self.driver.find_element(By.ID, "password")
                password_field.clear()
                password_field.send_keys(self.password)
                
                # Click login button with retry
                login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_button.click()
                
                # Wait for successful login with multiple checks
                try:
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.ID, "global-nav"))
                    )
                    print("Successfully logged in to LinkedIn")
                    return True
                
                except TimeoutException:
                    # Additional checks for login success
                    current_url = self.driver.current_url
                    if 'feed' in current_url or 'home' in current_url:
                        print("Login successful (URL-based verification)")
                        return True
                    
                    print(f"Login verification failed (Attempt {attempt + 1})")
            
            except Exception as e:
                print(f"Login attempt {attempt + 1} failed: {str(e)}")
                
                # Take screenshot for debugging
                try:
                    screenshot_path = f'login_error_attempt_{attempt + 1}.png'
                    self.driver.save_screenshot(screenshot_path)
                    print(f"Error screenshot saved to {screenshot_path}")
                except Exception as screenshot_err:
                    print(f"Could not save error screenshot: {screenshot_err}")
                
                # Cleanup and reset driver
                if self.driver:
                    self.driver.quit()
                    self.driver = None
        
        # All attempts failed
        print("Failed to log in to LinkedIn after multiple attempts")
        return False
        
    def set_company_id(self, company_id: str):
        """Set the company ID for operations"""
        self.company_id = company_id
        
    def generate_content_with_ai(self, prompt: str) -> str:
        """
        Generate content using Groq's API
        
        Args:
            prompt: Content generation prompt
            
        Returns:
            Generated content string
        """
        try:
            payload = {
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional LinkedIn content writer. Create engaging, business-appropriate content that resonates with a professional audience. Focus on clarity, value, and maintaining a professional tone."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 800,
                "top_p": 1,
                "stream": False
            }

            response = requests.post(
                GROQ_API_URL,
                headers=GROQ_HEADERS,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result and "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    print("No content in response:", result)
                    return None
            else:
                print(f"API request failed with status code {response.status_code}")
                print("Response:", response.text)
                return None

        except requests.exceptions.RequestException as e:
            print(f"Network error while generating content: {str(e)}")
            return None
        except Exception as e:
            print(f"Error generating content: {str(e)}")
            return None
        
    def create_post(self, text: str, media_urls: Optional[List[str]] = None, drag_and_drop: bool = True) -> Dict:
        """
        Create a new LinkedIn post using Selenium with advanced media handling
        
        Args:
            text: Post content
            media_urls: Optional list of media URLs to attach
            drag_and_drop: Whether to use drag and drop for image upload
            
        Returns:
            Dict indicating success/failure
        """
        try:
            if not self.driver:
                if not self.login():
                    raise Exception("Failed to login to LinkedIn")
            
            # Navigate to posting interface
            if self.company_id:
                self.driver.get(f'https://www.linkedin.com/company/{self.company_id}/admin/')
                time.sleep(3)
            else:
                self.driver.get('https://www.linkedin.com/feed/')
                time.sleep(3)
            
            # Click on start post button
            start_post_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='share-box-feed-entry__trigger']"))
            )
            start_post_button.click()
            time.sleep(2)
            
            # Switch to company account if needed
            if self.company_id:
                try:
                    posting_as_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='share-actor-toggle']"))
                    )
                    posting_as_button.click()
                    time.sleep(1)
                    
                    company_option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, f"div[data-company-id='{self.company_id}']"))
                    )
                    company_option.click()
                    time.sleep(1)
                except Exception as e:
                    print(f"Warning: Could not switch to company account: {str(e)}")
            
            # Find post textarea
            post_textarea = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-placeholder='What do you want to talk about?']"))
            )
            
            # Set post text using JavaScript
            self.driver.execute_script(
                "arguments[0].innerHTML = arguments[1];", 
                post_textarea,
                text.replace('\n', '<br>')
            )
            time.sleep(1)
            
            # Advanced Media Upload
            if media_urls and len(media_urls) > 0:
                try:
                    # Prepare a temporary directory for downloads
                    temp_dir = os.path.join(os.getcwd(), 'temp_linkedin_uploads')
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Download and prepare media files
                    media_files = []
                    for i, url in enumerate(media_urls):
                        try:
                            # Download image
                            response = requests.get(url)
                            if response.status_code == 200:
                                # Save with unique filename
                                file_ext = os.path.splitext(url.split('/')[-1])[-1] or '.jpg'
                                temp_file = os.path.join(temp_dir, f'linkedin_media_{i}{file_ext}')
                                
                                with open(temp_file, 'wb') as f:
                                    f.write(response.content)
                                media_files.append(temp_file)
                        except Exception as download_err:
                            print(f"Error downloading media {url}: {download_err}")
                    
                    # Media Upload Methods
                    if drag_and_drop:
                        # Drag and Drop Method
                        media_button = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label*='Add media']"))
                        )
                        media_button.click()
                        time.sleep(1)
                        
                        # Find the drop zone
                        drop_zone = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='file-upload-input']"))
                        )
                        
                        # Use JavaScript to simulate drag and drop
                        for media_file in media_files:
                            # Create a file list for drag and drop
                            file_list = self.driver.execute_script("""
                                var files = new DataTransfer();
                                files.items.add(new File([''], arguments[0], {type: 'image/jpeg'}));
                                return files.files;
                            """, media_file)
                            
                            # Simulate drag and drop
                            self.driver.execute_script("""
                                var event = new DragEvent('drop', {
                                    bubbles: true,
                                    cancelable: true,
                                    dataTransfer: arguments[0]
                                });
                                arguments[1].dispatchEvent(event);
                            """, file_list, drop_zone)
                            
                            time.sleep(2)
                    else:
                        # Traditional File Input Method
                        media_button = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label*='Add media']"))
                        )
                        media_button.click()
                        time.sleep(1)
                        
                        # Find file input
                        file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                        
                        # Send files
                        file_paths = '\n'.join(media_files)
                        file_input.send_keys(file_paths)
                        time.sleep(3)
                    
                    # Verify media upload
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "img[class*='share-mixed-media-image']"))
                    )
                    
                    # Clean up temporary files
                    for media_file in media_files:
                        try:
                            os.remove(media_file)
                        except Exception as cleanup_err:
                            print(f"Error cleaning up {media_file}: {cleanup_err}")
                    
                except Exception as media_err:
                    print(f"Media upload error: {media_err}")
            
            # Post button
            post_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='share-actions__primary-action']"))
            )
            post_button.click()
            
            # Wait for post confirmation
            time.sleep(5)
            
            return {
                "success": True, 
                "message": "Post created successfully", 
                "media_count": len(media_urls) if media_urls else 0
            }
            
        except Exception as e:
            print(f"Error creating LinkedIn post: {str(e)}")
            # Take a screenshot for debugging
            try:
                screenshot_path = os.path.join(os.getcwd(), 'linkedin_post_error.png')
                self.driver.save_screenshot(screenshot_path)
                print(f"Error screenshot saved to {screenshot_path}")
            except Exception as screenshot_err:
                print(f"Could not save error screenshot: {screenshot_err}")
            
            return {
                "success": False, 
                "error": str(e),
                "media_count": len(media_urls) if media_urls else 0
            }
        
    def generate_and_post(self, topic: str, include_hashtags: bool = True) -> Dict:
        """
        Generate content using AI and post it to LinkedIn
        
        Args:
            topic: Topic to generate content about
            include_hashtags: Whether to include relevant hashtags
            
        Returns:
            Dict with results
        """
        try:
            # Generate the content
            prompt = f"Write a professional LinkedIn post about {topic}"
            if include_hashtags:
                prompt += " Include 3-5 relevant hashtags at the end."
                
            content = self.generate_content_with_ai(prompt)
            if not content:
                raise Exception("Failed to generate content")
            
            print("Generated content successfully")
            print("Content preview:", content[:100] + "..." if len(content) > 100 else content)
            
            # Create the post
            result = self.create_post(content)
            if not result.get("success"):
                raise Exception(f"Failed to create LinkedIn post: {result.get('error')}")
            
            print("Successfully posted to LinkedIn")
            return {
                "success": True,
                "content": content,
                "post_data": result
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error in generate_and_post: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "content": content if 'content' in locals() else None
            }
    
    def close(self):
        """Close the browser session"""
        if self.driver:
            self.driver.quit()
            self.driver = None