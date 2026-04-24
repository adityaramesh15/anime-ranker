import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def upload_data():
    cred = credentials.Certificate('firebase_credentials.json')
    firebase_admin.initialize_app(cred)

    db = firestore.client()

    with open('data/datasets/clean_anime_list.json', 'r', encoding='utf-8') as f:
        anime_list = json.load(f)
    
    print(f"Uploading {len(anime_list)} shows to Firestore...")

    for anime in anime_list:
        doc_ref = db.collection('anime').document(str(anime['id']))
        doc_ref.set(anime)
    
    print("Upload complete! Check your Firebase Console to see the data.")

if __name__ == "__main__":
    upload_data()
