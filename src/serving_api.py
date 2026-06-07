import os
import sys
import json
import random
import pandas as pd
import numpy as np
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Adjust paths to make sure src is on path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.models import Product, User
from src.feature_store import FeatureStore
from src.graph import Graph
from src.candidate_generators import (
    CoOccurrenceCandidateGenerator,
    TfidfVectorSearchGenerator,
    ColdStartFallbackGenerator
)

# Try importing LightGBM
try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

# Initialize FastAPI App
app = FastAPI(
    title="E-Commerce Recommendation System API",
    description="FastAPI microservice exposing candidate fusion, LightGBM ranking, diversity filtering, and exploration.",
    version="1.0.0"
)

# Enable CORS (Cross-Origin Resource Sharing)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances loaded at startup
engine_data: Dict[str, Any] = {}

class RecommendationResponse(BaseModel):
    id: str
    title: str
    category: str
    price: float
    rating: float
    score: float
    source: str


@app.on_event("startup")
def startup_event():
    """Loads datasets, builds Feature Store, Graph, Generators, and loads LightGBM model."""
    print("[STARTUP] Initializing recommendation pipeline serving modules...")
    
    # Paths
    products_path = os.path.join(base_dir, "data", "products.json")
    users_path = os.path.join(base_dir, "data", "users.json")
    events_path = os.path.join(base_dir, "data", "events.csv")
    items_path = os.path.join(base_dir, "data", "items.csv")
    model_path = os.path.join(base_dir, "outputs", "lightgbm_ranker.txt")

    # Verify files
    if not (os.path.exists(products_path) and os.path.exists(events_path)):
        # Run preparation pipeline if CSVs are missing
        from src.data_prep import build_csv_and_parquet_datasets
        build_csv_and_parquet_datasets()

    # 1. Load Products Map
    with open(products_path, "r", encoding="utf-8") as f:
        raw_products = json.load(f)
    products_map = {p["id"]: Product.from_dict(p) for p in raw_products}

    # 2. Load Users Map
    with open(users_path, "r", encoding="utf-8") as f:
        raw_users = json.load(f)
    users_map = {u["id"]: User.from_dict(u) for u in raw_users}

    # 3. Fit Feature Store
    events_df = pd.read_csv(events_path, parse_dates=["ts"])
    items_df = pd.read_csv(items_path)
    fs = FeatureStore()
    fs.fit(events_df, items_df)

    # 4. Load Purchase Graph
    graph = Graph()
    for _, row in events_df[events_df["event"] == "purchase"].iterrows():
        graph.add_edge(row["user_id"], row["item_id"])

    # 5. Initialize Candidate Generators
    co_generator = CoOccurrenceCandidateGenerator(graph)
    tfidf_generator = TfidfVectorSearchGenerator(products_map)
    fallback_generator = ColdStartFallbackGenerator(co_generator, fs)

    # 6. Load LightGBM model
    booster = None
    if HAS_LIGHTGBM and os.path.exists(model_path):
        booster = lgb.Booster(model_file=model_path)
        print(f"[STARTUP] LightGBM Model loaded successfully from: {model_path}")
    else:
        print(f"[STARTUP] [WARNING] LightGBM Model missing at {model_path}. Falling back to default heuristics.")

    # Save to global config
    engine_data.update({
        "products_map": products_map,
        "users_map": users_map,
        "feature_store": fs,
        "graph": graph,
        "co_generator": co_generator,
        "tfidf_generator": tfidf_generator,
        "fallback_generator": fallback_generator,
        "booster": booster
    })
    print("[STARTUP] Recommendation service ready.")


