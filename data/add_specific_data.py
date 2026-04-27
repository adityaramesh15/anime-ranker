import json
import os
import requests
import time



def fetch_and_append_missing_shows():
    target_titles = [
        "Blue Box", 
        "The Disastrous Life of Saiki K.", 
        "The Saint's Magic Power is Omnipotent", 
        "Ascendance of a Bookworm", 
        "BORUTO", 
        "The Faraway Paladin", 
        "Clevatess"
    ]

    # File paths
    json_path = 'data/datasets/clean_anime_list.json'
    img_dir = 'frontend/images'
    
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    existing_data = []
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            
    existing_ids = {item['id'] for item in existing_data}
    new_additions = []

    url = 'https://graphql.anilist.co'
    query = '''
    query ($search: String) {
      Media (search: $search, type: ANIME, sort: POPULARITY_DESC) {
        id
        title { romaji english }
        format
        coverImage { extraLarge }
      }
    }
    '''

    print(f"Hunting for {len(target_titles)} specific heavyweights...")

    for target in target_titles:
        variables = {'search': target}
        response = requests.post(url, json={'query': query, 'variables': variables})
        
        if response.status_code == 200:
            data = response.json()
            media = data.get('data', {}).get('Media')
            
            if not media:
                print(f"Could not find a match for: {target}")
                continue
                
            anime_id = media['id']
            
            if anime_id in existing_ids:
                print(f"Already in dataset, skipping: {target}")
                continue

            # Figure out the best title
            title = media['title'].get('english') or media['title'].get('romaji') or target
            image_url = media['coverImage']['extraLarge']
            
            # Download the cover art
            image_path = f"{img_dir}/{anime_id}.jpg"
            if not os.path.exists(image_path) and image_url:
                try:
                    img_data = requests.get(image_url).content
                    with open(image_path, 'wb') as handler:
                        handler.write(img_data)
                    print(f"Downloaded image for {title}")
                except Exception as e:
                    print(f"Failed to download image for {title}: {e}")


            new_additions.append({
                "id": anime_id,
                "title": title,
                "elo_score": 1200,
                "merged_entries": 1 
            })
            
            existing_ids.add(anime_id)
            print(f"Added {title} to the roster!")
            
            # Play nice with the API rate limits
            time.sleep(1)
            
        else:
            print(f"API Error for {target}: {response.status_code}")

    if new_additions:
        existing_data.extend(new_additions)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
        print(f"\nSuccess! Appended {len(new_additions)} new shows to {json_path}.")
    else:
        print("\nNo new shows were added (they might already be in your dataset).")

if __name__ == "__main__":
    fetch_and_append_missing_shows()