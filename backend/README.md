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
HF_MODEL_REPO=your-huggingface-username/your-model-repo
HF_MODEL_REVISION=main
HF_TOKEN=optional_for_private_model_repo
MODEL_LOAD_ON_STARTUP=false
```

`FRONTEND_URL` is used by CORS for deployed frontend access.
`HF_MODEL_REPO` lets Render download the model weights if `model.safetensors` is not committed to GitHub.
Use `HF_TOKEN` only if your Hugging Face model repository is private.

## Run locally

1. Open terminal in `backend/`.
2. Create and activate virtual environment.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Add `.env` with your TMDb key.
5. Start server:
   - `python app.py`
6. API will be available at `http://127.0.0.1:5000`.

## API endpoints

- `GET /health`
- `GET /api/search-movies?query=<movie_name>`
- `GET /api/movie/<movie_id>`
- `GET /api/movie/<movie_id>/reviews`
- `GET /api/analyze-movie/<movie_id>`
- `POST /api/analyze-review`
- `POST /api/analyze-reviews-batch`
- `POST /api/explain-review`

## Deploy backend on Render

1. Push repository to GitHub.
2. Upload the full saved model folder to a Hugging Face model repository.
3. Create a new Render web service for `backend/`.
4. Use build command: `pip install -r requirements.txt`.
5. Use start command: `gunicorn app:app`.
6. Add environment variables:
   - `TMDB_API_KEY`
   - `FRONTEND_URL` (your Vercel frontend URL)
   - `HF_MODEL_REPO` (example: `username/movie-sst5-distilbert`)
   - `HF_MODEL_REVISION` (usually `main`)
   - `HF_TOKEN` (only needed for private Hugging Face repos)
   - `MODEL_LOAD_ON_STARTUP=false`
7. Deploy and copy the backend URL.
8. Update frontend `assets/js/config.js` to use deployed backend URL.

## Hugging Face model files

The Hugging Face model repository should contain:

- `config.json`
- `model.safetensors`
- `tokenizer.json`
- `tokenizer_config.json`
- `special_tokens_map.json`
- `training_args.bin`

By default, Render starts the web server first and loads the model on the first analysis request. This keeps Render's
port check from timing out while the model downloads. If you want the app to load the model during startup instead,
set `MODEL_LOAD_ON_STARTUP=true`.
