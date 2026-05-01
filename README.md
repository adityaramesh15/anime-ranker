# Anime Ranker

Anime Ranker is a full-stack web app where users rank anime through head-to-head Elo matchups, track personal lists, compare against global sentiment, and manage a watchlist.  
Live app: [show-ranker-project.web.app](https://show-ranker-project.web.app/)

## Current Features (V2)

- Elo-based matchup voting (`Choose This`, `Tie`, `Seen Neither`, `Haven't seen this`)
- Personal and Global leaderboards
- Compare view in leaderboard (`Personal`, `Global`, `Compare`) for user-to-user side-by-side ranking checks
- Watchlist improvements:
  - Favorite toggle per show
  - Favorites filter toggle
  - Sort toggle (`Alphabetical` / `Global Elo Rank`)
  - Watchlist local cache in browser storage to reduce repeated reads
  - Direct AniList links from each card
- Account page with:
  - Google profile picture
  - Editable `display_name` (used for comparisons)
  - Stats (total matches, completion %, top-10 alignment %, biggest positive/negative divergence)
  - Sign out
  - Personal Elo reset action
- Copy-to-clipboard export of personal Top 10
- Google Analytics (`gtag`) integrated across app pages
- Expanded catalog and image optimization (cover images served as `.webp`)

## Tech Stack

- **Frontend:** HTML, CSS, Vanilla JavaScript (ES Modules), hosted on Firebase Hosting
- **Backend:** Python + Flask API, deployed to Google Cloud Run
- **Auth:** Firebase Authentication (Google Sign-in)
- **Database:** Firestore (Firebase Admin SDK)
- **Data prep:** Python scripts + AniList GraphQL source data

## Firestore Schema

```json
{
  "global_anime": {
    "__fields__": ["matches_played", "id", "elo_score", "title"]
  },
  "users": {
    "__fields__": ["display_name", "display_name_lower", "total_matches"],
    "personal_anime": {
      "__fields__": ["id", "ignored", "favorite", "elo_score", "title"]
    }
  }
}
```

## Project Structure

```text
show-ranker/
├── backend/
│   ├── app.py
│   ├── ranker.py
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   ├── datasets/
│   ├── clean_data.py
│   ├── ingest_data.py
│   └── upload_to_firestore.py
├── frontend/
│   ├── js/
│   │   ├── api.js
│   │   ├── auth.js
│   │   └── firebase-config.js
│   ├── images/                 # .webp cover images
│   ├── 404.html
│   ├── index.html
│   ├── leaderboard.html
│   ├── watchlist.html
│   ├── account.html
│   └── style.css
├── firebase.json
├── .firebaserc
└── README.md
```

## How It Works

To stay within Firestore free-tier limits, the backend and frontend both reduce unnecessary reads/writes:

1. Backend caches global and per-user ranking data in memory (`cachetools.TTLCache` for user caches).
2. Matchups are generated from cache, not by querying Firestore for each request.
3. Vote processing writes global + personal updates in a Firestore batch.
4. Watchlist UI uses browser storage caching so page-to-page navigation does not always hit Firestore.
5. Display name lookups for compare use bounded queries (`limit(1)`).

## API Endpoints (High Level)

- `GET /api/matchup`
- `POST /api/vote`
- `GET /api/leaderboard`
- `POST /api/ignore`
- `GET /api/watchlist`
- `POST /api/unignore`
- `POST /api/favorite`
- `GET /api/user`
- `POST /api/user/display_name`
- `GET /api/stats`
- `POST /api/reset_account`
- `GET /api/compare`

## Local Development

### 1) Run backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Local backend uses `backend/firebase_credentials.json` (service account key).

### 2) Run frontend (required for local Google Auth)

```bash
firebase serve --only hosting
```

Use the localhost URL shown by Firebase CLI (commonly `http://localhost:5002`).  
Do not open raw HTML files directly for auth testing.

## Deployment

### Backend (Cloud Run)

```bash
cd backend
gcloud run deploy anime-ranker-backend --source . --region us-central1 --allow-unauthenticated
```

### Frontend (Firebase Hosting)

```bash
firebase deploy --only hosting
```

## Additional Notes

- Technical, implementation-level change history for V2 is documented in `RELEASE_NOTES_V2.md`.