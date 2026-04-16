# Backend (Flask API)

This backend exposes TMDb retrieval + DistilBERT SST-5 sentiment analysis + LIME explanation APIs.

## Files

- `app.py`: Flask entry point, CORS setup, and route definitions
- `model_service.py`: loads model from `./saved_sst5_model`, provides single/batch prediction helpers
- `movie_service.py`: TMDb API integration (search, movie details, reviews)
- `explain_service.py`: LIME explanation image generation
- `requirements.txt`: Python dependencies
- `.env.example`: required environment variables
- `saved_sst5_model/`: local fine-tuned model directory (replace starter files with real model artifacts)
- `static/explanations/`: generated explanation images

## Required model folder

Put your fine-tuned DistilBERT SST-5 model files in:

`backend/saved_sst5_model/`

Expected filenames:

- `config.json`
- `model.safetensors`
- `tokenizer.json`
- `tokenizer_config.json`
- `special_tokens_map.json`
- `training_args.bin`

If files are missing or invalid, API returns a clear model loading error.

## Environment variables

Copy `.env.example` to `.env` and update values:

```bash
TMDB_API_KEY=your_tmdb_api_key_here
FRONTEND_URL=https://your-frontend-domain.vercel.app
```

`FRONTEND_URL` is used by CORS for deployed frontend access.

## Run locally

1. Open terminal in `backend/`.
2. Create and activate virtual environment.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Add `.env` with your TMDb key.
5. Start server:
   - `python app.py`
6. API will be available at `http://127.0.0.1:5500`.

## API endpoints

- `GET /health`
- `GET /api/search-movies?query=<movie_name>`
- `GET /api/movie/<movie_id>`
- `GET /api/movie/<movie_id>/reviews`
- `GET /api/analyze-movie/<movie_id>`
- `POST /api/analyze-review`
- `POST /api/analyze-reviews-batch`
- `POST /api/explain-review`

## Deploy backend (Render or Railway)

1. Push repository to GitHub.
2. Create a new Render or Railway web service for `backend/`.
3. Set start command to `python app.py` (or `gunicorn app:app` if preferred).
4. Add environment variables:
   - `TMDB_API_KEY`
   - `FRONTEND_URL` (your Vercel frontend URL)
5. Deploy and copy the backend URL.
6. Update frontend `assets/js/config.js` to use deployed backend URL.
