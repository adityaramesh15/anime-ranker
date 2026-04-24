from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from ranker import AnimeRanker

cred = credentials.Certificate('firebase_credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

ranker = AnimeRanker(db)
app = Flask(__name__)
CORS(app)

@app.route('/api/matchup', methods = ['GET'])
def get_matchup():
    try:
        show_a, show_b = ranker.get_matchup()
        return jsonify({"show_a": show_a, "show_b": show_b}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/vote', methods=['POST'])
def submit_vote():
    data = request.json
    anime_a_id = data.get('anime_a_id')
    anime_b_id = data.get('anime_b_id')
    outcome = data.get('outcome') # 1, 0, or 0.5

    if outcome not in [1, 0, 0.5]:
        return jsonify({"error": "Invalid outcome. Must be 1, 0, or 0.5"}), 400
    
    try:
        result = ranker.process_match(anime_a_id, anime_b_id, outcome)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Returns the top 150 list."""
    try:
        leaderboard = ranker.get_leaderboard()
        return jsonify(leaderboard), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)