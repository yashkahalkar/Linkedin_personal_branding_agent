import google.generativeai as genai
import logging
import json
import re
from typing import List, Dict, Optional
from config.settings import settings
from models.user import UserProfile, ContentStrategy
from models.content import LinkedInPost, PostType

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def _extract_json_from_response(self, content: str) -> Dict:
        """Extract JSON from AI response, handling various formats"""
        try:
            # Try to parse the entire content as JSON first
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass
        
        # Look for JSON within markdown code blocks
        json_patterns = [
            r'``````',
            r'``````',
            r'\{.*\}',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                try:
                    # Take the first match and try to parse it
                    json_text = matches[0].strip()
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    continue
        
        # If no valid JSON found, raise an error
        raise ValueError("No valid JSON found in response")
    
    def _normalize_hashtag_strategy(self, hashtag_data) -> List[str]:
        """Convert hashtag data to flat list format"""
        if isinstance(hashtag_data, list):
            # Already in correct format
            return [tag.replace('#', '') for tag in hashtag_data if isinstance(tag, str)]
        elif isinstance(hashtag_data, dict):
            # Convert dictionary to flat list
            hashtags = []
            for category, tags in hashtag_data.items():
                if isinstance(tags, list):
                    hashtags.extend([tag.replace('#', '') for tag in tags if isinstance(tag, str)])
                elif isinstance(tags, str):
                    hashtags.append(tags.replace('#', ''))
            return hashtags
        else:
            # Fallback
            return ["linkedin", "professional", "career", "business", "networking"]
        
    def generate_content_strategy(self, user_profile: UserProfile) -> Dict:
        """Generate a comprehensive content strategy for the user"""
        prompt = f"""
        Create a comprehensive LinkedIn content strategy for:
        
        User Profile:
        - Name: {user_profile.full_name}
        - Industry: {user_profile.industry}
        - Job Title: {user_profile.job_title}
        - Company: {user_profile.company}
        - Skills: {', '.join(user_profile.skills)}
        - Interests: {', '.join(user_profile.interests)}
        - Bio: {user_profile.bio}
        - Brand Voice: {user_profile.brand_voice}
        - Target Audience: {user_profile.target_audience}
        
        IMPORTANT: Return ONLY valid JSON with this exact structure:
        {{
            "content_pillars": ["Theme 1", "Theme 2", "Theme 3", "Theme 4"],
            "hashtag_strategy": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"],
            "trending_topics": ["Topic 1", "Topic 2", "Topic 3"],
            "content_ideas": ["Idea 1", "Idea 2", "Idea 3"],
            "content_mix": {{
                "thought_leadership": 30,
                "industry_insights": 25,
                "personal_experience": 25,
                "company_updates": 20
            }}
        }}
        
        Requirements:
        - content_pillars: 4-5 main themes for content creation
        - hashtag_strategy: MUST be a flat array of 15-20 hashtag strings (without # symbol)
        - trending_topics: 8-10 current industry trends
        - content_ideas: 15-20 specific post ideas
        - content_mix: percentage distribution as numbers
        
        Return ONLY the JSON, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            strategy_data = self._extract_json_from_response(response.text)
            
            # Normalize hashtag_strategy to ensure it's a flat list
            if 'hashtag_strategy' in strategy_data:
                strategy_data['hashtag_strategy'] = self._normalize_hashtag_strategy(
                    strategy_data['hashtag_strategy']
                )
            
            return strategy_data
        except Exception as e:
            logger.error(f"Error generating content strategy: {e}")
            return self._default_content_strategy()
    
    def generate_linkedin_post(self, 
                             user_profile: UserProfile, 
                             content_strategy: ContentStrategy,
                             topic: str,
                             post_type: PostType = PostType.TEXT) -> Dict:
        """Generate a LinkedIn post based on user profile and topic"""
        
        prompt = f"""
        Create a LinkedIn post for:
        
        User: {user_profile.full_name} - {user_profile.job_title} at {user_profile.company}
        Industry: {user_profile.industry}
        Brand Voice: {user_profile.brand_voice}
        Content Pillars: {', '.join(content_strategy.content_pillars)}
        Available Hashtags: {', '.join(content_strategy.hashtag_strategy[:15])}
        
        Topic: {topic}
        Post Type: {post_type.value}
        
        Requirements:
        - Maximum {settings.MAX_POST_LENGTH} characters
        - Engaging and professional tone matching brand voice
        - Include relevant call-to-action
        - Optimize for LinkedIn algorithm
        
        Return ONLY valid JSON with this exact structure:
        {{
            "content": "The main post text here",
            "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
            "engagement_hooks": ["hook1", "hook2"],
            "confidence_score": 0.85
        }}
        
        - content: the main post text
        - hashtags: array of 3-5 hashtags (without # symbol)
        - engagement_hooks: array of engagement strategies used
        - confidence_score: number between 0 and 1
        
        Return ONLY the JSON, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._extract_json_from_response(response.text)
        except Exception as e:
            logger.error(f"Error generating LinkedIn post: {e}")
            return self._default_post_content(topic)
    
    def generate_content_ideas(self, user_profile: UserProfile, count: int = 10) -> List[str]:
        """Generate content ideas based on user profile"""
        prompt = f"""
        Generate {count} specific LinkedIn content ideas for:
        
        - Industry: {user_profile.industry}
        - Role: {user_profile.job_title}
        - Skills: {', '.join(user_profile.skills)}
        - Interests: {', '.join(user_profile.interests)}
        
        Return ONLY a JSON array of strings like this:
        ["Idea 1", "Idea 2", "Idea 3", "Idea 4", "Idea 5"]
        
        Ideas should be:
        - Relevant to their industry and role
        - Engaging and shareable
        - Mix of educational, inspirational, and personal content
        - Suitable for LinkedIn professional audience
        
        Return ONLY the JSON array, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            # Try to extract JSON array
            try:
                result = json.loads(content)
                if isinstance(result, list):
                    return result[:count]
                else:
                    return self._default_content_ideas()
            except json.JSONDecodeError:
                # Look for JSON array in the response
                array_pattern = r'\[(.*?)\]'
                matches = re.findall(array_pattern, content, re.DOTALL)
                if matches:
                    try:
                        return json.loads(f"[{matches[0]}]")[:count]
                    except json.JSONDecodeError:
                        pass
                
                # If JSON parsing fails, extract ideas manually
                ideas = []
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line.startswith('"')):
                        idea = line.lstrip('-•"').rstrip('"').strip()
                        if idea and len(ideas) < count:
                            ideas.append(idea)
                
                return ideas if ideas else self._default_content_ideas()
        except Exception as e:
            logger.error(f"Error generating content ideas: {e}")
            return self._default_content_ideas()
    
    def analyze_post_performance(self, post: LinkedInPost) -> Dict:
        """Analyze post performance and provide insights"""
        engagement_rate = post.engagement_rate
        
        prompt = f"""
        Analyze this LinkedIn post performance:
        
        Post Content: {post.content[:500]}...
        Hashtags: {', '.join(post.hashtags)}
        Metrics:
        - Likes: {post.likes_count}
        - Comments: {post.comments_count}
        - Shares: {post.shares_count}
        - Views: {post.views_count}
        - Engagement Rate: {engagement_rate}%
        
        Return ONLY valid JSON with this exact structure:
        {{
            "performance_rating": "excellent",
            "key_insights": ["Insight 1", "Insight 2"],
            "improvement_suggestions": ["Suggestion 1", "Suggestion 2"],
            "content_score": 85
        }}
        
        - performance_rating: "excellent", "good", "average", or "poor"
        - key_insights: array of insights about what worked/didn't work
        - improvement_suggestions: array of specific suggestions
        - content_score: number between 0-100
        
        Return ONLY the JSON, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._extract_json_from_response(response.text)
        except Exception as e:
            logger.error(f"Error analyzing post performance: {e}")
            return self._default_performance_analysis()
    
    def optimize_hashtags(self, content: str, industry: str) -> List[str]:
        """Generate optimized hashtags for content"""
        prompt = f"""
        Generate 10 optimized LinkedIn hashtags for this content in {industry} industry:
        
        Content: {content[:500]}
        
        Return ONLY a JSON array like this:
        ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"]
        
        Requirements:
        - Mix of popular and niche hashtags
        - Relevant to content and industry
        - Good balance of reach and engagement potential
        - WITHOUT # symbol
        
        Return ONLY the JSON array, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            content_response = response.text.strip()
            
            try:
                result = json.loads(content_response)
                if isinstance(result, list):
                    return [tag.replace('#', '') for tag in result[:10]]
                else:
                    return self._default_hashtags(industry)
            except json.JSONDecodeError:
                # Extract hashtags manually if JSON parsing fails
                hashtags = []
                lines = content_response.split('\n')
                for line in lines:
                    line = line.strip()
                    if '#' in line:
                        # Extract hashtags from line
                        tags = re.findall(r'#?(\w+)', line)
                        hashtags.extend([tag for tag in tags if len(tag) > 2])
                    elif line and (line.startswith('-') or line.startswith('•') or line.startswith('"')):
                        tag = line.lstrip('-•"').rstrip('"').strip().replace('#', '')
                        if tag and len(tag) > 2:
                            hashtags.append(tag)
                
                return hashtags[:10] if hashtags else self._default_hashtags(industry)
        except Exception as e:
            logger.error(f"Error optimizing hashtags: {e}")
            return self._default_hashtags(industry)
    
    def _default_hashtags(self, industry: str) -> List[str]:
        """Default hashtags based on industry"""
        base_tags = ["linkedin", "professional", "career", "networking"]
        industry_tag = industry.lower().replace(" ", "").replace("-", "")
        return base_tags + [industry_tag, "business", "growth"]
    
    def _default_content_strategy(self) -> Dict:
        """Default content strategy fallback"""
        return {
            "content_pillars": [
                "Industry Insights", 
                "Professional Growth", 
                "Leadership", 
                "Innovation", 
                "Career Development"
            ],
            "hashtag_strategy": [
                "linkedin", "professional", "career", "leadership", "growth", 
                "industry", "business", "networking", "success", "motivation",
                "innovation", "development", "skills", "workplace", "team"
            ],
            "trending_topics": [
                "AI trends", "Remote work", "Digital transformation", 
                "Industry innovation", "Professional development",
                "Leadership skills", "Career growth", "Workplace culture"
            ],
            "content_ideas": [
                "Share a professional achievement",
                "Industry prediction for next year", 
                "Career advice for newcomers",
                "Lessons learned from recent project",
                "Thoughts on industry trends",
                "Team collaboration success story",
                "Professional development tips",
                "Industry best practices"
            ],
            "content_mix": {
                "thought_leadership": 30,
                "industry_insights": 25,
                "personal_experience": 25,
                "company_updates": 20
            }
        }
    
    def _default_post_content(self, topic: str) -> Dict:
        """Default post content fallback"""
        return {
            "content": f"Sharing my thoughts on {topic}. This is an important topic in our industry, and I believe it's worth discussing. What's your perspective on this? I'd love to hear your thoughts in the comments.",
            "hashtags": ["linkedin", "professional", "networking", "industry", "discussion"],
            "engagement_hooks": ["question", "call-to-action", "personal-opinion"],
            "confidence_score": 0.6
        }
    
    def _default_content_ideas(self) -> List[str]:
        """Default content ideas fallback"""
        return [
            "Share a recent professional achievement",
            "Discuss current industry trends and predictions",
            "Provide career advice for newcomers in your field",
            "Share lessons learned from recent failures or challenges",
            "Highlight successful team collaboration",
            "Discuss emerging technologies in your industry",
            "Share insights from recent professional development",
            "Discuss work-life balance strategies",
            "Share thoughts on leadership and management",
            "Discuss industry best practices"
        ]
    
    def _default_performance_analysis(self) -> Dict:
        """Default performance analysis fallback"""
        return {
            "performance_rating": "average",
            "key_insights": [
                "Standard engagement levels for this type of content",
                "Post timing may have affected reach",
                "Content resonated with core audience"
            ],
            "improvement_suggestions": [
                "Add more engaging visuals or media",
                "Include a clear call-to-action",
                "Post during peak engagement hours",
                "Use more relevant hashtags"
            ],
            "content_score": 60
        }
