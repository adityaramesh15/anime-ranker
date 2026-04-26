import time
import random
import math
from firebase_admin import firestore
from cachetools import TTLCache


class AnimeRanker:
    def __init__(self, db):
        self.db = db
        self.k_factor = 32

        self.global_cache = []
        self.global_last_update = 0
        self.CACHE_TTL = 300  # 5 minutes

        self.user_caches = TTLCache(maxsize=250, ttl=3600)

    def _refresh_global_cache_if_needed(self):
        current_time = time.time()
        if (
            current_time - self.global_last_update > self.CACHE_TTL
            or not self.global_cache
        ):
            docs = self.db.collection("global_anime").stream()
            self.global_cache = [doc.to_dict() for doc in docs]
            self.global_last_update = current_time

    def _refresh_user_cache_if_needed(self, uid):
        if uid not in self.user_caches:
            personal_ref = (
                self.db.collection("users")
                .document(uid)
                .collection("personal_anime")
            )

            docs = list(personal_ref.stream())

            if len(docs) == 0:
                print(f"New user detected ({uid}). Initializing baseline stats...")
                self._initialize_new_user(uid)
                docs = list(personal_ref.stream())

            self.user_caches[uid] = [doc.to_dict() for doc in docs]

    def _initialize_new_user(self, uid):
        self._refresh_global_cache_if_needed()

        batch = self.db.batch()
        personal_ref = (
            self.db.collection("users")
            .document(uid)
            .collection("personal_anime")
        )

        for anime in self.global_cache:
            doc_ref = personal_ref.document(str(anime["id"]))
            base_anime = anime.copy()
            base_anime["elo_score"] = 1200
            batch.set(doc_ref, base_anime)

        batch.commit()

    def get_matchup(self, uid):
        self._refresh_user_cache_if_needed(uid)

        user_list = [anime for anime in self.user_caches[uid] if not anime.get("ignored", False)]

        if len(user_list) < 2:
            raise ValueError("Not enough anime entries for matchup.")

        random.shuffle(user_list)
        sorted_data = sorted(
            user_list, key=lambda x: x.get("elo_score", 1200)
        )

        idx = random.randint(0, len(sorted_data) - 2)
        return sorted_data[idx], sorted_data[idx + 1]

    def get_leaderboards(self, uid):
        self._refresh_global_cache_if_needed()
        self._refresh_user_cache_if_needed(uid)

        global_sorted = sorted(
            self.global_cache,
            key=lambda x: x.get("elo_score", 1200),
            reverse=True,
        )

        watched_personal_shows = [anime for anime in self.user_caches[uid] if not anime.get("ignored", False)]

        personal_sorted = sorted(
            watched_personal_shows,
            key=lambda x: x.get("elo_score", 1200),
            reverse=True,
        )

        return {
            "global": global_sorted,
            "personal": personal_sorted,
        }
    
    def ignore_shows(self, uid, anime_ids):
        self._refresh_user_cache_if_needed(uid)
        
        batch = self.db.batch()
        
        for anime_id in anime_ids:
            doc_ref = (
                self.db.collection("users")
                .document(uid)
                .collection("personal_anime")
                .document(str(anime_id))
            )
            batch.update(doc_ref, {"ignored": True})
            
            if uid in self.user_caches:
                for anime in self.user_caches[uid]:
                    if str(anime["id"]) == str(anime_id):
                        anime["ignored"] = True
                        
        batch.commit()
        return {"status": "success"}
    
    def get_watchlist(self, uid):
        self._refresh_user_cache_if_needed(uid)
        
        watchlist = [anime for anime in self.user_caches.get(uid, []) if anime.get("ignored", False)]
        return sorted(watchlist, key=lambda x: x['title'])

    def unignore_show(self, uid, anime_id):
        self._refresh_user_cache_if_needed(uid)
        
        doc_ref = (
            self.db.collection("users")
            .document(uid)
            .collection("personal_anime")
            .document(str(anime_id))
        )
        
        doc_ref.update({"ignored": False})
        
        # Update the in-memory cache instantly
        if uid in self.user_caches:
            for anime in self.user_caches[uid]:
                if str(anime["id"]) == str(anime_id):
                    anime["ignored"] = False
                    
        return {"status": "success"}

    def process_match(self, uid, anime_a_id, anime_b_id, outcome):
        self._refresh_user_cache_if_needed(uid)

        global_a_ref = self.db.collection("global_anime").document(
            str(anime_a_id)
        )
        global_b_ref = self.db.collection("global_anime").document(
            str(anime_b_id)
        )

        pers_a_ref = (
            self.db.collection("users")
            .document(uid)
            .collection("personal_anime")
            .document(str(anime_a_id))
        )

        pers_b_ref = (
            self.db.collection("users")
            .document(uid)
            .collection("personal_anime")
            .document(str(anime_b_id))
        )

        g_a = global_a_ref.get().to_dict()
        g_b = global_b_ref.get().to_dict()
        p_a = pers_a_ref.get().to_dict()
        p_b = pers_b_ref.get().to_dict()

        def calc_new_elo(ra, rb, outcome_val):
            ea = 1 / (1 + math.pow(10, (rb - ra) / 400))
            eb = 1 / (1 + math.pow(10, (ra - rb) / 400))

            if outcome_val == 1:
                sa, sb = 1, 0
            elif outcome_val == 0:
                sa, sb = 0, 1
            else:
                sa, sb = 0.5, 0.5

            return (
                round(ra + self.k_factor * (sa - ea)),
                round(rb + self.k_factor * (sb - eb)),
            )

        new_g_a, new_g_b = calc_new_elo(
            g_a.get("elo_score", 1200),
            g_b.get("elo_score", 1200),
            outcome,
        )

        new_p_a, new_p_b = calc_new_elo(
            p_a.get("elo_score", 1200),
            p_b.get("elo_score", 1200),
            outcome,
        )

        batch = self.db.batch()
        batch.update(global_a_ref, {"elo_score": new_g_a})
        batch.update(global_b_ref, {"elo_score": new_g_b})
        batch.update(pers_a_ref, {"elo_score": new_p_a})
        batch.update(pers_b_ref, {"elo_score": new_p_b})
        batch.commit()

        # Update in-memory global cache
        for anime in self.global_cache:
            if str(anime["id"]) == str(anime_a_id):
                anime["elo_score"] = new_g_a
            elif str(anime["id"]) == str(anime_b_id):
                anime["elo_score"] = new_g_b

        # Update in-memory user cache
        if uid in self.user_caches:
            for anime in self.user_caches[uid]:
                if str(anime["id"]) == str(anime_a_id):
                    anime["elo_score"] = new_p_a
                elif str(anime["id"]) == str(anime_b_id):
                    anime["elo_score"] = new_p_b

        return {"status": "success"}