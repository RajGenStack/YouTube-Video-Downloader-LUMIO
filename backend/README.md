# Lumio Backend — Production Grade API

FastAPI + yt-dlp + FFmpeg YouTube downloader backend.

---

## Project Structure

```
backend/
├── main.py                  ← App factory, middleware, exception handlers
├── requirements.txt         ← Pinned Python dependencies
├── Dockerfile               ← Multi-stage production Docker image
├── docker-compose.yml       ← Local development with Docker
├── render.yaml              ← Render.com one-click deploy
├── Procfile                 ← Heroku / Railway deploy
├── pytest.ini               ← Test runner config
├── .env.example             ← Environment variable template
├── .gitignore
└── app/
    ├── __init__.py
    ├── config.py            ← All settings from env vars (pydantic-settings)
    ├── logger.py            ← Structured logging (JSON in prod)
    ├── schemas.py           ← Pydantic request/response models + validation
    ├── downloader.py        ← yt-dlp + FFmpeg core logic
    ├── cleanup.py           ← Background temp file sweeper
    └── routes.py            ← All HTTP endpoints with rate limiting
└── tests/
    ├── __init__.py
    ├── conftest.py          ← Shared pytest fixtures
    └── test_api.py          ← Unit + integration tests
```

---

## Local Setup (No Docker)

### 1. Prerequisites
- Python 3.11+
- FFmpeg

```bash
# Ubuntu / Debian
sudo apt install ffmpeg python3.11 python3.11-venv

# macOS
brew install ffmpeg python@3.11

# Windows
# Python: https://python.org/downloads
# FFmpeg: https://ffmpeg.org/download.html → add to PATH
```

### 2. Create virtual environment
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — set ALLOWED_ORIGINS to your frontend URL
```

### 4. Run
```bash
uvicorn main:app --reload --port 8000
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

---

## Local Setup (Docker)

```bash
cd backend
cp .env.example .env

docker-compose up --build
```

API available at http://localhost:8000

---

## Run Tests

```bash
pip install -r requirements.txt
pytest
```

---

## API Reference

### `GET /health`
Returns service health, version, and yt-dlp version.

```json
{
  "status": "ok",
  "service": "Lumio API",
  "version": "1.0.0",
  "environment": "production",
  "yt_dlp_version": "2024.5.27"
}
```

---

### `POST /api/fetch-info`

Fetch video metadata without downloading.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "title": "Rick Astley - Never Gonna Give You Up",
  "duration_seconds": 212,
  "duration_str": "3:32",
  "thumbnail": "https://...",
  "uploader": "Rick Astley",
  "channel_url": "https://www.youtube.com/channel/...",
  "view_count": 1400000000,
  "like_count": 16000000,
  "upload_date": "20091025",
  "description_snippet": "The official video for ...",
  "is_live": false,
  "available_formats": ["144p","240p","360p","480p","720p","1080p"]
}
```

**Rate limit:** 30 requests/minute per IP

---

### `POST /api/download`

Download and stream video or audio file.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "mode": "mp3",
  "quality": "320k"
}
```

| Field | Values |
|---|---|
| `mode` | `mp3` or `mp4` |
| MP3 `quality` | `70k` `128k` `160k` `320k` `620k` |
| MP4 `quality` | `144p` `240p` `360p` `480p` `720p` `1080p` `1440p` `2160p` `4320p` `1080p-hdr` `1440p-hdr` `4k-hdr` `8k-hdr` |

**Response:** Binary file stream with `Content-Disposition` header.

**Rate limit:** 10 requests/minute per IP

---

## Deploy to Render.com (Free)

1. Push this `backend/` folder to a GitHub repo.
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your GitHub repo, select the `backend/` folder as root.
4. Render auto-detects `render.yaml` — click **Apply**.
5. In the Render dashboard → **Environment**, set:
   ```
   ALLOWED_ORIGINS = https://your-lumio.vercel.app
   ```
6. Deploy. Your URL will be `https://lumio-api.onrender.com`.

> **Free tier** spins down after 15 min idle. First cold-start takes ~30s.
> Upgrade to **Starter ($7/mo)** to keep it always-on.

---

## Deploy to Railway

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

Set env vars in the Railway dashboard. No build command needed — Railway reads `Procfile`.

---

## Deploy with Docker (VPS / DigitalOcean / Hetzner)

```bash
# Build
docker build -t lumio-api:latest .

# Run
docker run -d \
  --name lumio-api \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e ALLOWED_ORIGINS=https://your-site.vercel.app \
  -e RATE_LIMIT_DOWNLOAD=10/minute \
  lumio-api:latest
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `production` | `production` / `development` |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` |
| `ALLOWED_ORIGINS` | localhost | Comma-separated frontend URLs |
| `RATE_LIMIT_FETCH` | `30/minute` | Per-IP limit for fetch-info |
| `RATE_LIMIT_DOWNLOAD` | `10/minute` | Per-IP limit for downloads |
| `MAX_VIDEO_DURATION_SECONDS` | `10800` | Max video length (3 hours) |
| `DOWNLOAD_TIMEOUT_SECONDS` | `600` | Kill stalled downloads after N secs |
| `TMP_DIR` | `/tmp/lumio_downloads` | Temp file directory |
| `CLEANUP_AFTER_SECONDS` | `300` | Auto-delete temp files after N secs |
| `COOKIES_FILE` | _(empty)_ | Path to cookies.txt (optional) |

---

## Production Checklist

- [ ] Set `ENVIRONMENT=production` (disables Swagger UI)
- [ ] Set `ALLOWED_ORIGINS` to your exact frontend URL only
- [ ] Confirm FFmpeg is installed (`ffmpeg -version`)
- [ ] Confirm yt-dlp is up to date (`pip install -U yt-dlp`)
- [ ] Set up monthly yt-dlp updates (YouTube frequently changes APIs)
- [ ] Configure a reverse proxy (nginx / Cloudflare) in front if self-hosting
- [ ] Enable HTTPS (Render/Railway/Vercel handle this automatically)

---

## Keeping yt-dlp Updated

YouTube changes its internal APIs frequently. When downloads start failing, update yt-dlp:

```bash
pip install -U yt-dlp
# Then redeploy
```

On Render.com, simply trigger a manual redeploy to pick up the latest yt-dlp from PyPI.
