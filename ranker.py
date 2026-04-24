import json
import random
import math

class AnimeRanker:
    def __init__(self, data_file='data/clean_anime_list.json'):
        """Initializes the ranker, sets the K-factor, and loads the data."""
        self.data_file = data_file
        self.k_factor = 32 
        self.anime_data = self.load_data()

    def load_data(self):
        """Reads the current anime data and Elo scores from the JSON file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Could not find {self.data_file}. Did you run clean_data.py?")
            return []

    def save_data(self):
        """Saves the updated Elo scores back to the JSON file."""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.anime_data, f, indent=4, ensure_ascii=False)

    def calculate_expected_score(self, rating_a, rating_b):
        """Calculates the expected probability of 'A' winning against 'B'."""
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))

    def get_matchup(self):
        """
        Finds two anime with similar Elo scores for a fair matchup.
        We achieve this by sorting the list by score and picking two adjacent items.
        """
        random.shuffle(self.anime_data)
        
        sorted_data = sorted(self.anime_data, key=lambda x: x['elo_score'])
        idx = random.randint(0, len(sorted_data) - 2)
        
        return sorted_data[idx], sorted_data[idx + 1]

    def process_match(self, anime_a_id, anime_b_id, outcome):
        """
        Updates the scores for two anime based on the match outcome.
        Outcome: 1 (A wins), 0 (B wins), 0.5 (Tie)
        """
        # Locate the specific anime dictionaries in our loaded data
        anime_a = next(item for item in self.anime_data if item['id'] == anime_a_id)
        anime_b = next(item for item in self.anime_data if item['id'] == anime_b_id)

        ra = anime_a['elo_score']
        rb = anime_b['elo_score']

        # 1. Calculate expected scores
        ea = self.calculate_expected_score(ra, rb)
        eb = self.calculate_expected_score(rb, ra)

        # 2. Determine actual scores based on user's choice
        if outcome == 1:     
            sa, sb = 1, 0
        elif outcome == 0:   
            sa, sb = 0, 1
        else:                
            sa, sb = 0.5, 0.5

        # 3. Apply the Elo formula and update the dictionaries
        anime_a['elo_score'] = round(ra + self.k_factor * (sa - ea))
        anime_b['elo_score'] = round(rb + self.k_factor * (sb - eb))

        # 4. Save the new state immediately
        self.save_data()
        
        return anime_a, anime_b

    def skip_match(self):
        """
        If you haven't seen a show, we simply do nothing. 
        The CLI loop will just call get_matchup() again.
        """
        pass