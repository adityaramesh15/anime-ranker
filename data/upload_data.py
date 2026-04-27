import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def safe_upload_data():
    cred = credentials.Certificate('firebase_credentials.json')

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    with open('data/datasets/clean_anime_list.json', 'r', encoding='utf-8') as f:
        anime_list = json.load(f)
    
    print(f"Loading {len(anime_list)} local shows...")

    print("Checking Firestore for existing entries...")
    existing_docs_ref = db.collection('global_anime').select([]).get()
    existing_ids = {doc.id for doc in existing_docs_ref}

    new_shows_count = 0

    # 2. Upload only the new shows
    for anime in anime_list:
        anime_id_str = str(anime['id'])
        
        # If it's already in the database, do nothing to protect the Elo
        if anime_id_str in existing_ids:
            continue
            
        # If it is new, set it
        doc_ref = db.collection('global_anime').document(anime_id_str)
        doc_ref.set(anime)
        print(f"Added new show: {anime['title']}")
        new_shows_count += 1
    
    print(f"\nUpload complete! Added {new_shows_count} new shows. All existing Elo scores were preserved.")

if __name__ == "__main__":
    safe_upload_data()