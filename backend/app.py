import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from ranker import AnimeRanker

if os.environ.get('K_SERVICE'):
    firebase_admin.initialize_app()
else:
    cred = credentials.Certificate('firebase_credentials.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()
ranker = AnimeRanker(db)
app = Flask(__name__)
CORS(app)

@app.route('/api/matchup', methods=['GET'])
def get_matchup():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "Missing User ID"}), 400
        
    try:
        show_a, show_b = ranker.get_matchup(uid)
        return jsonify({"show_a": show_a, "show_b": show_b}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vote', methods=['POST'])
def submit_vote():
    data = request.json
    uid = data.get('uid')
    anime_a_id = data.get('anime_a_id')
    anime_b_id = data.get('anime_b_id')
    outcome = data.get('outcome')

    if not uid or outcome not in [1, 0, 0.5]:
        return jsonify({"error": "Invalid payload."}), 400
    
    try:
        result = ranker.process_match(uid, anime_a_id, anime_b_id, outcome)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "Missing User ID"}), 400

    try:
        leaderboards = ranker.get_leaderboards(uid)
        return jsonify(leaderboards), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ignore', methods=['POST'])
def ignore_shows():
    data = request.json
    uid = data.get('uid')
    anime_ids = data.get('anime_ids', []) 

    if not uid or not isinstance(anime_ids, list):
        return jsonify({"error": "Invalid payload."}), 400
    
    try:
        result = ranker.ignore_shows(uid, anime_ids)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "Missing User ID"}), 400
    try:
        watchlist = ranker.get_watchlist(uid)
        return jsonify(watchlist), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/unignore', methods=['POST'])
def unignore_show():
    data = request.json
    uid = data.get('uid')
    anime_id = data.get('anime_id')
    
    if not uid or not anime_id:
        return jsonify({"error": "Invalid payload."}), 400
    try:
        result = ranker.unignore_show(uid, anime_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user', methods=['GET'])
def get_user():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "Missing User ID"}), 400
    try:
        user_doc = ranker.get_user(uid)
        if not user_doc:
            return jsonify({"exists": False}), 200
        return jsonify({"exists": True, "user": user_doc}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/display_name', methods=['POST'])
def set_display_name():
    data = request.json
    uid = data.get('uid')
    display_name = data.get('display_name')
    if not uid or not display_name:
        return jsonify({"error": "Missing parameters"}), 400
    
    try:
        result = ranker.set_display_name(uid, display_name)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "Missing User ID"}), 400
    try:
        stats = ranker.get_stats(uid)
        return jsonify(stats), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset_account', methods=['POST'])
def reset_account():
    data = request.json
    uid = data.get("uid")
    if not uid:
        return jsonify({"error": "Missing User ID"}), 400
    try:
        response = ranker.reset_account(uid)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/favorite', methods=['POST'])
def toggle_favorite():
    data = request.json
    uid = data.get("uid")
    anime_id = data.get("anime_id")
    favorite_status = data.get("favorite")
    
    if not uid or not anime_id or favorite_status is None:
        return jsonify({"error": "Missing parameters"}), 400
        
    try:
        response = ranker.toggle_favorite(uid, anime_id, favorite_status)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/compare', methods=['GET'])
def compare_users():
    user1_id = request.args.get('user1_id')
    user2_display_name = request.args.get('user2_display_name')

    if not user1_id or not user2_display_name:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        result = ranker.compare_users(user1_id, user2_display_name)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)