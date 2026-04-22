import json

def clean_and_group_anime():
    with open('data/raw_anime_data.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    anime_dict = {item['id']: item for item in raw_data}
    adjacency_list = {item['id']: set() for item in raw_data}
    
    for item in raw_data:
        item_id = item['id']
        if not item.get('relations'):
            continue
            
        for edge in item['relations']['edges']:
            relation_type = edge['relationType']
            
            # Skip relationships that represent a different timeline or a side-story
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
    
    for group in franchises:
        has_main_show = any(anime['format'] in valid_main_formats for anime in group)
        
        if not has_main_show:
            continue 
        

        main_shows = [anime for anime in group if anime['format'] in valid_main_formats]
        
        main_show = min(main_shows, key=lambda x: x['id'])
        title = main_show['title']['english'] or main_show['title']['romaji']
        
        final_list.append({
            "id": main_show['id'],
            "title": title,
            "elo_score": 1200,
            "merged_entries": len(group)
        })

    with open('data/clean_anime_list.json', 'w', encoding='utf-8') as f:
        json.dump(final_list, f, indent=4, ensure_ascii=False)
        
    print(f"Data cleaned! We now have {len(final_list)} distinct TV/ONA franchises.")

if __name__ == "__main__":
    clean_and_group_anime()