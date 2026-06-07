import pandas as pd
from typing import Dict, Any, List

class FeatureStore:
    """
    An in-memory Feature Store managing user and item aggregates
    built from implicit event weights.
    """
    def __init__(self):
        # Implicit action weights configuration
        self.weights = {
            "view": 1.0,
            "cart": 3.0,
            "purchase": 5.0
        }
        
        # User aggregates: user_id -> { total_weight, category_interests: {cat: weight}, item_interactions: {pid: weight} }
        self.user_features: Dict[str, Dict[str, Any]] = {}
        
        # Item aggregates: item_id -> { popularity_score, total_interactions, category }
        self.item_features: Dict[str, Dict[str, Any]] = {}

    def get_implicit_weight(self, event_type: str) -> float:
        """Returns the numerical weight of an interaction type."""
        return self.weights.get(event_type.lower(), 1.0)

    def fit(self, events_df: pd.DataFrame, items_df: pd.DataFrame) -> None:
        """
        Populates the feature store by aggregating historical events and catalog metadata.
        Time Complexity: O(E + I) where E is events count and I is items count.
        """
        # Initialize item base properties
        for _, row in items_df.iterrows():
            self.item_features[row["item_id"]] = {
                "popularity_score": 0.0,
                "total_interactions": 0,
                "category": row["category"]
            }

        # Build user and item features from interactions
        for _, row in events_df.iterrows():
            uid = row["user_id"]
            pid = row["item_id"]
            action = row["event"]
            
            weight = self.get_implicit_weight(action)
            
            # --- Populate Item Features ---
            if pid in self.item_features:
                self.item_features[pid]["popularity_score"] += weight
                self.item_features[pid]["total_interactions"] += 1
                
            # --- Populate User Features ---
            if uid not in self.user_features:
                self.user_features[uid] = {
                    "total_weight": 0.0,
                    "category_interests": {},
                    "item_interactions": {}
                }
                
            u_feats = self.user_features[uid]
            u_feats["total_weight"] += weight
            u_feats["item_interactions"][pid] = u_feats["item_interactions"].get(pid, 0.0) + weight
            
            # Retrieve item category to update user category interests
            if pid in self.item_features:
                category = self.item_features[pid]["category"]
                u_feats["category_interests"][category] = u_feats["category_interests"].get(category, 0.0) + weight

    def get_user_features(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves user interaction aggregates in O(1) time.
        """
        return self.user_features.get(user_id, {
            "total_weight": 0.0,
            "category_interests": {},
            "item_interactions": {}
        })

    def get_item_features(self, item_id: str) -> Dict[str, Any]:
        """
        Retrieves item popularity aggregates in O(1) time.
        """
        return self.item_features.get(item_id, {
            "popularity_score": 0.0,
            "total_interactions": 0,
            "category": "Unknown"
        })

    def get_user_top_categories(self, user_id: str, top_n: int = 2) -> List[str]:
        """
        Identifies a user's favorite categories sorted by implicit weight.
        """
        u_feats = self.get_user_features(user_id)
        interests = u_feats.get("category_interests", {})
        sorted_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, _ in sorted_interests[:top_n]]

    def update_interaction(self, user_id: str, item_id: str, event_type: str) -> None:
        """
        Dynamically updates the feature store on new checkout or click actions.
        Enables real-time profile adjustments.
        Time Complexity: O(1)
        """
        weight = self.get_implicit_weight(event_type)

        # Update Item Features
        if item_id in self.item_features:
            self.item_features[item_id]["popularity_score"] += weight
            self.item_features[item_id]["total_interactions"] += 1

        # Update User Features
        if user_id not in self.user_features:
            self.user_features[user_id] = {
                "total_weight": 0.0,
                "category_interests": {},
                "item_interactions": {}
            }

        u_feats = self.user_features[user_id]
        u_feats["total_weight"] += weight
        u_feats["item_interactions"][item_id] = u_feats["item_interactions"].get(item_id, 0.0) + weight

        if item_id in self.item_features:
            category = self.item_features[item_id]["category"]
            u_feats["category_interests"][category] = u_feats["category_interests"].get(category, 0.0) + weight
