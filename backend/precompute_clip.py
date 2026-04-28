"""
Precompute CLIP embeddings for all destinations and store in PostgreSQL.
Run this once to populate the clip_embedding column.
"""
import sys, asyncio
sys.path.insert(0, '.')

from engine import data_loader
data_loader.load_data()

df = data_loader.get_destinations()
print(f"Found {len(df)} destinations to encode with CLIP...")

# Encode all destinations using CLIP text encoder
import torch
from engine.clip_engine import _processor, _model, _to_tensor

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
    print(f"  Batch {i//batch_size + 1}: encoded {min(i+batch_size, len(texts))}/{len(texts)}")

print(f"[CLIP] All {len(all_embeddings)} embeddings computed. Each is {len(all_embeddings[0])}-dim.")

# Now upsert into db in small batches
async def store_embeddings():
    from database import async_session
    from models import Destination
    from sqlalchemy import update
    
    # We will do smaller chunks and use a single update statement per item to avoid long transactions
    for i in range(len(dest_ids)):
        did = dest_ids[i]
        emb = all_embeddings[i]
        
        # Retry logic for dropped connections
        for attempt in range(3):
            try:
                async with async_session() as session:
                    stmt = update(Destination).where(Destination.id == did).values(clip_embedding=emb)
                    await session.execute(stmt)
                    await session.commit()
                if i % 10 == 0:
                    print(f"  Stored {i+1}/{len(dest_ids)}")
                break
            except Exception as e:
                print(f"  Attempt {attempt+1} failed for {did}: {e}")
                await asyncio.sleep(2)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(store_embeddings())
print("\nDone! CLIP embeddings are now stored in PostgreSQL.")
