# YouTube Downloader

Organised repository for the Lumio YouTube downloader app.

## Structure

- `frontend/` — Static frontend site and client assets.
- `backend/` — FastAPI downloader API and deployment config.
- `docker-compose.yml` — Local Docker orchestration for frontend + backend.

## Local setup

### 1. Start the full stack with Docker

```powershell
cd "c:\Users\sarah\Desktop\yt downloader"
docker compose up --build
```

Frontend: `http://localhost:3000`
Backend: `http://localhost:8000`

### 2. Frontend only

```powershell
cd frontend
docker build -t lumio-frontend .
docker run --rm -p 3000:80 lumio-frontend
```

### 3. Backend only

```powershell
cd backend
cp .env.example .env
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Notes

- Update `frontend/js/app.js` to point `downloadApiEndpoint` at your backend URL.
- Backend Docker config includes FFmpeg and production-ready packaging.
- Use `backend/README.md` for backend-specific documentation.