@app.get("/recommend", response_model=List[RecommendationResponse])
def recommend(
    user_id: str = Query(..., description="Target User ID"),
    item_id: Optional[str] = Query(None, description="Current item ID context (for PDP similar recommendations)"),
    top_n: int = Query(5, description="Number of items to recommend"),
    epsilon: float = Query(0.10, description="Epsilon-greedy exploration rate")
):
    """
    Fuses candidates, joins user/item features, scores using LightGBM ranker,
    enforces category diversity constraints, and applies epsilon-greedy exploration.
    """
    # Verify User exists
    users_map = engine_data["users_map"]
    if user_id not in users_map:
        raise HTTPException(status_code=404, detail="User ID not found.")

    user = users_map[user_id]
    products_map = engine_data["products_map"]
    fs: FeatureStore = engine_data["feature_store"]
    fallback_gen: ColdStartFallbackGenerator = engine_data["fallback_generator"]

    # 1. CANDIDATE RETRIEVAL & FUSION
    # Identify context item
    context_pid = item_id
    if not context_pid:
        # Fall back to user's last purchased item as context, if any
        purchased_list = list(user.purchase_history)
        if purchased_list:
            context_pid = purchased_list[-1]
            
    fused_candidates: Set[str] = set()
    
    # Retrieve Candidates (if context item is set)
    if context_pid and context_pid in products_map:
        # Pull from Co-occurrence
        co_cands = engine_data["co_generator"].generate_candidates(context_pid, top_n=5)
        # Pull from Content Similarity (TF-IDF)
        tfidf_cands = engine_data["tfidf_generator"].generate_candidates(context_pid, top_n=5)
        
        fused_candidates.update(co_cands)
        fused_candidates.update(tfidf_cands)

    # Exclude items user already purchased or currently in active cart
    excluded_items = user.purchase_history.union(user.cart)
    fused_candidates = fused_candidates - excluded_items

    # Cold Start fallback padding: if candidates set is smaller than needed, pad it
    if len(fused_candidates) < top_n * 2:
        pad_context = context_pid if context_pid else (list(products_map.keys())[0])
        padded = fallback_gen.generate_candidates(pad_context, top_n=top_n * 3)
        fused_candidates.update(padded)
        fused_candidates = fused_candidates - excluded_items

    candidates_list = list(fused_candidates)

    # 2. FEATURE CONSTRUCTION & LIGHTGBM SCORING
    scored_items: List[Tuple[str, float, str]] = []
    booster = engine_data["booster"]

    if booster and len(candidates_list) > 0:
        # Build DataFrame of features matching LightGBM input
        rows = []
        for pid in candidates_list:
            u_feats = fs.get_user_features(user_id)
            i_feats = fs.get_item_features(pid)
            
            category = i_feats.get("category", "Unknown")
            user_category_interest = u_feats["category_interests"].get(category, 0.0)
            user_item_past_interaction = u_feats["item_interactions"].get(pid, 0.0)
            
            rows.append({
                "user_total_weight": u_feats["total_weight"],
                "item_popularity_score": i_feats["popularity_score"],
                "item_total_interactions": i_feats["total_interactions"],
                "user_category_interest_weight": user_category_interest,
                "user_item_past_interaction_weight": user_item_past_interaction
            })
            
        X = pd.DataFrame(rows)
        # Predict ranking scores
        predictions = booster.predict(X)
        
        for idx, score in enumerate(predictions):
            scored_items.append((candidates_list[idx], float(score), "LightGBM LambdaMART"))
    else:
        # Fall back to heuristic scoring if model is missing: combined tag similarity + rating weight
        print("[WARNING] Heuristic fallback search used.")
        for pid in candidates_list:
            prod = products_map[pid]
            # Simple score: rating / 5.0
            score = prod.rating / 5.0
            scored_items.append((pid, score, "Popularity Heuristic"))

    # Sort candidates by score descending
    scored_items = sorted(scored_items, key=lambda x: x[1], reverse=True)

    # 3. DIVERSITY CAPPING
    # Limit to max 2 recommendations per category
    category_counts: Dict[str, int] = {}
    fused_recs: List[Tuple[str, float, str]] = []
    category_limit = 2

    for pid, score, source in scored_items:
        prod = products_map[pid]
        cat = prod.category
        
        count = category_counts.get(cat, 0)
        if count < category_limit:
            fused_recs.append((pid, score, source))
            category_counts[cat] = count + 1
            
        if len(fused_recs) >= top_n:
            break

    # 4. EPSILON-GREEDY EXPLORATION
    # With probability epsilon, inject a random item to discover new tastes
    final_recs = []
    
    if random.random() < epsilon and len(fused_recs) > 0:
        # Select a random item from the global catalog that is not excluded or already in top recommendations
        chosen_rec_pids = set(pid for pid, _, _ in fused_recs)
        exploration_candidates = list(set(products_map.keys()) - excluded_items - chosen_rec_pids)
        
        if exploration_candidates:
            # Pick a random product
            explored_pid = random.choice(exploration_candidates)
            explored_score = 0.5 # Mid-score benchmark
            
            # Inject at the 2nd or 3rd slot (index 1 or 2) to ensure visibility without breaking top slot
            idx_to_inject = min(2, len(fused_recs))
            
            fused_recs.insert(idx_to_inject, (explored_pid, explored_score, "e-Greedy Exploration"))
            # Truncate to top_n
            fused_recs = fused_recs[:top_n]
            print(f"[EXPLORE] Injected random exploration item {explored_pid} at index {idx_to_inject}")

    # 5. CONVERT TO JSON RESPONSE
    for pid, score, source in fused_recs:
        prod = products_map[pid]
        final_recs.append(RecommendationResponse(
            id=prod.id,
            title=prod.name,
            category=prod.category,
            price=prod.price,
            rating=prod.rating,
            score=score,
            source=source
        ))

    return final_recs
