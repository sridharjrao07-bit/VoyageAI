"""
Precompute CLIP embeddings using raw asyncpg.
"""
import sys, asyncio, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from engine import data_loader
data_loader.load_data()

df = data_loader.get_destinations()
print(f"Found {len(df)} destinations to encode with CLIP...")

import torch
from engine.clip_engine import _processor, _model, _to_tensor
import asyncpg

texts = []
dest_ids = []
for _, row in df.iterrows():
    combined = (
        f"A travel photo of {row.get('name', '')} in {row.get('country', '')}. "
        f"{row.get('description', '')} "
        f"{row.get('tags', '')}. "
        f"{row.get('climate', '')} climate."
    )
    texts.append(combined)
    dest_ids.append(str(row["id"]))

print(f"[CLIP] Encoding {len(texts)} destinations...")
all_embeddings = []
batch_size = 32
for i in range(0, len(texts), batch_size):
    batch = texts[i : i + batch_size]
    inputs = _processor(text=batch, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        raw = _model.get_text_features(input_ids=inputs.input_ids, attention_mask=inputs.attention_mask)
    features = _to_tensor(raw)
    features = torch.nn.functional.normalize(features, dim=-1)
    all_embeddings.extend(features.cpu().numpy().tolist())

db_url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg", "postgresql")

async def store_embeddings_raw():
    print("Connecting to DB raw...")
    # use a long statement timeout
    conn = await asyncpg.connect(db_url, command_timeout=60)
    for i in range(len(dest_ids)):
        did = dest_ids[i]
        emb = all_embeddings[i]
        # format vector properly for pgvector literal
        vector_str = "[" + ",".join(f"{x:.6f}" for x in emb) + "]"
        
        for attempt in range(3):
            try:
                await conn.execute("UPDATE destinations SET clip_embedding = $1::vector WHERE id = $2", vector_str, did)
                if i % 10 == 0:
                    print(f"  Stored {i+1}/{len(dest_ids)}")
                break
            except Exception as e:
                print(f"  Attempt {attempt+1} failed for {did}: {e}")
                await asyncio.sleep(2)
                try:
                    await conn.close()
                except:
                    pass
                conn = await asyncpg.connect(db_url, command_timeout=60)
    
    await conn.close()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(store_embeddings_raw())
print("\nDone! CLIP embeddings are now stored in PostgreSQL.")
