import streamlit as st
from flask import Flask, request, redirect
import threading
import time
from services.linkedin_service import LinkedInService
from services.database_service import DatabaseService

app = Flask(__name__)
linkedin_service = LinkedInService()
db_service = DatabaseService()

oauth_results = {}

@app.route('/linkedin/callback')
def linkedin_callback():
    """Handle LinkedIn OAuth callback with better error handling"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    error_description = request.args.get('error_description', '')
    
    if error:
        # Log the full error for debugging
        print(f"LinkedIn OAuth Error: {error}")
        print(f"Error Description: {error_description}")
        
        oauth_results[state] = {
            'success': False, 
            'error': error,
            'error_description': error_description
        }
        
        return f"""
        <html>
        <body>
            <h2>LinkedIn Authentication Failed</h2>
            <p><strong>Error:</strong> {error}</p>
            <p><strong>Description:</strong> {error_description}</p>
            <p><strong>Possible Solutions:</strong></p>
            <ul>
                <li>Check your LinkedIn Developer App permissions</li>
                <li>Ensure required products are approved</li>
                <li>Verify your app's redirect URL settings</li>
            </ul>
            <p>You can close this window and try again.</p>
            <script>setTimeout(function(){{window.close();}}, 10000);</script>
        </body>
        </html>
        """
    
    if code:
        print(f"Received authorization code: {code[:10]}...")
        
        # Exchange code for token
        token_data = linkedin_service.exchange_code_for_token(code)
        
        if token_data:
            oauth_results[state] = {
                'success': True, 
                'token_data': token_data
            }
            return f"""
            <html>
            <body>
                <h2>✅ LinkedIn Connected Successfully!</h2>
                <p>Your LinkedIn account has been connected.</p>
                <p>You can now close this window and return to the app.</p>
                <script>setTimeout(function(){{window.close();}}, 3000);</script>
            </body>
            </html>
            """
        else:
            oauth_results[state] = {'success': False, 'error': 'Token exchange failed'}
            return f"""
            <html>
            <body>
                <h2>❌ LinkedIn Authentication Failed</h2>
                <p>Failed to exchange authorization code for access token.</p>
                <p>Please check your LinkedIn app configuration.</p>
                <script>setTimeout(function(){{window.close();}}, 5000);</script>
            </body>
            </html>
            """
    
    return "Invalid request - no code or error received"

def run_oauth_server():
    """Run the OAuth callback server"""
    try:
        app.run(host='localhost', port=8502, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Failed to start OAuth server: {e}")

def start_oauth_server():
    """Start OAuth server in background thread"""
    oauth_thread = threading.Thread(target=run_oauth_server, daemon=True)
    oauth_thread.start()
    time.sleep(1)

def get_oauth_result(state: str) -> dict:
    """Get OAuth result for given state"""
    return oauth_results.get(state, {})

def clear_oauth_result(state: str):
    """Clear OAuth result for given state"""
    if state in oauth_results:
        del oauth_results[state]
