import requests
import logging
import urllib.parse
from typing import Dict, Optional, List
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

class LinkedInService:
    def __init__(self):
        self.base_url = "https://api.linkedin.com/v2"
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    
    def get_authorization_url(self, state: str = "random_state") -> str:
        """Generate LinkedIn OAuth authorization URL with minimal scopes"""
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": "http://localhost:8502/linkedin/callback",
            # Using OpenID Connect scope instead
            "scope": "openid profile w_member_social",
            "state": state
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.auth_url}?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:8502/linkedin/callback",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(self.token_url, data=data, headers=headers)
            response.raise_for_status()
            token_data = response.json()
            
            # Get user profile immediately after token exchange
            profile = self.get_user_profile(token_data['access_token'])
            if profile:
                token_data['profile'] = profile
            
            return token_data
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None
    
    def get_user_profile(self, access_token: str) -> Optional[Dict]:
        """Get user's LinkedIn profile information using OpenID Connect"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            # Try OpenID Connect userinfo endpoint first
            userinfo_response = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=headers
            )
            
            if userinfo_response.status_code == 200:
                userinfo_data = userinfo_response.json()
                
                result = {
                    "id": userinfo_data.get("sub"),  # OpenID Connect subject
                    "firstName": userinfo_data.get("given_name", ""),
                    "lastName": userinfo_data.get("family_name", ""),
                    "fullName": userinfo_data.get("name", ""),
                    "email": userinfo_data.get("email", "Not available"),
                    "picture": userinfo_data.get("picture", "")
                }
                
                return result
            
            # Fallback to basic profile endpoint
            profile_response = requests.get(
                f"{self.base_url}/people/~:(id,firstName,lastName)",
                headers=headers
            )
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                
                result = {
                    "id": profile_data.get("id"),
                    "firstName": profile_data.get("firstName", {}).get("localized", {}).get("en_US", ""),
                    "lastName": profile_data.get("lastName", {}).get("localized", {}).get("en_US", ""),
                    "fullName": "",
                    "email": "Not available",
                    "picture": ""
                }
                
                result["fullName"] = f"{result['firstName']} {result['lastName']}".strip()
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def publish_post(self, access_token: str, content: str, hashtags: List[str] = None) -> Optional[str]:
        """Publish a post to LinkedIn"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # Get user ID first
        user_id = self._get_user_id(access_token)
        if not user_id:
            logger.error("Could not get user ID")
            return None
        
        # Prepare content with hashtags
        post_content = content
        if hashtags:
            hashtag_text = "\n\n" + " ".join([f"#{tag}" for tag in hashtags])
            post_content += hashtag_text
        
        # Prepare post data
        post_data = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers=headers,
                json=post_data
            )
            
            if response.status_code == 201:
                result = response.json()
                return result.get("id")
            else:
                logger.error(f"Failed to publish post: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error publishing post: {e}")
            return None
    
    def _get_user_id(self, access_token: str) -> Optional[str]:
        """Get user ID from access token"""
        profile = self.get_user_profile(access_token)
        return profile.get("id") if profile else None
    
    def test_connection(self, access_token: str) -> bool:
        """Test if the LinkedIn connection is working"""
        try:
            profile = self.get_user_profile(access_token)
            return profile is not None and profile.get("id") is not None
        except Exception:
            return False
