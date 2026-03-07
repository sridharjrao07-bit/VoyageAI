import os
import sqlite3
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(__file__))

from engine.data_loader import load_data, get_destinations
from engine.db import DB_PATH, get_db_connection, init_db

def setup_mock_data():
    init_db()
    load_data()
    df = get_destinations()
    
    if df is None or df.empty:
        print("No destinations data available.")
        return

    destinations = df.to_dict(orient="records")
    dest1 = destinations[0]
    dest2 = destinations[1]
    dest3 = destinations[2]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Clear existing
        cursor.execute("DELETE FROM user_comments")
        
        # Dest 1: Critical safety issue
        cursor.execute("INSERT INTO user_comments (destination_id, user_id, comment_text, rating, is_verified_visit) VALUES (?, ?, ?, ?, ?)", 
                       (str(dest1['id']), "user1", "Bridge washed out, completely inaccessible right now. DO NOT GO.", 1, True))
        cursor.execute("INSERT INTO user_comments (destination_id, user_id, comment_text, rating, is_verified_visit) VALUES (?, ?, ?, ?, ?)", 
                       (str(dest1['id']), "user2", "Road closed due to landslides.", 1, True))

        # Dest 2: Verified visit with pro-tip
        cursor.execute("INSERT INTO user_comments (destination_id, user_id, comment_text, rating, is_verified_visit) VALUES (?, ?, ?, ?, ?)", 
                       (str(dest2['id']), "user3", "Amazing place! We loved the views. Make sure to visit the north-side trail for sunrise, it's breathtaking.", 5, True))
        cursor.execute("INSERT INTO user_comments (destination_id, user_id, comment_text, rating, is_verified_visit) VALUES (?, ?, ?, ?, ?)", 
                       (str(dest2['id']), "user4", "Beautiful spot, very peaceful.", 4, True))

        # Dest 3: Spam
        cursor.execute("INSERT INTO user_comments (destination_id, user_id, comment_text, rating, is_verified_visit) VALUES (?, ?, ?, ?, ?)", 
                       (str(dest3['id']), "user5", "Test Fake sdfksdfk", 5, False))
        cursor.execute("INSERT INTO user_comments (destination_id, user_id, comment_text, rating, is_verified_visit) VALUES (?, ?, ?, ?, ?)", 
                       (str(dest3['id']), "user6", "Test", 1, False))

    print("Mock data inserted.")
    print(f"Dest 1 (Safety Issue): {dest1['name']} ({dest1['id']})")
    print(f"Dest 2 (Good/Pro-Tip): {dest2['name']} ({dest2['id']})")
    print(f"Dest 3 (Spam): {dest3['name']} ({dest3['id']})")

if __name__ == "__main__":
    setup_mock_data()
