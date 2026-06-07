import os
import json
import pandas as pd
from datetime import datetime, timedelta

def build_csv_and_parquet_datasets():
    """
    Loads JSON mock datasets, generates events/items CSV contracts,
    and runs the time-based splitting pipeline.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    products_json_path = os.path.join(data_dir, "products.json")
    users_json_path = os.path.join(data_dir, "users.json")
    
    items_csv_path = os.path.join(data_dir, "items.csv")
    events_csv_path = os.path.join(data_dir, "events.csv")
    
    # 1. Load Products and convert to items.csv
    with open(products_json_path, "r", encoding="utf-8") as f:
        products = json.load(f)
        
    items_records = []
    for p in products:
        items_records.append({
            "item_id": p["id"],
            "title": p["name"],
            "category": p["category"],
            "brand": "StandardBrand",
            "price": p["price"],
            "desc_text": f"This is product text details for {p['name']} under {p['category']}.",
            "tags": ", ".join(p["tags"])
        })
        
    pd.DataFrame(items_records).to_csv(items_csv_path, index=False)
    print(f"[OK] Generated items CSV contract: {items_csv_path}")

    # 2. Load Users and generate event rows with incremental timestamps
    with open(users_json_path, "r", encoding="utf-8") as f:
        users = json.load(f)
        
    events_records = []
    # Start time anchor
    start_time = datetime(2026, 6, 1, 9, 0, 0)
    time_offset = 0
    
    for u in users:
        uid = u["id"]
        
        # A. Purchases events (oldest)
        for pid in u["purchase_history"]:
            ts = start_time + timedelta(hours=time_offset)
            events_records.append({
                "user_id": uid,
                "item_id": pid,
                "event": "purchase",
                "ts": ts
            })
            time_offset += 1
            
        # B. Cart events
        for pid in u["cart"]:
            ts = start_time + timedelta(hours=time_offset)
            events_records.append({
                "user_id": uid,
                "item_id": pid,
                "event": "cart",
                "ts": ts
            })
            time_offset += 1
            
        # C. Search logs as view events (newest)
        # Match search terms to product IDs if possible, or mock views
        for query in u["search_history"]:
            ts = start_time + timedelta(hours=time_offset)
            # Find a product matching query tag
            matched_pid = "P101" # Default
            for p in products:
                if any(tag in query for tag in p["tags"]):
                    matched_pid = p["id"]
                    break
            events_records.append({
                "user_id": uid,
                "item_id": matched_pid,
                "event": "view",
                "ts": ts
            })
            time_offset += 1
            
    pd.DataFrame(events_records).to_csv(events_csv_path, index=False)
    print(f"[OK] Generated events CSV contract: {events_csv_path}")
    
    # 3. Perform Chronological splitting
    validate_and_split_parquet(events_csv_path, items_csv_path, data_dir)


def validate_and_split_parquet(events_path: str, items_path: str, output_dir: str):
    """
    Schema validator and Chronological dataset splitter.
    """
    ev = pd.read_csv(events_path, parse_dates=["ts"])
    it = pd.read_csv(items_path)
    
    # Assert contracts
    assert set(["user_id", "item_id", "event", "ts"]).issubset(ev.columns), "Missing event columns."
    assert set(["item_id", "title", "category", "price", "tags"]).issubset(it.columns), "Missing item columns."
    
    # Sort chronologically
    ev = ev.sort_values("ts").reset_index(drop=True)
    
    # Cutoff Train at 80% mark
    cutoff_train = ev["ts"].quantile(0.80)
    train = ev[ev["ts"] <= cutoff_train]
    
    # Split remaining 20% into Val (50%) and Test (50%)
    remaining = ev[ev["ts"] > cutoff_train]
    cutoff_val = remaining["ts"].quantile(0.50)
    
    val = remaining[remaining["ts"] <= cutoff_val]
    test = remaining[remaining["ts"] > cutoff_val]
    
    # Save to Parquet
    train.to_parquet(os.path.join(output_dir, "train.parquet"), index=False)
    val.to_parquet(os.path.join(output_dir, "val.parquet"), index=False)
    test.to_parquet(os.path.join(output_dir, "test.parquet"), index=False)
    
    print("\n[SUCCESS] Verification and time-based splits completed:")
    print(f"  -> Train: {len(train)} records")
    print(f"  -> Val:   {len(val)} records")
    print(f"  -> Test:  {len(test)} records")


if __name__ == "__main__":
    build_csv_and_parquet_datasets()
