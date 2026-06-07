import os
import sys
import pandas as pd
import numpy as np
from src.feature_store import FeatureStore
from src.dataset_generator import DatasetGenerator

# Try importing LightGBM. Print installation advice if missing.
try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False


def train_lgb_ranker(
    train_events_path: str,
    val_events_path: str,
    items_csv_path: str,
    model_output_path: str = "outputs/lightgbm_ranker.txt"
) -> bool:
    """
    Trains a LightGBM LambdaMART ranker optimizing NDCG@5/10
    and saves the model checkpoint.
    """
    if not HAS_LIGHTGBM:
        print("[ERROR] LightGBM is not installed. Please run: pip install lightgbm")
        return False

    print("\n--- Training LightGBM LambdaMART Ranker ---")
    
    # 1. Load Parquets and Catalog
    train_ev = pd.read_parquet(train_events_path)
    val_ev = pd.read_parquet(val_events_path)
    items_df = pd.read_csv(items_csv_path)

    # 2. Fit Feature Store on Train split
    fs = FeatureStore()
    fs.fit(train_ev, items_df)

    # 3. Generate Labeled Datasets with Negative Sampling
    dg = DatasetGenerator(fs)
    print("  Generating training pairs...")
    train_df = dg.generate_training_data(train_ev, items_df, negative_ratio=3.0)
    print("  Generating validation pairs...")
    val_df = dg.generate_training_data(val_ev, items_df, negative_ratio=3.0)

    if train_df.empty or val_df.empty:
        print("[ERROR] Failed to generate training or validation data splits. Dataset empty.")
        return False

    # 4. LightGBM Ranker requires data sorted by the query group key (user_id)
    train_df = train_df.sort_values("user_id").reset_index(drop=True)
    val_df = val_df.sort_values("user_id").reset_index(drop=True)

    # Calculate group sizes (query sizes per user)
    train_groups = train_df.groupby("user_id").size().values
    val_groups = val_df.groupby("user_id").size().values

    # Define training features
    features = [
        "user_total_weight",
        "item_popularity_score",
        "item_total_interactions",
        "user_category_interest_weight",
        "user_item_past_interaction_weight"
    ]

    X_train = train_df[features]
    y_train = train_df["label"]

    X_val = val_df[features]
    y_val = val_df["label"]

    print(f"  Train set size: {X_train.shape[0]} rows | Groups: {len(train_groups)}")
    print(f"  Val set size:   {X_val.shape[0]} rows | Groups: {len(val_groups)}")

    # 5. Initialize and Fit LambdaMART Ranker
    # lambdarank objective optimizes NDCG (Normalized Discounted Cumulative Gain)
    ranker = lgb.LGBMRanker(
        objective="lambdarank",
        metric="ndcg",
        ndcg_eval_at=[5, 10],
        learning_rate=0.05,
        n_estimators=100,
        random_state=42
    )

    print("  Fitting LightGBM Ranker (optimizing NDCG@5/10)...")
    ranker.fit(
        X_train,
        y_train,
        group=train_groups,
        eval_set=[(X_val, y_val)],
        eval_group=[val_groups],
        callbacks=[lgb.early_stopping(stopping_rounds=10), lgb.log_evaluation(period=10)]
    )

    # 6. Save Model
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    ranker.booster_.save_model(model_output_path)
    print(f"[SUCCESS] LightGBM LambdaMART ranker saved to: {model_output_path}")
    
    # Print feature importances
    print("\nFeature Importances:")
    importances = ranker.feature_importances_
    for name, imp in sorted(zip(features, importances), key=lambda x: x[1], reverse=True):
        print(f"  - {name:<35}: {imp}")
        
    return True


if __name__ == "__main__":
    # Resolve absolute paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    train_path = os.path.join(base_dir, "data", "train.parquet")
    val_path = os.path.join(base_dir, "data", "val.parquet")
    items_path = os.path.join(base_dir, "data", "items.csv")
    
    # Check if parquet splits exist. If not, generate them.
    if not os.path.exists(train_path) or not os.path.exists(val_path):
        print("[INFO] Parquet files not found. Running data_prep script...")
        sys.path.append(base_dir)
        try:
            from src.data_prep import build_csv_and_parquet_datasets
            build_csv_and_parquet_datasets()
        except Exception as e:
            print(f"[ERROR] Could not generate Parquet splits: {e}")
            sys.exit(1)

    train_lgb_ranker(train_path, val_path, items_path)
