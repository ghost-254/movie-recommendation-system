# Movie Recommendation System

This repository contains a full-stack academic starter project:

- `frontend/`: static HTML/CSS/JS client (Vercel-ready)
- `backend/`: Flask API with TMDb integration, DistilBERT SST-5 sentiment prediction, and LIME explanations

## Project structure

```text
movie-recommendation-system/
├── frontend/
│   ├── index.html
│   ├── movie.html
│   ├── about.html
│   ├── assets/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   ├── config.js
│   │   │   ├── api.js
│   │   │   ├── main.js
│   │   │   ├── movie.js
│   │   │   └── utils.js
│   │   └── images/
│   │       └── placeholders/
│   ├── favicon.ico
│   ├── vercel.json
│   └── README.md
├── backend/
│   ├── app.py
│   ├── model_service.py
│   ├── movie_service.py
│   ├── explain_service.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── static/
│   │   └── explanations/
│   ├── saved_sst5_model/
│   │   ├── config.json
│   │   ├── model.safetensors
│   │   ├── tokenizer.json
│   │   ├── tokenizer_config.json
│   │   ├── special_tokens_map.json
│   │   └── training_args.bin
│   └── README.md
└── README.md
```

## Quick start

1. Configure backend:
   - Follow `backend/README.md`
   - Add real model artifacts into `backend/saved_sst5_model/`
   - Set `TMDB_API_KEY`
2. Start backend (`python app.py`) at `http://127.0.0.1:5500`
3. Configure frontend API URL in `frontend/assets/js/config.js`
4. Serve frontend statically (`python -m http.server 5500` in `frontend/`)
5. Open `http://127.0.0.1:5500`

## Deployment notes

- Frontend: deploy `frontend/` to Vercel as static site.
- Backend: deploy `backend/` to Render or Railway.
- After backend deploy, update `frontend/assets/js/config.js` with deployed backend URL.
