import json
import os
import requests
import time

def clean_and_group_anime():
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/images', exist_ok=True)

    with open('data/datasets/raw_anime_data.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    anime_dict = {item['id']: item for item in raw_data}
    adjacency_list = {item['id']: set() for item in raw_data}
    
    for item in raw_data:
        item_id = item['id']
        if not item.get('relations'):
            continue
            
        for edge in item['relations']['edges']:
            relation_type = edge['relationType']
            
            if relation_type in ['ALTERNATIVE', 'SPIN_OFF']:
                continue
                
            related_id = edge['node']['id']
            if related_id in adjacency_list:
                adjacency_list[item_id].add(related_id)
                adjacency_list[related_id].add(item_id)

    visited = set()
    franchises = []

    for item_id in adjacency_list:
        if item_id not in visited:
            component = []
            stack = [item_id]
            while stack:
                current_id = stack.pop()
                if current_id not in visited:
                    visited.add(current_id)
                    component.append(anime_dict[current_id])
                    stack.extend(adjacency_list[current_id])
            
            franchises.append(component)

    final_list = []
    valid_main_formats = ['TV', 'ONA']
    
    print(f"Processing {len(franchises)} potential franchises and downloading images. This might take a minute...")
    
    for group in franchises:
        has_main_show = any(anime['format'] in valid_main_formats for anime in group)
        
        if not has_main_show:
            continue 
        
        main_shows = [anime for anime in group if anime['format'] in valid_main_formats]
        main_show = min(main_shows, key=lambda x: x['id'])
        title = main_show['title']['english'] or main_show['title']['romaji']
        
        anime_id = main_show['id']
        image_url = main_show['coverImage']['extraLarge']
        image_path = f"data/images/{anime_id}.jpg"
        
        if not os.path.exists(image_path) and image_url:
            try:
                img_data = requests.get(image_url).content
                with open(image_path, 'wb') as handler:
                    handler.write(img_data)
                time.sleep(0.1) 
            except Exception as e:
                print(f"Failed to download image for {title}: {e}")

        final_list.append({
            "id": anime_id,
            "title": title,
            "elo_score": 1200,
            "merged_entries": len(group)
        })

    with open('data/datasets/clean_anime_list.json', 'w', encoding='utf-8') as f:
        json.dump(final_list, f, indent=4, ensure_ascii=False)
        
    print(f"Done! Cleaned data saved, and {len(final_list)} images are ready in the /images folder.")

if __name__ == "__main__":
    clean_and_group_anime()