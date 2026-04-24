

# Anime Ranker

A full-stack, serverless web application that allows users to rank the top 150 anime franchises through head-to-head, Elo-based matchups. 

## Architecture & Tech Stack
* **Frontend:** HTML, CSS, JavaScript (Vanilla) hosted on **Firebase Hosting**.
* **Backend:** Python and Flask, containerized and deployed on **Google Cloud Run**.
* **Database:** **Google Firestore** (NoSQL) for durable Elo score tracking.
* **Data Pipeline:** Python scripts that fetch, clean, and consolidate franchise data from the **AniList GraphQL API**.

## 📂 Project Structure

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
│   ├── ingest_data.py          # Fetches Top 150 from AniList GraphQL
│   └── upload_to_firestore.py  # One-time script to populate the live database
├── frontend/                   # Firebase Hosting Static Assets
│   ├── images/                 # 150 downloaded cover images ({id}.jpg)
│   ├── index.html              # The Matchup voting UI
│   ├── leaderboard.html        # The Global Top 150 UI
│   └── style.css
├── .firebaserc                 # Firebase project target
├── firebase.json               # Firebase deployment rules
├── .gitignore
├── README.md
└── requirements.txt 
```

## How it Works (The Elo System & Caching)
To optimize database reads and stay within GCP Free Tier limits, the backend utilizes an in-memory cache. 
1. The Flask server reads the top 150 shows into memory on startup (150 reads).
2. Matchups are generated entirely from memory by comparing adjacent scores (0 reads).
3. When a user votes, the server fetches ONLY the two competing shows, calculates the new expected outcome using standard Elo math (K-factor = 32), and writes the two updated scores back to Firestore.
4. The local memory cache is patched with the new scores, avoiding the need for a full database re-fetch.
5. The Leaderboard page performs a fresh query to ensure eventual consistency for all users.

## 🛠️ Local Development Setup

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
Since the frontend uses standard web APIs, simply open `frontend/index.html` in your web browser. Ensure the `API_BASE` variable in the JavaScript points to `http://127.0.0.1:8080/api` for local testing.

## ☁️ Deployment

**Deploy the Backend (Cloud Run):**
```bash
cd backend
gcloud run deploy anime-ranker-backend --source . --region us-central1 --allow-unauthenticated
```

**Deploy the Frontend (Firebase Hosting):**
Update the `API_BASE` in your frontend JS to match your new Cloud Run URL, then run:
```bash
firebase deploy --only hosting
```
