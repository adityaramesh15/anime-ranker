const CLOUD_RUN_URL = 'https://anime-ranker-backend-10037187822.us-central1.run.app/api';

export const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080/api' 
    : CLOUD_RUN_URL;
