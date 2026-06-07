import pandas as pd
import numpy as np
from typing import Tuple
from src.feature_store import FeatureStore

class DatasetGenerator:
    """
    Generates labeled training datasets by pairing positive interactions
    (future cart/purchases) with sampled negative items, then joining
    user and item features from the Feature Store.
    """
    def __init__(self, feature_store: FeatureStore):
        self.feature_store = feature_store

    def create_labeled_pairs(
        self, 
        label_events: pd.DataFrame, 
        items_df: pd.DataFrame, 
        negative_ratio: float = 3.0
    ) -> pd.DataFrame:
        """
        Creates (user_id, item_id, label) pairs.
        - Positive (1): user has a future cart or purchase in label_events.
        - Negative (0): randomly sampled items that the user did not interact with.
        """
        all_items = set(items_df["item_id"].unique())
        records = []

        # Group label events by user
        user_grouped = label_events.groupby("user_id")

        for uid, group in user_grouped:
            # Positive items are those with cart or purchase actions in future window
            positives = set(group[group["event"].isin(["cart", "purchase"])]["item_id"].unique())
            
            # Skip users who have no positive conversions in this window
            if not positives:
                continue

            # Add Positive rows
            for pid in positives:
                records.append({
                    "user_id": uid,
                    "item_id": pid,
                    "label": 1
                })

            # Negative Sampling:
            # Identify candidate negative items (catalog items user has NOT interacted with in the label window)
            interacted_in_window = set(group["item_id"].unique())
            negative_candidates = list(all_items - interacted_in_window)

            if not negative_candidates:
                continue

            # Number of negatives to sample
            num_negatives = int(len(positives) * negative_ratio)
            num_negatives = min(num_negatives, len(negative_candidates))

            # Randomly sample negatives
            sampled_negatives = np.random.choice(negative_candidates, size=num_negatives, replace=False)

            for pid in sampled_negatives:
                records.append({
                    "user_id": uid,
                    "item_id": pid,
                    "label": 0
                })

        return pd.DataFrame(records)

    def join_features(self, pairs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Joins user, item, and relational match features into the labeled pairs dataset.
        """
        joined_records = []

        for _, row in pairs_df.iterrows():
            uid = row["user_id"]
            pid = row["item_id"]
            label = row["label"]

            # 1. Fetch features from store
            u_feats = self.feature_store.get_user_features(uid)
            i_feats = self.feature_store.get_item_features(pid)

            category = i_feats.get("category", "Unknown")

            # 2. Compute relational cross-features
            # Retrieve user's specific interest score for this product's category
            user_category_interest = u_feats["category_interests"].get(category, 0.0)
            
            # Retrieve user's historical cumulative interaction weight for this specific product
            user_item_past_interaction = u_feats["item_interactions"].get(pid, 0.0)

            # Compile feature row
            joined_records.append({
                "user_id": uid,
                "item_id": pid,
                
                # --- User Aggregates ---
                "user_total_weight": u_feats["total_weight"],
                
                # --- Item Aggregates ---
                "item_popularity_score": i_feats["popularity_score"],
                "item_total_interactions": i_feats["total_interactions"],
                
                # --- Relational Match Features ---
                "user_category_interest_weight": user_category_interest,
                "user_item_past_interaction_weight": user_item_past_interaction,
                
                # --- Target Label ---
                "label": label
            })

        return pd.DataFrame(joined_records)

    def generate_training_data(
        self, 
        label_events: pd.DataFrame, 
        items_df: pd.DataFrame, 
        negative_ratio: float = 3.0
    ) -> pd.DataFrame:
        """
        Runs full pipeline: creates pairs, samples negatives, and joins features.
        """
        pairs = self.create_labeled_pairs(label_events, items_df, negative_ratio)
        if pairs.empty:
            return pd.DataFrame()
        return self.join_features(pairs)
