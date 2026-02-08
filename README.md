# 📻 Akashvani - Voice of the Sky

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://akashvani.cxloop.co)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Senior-Friendly News-to-Speech Application** delivering trusted news from Indian and international sources in 12 Indian languages with AI-powered summaries and text-to-speech capabilities.

🔗 **Live Demo:** [https://akashvani.cxloop.co](https://akashvani.cxloop.co)

---

## 🌟 Features

### 📰 **Multi-Source News Aggregation**
- Real-time news from 30+ trusted Indian and international sources
- Dual API system (NewsAPI + GNews) for 200 requests/day
- Automatic fallback ensures zero downtime
- 2-day news filtering for latest updates only

### 🗣️ **12 Indian Languages Support**
| Language | Native Name | TTS Support |
|----------|-------------|-------------|
| English | English | ✅ |
| Hindi | हिन्दी | ✅ |
| Bengali | বাংলা | ✅ |
| Telugu | తెలుగు | ✅ |
| Marathi | मराठी | ✅ |
| Tamil | தமிழ் | ✅ |
| Gujarati | ગુજરાતી | ✅ |
| Urdu | اردو | ✅ |
| Kannada | ಕನ್ನಡ | ✅ |
| Odia | ଓଡ଼ିଆ | ✅ |
| Malayalam | മലയാളം | ✅ |
| Punjabi | ਪੰਜਾਬੀ | ✅ |

### 🤖 **AI-Powered Features**
- **Smart Summaries:** 1-3 minute audio briefs (150-450 words)
- **Senior-Friendly Language:** Simplified, easy-to-understand content
- **OpenAI Translation:** High-quality translations for all languages
- **Context-Aware:** Maintains meaning across languages

### 🏏 **Cricket Score Integration**
- Live cricket scores extracted from news articles
- Supports all formats: Test, ODI, T20, IPL
- Team detection: India, Pakistan, Australia, England, etc.
- IPL team support: RCB, CSK, MI, KKR, and more
- Spoken cricket scores in 12 languages

### 🎧 **Text-to-Speech (TTS)**
- Google Text-to-Speech (gTTS) integration
- Two speed modes: Normal ⚡ and Slow 🐢
- High-quality voice output for all 12 languages
- Optimized for senior citizens' listening comfort

### 📱 **Senior-Friendly UI**
- Large, readable fonts (18px base)
- High contrast colors for better visibility
- Simple, intuitive navigation
- One-click voice playback
- Mobile-responsive design

---

## 🏗️ Architecture

### 📁 **Project Structure**


akashvani/
├── app.py                      # Main application (user interface)
├── pages/
│   └── admin.py               # Admin dashboard (password protected)
├── config/
│   └── languages.py           # Language configurations and mappings
├── utils/
│   ├── news_fetcher.py        # NewsAPI integration with fallback
│   ├── gnews_fetcher.py       # GNews API fallback handler
│   ├── cricket_scraper.py     # Cricket score extraction
│   ├── translator.py          # OpenAI translation utilities
│   └── tts_handler.py         # Text-to-speech with gTTS
├── .streamlit/
│   └── secrets.toml           # API keys and secrets (not in repo)
├── requirements.txt           # Python dependencies
├── privacy-policy.md          # Privacy policy document
└── README.md                  # This file

### **Rate Limit Strategy**

User Request
    ↓
Try NewsAPI (100/day)
    ↓ (if 429 error)
Try GNews (100/day)
    ↓ (if both fail)
Show user-friendly error

### **Support & Contact**
### **Get Help**
- 📧 Email: support@cxloop.co
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

### **Credits**
- Author: CX Data & Analytics LLC
- Contributors: [List of contributors]
- Libraries: Streamlit, OpenAI, gTTS, NewsAPI, GNews

### 🙏 Acknowledgments
- Streamlit for the amazing framework
- OpenAI for GPT-3.5 API
- NewsAPI for reliable news data
- GNews for backup news source
- gTTS for text-to-speech capabilities
- Senior citizens community for valuable feedback
