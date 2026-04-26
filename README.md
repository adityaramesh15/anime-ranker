# Anime Ranker

A full-stack, serverless web application that allows users to rank the top 200 anime franchises through head-to-head, Elo-based matchups. Features secure Google Sign-in to track both personal tier lists, a community-driven global leaderboard, and a personalized watchlist for managing unseen shows. Try it out [here!](https://show-ranker-project.web.app/)

## Architecture & Tech Stack
* **Frontend:** HTML, CSS, JavaScript (Vanilla) hosted on **Firebase Hosting**.
* **Authentication:** **Firebase Auth** (Google Sign-In) for personalized ranking profiles.
* **Backend:** Python and Flask, containerized and deployed on **Google Cloud Run**.
* **Database:** **Google Firestore** (NoSQL) for durable Elo score tracking.
* **Data Pipeline:** Python scripts that fetch, clean, and consolidate franchise data from the **AniList GraphQL API**.

## Project Structure

```text
show-ranker/
├── backend/                    # Google Cloud Run Flask Server
│   ├── app.py                  # API Routing and endpoint logic
│   ├── ranker.py               # Business logic, Elo math, and DB caching
│   ├── Dockerfile              # Container configuration
│   └── requirements.txt        # Python dependencies
├── data/                       # Local data pipeline
│   ├── datasets/
│   │   ├── raw_anime_data.json
│   │   └── clean_anime_list.json
│   ├── clean_data.py           # Consolidates seasons/spinoffs into franchises
│   ├── ingest_data.py          # Fetches Top 200 from AniList GraphQL
│   └── upload_to_firestore.py  # One-time script to populate the live database
├── frontend/                   # Firebase Hosting Static Assets
│   ├── images/                 # 200 downloaded cover images ({id}.jpg)
│   ├── 404.html                # Custom error page
│   ├── index.html              # The Matchup voting UI (with Auth)
│   ├── leaderboard.html        # The Global & Personal Leaderboard UI
│   ├── style.css               # Core styling
│   └── watchlist.html          # UI for managing ignored/unseen shows
├── .firebaserc                 # Firebase project target
├── firebase.json               # Firebase deployment rules
├── .gitignore
├── README.md
└── requirements.txt 
```

## How it Works (The Elo System, Auth & Caching)
To optimize database reads and stay well within GCP Free Tier limits, the backend utilizes a dual-layer in-memory caching system using standard arrays and `cachetools`.

1. **Initialization:** When a user logs in for the first time, a baseline copy of the Top 200 shows (starting at 1200 Elo) is created in their personal Firestore sub-collection.
2. **Matchmaking (0 Reads):** Matchups are generated entirely from memory by comparing adjacent scores in the user's specific `TTLCache`.
3. **Processing (Atomic Writes):** When a user votes, the server fetches the two specific shows from the database. It calculates the new expected outcomes using standard Elo math (K-factor = 32) for *both* the Global baseline and the User's personal baseline.
4. **Batch Updates:** The updated Global and Personal scores are written back to Firestore simultaneously using a `db.batch()` operation to ensure data integrity.
5. **Memory Patching:** The local memory caches are instantly patched with the new scores, avoiding the need for a full database re-fetch on the next request.
6. **Watchlist Management:** Shows marked as unwatched are dynamically filtered out of the matchmaking pool and stored in a personalized watchlist, where they can be added back later once watched.

## Local Development Setup

### 1. Backend
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the local Flask server
python app.py
```
*(Note: You will need a `firebase_credentials.json` service account key in the `backend` folder for local database access).*

### 2. Frontend
Since the frontend uses standard web APIs, simply open `frontend/index.html` in your web browser. 
* Ensure the `API_BASE` variable in the JavaScript points to `http://127.0.0.1:8080/api` for local testing.
* **Important:** You must paste your project's `firebaseConfig` object from the Firebase Console into the `<script type="module">` blocks of the HTML files for Authentication to work locally.

## Deployment

**Deploy the Backend (Cloud Run):**
```bash
cd backend
gcloud run deploy anime-ranker-backend --source . --region us-central1 --allow-unauthenticated
```

**Deploy the Frontend (Firebase Hosting):**
The frontend code is configured to automatically detect if it is running locally or in the cloud. Simply run:
```bash
firebase deploy --only hosting
```