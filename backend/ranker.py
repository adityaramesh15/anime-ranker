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
        self.CACHE_TTL = 3600  # 1 hour

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
            self._refresh_global_cache_if_needed()
            
            personal_ref = (
                self.db.collection("users")
                .document(uid)
                .collection("personal_anime")
            )

            docs_ref = list(personal_ref.stream())
            docs = [doc.to_dict() for doc in docs_ref]

            if len(docs) < len(self.global_cache):
                print(f"Syncing missing shows for user ({uid})...")
                new_shows = self._sync_missing_shows(uid, docs_ref)
                
                docs.extend(new_shows) 

            self.user_caches[uid] = docs

    def _sync_missing_shows(self, uid, existing_docs_ref):
        batch = self.db.batch()
        personal_ref = (
            self.db.collection("users")
            .document(uid)
            .collection("personal_anime")
        )

        existing_ids = {doc.id for doc in existing_docs_ref}
        new_shows_added = []

        for anime in self.global_cache:
            if str(anime["id"]) not in existing_ids:
                doc_ref = personal_ref.document(str(anime["id"]))
                base_anime = anime.copy()
                base_anime["elo_score"] = 1200
                base_anime["ignored"] = False 
                batch.set(doc_ref, base_anime)
                
                new_shows_added.append(base_anime)

        batch.commit()
        return new_shows_added

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
            key=lambda x: (x.get("matches_played", 0) == 0, -x.get("elo_score", 1200))
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
    
    def get_user(self, uid):
        doc_ref = self.db.collection("users").document(uid)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    def set_display_name(self, uid, display_name):
        display_name_lower = display_name.lower().strip()
        
        # Check uniqueness (limit to 1 document to save reads)
        query = self.db.collection("users").where("display_name_lower", "==", display_name_lower).limit(1).get()
        if query:
            # Check if it belongs to the SAME user (in case they are saving the same name)
            if query[0].id != uid:
                raise ValueError("Display name already taken.")
                
        doc_ref = self.db.collection("users").document(uid)
        
        doc = doc_ref.get()
        if not doc.exists:
            doc_ref.set({
                "display_name": display_name.strip(),
                "display_name_lower": display_name_lower,
                "total_matches": 0
            })
        else:
            doc_ref.update({
                "display_name": display_name.strip(),
                "display_name_lower": display_name_lower
            })
        
        return {"status": "success", "display_name": display_name.strip()}

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

        g_a_matches = g_a.get("matches_played", 0) + 1
        g_b_matches = g_b.get("matches_played", 0) + 1

        new_p_a, new_p_b = calc_new_elo(
            p_a.get("elo_score", 1200),
            p_b.get("elo_score", 1200),
            outcome,
        )

        batch = self.db.batch()
        batch.update(global_a_ref, {"elo_score": new_g_a, "matches_played": g_a_matches})
        batch.update(global_b_ref, {"elo_score": new_g_b, "matches_played": g_b_matches})
        batch.update(pers_a_ref, {"elo_score": new_p_a})
        batch.update(pers_b_ref, {"elo_score": new_p_b})
        
        user_ref = self.db.collection("users").document(uid)
        batch.update(user_ref, {"total_matches": firestore.Increment(1)})

        batch.commit()

        # Update in-memory global cache
        for anime in self.global_cache:
            if str(anime["id"]) == str(anime_a_id):
                anime["elo_score"] = new_g_a
                anime["matches_played"] = g_a_matches
            elif str(anime["id"]) == str(anime_b_id):
                anime["elo_score"] = new_g_b
                anime["matches_played"] = g_b_matches

        # Update in-memory user cache
        if uid in self.user_caches:
            for anime in self.user_caches[uid]:
                if str(anime["id"]) == str(anime_a_id):
                    anime["elo_score"] = new_p_a
                elif str(anime["id"]) == str(anime_b_id):
                    anime["elo_score"] = new_p_b

        return {"status": "success"}

    def get_stats(self, uid):
        user_doc = self.get_user(uid)
        if not user_doc:
            raise ValueError("User not found")

        total_matches = user_doc.get("total_matches", 0)

        self._refresh_global_cache_if_needed()
        self._refresh_user_cache_if_needed(uid)

        total_global = len(self.global_cache)
        watched_shows = [anime for anime in self.user_caches.get(uid, []) if not anime.get("ignored", False)]
        watched_count = len(watched_shows)

        completion_percentage = (watched_count / total_global * 100) if total_global > 0 else 0

        global_sorted = sorted(self.global_cache, key=lambda x: (x.get("matches_played", 0) == 0, -x.get("elo_score", 1200)))
        global_top_10_ids = {str(a["id"]) for a in global_sorted[:10]}

        personal_sorted = sorted(watched_shows, key=lambda x: x.get("elo_score", 1200), reverse=True)
        personal_top_10_ids = {str(a["id"]) for a in personal_sorted[:10]}

        intersection = global_top_10_ids.intersection(personal_top_10_ids)
        alignment_percentage = (len(intersection) / 10) * 100

        biggest_positive = {"title": "N/A", "diff": 0}
        biggest_negative = {"title": "N/A", "diff": 0}

        global_dict = {str(a["id"]): a for a in self.global_cache}

        for p_anime in watched_shows:
            g_anime = global_dict.get(str(p_anime["id"]))
            if g_anime:
                p_elo = p_anime.get("elo_score", 1200)
                g_elo = g_anime.get("elo_score", 1200)
                diff = p_elo - g_elo

                if diff > biggest_positive["diff"]:
                    biggest_positive = {"title": p_anime.get("title", "Unknown"), "diff": round(diff)}
                elif diff < biggest_negative["diff"]:
                    biggest_negative = {"title": p_anime.get("title", "Unknown"), "diff": round(diff)}

        return {
            "total_matches": total_matches,
            "completion_percentage": round(completion_percentage, 1),
            "alignment_percentage": round(alignment_percentage, 1),
            "biggest_positive_divergence": biggest_positive,
            "biggest_negative_divergence": biggest_negative
        }