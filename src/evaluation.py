import os
import sys
import numpy as np
import pandas as pd
from typing import List, Set, Dict, Tuple

# Adjust paths to make sure src is on path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.models import Product
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


class OfflineEvaluator:
    """
    Computes offline evaluation metrics (Recall@K and NDCG@K)
    on a test holdout split.
    """
    def __init__(self, train_parquet_path: str, items_csv_path: str, model_path: str):
        self.train_df = pd.read_parquet(train_parquet_path)
        self.items_df = pd.read_csv(items_csv_path)
        self.model_path = model_path
        
        # Load catalog
        self.products_map = {
            row["item_id"]: Product(
                row["item_id"], row["title"], row["category"], row["price"], row["tags"].split(", "), 4.5
            ) for _, row in self.items_df.iterrows()
        }

        # Initialize core DSA pipeline
        self.fs = FeatureStore()
        self.fs.fit(self.train_df, self.items_df)

        self.graph = Graph()
        for _, row in self.train_df[self.train_df["event"] == "purchase"].iterrows():
            self.graph.add_edge(row["user_id"], row["item_id"])

        self.co_gen = CoOccurrenceCandidateGenerator(self.graph)
        self.tfidf_gen = TfidfVectorSearchGenerator(self.products_map)
        self.fallback_gen = ColdStartFallbackGenerator(self.co_gen, self.fs)

        # Load LightGBM Ranker
        self.booster = None
        if HAS_LIGHTGBM and os.path.exists(model_path):
            self.booster = lgb.Booster(model_file=model_path)
            print(f"[EVALUATOR] LightGBM Model loaded successfully from: {model_path}")
        else:
            print("[EVALUATOR] [WARNING] LightGBM Model missing. Evaluating with heuristic popularity weights.")

    def get_user_recommendations(self, user_id: str, top_k: int) -> List[str]:
        """Runs candidate fusion and LightGBM ranking to get top-K recommendations."""
        # 1. Candidate Fusion
        fused_candidates: Set[str] = set()
        user_history = self.train_df[self.train_df["user_id"] == user_id]
        
        # Determine context item from user's last interaction in train split
        context_pid = None
        if not user_history.empty:
            context_pid = user_history.iloc[-1]["item_id"]

        if context_pid and context_pid in self.products_map:
            fused_candidates.update(self.co_gen.generate_candidates(context_pid, top_n=5))
            fused_candidates.update(self.tfidf_gen.generate_candidates(context_pid, top_n=5))

        # Filter out items user already bought/carted in train window
        excluded = set(user_history["item_id"].unique())
        fused_candidates = fused_candidates - excluded

        # Pad candidates if needed
        if len(fused_candidates) < top_k * 2:
            pad_pid = context_pid if context_pid else list(self.products_map.keys())[0]
            padded = self.fallback_gen.generate_candidates(pad_pid, top_n=top_k * 3)
            fused_candidates.update(padded)
            fused_candidates = fused_candidates - excluded

        candidates_list = list(fused_candidates)
        if not candidates_list:
            return []

        # 2. Ranking
        scored_items: List[Tuple[str, float]] = []
        if self.booster:
            rows = []
            for pid in candidates_list:
                u_feats = self.fs.get_user_features(user_id)
                i_feats = self.fs.get_item_features(pid)
                
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
            predictions = self.booster.predict(X)
            for idx, score in enumerate(predictions):
                scored_items.append((candidates_list[idx], float(score)))
        else:
            # Heuristic fallback
            for pid in candidates_list:
                i_feats = self.fs.get_item_features(pid)
                scored_items.append((pid, i_feats["popularity_score"]))

        # Sort descending
        scored_items = sorted(scored_items, key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in scored_items[:top_k]]

    @staticmethod
    def calculate_recall_at_k(recommendations: List[str], ground_truth: Set[str], k: int) -> float:
        """
        Recall@K = |Recs@K Intersection GroundTruth| / |GroundTruth|
        """
        recs_k = set(recommendations[:k])
        intersection = recs_k.intersection(ground_truth)
        return len(intersection) / len(ground_truth)

    @staticmethod
    def calculate_ndcg_at_k(recommendations: List[str], ground_truth: Set[str], k: int) -> float:
        """
        NDCG@K = DCG@K / IDCG@K
        DCG@K = Sum_{i=1}^K (rel_i / log2(i + 1))
        IDCG@K = Sum_{i=1}^{min(K, |GroundTruth|)} (1 / log2(i + 1))
        """
        recs_k = recommendations[:k]
        dcg = 0.0
        
        # Calculate DCG@K
        for idx, item in enumerate(recs_k):
            if item in ground_truth:
                dcg += 1.0 / np.log2(idx + 2)  # idx+2 matches 1-indexed rank formula (i+1)

        # Calculate IDCG@K (Ideal sorting: all ground truths ranked at the top)
        idcg = 0.0
        num_ideal = min(k, len(ground_truth))
        for idx in range(num_ideal):
            idcg += 1.0 / np.log2(idx + 2)

        if idcg == 0.0:
            return 0.0
            
        return dcg / idcg

    def evaluate_on_test_split(self, test_parquet_path: str, k_list: List[int] = [3, 5, 10]):
        """Runs evaluation over all test split users."""
        test_df = pd.read_parquet(test_parquet_path)
        
        # Group test events by user to extract ground-truth (future views, carts, and purchases)
        user_ground_truths: Dict[str, Set[str]] = {}
        for uid, group in test_df.groupby("user_id"):
            positives = set(group[group["event"].isin(["view", "cart", "purchase"])]["item_id"].unique())
            if positives:
                user_ground_truths[uid] = positives

        if not user_ground_truths:
            print("[EVALUATOR] [ERROR] No ground truth test interactions found in the test split.")
            return

        # Metrics accumulator
        metrics_sum: Dict[int, Dict[str, List[float]]] = {
            k: {"recall": [], "ndcg": []} for k in k_list
        }

        print(f"\nEvaluating on {len(user_ground_truths)} test users...")

        for uid, truth in user_ground_truths.items():
            # Generate recommendations up to max K needed
            max_k = max(k_list)
            recs = self.get_user_recommendations(uid, top_k=max_k)
            
            for k in k_list:
                recall = self.calculate_recall_at_k(recs, truth, k)
                ndcg = self.calculate_ndcg_at_k(recs, truth, k)
                
                metrics_sum[k]["recall"].append(recall)
                metrics_sum[k]["ndcg"].append(ndcg)

        # Print report
        print("\n==================================================")
        print("          OFFLINE EVALUATION SUMMARY REPORT       ")
        print("==================================================")
        print(f"{'Metric':<15} | {'Mean Value':<12} | {'Evaluated Users':<15}")
        print("--------------------------------------------------")
        for k in k_list:
            mean_recall = np.mean(metrics_sum[k]["recall"])
            mean_ndcg = np.mean(metrics_sum[k]["ndcg"])
            print(f"Recall@{k:<10} | {mean_recall:<12.4f} | {len(metrics_sum[k]['recall']):<15}")
            print(f"NDCG@{k:<12} | {mean_ndcg:<12.4f} | {len(metrics_sum[k]['ndcg']):<15}")
            print("--------------------------------------------------")
        print("==================================================")


if __name__ == "__main__":
    # Resolve paths
    train_path = os.path.join(base_dir, "data", "train.parquet")
    test_path = os.path.join(base_dir, "data", "test.parquet")
    items_path = os.path.join(base_dir, "data", "items.csv")
    model_path = os.path.join(base_dir, "outputs", "lightgbm_ranker.txt")

    evaluator = OfflineEvaluator(train_path, items_path, model_path)
    evaluator.evaluate_on_test_split(test_path)
