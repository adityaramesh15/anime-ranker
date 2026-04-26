import requests
import json
import time

def fetch_top_anime(pages_per_sort=5, per_page=50):
    url = 'https://graphql.anilist.co'
    
    # Notice we added $sort as a variable here
    query = '''
    query ($page: Int, $perPage: Int, $sort: [MediaSort]) {
      Page (page: $page, perPage: $perPage) {
        media (sort: $sort, type: ANIME) {
          id
          title { romaji english }
          format
          popularity
          coverImage { extraLarge }
          relations {
            edges { relationType node { id format } }
          }
        }
      }
    }
    '''
    
    all_media = []
    
    # We will loop through two different sorting methods
    sort_methods = ['POPULARITY_DESC', 'FAVOURITES_DESC']
    
    for sort_method in sort_methods:
        print(f"\nFetching by {sort_method}...")
        for page in range(1, pages_per_sort + 1):
            variables = {'page': page, 'perPage': per_page, 'sort': [sort_method]}
            response = requests.post(url, json={'query': query, 'variables': variables})
            
            if response.status_code == 200:
                data = response.json()
                all_media.extend(data['data']['Page']['media'])
                print(f"Fetched page {page}...")
                time.sleep(1) 
            else:
                print(f"Failed to fetch: {response.status_code}")
    
    with open('data/datasets/raw_anime_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_media, f, indent=4, ensure_ascii=False)
        
    print(f"\nSuccessfully saved {len(all_media)} raw shows to data/datasets/raw_anime_data.json")

if __name__ == "__main__":
    fetch_top_anime()