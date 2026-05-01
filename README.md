# Anime Ranker

A full-stack, serverless web application that allows users to rank a curated list of top anime franchises through head-to-head, Elo-based matchups. Anime Ranker goes beyond simple tier lists by using a robust rating algorithm to track your personal taste, contrast it with global community sentiment, and let you compare your rankings side-by-side with friends.

Try the live app: [show-ranker-project.web.app](https://show-ranker-project.web.app/)

## Key Features

### Dynamic Elo Matchmaking
* **Head-to-Head Voting:** Rank shows naturally by choosing a winner, calling a tie, or skipping shows you haven't seen.
* **Dual-Track Scoring:** Every vote simultaneously updates the global community leaderboard and your personal ranking baseline. 
* **Optimized Media:** Cover art is served in lightweight `.webp` format for fast, responsive UI during rapid-fire voting.

### Personalized Accounts & Deep Stats
* **Seamless Authentication:** Secure Google Sign-In with customizable display names.
* **Analytics Dashboard:** A dedicated account page tracks your voting habits, including:
  * Total matches played and overall completion percentage.
  * **Global Alignment:** A percentage showing how closely your Top 10 matches the community's Top 10.
  * **Hot Takes:** Identifies your biggest positive divergence (shows you love way more than the community) and negative divergence (shows you rate much harsher than the community).
* **Export Options:** Easily copy your Top 10 to your clipboard or export your entire personal list for sharing.

### Community Comparisons
* **Side-by-Side Leaderboards:** Toggle between Personal and Global standings.
* **Compare Mode:** Search for other users by their custom display name and view your tier lists side-by-side to see how your tastes align.

### Smart Watchlist Management
* Shows you mark as "Haven't seen" are dynamically filtered out of your matchmaking pool and saved to your watchlist.
* Sort your backlog alphabetically or by global Elo rank to see what the community highly recommends.
* Toggle favorites, and jump straight to a show's AniList page for more details. 

## Architecture & Tech Stack

Designed to stay strictly within GCP's Free Tier, Anime Ranker utilizes heavy caching and batched database operations to minimize reads and writes.

* **Frontend:** HTML, CSS, Vanilla JavaScript (structured with ES Modules for DRY, reusable components). Hosted on **Firebase Hosting**.
* **Authentication:** **Firebase Auth** (Google Sign-In).
* **Backend:** Python and Flask, containerized and deployed on **Google Cloud Run**.
* **Database:** **Google Firestore** (Firebase Admin SDK).
* **Data Pipeline:** Python scripts that fetch, clean, and consolidate franchise data from the **AniList GraphQL API**.
* **Analytics:** Instrumented with Google Analytics (`gtag`).

### Under the Hood: Caching & Data Integrity
1. **Memory Caching (`TTLCache`):** Global and per-user ranking data is cached in backend memory. Matchups are generated with *zero database reads* by comparing adjacent scores in the cache. 
2. **Client-Side Caching:** The Watchlist UI utilizes browser storage to prevent redundant database queries on page revisits.
3. **Atomic Writes:** When a user votes, the updated Global and Personal Elo scores (calculated with a K-factor of 32) are written back to Firestore simultaneously using batched operations.
4. **Optimized Schema:** User-specific fields (like total matches and custom display names) are isolated at the root `users` document to keep the `personal_anime` sub-collections lightweight, while bounded queries (`limit(1)`) ensure efficient user lookups for the Compare feature.

## Project Structure

```text
show-ranker/
├── backend/                    # Google Cloud Run Flask Server
│   ├── app.py                  # API Routing and endpoint logic
│   ├── ranker.py               # Business logic, Elo math, and DB caching
│   ├── Dockerfile              # Container configuration
│   └── requirements.txt        # Python dependencies
├── data/                       # Local data pipeline
│   ├── datasets/               # Raw and cleaned JSON data
│   ├── clean_data.py           # Consolidates seasons/spinoffs into franchises
│   ├── ingest_data.py          # Fetches show data from AniList GraphQL
│   └── upload_to_firestore.py  # Script to populate the live database
├── frontend/                   # Firebase Hosting Static Assets
│   ├── js/                     # Modular Vanilla JS components
│   │   ├── api.js
│   │   ├── auth.js
│   │   └── firebase-config.js
│   ├── images/                 # Optimized .webp cover images
│   ├── index.html              # The Matchup voting UI
│   ├── leaderboard.html        # Global, Personal, & Compare UI
│   ├── watchlist.html          # Backlog management UI
│   ├── account.html            # User stats & profile management
│   └── style.css               # Core styling
├── firebase.json               # Firebase deployment rules
├── .firebaserc                 # Firebase project target
└── README.md
```

## Local Development Setup

### 1. Backend
Navigate to the backend directory, set up a virtual environment, and run the Flask server:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python3 app.py
```
*(Note: You will need a `firebase_credentials.json` service account key in the `backend` folder for local database access).*

### 2. Frontend
Because the application uses ES Modules and Firebase Authentication, opening the raw HTML files directly in a browser will not work. You must serve the files locally using the Firebase CLI:

```bash
firebase serve --only hosting
```
Open the localhost URL provided by the CLI (usually `http://localhost:5002`). Ensure the `API_BASE` variable in your frontend code points to your local Flask server (`http://127.0.0.1:8080/api`) during testing.

## Deployment

**Deploy the Backend (Cloud Run):**
```bash
cd backend
gcloud run deploy anime-ranker-backend --source . --region us-central1 --allow-unauthenticated
```

**Deploy the Frontend (Firebase Hosting):**
```bash
firebase deploy --only hosting
```