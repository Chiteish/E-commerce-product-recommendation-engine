# 📊 Data Contracts & Time-Based Dataset Splits

This document defines the schemas (data contracts) for raw events and item datasets, and outlines the time-based splitting strategy used to prepare training, validation, and testing subsets for recommendation modeling.

---

## 📋 Data Contracts (Schemas)

### 1. User Interaction Events Schema (`events.csv`)
This dataset records user clickstream interactions.
*   **`user_id`** (`VARCHAR` / `String`): Unique identifier for the customer.
*   **`item_id`** (`VARCHAR` / `String`): Unique identifier for the product.
*   **`event`** (`ENUM`): Interaction action. Must be one of:
    *   `view`: User viewed the product details page (implicit positive feedback).
    *   `cart`: User added the item to their shopping cart (medium-strength interest).
    *   `purchase`: User checked out and purchased the item (strong positive feedback).
*   **`ts`** (`TIMESTAMP`): Unix timestamp or UTC datetime indicating when the event occurred.

### 2. Product Catalog Schema (`items.csv`)
This dataset contains product metadata.
*   **`item_id`** (`VARCHAR` / `String`): Unique identifier matching `events.csv`.
*   **`title`** (`VARCHAR` / `String`): Display name of the product.
*   **`category`** (`VARCHAR` / `String`): Product classification index (e.g. `Electronics`).
*   **`brand`** (`VARCHAR` / `String`): Manufacturer brand name.
*   **`price`** (`DECIMAL` / `Float`): Cost of the item.
*   **`desc_text`** (`TEXT` / `String`): Long-form textual description (used for TF-IDF / vector embeddings).
*   **`tags`** (`VARCHAR` / `String`): Comma-separated list of search keywords.

---

## 🔄 Splitting Strategy: Time-Based Split

In recommendation systems, we **never** perform random splits (like K-Fold Cross-Validation) because it causes **data leakage** (future events leaking into past predictions). Instead, we use a **Chronological (Time-Based) Split**:

```text
  [================== TRAIN ==================] [==== VAL ====] [==== TEST ====]
  | <----------------- 80% -----------------> | <--- 10% ---> | <--- 10% ---> |
  Start                                      Cutoff D        Day D+3         Day D+6
```

1.  **Train Dataset**: Interactions up to timestamp $D$ (typically $80\%$ of historical logs). Used to build similarity vectors, graph connections, and fit ranking weights.
2.  **Validation Dataset**: Interactions from day $D$ to day $D+3$. Used to tune hyperparameters (e.g. learning rate, regularization, or blending weights).
3.  **Test Dataset**: Interactions from day $D+3$ to day $D+6$. Used as a holdout subset to evaluate final metrics (Recall@K, Precision@K, NDCG).

---

## 🐍 Data Splitting Validation Script

Below is the Python pipeline using `pandas` that validates schemas, processes timestamps, applies the $80/10/10$ quantile chronological split, and exports the outputs into optimized binary **Parquet** formats for fast model loading:

```python
import pandas as pd
import numpy as np

def validate_and_split_data(events_csv: str, items_csv: str):
    """
    Validates CSV schema contracts and performs chronological splitting.
    """
    # 1. Parse and load datasets
    ev = pd.read_csv(events_csv, parse_dates=["ts"])
    it = pd.read_csv(items_csv)

    # 2. Schema Assertions (Data Contracts enforcement)
    required_event_cols = {"user_id", "item_id", "event", "ts"}
    required_item_cols = {"item_id", "title", "category", "price", "tags"}
    
    assert required_event_cols.issubset(ev.columns), f"Missing event columns: {required_event_cols - set(ev.columns)}"
    assert required_item_cols.issubset(it.columns), f"Missing item columns: {required_item_cols - set(it.columns)}"
    
    # Enforce ENUM validation on event actions
    valid_events = {"view", "cart", "purchase"}
    assert set(ev["event"].unique()).issubset(valid_events), "Invalid event actions found in logs."

    # 3. Chronological splits
    # Sorting values chronologically
    ev = ev.sort_values("ts").reset_index(drop=True)
    
    # Calculate Cutoff point (e.g., 80% train quantile boundary)
    cutoff_train = ev["ts"].quantile(0.80)
    train = ev[ev["ts"] <= cutoff_train]
    
    # Remaining 20% split equally (50% validation, 50% test)
    remaining_events = ev[ev["ts"] > cutoff_train]
    cutoff_val = remaining_events["ts"].quantile(0.50)
    
    val = remaining_events[remaining_events["ts"] <= cutoff_val]
    test = remaining_events[remaining_events["ts"] > cutoff_val]

    # 4. Save to optimized Parquet format
    train.to_parquet("data/train.parquet", index=False)
    val.to_parquet("data/val.parquet", index=False)
    test.to_parquet("data/test.parquet", index=False)
    
    print(f"[SUCCESS] Dataset splits completed:")
    print(f"  - Train records:  {len(train)} (up to {cutoff_train})")
    print(f"  - Val records:    {len(val)} (up to {cutoff_val})")
    print(f"  - Test records:   {len(test)}")

if __name__ == "__main__":
    # Example execution paths
    # validate_and_split_data("data/events.csv", "data/items.csv")
    pass
```
