from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from linkedin_manager import LinkedInAutomation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
LINKEDIN_USERNAME = os.getenv('LINKEDIN_USERNAME')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
COMPANY_ID = os.getenv('COMPANY_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize LinkedIn Automation
linkedin = LinkedInAutomation(
    linkedin_username=LINKEDIN_USERNAME,
    linkedin_password=LINKEDIN_PASSWORD
)

if COMPANY_ID:
    linkedin.set_company_id(COMPANY_ID)

# Simple user model
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Mock user database
users = {
    1: User(1, "admin", generate_password_hash("admin"))
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        for user in users.values():
            if user.username == username and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('index'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        text = request.form.get('text')
        media_urls = request.form.get('media_urls', '').split(',')
        media_urls = [url.strip() for url in media_urls if url.strip()]
        
        try:
            response = linkedin.create_post(text=text, media_urls=media_urls if media_urls else None)
            flash('Post created successfully!')
        except Exception as e:
            flash(f'Error creating post: {str(e)}')
            
    return render_template('create_post.html')

@app.route('/generate_content', methods=['GET', 'POST'])
@login_required
def generate_content():
    if request.method == 'POST':
        topic = request.form.get('topic')
        include_hashtags = request.form.get('include_hashtags') == 'true'
        include_cta = request.form.get('include_cta') == 'true'
        tone = request.form.get('tone', 'professional')
        content_type = request.form.get('content_type', 'post')
        
        try:
            # Construct a more detailed prompt
            prompt = f"Write a {tone} LinkedIn {content_type} about {topic}"
            
            if include_hashtags:
                prompt += " Include 3-5 relevant hashtags at the end."
            
            if include_cta:
                prompt += " Add a clear call-to-action at the end."
            
            # Generate content with AI
            content = linkedin.generate_content_with_ai(prompt)
            
            # Try to parse the content if it's a JSON string
            try:
                import json
                content_dict = json.loads(content)
                # Extract the content, preferring a 'text' or 'content' key
                generated_content = content_dict.get('text') or content_dict.get('content') or content
            except (json.JSONDecodeError, TypeError):
                # If not JSON or parsing fails, use the content as-is
                generated_content = content
            
            # If content is still empty, set a default message
            if not generated_content:
                generated_content = "Unable to generate content. Please try again."
            
            return jsonify({'content': generated_content})
        
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    return render_template('generate_content.html')

@app.route('/schedule_post', methods=['GET', 'POST'])
@login_required
def schedule_post():
    if request.method == 'POST':
        text = request.form.get('text')
        schedule_time = request.form.get('schedule_time')
        media_urls = request.form.get('media_urls', '').split(',')
        media_urls = [url.strip() for url in media_urls if url.strip()]
        
        try:
            schedule_datetime = datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M')
            response = linkedin.schedule_post(
                text=text,
                schedule_time=schedule_datetime,
                media_urls=media_urls if media_urls else None
            )
            flash('Post scheduled successfully!')
        except Exception as e:
            flash(f'Error scheduling post: {str(e)}')
            
    return render_template('schedule_post.html')

@app.route('/analytics')
@login_required
def analytics():
    try:
        # Ensure company ID is set before fetching updates
        if not linkedin.company_id:
            linkedin.set_company_id(COMPANY_ID)
        
        # Debugging: Print out the method signature and available methods
        import inspect
        print("LinkedIn API methods:", dir(linkedin.api))
        
        # Multiple approaches to fetch updates
        updates = []
        error_messages = []
        
        # Approach 1: Try with company ID
        try:
            updates = linkedin.get_company_updates(limit=5)
        except Exception as e1:
            error_messages.append(f"Approach 1 failed: {e1}")
            print(f"Approach 1 failed: {e1}")
        
        # If no updates, add a flash message
        if not updates:
            flash('No company updates found.')
            # Combine all error messages for logging
            if error_messages:
                print("Errors encountered:", " | ".join(error_messages))
        
        return render_template('analytics.html', updates=updates)
    except Exception as e:
        # Log the full error for debugging
        import traceback
        traceback.print_exc()
        
        # Provide a user-friendly error message
        flash(f'Error fetching analytics: {str(e)}')
        return render_template('analytics.html', updates=[])

@app.route('/api/post_analytics/<post_id>')
@login_required
def post_analytics(post_id):
    try:
        analytics = linkedin.get_post_analytics(post_id)
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)