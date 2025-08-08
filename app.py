import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
import json
import uuid
import webbrowser
import time
try:
    from oauth_handler import start_oauth_server, get_oauth_result, clear_oauth_result
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

# Import services
from services.database_service import DatabaseService
from services.cache_service import CacheService
from services.ai_service import AIService
from services.linkedin_service import LinkedInService

# Import models
from models.user import UserProfile, ContentStrategy
from models.content import LinkedInPost, PostType, PostStatus, ContentCalendar

# Page config
st.set_page_config(
    page_title="LinkedIn AI Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def init_services():
    return {
        'db': DatabaseService(),
        'cache': CacheService(),
        'ai': AIService(),
        'linkedin': LinkedInService()
    }

services = init_services()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Sidebar navigation
def sidebar_navigation():
    st.sidebar.title("🚀 LinkedIn AI Agent")
    
    if st.session_state.user_id:
        st.sidebar.success(f"Welcome, {st.session_state.current_user.full_name}!")
        
        pages = {
            "🏠 Dashboard": "dashboard",
            "👤 Profile Setup": "profile",
            "🎯 Content Strategy": "strategy",
            "✍️ Content Generator": "generator",
            "📅 Content Calendar": "calendar",
            "📊 Analytics": "analytics",
            "⚙️ Settings": "settings"
        }
        
        selected_page = st.sidebar.selectbox("Navigation", list(pages.keys()))
        
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.session_state.current_user = None
            st.rerun()
        
        return pages[selected_page]
    else:
        return "login"

# Login/Registration page
def login_page():
    st.title("🚀 LinkedIn Personal Branding AI Agent")
    st.markdown("Transform your LinkedIn presence with AI-powered content creation and analytics.")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        email = st.text_input("Email")
        if st.button("Login", key="login_btn"):
            # Simple email-based login (in production, use proper authentication)
            user = services['db'].users.find_one({"email": email})
            if user:
                st.session_state.user_id = user['user_id']
                st.session_state.current_user = UserProfile(**user)
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("User not found. Please register first.")
    
    with tab2:
        st.subheader("Create New Account")
        with st.form("registration_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name")
                email = st.text_input("Email")
                industry = st.selectbox("Industry", [
                    "Technology", "Healthcare", "Finance", "Education", "Marketing",
                    "Sales", "Consulting", "Manufacturing", "Real Estate", "Other"
                ])
                company = st.text_input("Company")
            
            with col2:
                last_name = st.text_input("Last Name")
                job_title = st.text_input("Job Title")
                brand_voice = st.selectbox("Brand Voice", [
                    "professional", "casual", "authoritative", "friendly"
                ])
                target_audience = st.text_input("Target Audience")
            
            skills = st.text_area("Skills (comma-separated)").split(",")
            interests = st.text_area("Interests (comma-separated)").split(",")
            bio = st.text_area("Professional Bio")
            
            if st.form_submit_button("Register"):
                if first_name and last_name and email and industry and job_title:
                    user_id = str(uuid.uuid4())
                    user_profile = UserProfile(
                        user_id=user_id,
                        email=email,
                        full_name=f"{first_name} {last_name}",
                        industry=industry,
                        job_title=job_title,
                        company=company,
                        skills=[s.strip() for s in skills if s.strip()],
                        interests=[i.strip() for i in interests if i.strip()],
                        bio=bio,
                        brand_voice=brand_voice,
                        target_audience=target_audience
                    )
                    
                    if services['db'].create_user(user_profile):
                        st.session_state.user_id = user_id
                        st.session_state.current_user = user_profile
                        st.success("Registration successful!")
                        st.rerun()
                    else:
                        st.error("Registration failed. Email might already exist.")
                else:
                    st.error("Please fill in all required fields.")

# Dashboard page
def dashboard_page():
    st.title("📊 Dashboard")
    
    user = st.session_state.current_user
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    user_posts = services['db'].get_user_posts(user.user_id, limit=100)
    total_posts = len(user_posts)
    
    with col1:
        st.metric("Total Posts", total_posts)
    
    with col2:
        avg_engagement = sum(post.engagement_rate for post in user_posts) / max(total_posts, 1)
        st.metric("Avg Engagement Rate", f"{avg_engagement:.1f}%")
    
    with col3:
        scheduled_posts = services['db'].get_scheduled_posts(user.user_id)
        st.metric("Scheduled Posts", len(scheduled_posts))
    
    with col4:
        total_likes = sum(post.likes_count for post in user_posts)
        st.metric("Total Likes", total_likes)
    
    # Recent activity
    st.subheader("Recent Posts")
    if user_posts:
        for post in user_posts[:5]:
            with st.expander(f"Post from {post.created_at.strftime('%Y-%m-%d')} - {post.status}"):
                st.write(post.content[:200] + "..." if len(post.content) > 200 else post.content)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Likes", post.likes_count)
                col2.metric("Comments", post.comments_count)
                col3.metric("Shares", post.shares_count)
    else:
        st.info("No posts yet. Start creating content in the Content Generator!")
    
    # Engagement chart
    if user_posts:
        st.subheader("Engagement Over Time")
        df = pd.DataFrame([{
            'date': post.created_at,
            'engagement_rate': post.engagement_rate,
            'likes': post.likes_count,
            'comments': post.comments_count,
            'shares': post.shares_count
        } for post in user_posts])
        
        fig = px.line(df, x='date', y='engagement_rate', title='Engagement Rate Over Time')
        st.plotly_chart(fig, use_container_width=True)

# Profile setup page
def profile_page():
    st.title("👤 Profile Setup")
    
    user = st.session_state.current_user
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name", value=user.full_name)
            email = st.text_input("Email", value=user.email)
            industry = st.selectbox("Industry", [
                "Technology", "Healthcare", "Finance", "Education", "Marketing",
                "Sales", "Consulting", "Manufacturing", "Real Estate", "Other"
            ], index=0 if user.industry == "Technology" else 0)
            job_title = st.text_input("Job Title", value=user.job_title)
            company = st.text_input("Company", value=user.company)
        
        with col2:
            brand_voice = st.selectbox("Brand Voice", [
                "professional", "casual", "authoritative", "friendly"
            ], index=["professional", "casual", "authoritative", "friendly"].index(user.brand_voice))
            
            target_audience = st.text_input("Target Audience", value=user.target_audience)
            posting_frequency = st.number_input("Posts per Week", min_value=1, max_value=7, value=user.posting_frequency)
            
            linkedin_url = st.text_input("LinkedIn Profile URL", value=user.linkedin_profile_url or "")
        
        skills = st.text_area("Skills (comma-separated)", value=", ".join(user.skills))
        interests = st.text_area("Interests (comma-separated)", value=", ".join(user.interests))
        bio = st.text_area("Professional Bio", value=user.bio)
        
        if st.form_submit_button("Update Profile"):
            update_data = {
                "full_name": full_name,
                "email": email,
                "industry": industry,
                "job_title": job_title,
                "company": company,
                "brand_voice": brand_voice,
                "target_audience": target_audience,
                "posting_frequency": posting_frequency,
                "linkedin_profile_url": linkedin_url,
                "skills": [s.strip() for s in skills.split(",") if s.strip()],
                "interests": [i.strip() for i in interests.split(",") if i.strip()],
                "bio": bio
            }
            
            if services['db'].update_user(user.user_id, update_data):
                # Update session state
                for key, value in update_data.items():
                    setattr(st.session_state.current_user, key, value)
                st.success("Profile updated successfully!")
            else:
                st.error("Failed to update profile.")

# Content strategy page
def strategy_page():
    st.title("🎯 Content Strategy")
    
    user = st.session_state.current_user
    
    # Check if strategy exists
    strategy = services['db'].get_content_strategy(user.user_id)
    
    if not strategy:
        st.info("No content strategy found. Let's create one!")
        
        if st.button("Generate AI-Powered Content Strategy"):
            with st.spinner("Generating your personalized content strategy..."):
                try:
                    strategy_data = services['ai'].generate_content_strategy(user)
                    
                    strategy = ContentStrategy(
                        user_id=user.user_id,
                        content_pillars=strategy_data.get('content_pillars', []),
                        hashtag_strategy=strategy_data.get('hashtag_strategy', []),
                        trending_topics=strategy_data.get('trending_topics', []),
                        content_mix=strategy_data.get('content_mix', {})
                    )
                    
                    services['db'].save_content_strategy(strategy)
                    st.success("Content strategy generated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating strategy: {e}")
    
    if strategy:
        st.subheader("Your Content Strategy")
        
        # Content pillars
        st.subheader("📋 Content Pillars")
        col1, col2 = st.columns(2)
        
        with col1:
            for i, pillar in enumerate(strategy.content_pillars[:len(strategy.content_pillars)//2]):
                st.info(f"🎯 {pillar}")
        
        with col2:
            for i, pillar in enumerate(strategy.content_pillars[len(strategy.content_pillars)//2:]):
                st.info(f"🎯 {pillar}")
        
        # Hashtag strategy
        st.subheader("🏷️ Hashtag Strategy")
        hashtag_cols = st.columns(4)
        for i, hashtag in enumerate(strategy.hashtag_strategy[:12]):
            hashtag_cols[i % 4].write(f"#{hashtag}")
        
        # Trending topics
        st.subheader("📈 Trending Topics")
        trending_cols = st.columns(3)
        for i, topic in enumerate(strategy.trending_topics[:9]):
            trending_cols[i % 3].write(f"🔥 {topic}")
        
        # Content mix visualization
        if strategy.content_mix:
            st.subheader("📊 Content Mix")
            fig = px.pie(
                values=list(strategy.content_mix.values()),
                names=list(strategy.content_mix.keys()),
                title="Recommended Content Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Update strategy
        if st.button("Regenerate Strategy"):
            with st.spinner("Regenerating strategy..."):
                try:
                    strategy_data = services['ai'].generate_content_strategy(user)
                    strategy.content_pillars = strategy_data.get('content_pillars', [])
                    strategy.hashtag_strategy = strategy_data.get('hashtag_strategy', [])
                    strategy.trending_topics = strategy_data.get('trending_topics', [])
                    strategy.content_mix = strategy_data.get('content_mix', {})
                    
                    services['db'].save_content_strategy(strategy)
                    st.success("Strategy updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating strategy: {e}")

# Content generator page
def generator_page():
    st.title("✍️ Content Generator")
    
    user = st.session_state.current_user
    strategy = services['db'].get_content_strategy(user.user_id)
    
    if not strategy:
        st.warning("Please create a content strategy first!")
        if st.button("Go to Strategy Page"):
            st.session_state.page = "strategy"
            st.rerun()
        return
    
    # Content generation form
    st.subheader("Generate New Content")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Content ideas from cache or generate new
        cached_ideas = services['cache'].get_content_ideas(user.user_id)
        if not cached_ideas:
            with st.spinner("Generating content ideas..."):
                cached_ideas = services['ai'].generate_content_ideas(user, count=20)
                services['cache'].cache_content_ideas(user.user_id, cached_ideas)
        
        topic = st.selectbox("Select Topic", ["Custom Topic"] + cached_ideas)
        
        if topic == "Custom Topic":
            topic = st.text_input("Enter your custom topic")
        
        post_type = st.selectbox("Post Type", ["text", "article", "carousel", "poll"])
        
        if st.button("Generate Content", type="primary"):
            if topic and topic != "Custom Topic":
                with st.spinner("Generating your LinkedIn post..."):
                    try:
                        content_data = services['ai'].generate_linkedin_post(
                            user, strategy, topic, PostType(post_type)
                        )
                        
                        # Create post object
                        post = LinkedInPost(
                            post_id=str(uuid.uuid4()),
                            user_id=user.user_id,
                            content=content_data.get('content', ''),
                            post_type=PostType(post_type),
                            hashtags=content_data.get('hashtags', []),
                            generated_from_topic=topic,
                            ai_confidence_score=content_data.get('confidence_score', 0.0),
                            status=PostStatus.DRAFT
                        )
                        
                        # Save to session state for preview
                        st.session_state.generated_post = post
                        st.success("Content generated successfully!")
                        
                    except Exception as e:
                        st.error(f"Error generating content: {e}")
            else:
                st.error("Please select or enter a topic.")
    
    with col2:
        st.subheader("Quick Actions")
        if st.button("🔄 Refresh Ideas"):
            # Clear cache and regenerate
            services['cache'].delete(f"content_ideas:{user.user_id}")
            st.rerun()
        
        if st.button("📈 Get Trending Topics"):
            # This would integrate with real trend analysis
            st.info("Feature coming soon!")
    
    # Preview generated content
    if 'generated_post' in st.session_state:
        st.subheader("Generated Content Preview")
        post = st.session_state.generated_post
        
        with st.container():
            st.text_area("Content", value=post.content, height=200, disabled=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Hashtags:**")
                st.write(" ".join([f"#{tag}" for tag in post.hashtags]))
            
            with col2:
                st.write("**AI Confidence:**")
                st.progress(post.ai_confidence_score)
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("💾 Save as Draft"):
                    if services['db'].save_post(post):
                        st.success("Saved as draft!")
                        del st.session_state.generated_post
                    else:
                        st.error("Failed to save.")
            
            with col2:
                if st.button("📅 Schedule Post"):
                    st.session_state.scheduling_post = post
                    st.info("Set schedule time below.")
            
            with col3:
                if st.button("🚀 Publish Now"):
                    if user.linkedin_access_token:
                        with st.spinner("Publishing to LinkedIn..."):
                            linkedin_service = services['linkedin']
                            post_id = linkedin_service.publish_post(
                                user.linkedin_access_token,
                                post.content,
                                post.hashtags
                            )
                            
                            if post_id:
                                # Update post status
                                post.status = PostStatus.PUBLISHED
                                post.published_time = datetime.utcnow()
                                post.linkedin_post_id = post_id
                                
                                if services['db'].save_post(post):
                                    st.success(f"✅ Post published successfully to LinkedIn!")
                                    st.info(f"LinkedIn Post ID: {post_id}")
                                    del st.session_state.generated_post
                                else:
                                    st.error("Published to LinkedIn but failed to update database.")
                            else:
                                st.error("❌ Failed to publish to LinkedIn. Check your connection.")
                    else:
                        st.warning("Please connect your LinkedIn account in Settings first.")
            
            with col4:
                if st.button("✨ Regenerate"):
                    del st.session_state.generated_post
                    st.rerun()
    
    # Scheduling interface
    if 'scheduling_post' in st.session_state:
        st.subheader("Schedule Post")
        
        col1, col2 = st.columns(2)
        with col1:
            scheduled_date = st.date_input("Date", min_value=datetime.now().date())
        with col2:
            scheduled_time = st.time_input("Time")
        
        if st.button("Confirm Schedule"):
            post = st.session_state.scheduling_post
            post.scheduled_time = datetime.combine(scheduled_date, scheduled_time)
            post.status = PostStatus.SCHEDULED
            
            if services['db'].save_post(post):
                st.success(f"Post scheduled for {post.scheduled_time}")
                del st.session_state.scheduling_post
                if 'generated_post' in st.session_state:
                    del st.session_state.generated_post
            else:
                st.error("Failed to schedule post.")

# Content calendar page
def calendar_page():
    st.title("📅 Content Calendar")
    
    user = st.session_state.current_user
    
    # Month selection
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox("Month", range(1, 13), 
                                    index=datetime.now().month - 1,
                                    format_func=lambda x: datetime(2023, x, 1).strftime('%B'))
    with col2:
        selected_year = st.selectbox("Year", range(2023, 2026), 
                                   index=datetime.now().year - 2023)
    
    # Get calendar data
    calendar_data = services['db'].get_calendar(user.user_id, selected_month, selected_year)
    scheduled_posts = services['db'].get_scheduled_posts(user.user_id)
    
    # Filter posts for selected month
    month_posts = [
        post for post in scheduled_posts 
        if post.scheduled_time and 
        post.scheduled_time.month == selected_month and 
        post.scheduled_time.year == selected_year
    ]
    
    # Calendar visualization
    st.subheader(f"Calendar for {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")
    
    # Create calendar grid
    import calendar as cal
    
    # Get calendar for the month
    month_calendar = cal.monthcalendar(selected_year, selected_month)
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Display calendar
    cols = st.columns(7)
    for i, day in enumerate(weekdays):
        cols[i].write(f"**{day}**")
    
    for week in month_calendar:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                # Check if there are posts on this day
                day_posts = [
                    post for post in month_posts 
                    if post.scheduled_time.day == day
                ]
                
                if day_posts:
                    cols[i].success(f"**{day}**\n{len(day_posts)} post(s)")
                else:
                    cols[i].write(f"{day}")
    
    # Scheduled posts list
    st.subheader("Scheduled Posts")
    if month_posts:
        for post in sorted(month_posts, key=lambda x: x.scheduled_time):
            with st.expander(f"{post.scheduled_time.strftime('%Y-%m-%d %H:%M')} - {post.post_type.value}"):
                st.write(post.content[:200] + "..." if len(post.content) > 200 else post.content)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Edit", key=f"edit_{post.post_id}"):
                        st.info("Edit functionality coming soon!")
                
                with col2:
                    if st.button("Reschedule", key=f"reschedule_{post.post_id}"):
                        st.info("Reschedule functionality coming soon!")
                
                with col3:
                    if st.button("Delete", key=f"delete_{post.post_id}"):
                        # Delete post logic
                        st.info("Delete functionality coming soon!")
    else:
        st.info("No posts scheduled for this month.")
    
    # Quick scheduling
    st.subheader("Quick Schedule")
    with st.form("quick_schedule"):
        content = st.text_area("Post Content")
        hashtags = st.text_input("Hashtags (comma-separated)")
        schedule_date = st.date_input("Date")
        schedule_time = st.time_input("Time")
        
        if st.form_submit_button("Schedule Post"):
            if content:
                post = LinkedInPost(
                    post_id=str(uuid.uuid4()),
                    user_id=user.user_id,
                    content=content,
                    hashtags=[h.strip() for h in hashtags.split(",") if h.strip()],
                    scheduled_time=datetime.combine(schedule_date, schedule_time),
                    status=PostStatus.SCHEDULED
                )
                
                if services['db'].save_post(post):
                    st.success("Post scheduled successfully!")
                    st.rerun()
                else:
                    st.error("Failed to schedule post.")

# Analytics page
def analytics_page():
    st.title("📊 Analytics")
    
    user = st.session_state.current_user
    user_posts = services['db'].get_user_posts(user.user_id, limit=100)
    
    if not user_posts:
        st.info("No posts available for analysis. Create some content first!")
        return
    
    # Overview metrics
    st.subheader("Performance Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_posts = len(user_posts)
    total_likes = sum(post.likes_count for post in user_posts)
    total_comments = sum(post.comments_count for post in user_posts)
    avg_engagement = sum(post.engagement_rate for post in user_posts) / total_posts
    
    col1.metric("Total Posts", total_posts)
    col2.metric("Total Likes", total_likes)
    col3.metric("Total Comments", total_comments)
    col4.metric("Avg Engagement", f"{avg_engagement:.1f}%")
    
    # Engagement trends
    st.subheader("Engagement Trends")
    
    # Create DataFrame for analysis
    df = pd.DataFrame([{
        'date': post.created_at.date(),
        'engagement_rate': post.engagement_rate,
        'likes': post.likes_count,
        'comments': post.comments_count,
        'shares': post.shares_count,
        'post_type': post.post_type.value,
        'content_length': len(post.content),
        'hashtag_count': len(post.hashtags)
    } for post in user_posts])
    
    # Engagement over time
    fig = px.line(df, x='date', y='engagement_rate', 
                  title='Engagement Rate Over Time')
    st.plotly_chart(fig, use_container_width=True)
    
    # Post type performance
    col1, col2 = st.columns(2)
    
    with col1:
        post_type_performance = df.groupby('post_type')['engagement_rate'].mean()
        fig = px.bar(x=post_type_performance.index, y=post_type_performance.values,
                     title='Average Engagement by Post Type')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Content length vs engagement
        fig = px.scatter(df, x='content_length', y='engagement_rate',
                        title='Content Length vs Engagement')
        st.plotly_chart(fig, use_container_width=True)
    
    # Top performing posts
    st.subheader("Top Performing Posts")
    top_posts = sorted(user_posts, key=lambda x: x.engagement_rate, reverse=True)[:5]
    
    for i, post in enumerate(top_posts, 1):
        with st.expander(f"#{i} - {post.engagement_rate:.1f}% engagement"):
            st.write(post.content[:300] + "..." if len(post.content) > 300 else post.content)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Likes", post.likes_count)
            col2.metric("Comments", post.comments_count)
            col3.metric("Shares", post.shares_count)
            col4.metric("Views", post.views_count)
    
    # AI insights
    st.subheader("AI Insights")
    if st.button("Generate Performance Insights"):
        with st.spinner("Analyzing your content performance..."):
            # Analyze top performing post
            if top_posts:
                insights = services['ai'].analyze_post_performance(top_posts[0])
                
                st.success("Analysis Complete!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Key Insights:**")
                    for insight in insights.get('key_insights', []):
                        st.write(f"• {insight}")
                
                with col2:
                    st.write("**Improvement Suggestions:**")
                    for suggestion in insights.get('improvement_suggestions', []):
                        st.write(f"• {suggestion}")
                
                st.info(f"Performance Rating: {insights.get('performance_rating', 'N/A').title()}")

# Settings page
def settings_page():
    st.title("⚙️ Settings")

    user = st.session_state.current_user

    # Initialize OAuth server state
    if 'oauth_server_started' not in st.session_state:
        st.session_state.oauth_server_started = False

    # Check if OAuth handler is available
    try:
        from oauth_handler import start_oauth_server, get_oauth_result, clear_oauth_result
        OAUTH_AVAILABLE = True
    except ImportError:
        OAUTH_AVAILABLE = False

    # =================================================================
    # LINKEDIN INTEGRATION SECTION
    # =================================================================
    st.subheader("🔗 LinkedIn Integration")

    if user.linkedin_access_token:
        # Test existing connection
        linkedin_service = services['linkedin']

        with st.spinner("Testing LinkedIn connection..."):
            connection_valid = linkedin_service.test_connection(user.linkedin_access_token)

        if connection_valid:
            st.success("✅ LinkedIn account connected and working!")

            # Show connected account info
        try:
            profile = linkedin_service.get_user_profile(user.linkedin_access_token)
            if profile:
                col1, col2 = st.columns([2, 1])
                with col1:
                    # Updated display without email requirement
                    full_name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}"
                    headline = profile.get('headline', 'No headline available')

                    st.info(f"**Connected as:** {full_name}")
                    if headline != "No headline available":
                        st.caption(f"*{headline}*")

                    # Only show email if available
                    email = profile.get('email', '')
                    if email and email != "Not available (scope not authorized)":
                        st.caption(f"📧 {email}")
                    else:
                        st.caption("📧 Email not available (requires additional LinkedIn approval)")

                with col2:
                    if st.button("🔄 Refresh Profile"):
                        st.rerun()
        except Exception as e:
            st.warning(f"Could not fetch profile details: {e}")

            # LinkedIn Actions
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🧪 Test Post", help="Publish a test post to verify connection"):
                    test_content = f"🤖 Test post from LinkedIn AI Agent at {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\nThis is an automated test to verify my LinkedIn integration is working correctly!"
                    test_hashtags = ["linkedintest", "ai", "automation", "testing"]

                    with st.spinner("Publishing test post to LinkedIn..."):
                        post_id = linkedin_service.publish_post(
                            user.linkedin_access_token,
                            test_content,
                            test_hashtags
                        )

                        if post_id:
                            st.success(f"✅ Test post published successfully!")
                            st.balloons()
                            st.info(f"LinkedIn Post ID: {post_id}")
                        else:
                            st.error("❌ Failed to publish test post. Please check your LinkedIn permissions or try reconnecting.")

            with col2:
                if st.button("📊 Connection Info", help="View detailed connection information"):
                    st.json({
                        "Status": "Connected",
                        "Token Available": bool(user.linkedin_access_token),
                        "Last Updated": user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else "Unknown"
                    })

            with col3:
                if st.button("🔌 Disconnect", help="Disconnect your LinkedIn account", type="secondary"):
                    if st.button("⚠️ Confirm Disconnect", type="secondary"):
                        success = services['db'].update_user(user.user_id, {
                            "linkedin_access_token": None,
                            "linkedin_refresh_token": None
                        })

                        if success:
                            user.linkedin_access_token = None
                            user.linkedin_refresh_token = None
                            st.success("LinkedIn account disconnected successfully.")
                            st.rerun()
                        else:
                            st.error("Failed to disconnect LinkedIn account.")
        else:
            st.warning("⚠️ LinkedIn connection exists but is not working properly.")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Possible issues:**")
                st.write("• Token has expired")
                st.write("• LinkedIn API permissions changed")
                st.write("• Network connectivity issues")

            with col2:
                if st.button("🔄 Reconnect LinkedIn", type="primary"):
                    # Clear existing tokens
                    services['db'].update_user(user.user_id, {
                        "linkedin_access_token": None,
                        "linkedin_refresh_token": None
                    })
                    user.linkedin_access_token = None
                    user.linkedin_refresh_token = None
                    st.info("Previous connection cleared. Please connect again below.")
                    st.rerun()
    else:
        # No LinkedIn connection - show connection interface
        st.info("Connect your LinkedIn account to enable automatic posting and enhanced features.")

        # Prerequisites check
        with st.expander("📋 Prerequisites for LinkedIn Integration"):
            st.write("**Before connecting, ensure you have:**")
            st.write("1. ✅ A LinkedIn Developer App created")
            st.write("2. ✅ Client ID and Secret in your .env file")
            st.write("3. ✅ Redirect URL set to: `http://localhost:8502/linkedin/callback`")
            st.write("4. ✅ Required permissions: `r_liteprofile`, `r_emailaddress`, `w_member_social`")

            if st.button("📖 View Setup Instructions"):
                st.markdown("""
                **LinkedIn Developer Setup Steps:**
                1. Visit [LinkedIn Developers](https://developer.linkedin.com/)
                2. Create a new app
                3. Add redirect URL: `http://localhost:8502/linkedin/callback`
                4. Request required permissions
                5. Copy Client ID and Secret to your .env file
                """)

        if OAUTH_AVAILABLE:
            st.success("OAuth handler is available and ready!")

            col1, col2 = st.columns([3, 1])

            with col1:
                if st.button("🔗 Connect LinkedIn Account", type="primary", help="Start LinkedIn OAuth flow"):
                    # Start OAuth server if not running
                    if not st.session_state.oauth_server_started:
                        try:
                            start_oauth_server()
                            st.session_state.oauth_server_started = True
                            st.success("OAuth server started on port 8502!")
                        except Exception as e:
                            st.error(f"Failed to start OAuth server: {e}")
                            st.info("Make sure port 8502 is available and try again.")
                            return

                    # Generate unique state for OAuth security
                    oauth_state = str(uuid.uuid4())
                    st.session_state.oauth_state = oauth_state
                    st.session_state.oauth_timestamp = time.time()

                    # Generate LinkedIn authorization URL
                    auth_url = services['linkedin'].get_authorization_url(oauth_state)

                    st.markdown("### 🚀 LinkedIn Authorization Process")
                    st.markdown("""
                    **Step 1**: Click the button below to open LinkedIn authorization

                    **Step 2**: Sign in to LinkedIn and authorize the app

                    **Step 3**: You'll be redirected back automatically

                    **Step 4**: Come back here and click "Check Connection Status"
                    """)

                    # LinkedIn authorization button
                    st.markdown(f'''
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{auth_url}" target="_blank" 
                           style="background-color: #0077B5; color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 8px; font-weight: bold;
                                  display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                            🔗 Open LinkedIn Authorization
                        </a>
                    </div>
                    ''', unsafe_allow_html=True)

                    st.info("💡 A new tab will open. Complete the authorization and return here.")

            with col2:
                if st.button("🔄 Check Status", help="Check if authorization was completed"):
                    if 'oauth_state' in st.session_state:
                        # Check for timeout (5 minutes)
                        if time.time() - st.session_state.get('oauth_timestamp', 0) > 300:
                            st.warning("Authorization session expired. Please try connecting again.")
                            if 'oauth_state' in st.session_state:
                                del st.session_state.oauth_state
                            return

                        oauth_result = get_oauth_result(st.session_state.oauth_state)

                        if oauth_result:
                            if oauth_result.get('success'):
                                token_data = oauth_result.get('token_data', {})
                                access_token = token_data.get('access_token')
                                refresh_token = token_data.get('refresh_token')

                                if access_token:
                                    # Test the token immediately
                                    if services['linkedin'].test_connection(access_token):
                                        # Save tokens to database
                                        update_success = services['db'].update_user(user.user_id, {
                                            "linkedin_access_token": access_token,
                                            "linkedin_refresh_token": refresh_token
                                        })

                                        if update_success:
                                            user.linkedin_access_token = access_token
                                            user.linkedin_refresh_token = refresh_token
                                            clear_oauth_result(st.session_state.oauth_state)

                                            # Clean up session state
                                            del st.session_state.oauth_state

                                            st.success("✅ LinkedIn connected successfully!")
                                            st.balloons()

                                            # Show profile info
                                            profile = services['linkedin'].get_user_profile(access_token)
                                            if profile:
                                                st.info(f"Connected as: {profile.get('firstName', '')} {profile.get('lastName', '')}")

                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error("Failed to save LinkedIn token to database.")
                                    else:
                                        st.error("Token received but connection test failed. Please try again.")
                                else:
                                    st.error("No access token received from LinkedIn.")
                            else:
                                error = oauth_result.get('error', 'Unknown error')
                                st.error(f"LinkedIn authorization failed: {error}")
                                clear_oauth_result(st.session_state.oauth_state)
                                if 'oauth_state' in st.session_state:
                                    del st.session_state.oauth_state
                        else:
                            st.info("⏳ Authorization in progress... Make sure you completed the LinkedIn authorization in the new tab.")
                    else:
                        st.warning("Please click 'Connect LinkedIn Account' first to start the authorization process.")
        else:
            st.error("❌ OAuth handler not available.")
            st.markdown("**To enable LinkedIn integration:**")
            st.code("pip install flask", language="bash")
            st.write("Then restart the application.")

    st.divider()

    # =================================================================
    # POSTING PREFERENCES SECTION
    # =================================================================
    st.subheader("📝 Posting Preferences")

    with st.form("posting_preferences", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**📅 Posting Schedule**")
            posting_frequency = st.number_input(
                "Posts per week",
                min_value=1,
                max_value=7,
                value=user.posting_frequency,
                help="How many posts you want to publish per week"
            )

            auto_publish = st.checkbox(
                "Enable auto-publishing",
                value=False,
                help="Automatically publish scheduled posts (requires LinkedIn connection)"
            )

        with col2:
            st.write("**⏰ Preferred Posting Times**")
            time_slots = []

            for i in range(3):
                default_time_str = user.preferred_posting_times[i] if i < len(user.preferred_posting_times) else "09:00"
                try:
                    default_time = datetime.strptime(default_time_str, "%H:%M").time()
                except:
                    default_time = datetime.strptime("09:00", "%H:%M").time()

                time_slot = st.time_input(
                    f"Time slot {i+1}",
                    value=default_time,
                    help=f"Preferred time for posting slot {i+1}"
                )
                time_slots.append(time_slot.strftime("%H:%M"))

        st.write("**🎯 Content Preferences**")
        col3, col4 = st.columns(2)

        with col3:
            default_post_length = st.selectbox(
                "Default post length",
                ["Short (< 300 chars)", "Medium (300-800 chars)", "Long (800+ chars)"],
                index=1
            )

            include_emojis = st.checkbox("Include emojis in posts", value=True)

        with col4:
            include_cta = st.checkbox("Always include call-to-action", value=True)

            personal_touch = st.slider(
                "Personal touch level",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Formal, 5 = Very personal"
            )

        if st.form_submit_button("💾 Update Preferences", type="primary"):
            update_data = {
                "posting_frequency": posting_frequency,
                "preferred_posting_times": time_slots
            }

            if services['db'].update_user(user.user_id, update_data):
                user.posting_frequency = posting_frequency
                user.preferred_posting_times = time_slots
                st.success("✅ Posting preferences updated successfully!")
            else:
                st.error("❌ Failed to update preferences.")

    st.divider()

    # =================================================================
    # ACCOUNT & PROFILE SECTION
    # =================================================================
    st.subheader("👤 Account & Profile")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Account Information**")
        st.info(f"**User ID:** {user.user_id}")
        st.info(f"**Email:** {user.email}")
        st.info(f"**Name:** {user.full_name}")
        st.info(f"**Industry:** {user.industry}")
        st.info(f"**Company:** {user.company}")

        if st.button("✏️ Edit Profile"):
            st.info("Use the Profile Setup page to edit your profile details.")

    with col2:
        st.write("**Account Statistics**")

        # Get user statistics
        user_posts = services['db'].get_user_posts(user.user_id, limit=1000)
        total_posts = len(user_posts)
        scheduled_posts = len(services['db'].get_scheduled_posts(user.user_id))

        avg_engagement = sum(post.engagement_rate for post in user_posts) / max(total_posts, 1)

        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Total Posts", total_posts)
            st.metric("Scheduled Posts", scheduled_posts)

        with col_stat2:
            st.metric("Avg Engagement", f"{avg_engagement:.1f}%")
            st.metric("Account Age", f"{(datetime.now() - user.created_at).days} days")

    st.divider()

    # =================================================================
    # DATA MANAGEMENT SECTION
    # =================================================================
    st.subheader("💾 Data Management")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**📤 Export Data**")
        st.write("Download all your data including profile, posts, and analytics.")

        if st.button("📊 Generate Export", help="Create a comprehensive data export"):
            with st.spinner("Preparing your data export..."):
                try:
                    # Gather all user data
                    user_posts = services['db'].get_user_posts(user.user_id, limit=1000)
                    strategy = services['db'].get_content_strategy(user.user_id)

                    export_data = {
                        "export_info": {
                            "generated_at": datetime.now().isoformat(),
                            "user_id": user.user_id,
                            "version": "1.0"
                        },
                        "profile": user.dict(),
                        "content_strategy": strategy.dict() if strategy else None,
                        "posts": [post.dict() for post in user_posts],
                        "statistics": {
                            "total_posts": len(user_posts),
                            "total_likes": sum(post.likes_count for post in user_posts),
                            "total_comments": sum(post.comments_count for post in user_posts),
                            "total_shares": sum(post.shares_count for post in user_posts),
                            "average_engagement": avg_engagement
                        }
                    }

                    # Convert to JSON with proper formatting
                    json_data = json.dumps(export_data, indent=2, default=str)

                    st.download_button(
                        label="💾 Download JSON Export",
                        data=json_data,
                        file_name=f"linkedin_ai_data_{user.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        help="Download your complete data export"
                    )

                    st.success("✅ Export ready for download!")

                except Exception as e:
                    st.error(f"Failed to generate export: {e}")

    with col2:
        st.write("**🗑️ Data Deletion**")
        st.write("Permanently delete all your data from the system.")

        st.warning("⚠️ **Warning**: This action cannot be undone!")

        # Two-step deletion process for safety
        if 'deletion_confirmed' not in st.session_state:
            st.session_state.deletion_confirmed = False

        if not st.session_state.deletion_confirmed:
            if st.button("🗑️ Request Data Deletion", type="secondary"):
                st.session_state.deletion_confirmed = True
                st.rerun()
        else:
            st.error("**FINAL WARNING**: This will permanently delete ALL your data!")
            st.write("This includes:")
            st.write("• Your profile and preferences")
            st.write("• All generated and scheduled posts")
            st.write("• Content strategy and analytics")
            st.write("• LinkedIn connection tokens")

            col_confirm1, col_confirm2 = st.columns(2)

            with col_confirm1:
                if st.button("❌ Cancel", type="secondary"):
                    st.session_state.deletion_confirmed = False
                    st.rerun()

            with col_confirm2:
                if st.button("💥 PERMANENTLY DELETE", type="secondary"):
                    try:
                        # Delete all user data
                        services['db'].users.delete_one({"user_id": user.user_id})
                        services['db'].posts.delete_many({"user_id": user.user_id})
                        services['db'].content_strategies.delete_one({"user_id": user.user_id})
                        services['db'].calendars.delete_many({"user_id": user.user_id})

                        # Clear cache
                        services['cache'].delete(f"session:{user.user_id}")
                        services['cache'].delete(f"content_ideas:{user.user_id}")

                        # Clear session
                        st.session_state.user_id = None
                        st.session_state.current_user = None
                        st.session_state.deletion_confirmed = False

                        st.success("✅ All data deleted successfully.")
                        st.info("You will be redirected to the login page.")
                        time.sleep(2)
                        st.rerun()

                    except Exception as e:
                        st.error(f"Failed to delete data: {e}")

    st.divider()

    # =================================================================
    # ADVANCED SETTINGS SECTION
    # =================================================================
    st.subheader("⚙️ Advanced Settings")

    with st.expander("🔧 System Configuration"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Cache Management**")
            if st.button("🧹 Clear Cache"):
                try:
                    services['cache'].delete(f"session:{user.user_id}")
                    services['cache'].delete(f"content_ideas:{user.user_id}")
                    st.success("Cache cleared successfully!")
                except Exception as e:
                    st.error(f"Failed to clear cache: {e}")

        with col2:
            st.write("**Database Connection**")
            try:
                # Test database connection
                services['db'].users.find_one({"user_id": user.user_id})
                st.success("✅ Database connection healthy")
            except Exception as e:
                st.error(f"❌ Database connection issue: {e}")

    with st.expander("🔍 Debug Information"):
        st.write("**Session State**")
        debug_info = {
            "User ID": st.session_state.get('user_id', 'Not set'),
            "OAuth Server Started": st.session_state.get('oauth_server_started', False),
            "Current User": bool(st.session_state.get('current_user')),
            "LinkedIn Connected": bool(user.linkedin_access_token),
        }

        for key, value in debug_info.items():
            st.write(f"• **{key}**: {value}")

        if st.button("📋 Copy Debug Info"):
            st.code(json.dumps(debug_info, indent=2))

    # Footer
    st.divider()
    st.markdown("---")
    st.caption("LinkedIn AI Agent v1.0 | Built with Streamlit, MongoDB, Redis & Gemini AI")

# Main app logic
def main():
    page = sidebar_navigation()
    
    if page == "login":
        login_page()
    elif page == "dashboard":
        dashboard_page()
    elif page == "profile":
        profile_page()
    elif page == "strategy":
        strategy_page()
    elif page == "generator":
        generator_page()
    elif page == "calendar":
        calendar_page()
    elif page == "analytics":
        analytics_page()
    elif page == "settings":
        settings_page()

if __name__ == "__main__":
    main()
