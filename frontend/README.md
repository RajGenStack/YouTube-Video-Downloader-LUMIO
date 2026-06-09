# Lumio Frontend

This is the static frontend for the YouTube downloader.

## Structure

- `index.html` — Single-page static entry.
- `css/styles.css` — Application styles.
- `js/app.js` — Client-side behavior.

## Local Preview

Open `frontend/index.html` in a browser or use Docker:

```bash
cd frontend
docker build -t lumio-frontend .
docker run --rm -p 3000:80 lumio-frontend
```

Then visit: `http://localhost:3000`

## API Configuration

Update `js/app.js` if you want to point the frontend to a backend API:

```js
const downloadApiEndpoint = 'http://localhost:8000';
```

Make sure `backend` allows CORS from the frontend origin.
