import time
import random
import math
from firebase_admin import firestore

class AnimeRanker:
    def __init__(self, db):
        self.db = db
        self.k_factor = 32
        self.cache = []
        self.last_cache_update = 0
        self.CACHE_TTL = 300 # arbitrary 5 min between refreshing local cache w/ updated scores

    def _refresh_cache_if_needed(self):
        current_time = time.time()
        if current_time - self.last_cache_update > self.CACHE_TTL or not self.cache:
            docs = self.db.collection('anime').stream() # stream gives me all docs in collection
            self.cache = [doc.to_dict() for doc in docs]
            self.last_cache_update = current_time

    def get_matchup(self):
        self._refresh_cache_if_needed()
        
        random.shuffle(self.cache)
        sorted_data = sorted(self.cache, key=lambda x: x.get('elo_score', 1200)) # grabbing 
        
        idx = random.randint(0, len(sorted_data) - 2)
        return sorted_data[idx], sorted_data[idx + 1]

    def get_leaderboard(self):
        docs = self.db.collection('anime').order_by(
            'elo_score', direction="DESCENDING"
        ).stream()
        return [doc.to_dict() for doc in docs]
    
    def process_match(self, anime_a_id, anime_b_id, outcome):
        # update the db based on the outcome by modifiying elo of anime a and b
        # 1 is A wins, 0 is B wins, 0.5 is Tie 

        doc_a_ref = self.db.collection('anime').document(str(anime_a_id))
        doc_b_ref = self.db.collection('anime').document(str(anime_b_id))

        doc_a = doc_a_ref.get()
        doc_b = doc_b_ref.get()

        if not doc_a.exists or not doc_b.exists:
            raise ValueError("One or both Anime IDs not found in database.")

        anime_a = doc_a.to_dict()
        anime_b = doc_b.to_dict()

        ra = anime_a.get('elo_score', 1200)
        rb = anime_b.get('elo_score', 1200)

        ea = 1 / (1 + math.pow(10, (rb - ra) / 400))
        eb = 1 / (1 + math.pow(10, (ra - rb) / 400))

        if outcome == 1:
            sa, sb = 1, 0
        elif outcome == 0:
            sa, sb = 0, 1
        else:
            sa, sb = 0.5, 0.5

        new_ra = round(ra + self.k_factor * (sa - ea))
        new_rb = round(rb + self.k_factor * (sb - eb))

        # 3. Save directly back to Firestore
        doc_a_ref.update({'elo_score': new_ra})
        doc_b_ref.update({'elo_score': new_rb})

        for anime in self.cache:
            if str(anime['id']) == str(anime_a_id):
                anime['elo_score'] = new_ra
            elif str(anime['id']) == str(anime_b_id):
                anime['elo_score'] = new_rb

        return {"status": "success", "new_scores": {anime_a_id: new_ra, anime_b_id: new_rb}}
    
    

