# 📐 Production Modular Recommender System (RecSys) Architecture

This document details the architecture and operational metrics of a production-grade, modular E-Commerce Recommender System. This modular design decouples candidate generation from ranking, enabling independent model deployment and sub-millisecond query evaluation.

---

## 🗺️ Architectural Pipeline

A production recommendation engine operates as a multi-stage pipeline:

```text
  [Ingestion / Event Stream] ---> [Feature Store (Redis/Feast)]
                                             |
                                             v
  [User Context / Request]  ---> [Candidate Generation (FAISS/Graph)] ---> (Retrieved: ~100-500 items)
                                             |
                                             v
                                  [LightGBM/XGBoost Ranker]         ---> (Scored: ~100-500 items)
                                             |
                                             v
                                  [Post-Processing & Knobs]         ---> (Filtered & Diversified: ~10-20 items)
                                             |
                                             v
                                  [FastAPI Serving Layer]           ---> [React / CLI Frontend]
```

### 1. Ingestion Layer
*   **Purpose**: Capture real-time clickstream events (`user_id`, `item_id`, `event_type` [click, cart, purchase], `timestamp`) and stream them into storage.
*   **Technologies**: Apache Kafka, AWS Kinesis, RabbitMQ.

### 2. Feature Store
*   **Purpose**: Dual-database structure to handle training (offline) and low-latency prediction (online). Stores user embeddings, category purchase frequency, dynamic click-through-rates (CTR), and product statistics.
*   **Technologies**: Feast, Redis (online cache), PostgreSQL/Parquet (offline training lake).

### 3. Candidate Generation (Retrieval / Filtering)
*   **Purpose**: Filter down millions of catalog items to 100–500 candidate products in sub-10 milliseconds.
*   **Techniques**: 
    *   **Approximate Nearest Neighbors (ANN)**: Dot-product vector lookup on user/item embeddings using **FAISS** or HNSW indices.
    *   **Heuristic Filters**: Retrieving category-popular items or collaborative bipartite graph links.

### 4. Ranking (Scoring)
*   **Purpose**: Apply a high-precision machine learning model to score the ~500 retrieved candidates.
*   **Model Types**: Pointwise Learning-to-Rank models using **LightGBM**, XGBoost, or deep learning models (e.g. Deep & Cross Networks).
*   **Features**: User demographics, item historical CTR, matching category flags, and real-time session vectors.

### 5. Post-Processing & Filtering
*   **Purpose**: Cleanse recommendations before presenting them to the client.
*   **Operations**:
    *   **Business Exclusions**: Filter out already purchased items, out-of-stock items, or items with high return rates.
    *   **Diversity Constraints**: Ensure the top-10 items aren't all from the same category using Maximal Marginal Relevance (MMR) algorithms.
    *   **Exploration Knobs**: Inject random/novel items using **$\epsilon$-greedy** exploration or **Thompson Sampling** to prevent "echo chambers" and gather feedback on fresh catalog arrivals.

### 6. Serving Layer (API & UI)
*   **Purpose**: Expose the pipeline through secure Rest API endpoints to client interfaces.
*   **Technologies**: FastAPI (Python), React.js (Frontend UI).

---

## 📊 Evaluation & Validation Metrics

To measure the effectiveness of a recommendation engine, we evaluate metrics across two environments:

### A. Offline Metrics (Model Quality)
Computed on historical test datasets before deployment:
*   **Recall@K**: Measures the proportion of relevant items successfully retrieved in the top-K recommendations:
    $$\text{Recall@K} = \frac{|\text{Relevant Items} \cap \text{Top-K Recommendations}|}{|\text{Relevant Items}|}$$
*   **Precision@K**: The fraction of recommendations that are actually relevant:
    $$\text{Precision@K} = \frac{|\text{Relevant Items} \cap \text{Top-K Recommendations}|}{K}$$
*   **MAP (Mean Average Precision)**: Evaluates precision across multiple query ranks, penalizing incorrect top suggestions.
*   **NDCG (Normalized Discounted Cumulative Gain)**: Measures ranking quality, heavily rewarding placing the most relevant items at the top slots.

### B. Online Business Metrics (Financial & Conversion Quality)
Measured through A/B testing on live users:
*   **CTR (Click-Through Rate)**: The ratio of users who clicked on a recommendation to total recommendation impressions.
*   **ATC (Add-to-Cart) Rate**: The percentage of sessions where a recommended item was added to the cart.
*   **Conversion Rate (CR)**: Percentage of impressions resulting in checkout purchases.
*   **Average Order Value (AOV)**: The monetary impact, demonstrating success in cross-selling.

---

## ⚙️ Online Knobs: Exploration vs. Exploitation

To keep recommendations fresh and discover new user interests, we balance:
1.  **Exploitation**: Showing products we are highly confident the user will buy (based on past history).
2.  **Exploration**: Showing novel or under-evaluated products to gather interest data.

### 1. $\epsilon$-Greedy Strategy
With probability $1-\epsilon$, the system recommends the highest scoring products (Exploit). With probability $\epsilon$ (typically $5\%-10\%$), the system selects products at random or from a pool of new catalog items (Explore).

### 2. Thompson Sampling (Bayesian approach)
Models click probabilities as Beta Distributions. The system draws random samples from each item's distribution and sorts them. Highly active, well-known items have narrow distributions, whereas new items have wide distributions, allowing new items to occasionally achieve high scores and get surfaced.
