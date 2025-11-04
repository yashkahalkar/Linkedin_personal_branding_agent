# 🚀 LinkedIn Personal Branding AI Agent

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green.svg)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-6.0+-red.svg)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Transform your LinkedIn presence with AI-powered content creation, strategic planning, and automated publishing.**

An intelligent AI agent that analyzes your professional profile, generates personalized content strategies, creates engaging LinkedIn posts, and provides comprehensive analytics to boost your personal brand.

*The deployed working link will some be updated here...*

---

## ✨ Features

### 🎯 **AI-Powered Content Strategy**
- **Personalized Analysis**: Deep dive into your professional background, skills, and industry
- **Content Pillars**: AI-generated themes tailored to your expertise and audience
- **Hashtag Strategy**: Industry-specific hashtag recommendations for maximum reach
- **Trending Topics**: Real-time industry trends integration for relevant content

### ✍️ **Intelligent Content Generation**
- **Multi-Format Posts**: Text posts, articles, carousels, and polls
- **Brand Voice Consistency**: Maintains your unique professional tone
- **Topic Suggestions**: AI-curated content ideas based on your profile
- **Content Optimization**: Gemini AI ensures high-quality, engaging posts

### 📅 **Smart Content Management**
- **Content Calendar**: Visual scheduling and planning interface
- **Automated Publishing**: Direct LinkedIn integration with OAuth
- **Draft Management**: Save, edit, and organize your content pipeline
- **Batch Scheduling**: Plan weeks of content in advance

### 📊 **Advanced Analytics**
- **Performance Tracking**: Monitor likes, comments, shares, and engagement rates
- **Trend Analysis**: Identify your best-performing content patterns
- **AI Insights**: Get actionable recommendations for improvement
- **Export Reports**: Comprehensive data export for external analysis

### 🔗 **LinkedIn Integration**
- **OAuth Authentication**: Secure LinkedIn account connection
- **Direct Publishing**: Seamless posting to your LinkedIn profile
- **Profile Sync**: Automatic profile data synchronization
- **Real-time Analytics**: Live engagement metrics from LinkedIn

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Streamlit | Interactive web interface |
| **AI Engine** | Google Gemini | Content generation and analysis |
| **Database** | MongoDB | User data and content storage |
| **Caching** | Redis | Performance optimization |
| **OAuth Server** | Flask | LinkedIn authentication |
| **Analytics** | Plotly | Data visualization |
| **APIs** | LinkedIn REST API | Social media integration |

---

## 🚦 Getting Started

### Prerequisites

- Python 3.9 or higher
- MongoDB (local or Atlas)
- Redis (local or cloud)
- Google Gemini API key
- LinkedIn Developer App (for OAuth)

### 📥 Installation

1. **Clone the repository** 
2. **Install dependencies**
3. **Start MongoDB and Redis (if running locally)**


### 🔧 Configuration

Create a `.env` file in the project root:

Database Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=linkedin_ai_agent

Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

API Keys
GEMINI_API_KEY=your_gemini_api_key_here
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

Application Settings
SECRET_KEY=your_secret_key_here

### Running the app
**start the redis server :**
*Open WSL and then type 
sudo service redis-server start,
redis-cli,
ping*

**Start the mongoDB server**
*In vs code start connection to mongoDB server*

**In your terminal type streamlit run app.py**

**made by Yash Kahalkar with  💻**
