# Frontend (Static HTML/CSS/JS)

This frontend is a plain HTML/CSS/JavaScript client designed for static deployment on Vercel.

## Files

- `index.html`: homepage with movie search UI
- `movie.html`: movie details, reviews, sentiment summary, and explanation image
- `about.html`: short project/methodology explanation
- `assets/css/style.css`: responsive academic-style UI
- `assets/js/config.js`: backend API base URL
- `assets/js/api.js`: fetch wrappers for backend endpoints
- `assets/js/main.js`: search-page logic
- `assets/js/movie.js`: movie analysis page logic
- `assets/js/utils.js`: reusable helpers

## Update backend URL

Edit `assets/js/config.js`:

```javascript
const API_BASE_URL = "http://127.0.0.1:5500";
```

Use local backend URL for development and your deployed backend URL for production.

## Run locally

1. Open a terminal in `frontend/`.
2. Start a static file server:
   - Python: `python -m http.server 5500`
3. Open `http://127.0.0.1:5500`.
4. Ensure backend is running on the URL in `config.js`.

## Deploy on Vercel

1. Push this repository to GitHub.
2. Import the project in Vercel.
3. Set the Vercel root directory to `frontend`.
4. Deploy.
5. Update `assets/js/config.js` so `API_BASE_URL` points to your deployed backend.
