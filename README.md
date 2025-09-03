# 🔍 AI-Powered User Profile Scraper

An AI-powered web scraping service that extracts user profile information from websites using multiple extraction strategies including CSS selectors, site-specific adapters, and Google's Gemini 2.0 Flash AI model.

---

## 🚀 Live Demo & Repository

- **GitHub Repository:** [https://github.com/Jaya3110/profile-scrape](https://github.com/Jaya3110/profile-scrape)
- **Backend API:** [https://profile-scrape.onrender.com](https://profile-scrape.onrender.com)
- **Frontend UI:** [https://profile-scrape.vercel.app](https://profile-scrape.vercel.app)

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Scraping      │
│   (HTML/JS)     │◄──►│   (FastAPI)     │◄──►│   Service       │
│                 │    │                 │    │                 │
│ - URL Input     │    │ - API Routes    │    │ - CSS Extractors│
│ - Profile Cards │    │ - Validation    │    │ - AI Extractors │
│ - Loading UI    │    │ - Rate Limiting │    │ - Site Adapters │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🛠️ Technology Stack

- **Backend:** Python 3.8+, FastAPI, Uvicorn
- **Scraping:** BeautifulSoup4, httpx, fake-useragent
- **AI:** Google Gemini 2.0 Flash API
- **Data Models:** Pydantic for validation
- **Caching:** In-memory with TTL
- **Rate Limiting:** Custom implementation
- **Frontend:** HTML, CSS, JavaScript, Axios
- **Deployment:** Render (backend), Vercel (frontend)

---

## 📋 Prerequisites

- Python 3.8 or higher
- Google AI Studio account (for Gemini API key)
- Modern web browser

---

## 🚀 Quick Start (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/Jaya3110/profile-scrape.git
cd profile-scrape
```

### 2. Setup Python environment and install dependencies

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp env.example .env
# Edit .env and add your Gemini API key
```

Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 4. Run the backend API server

```bash
python main.py
```

The API will be available at `http://localhost:8000`.

### 5. Serve the frontend

You can open `index.html` directly in your browser or serve it with a local HTTP server:

```bash
python -m http.server 3000
```

Open `http://localhost:3000` in your browser.

---

## 📚 API Endpoints

### Health Check

```http
GET /api/health
```

### URL Validation

```http
POST /api/validate-url
Content-Type: application/json

{
  "url": "https://example.com/profile"
}
```

### Profile Scraping

```http
POST /api/scrape
Content-Type: application/json

{
  "url": "https://example.com/profile",
  "max_profiles": 10,
  "timeout": 30
}
```

### Get Cached Profiles

```http
GET /api/profiles
```

---

## 🔧 Configuration

### Environment Variables

| Variable              | Description               | Default |
|-----------------------|---------------------------|---------|
| `GEMINI_API_KEY`      | Google Gemini API key      | Required|
| `PORT`                | Server port               | 8000    |
| `MAX_REQUESTS_PER_MINUTE` | Rate limit             | 10      |
| `CACHE_TTL_HOURS`     | Cache duration (hours)    | 24      |

### Rate Limiting

- Default: 10 requests per minute per IP
- Configurable in `rate_limiter.py`
- Rate limit info included in API response headers

---

## 🎯 Extraction Strategies

1. **CSS Selector Extraction**  
   Uses common CSS selectors to find profile data like names, titles, emails, social links, and images.

2. **AI-Powered Extraction**  
   Uses Google Gemini 2.0 Flash AI to analyze page content and extract profile information intelligently.

3. **Site-Specific Adapters**  
   Optimized extractors for LinkedIn, GitHub, Twitter, and company team pages.

---

## 🔒 Security Features

- Input validation and URL accessibility checks
- Rate limiting to prevent abuse
- CORS configured to allow frontend access
- Safe error handling and resource limits

---

## 📈 Performance

- 24-hour in-memory caching of scraped results
- Async non-blocking I/O operations
- Smart retries and fallback strategies for AI extraction
- Automatic cache cleanup

---

## 🧪 Testing

### Manual Testing with curl

```bash
curl http://localhost:8000/api/health

curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/username"}'
```

### Test URLs

- LinkedIn: `https://linkedin.com/in/username`
- GitHub: `https://github.com/username`
- Company Team: `https://company.com/about/team`

---

## 🚀 Deployment

### Backend (Render)

- Uses `render.yaml` for deployment configuration
- Automatically installs dependencies and runs `uvicorn main:app`
- Environment variables configured via Render dashboard

### Frontend (Vercel)

- Uses `vercel.json` to serve `index.html` as a static site
- Deployed on [https://profile-scrape.vercel.app](https://profile-scrape.vercel.app)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Google AI Studio for Gemini API
- BeautifulSoup4 for HTML parsing
- FastAPI for the web framework
- Community contributors and testers

---

## 📞 Support

- **Issues:** Use GitHub Issues on the repository
- **Discussions:** Use GitHub Discussions on the repository
- **Email:** [jaykrishna190@gmail.com]

