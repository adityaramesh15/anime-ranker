import requests
import json
import time

def fetch_top_anime(pages=3, per_page=50):
    url = 'https://graphql.anilist.co'
    query = '''
    query ($page: Int, $perPage: Int) {
      Page (page: $page, perPage: $perPage) {
        media (sort: POPULARITY_DESC, type: ANIME) {
          id
          title {
            romaji
            english
          }
          format
          relations {
            edges {
              relationType
              node {
                id
                format
              }
            }
          }
        }
      }
    }
    '''
    
    all_media = []
    
    for page in range(1, pages + 1):
        variables = {'page': page, 'perPage': per_page}
        response = requests.post(url, json={'query': query, 'variables': variables})
        
        if response.status_code == 200:
            data = response.json()
            all_media.extend(data['data']['Page']['media'])
            print(f"Fetched page {page}...")
            time.sleep(1) 
        else:
            print(f"Failed to fetch page {page}: {response.status_code}")
    

    with open('data/raw_anime_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_media, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully saved {len(all_media)} shows to data/raw_anime_data.json")

if __name__ == "__main__":
    fetch_top_anime()