import json
from src.models import Product, User
from src.trie import Trie
from src.graph import Graph
from src.heap import MaxHeap

class RecommenderEngine:
    """
    Orchestrates the E-Commerce Product Recommendation logic,
    integrating Trie, Graph, Heap, and HashMap structures.
    """
    def __init__(self):
        # Hash Map indices for O(1) lookups
        self.product_map = {}          # product_id -> Product
        self.user_map = {}             # user_id -> User
        self.category_index = {}       # category_name -> list of Product IDs
        
        # Trie for prefix autocomplete
        self.search_trie = Trie()
        
        # Graph for User-Product purchases (Collaborative Filtering)
        self.purchase_graph = Graph()

    def load_data_from_json(self, products_filepath: str, users_filepath: str) -> None:
        """
        Loads products and users from JSON files and initializes all indices.
        """
        # Load Products
        with open(products_filepath, 'r') as pf:
            products_data = json.load(pf)
            for item in products_data:
                product = Product.from_dict(item)
                
                # 1. Store in product Hash Map index
                self.product_map[product.id] = product
                
                # 2. Store in category Hash Map index
                if product.category not in self.category_index:
                    self.category_index[product.category] = []
                self.category_index[product.category].append(product.id)
                
                # 3. Insert product name into search Trie for autocomplete
                self.search_trie.insert(product.name)
                # Insert product category as well to allow category-based autocomplete
                self.search_trie.insert(product.category)

        # Load Users
        with open(users_filepath, 'r') as uf:
            users_data = json.load(uf)
            for item in users_data:
                user = User.from_dict(item)
                
                # 1. Store in user Hash Map index
                self.user_map[user.id] = user
                
                # 2. Map purchase interactions onto the purchase Graph
                for prod_id in user.purchase_history:
                    self.purchase_graph.add_edge(user.id, prod_id)

    # ==========================================
    # CORE ALGORITHMIC SCORING METRICS
    # ==========================================
    
    @staticmethod
    def calculate_jaccard_similarity(prod_a: Product, prod_b: Product) -> float:
        """
        Calculates Jaccard Similarity between two products based on their feature tags.
        Formula: (Tags_A Intersection Tags_B) / (Tags_A Union Tags_B)
        Time Complexity: O(T_A + T_B) where T is the number of tags.
        """
        intersection = prod_a.tags.intersection(prod_b.tags)
        union = prod_a.tags.union(prod_b.tags)
        
        if not union:
            return 0.0
            
        return len(intersection) / len(union)

    # ==========================================
    # RECOMMENDATION GENERATION PIPELINES
    # ==========================================

    def get_similar_products(self, target_product_id: str, top_n: int = 3) -> list:
        """
        Content-Based Recommendation: Finds products similar to the target product.
        Uses Max-Heap to extract the top-N items efficiently without sorting the entire catalog.
        
        Time Complexity: O(C * log K) where C is the number of items and K is top_n.
        """
        similarities = []
        target_prod = self.product_map.get(target_product_id)
        if not target_prod:
            return []

        # Calculate similarity with all other products
        for prod_id, product in self.product_map.items():
            if prod_id == target_product_id:
                continue  # Skip comparing with itself
                
            score = self.calculate_jaccard_similarity(target_prod, product)
            # Inject product rating to break ties and favor highly-rated items
            weighted_score = score * 0.7 + (product.rating / 5.0) * 0.3
            similarities.append((weighted_score, prod_id))

        # Use our custom Max-Heap to extract top_n recommendations
        heap = MaxHeap()
        heap.build_heap(similarities)
        
        results = []
        # Pop top-N items (or less if the heap is smaller than top_n)
        for _ in range(min(top_n, heap.size())):
            prod_id, score = heap.pop()
            results.append((self.product_map[prod_id], score))
            
        return results

    def get_category_recommendations(self, category_name: str, top_n: int = 3) -> list:
        """
        Category-Based Recommendation: Returns top-rated products in a given category.
        Uses a Heap to extract the highest rated products in O(C log K) time.
        """
        product_ids = self.category_index.get(category_name, [])
        if not product_ids:
            return []

        candidates = []
        for pid in product_ids:
            prod = self.product_map[pid]
            # Use rating as priority score
            candidates.append((prod.rating, pid))

        # Heapify candidates
        heap = MaxHeap()
        heap.build_heap(candidates)

        results = []
        for _ in range(min(top_n, heap.size())):
            pid, rating = heap.pop()
            results.append((self.product_map[pid], rating))
        return results

    def get_personalized_recommendations(self, user_id: str, top_n: int = 5) -> list:
        """
        Hybrid Recommendation Engine (Collaborative Filtering + Content-Based):
        Generates personalized product suggestions for a specific user.
        
        Pipeline:
        1. Fetch User profile and purchase/cart history.
        2. Extract co-purchased candidates using our 2-Hop Purchase Graph (Collaborative Filtering).
        3. Extract Category Preferences based on user purchase history (Content-Based).
        4. Calculate Jaccard similarity of all remaining products against the User's overall tag vector (User Profile).
        5. Combine Collaborative and Content scores.
        6. Filter out items already purchased or in the active cart.
        7. Use Max-Heap to extract the top-N matches.
        """
        user = self.user_map.get(user_id)
        if not user:
            return []

        # Set of items to exclude (items the user already owns or has in cart)
        excluded_items = user.purchase_history.union(user.cart)

        # Step A: Collaborative Filtering Candidate Scores
        # Get co-purchase frequencies from the Graph
        co_purchase_counts = {}
        for purchased_pid in user.purchase_history:
            freq_map = self.purchase_graph.get_co_purchased_products(purchased_pid)
            for pid, count in freq_map.items():
                if pid not in excluded_items:
                    co_purchase_counts[pid] = co_purchase_counts.get(pid, 0) + count

        # Normalize collaborative counts into a score between 0.0 and 1.0
        max_collab_count = max(co_purchase_counts.values()) if co_purchase_counts else 1
        collab_scores = {pid: count / max_collab_count for pid, count in co_purchase_counts.items()}

        # Step B: Content-Based User Profile Creation
        # Combine all tags of items the user has purchased or carted to represent user preference profile
        user_preference_tags = set()
        user_interacted_items = user.purchase_history.union(user.cart)
        for pid in user_interacted_items:
            if pid in self.product_map:
                user_preference_tags.update(self.product_map[pid].tags)

        # If user has no interactions, build profile tags using their query search history
        if not user_preference_tags:
            for query in user.search_history:
                user_preference_tags.update(query.split())

        # Step C: Score All Candidates in Catalog
        hybrid_scores = []
        for pid, product in self.product_map.items():
            if pid in excluded_items:
                continue

            # 1. Content score: Jaccard similarity between product tags and User Preference tags
            prod_intersection = product.tags.intersection(user_preference_tags)
            prod_union = product.tags.union(user_preference_tags)
            content_score = len(prod_intersection) / len(prod_union) if prod_union else 0.0

            # 2. Collaborative score
            collab_score = collab_scores.get(pid, 0.0)

            # 3. Rating weight
            rating_weight = product.rating / 5.0

            # Combined Score Formula:
            # 40% Content Similarity + 40% Collaborative purchases + 20% Product rating
            combined_score = (content_score * 0.4) + (collab_score * 0.4) + (rating_weight * 0.2)
            hybrid_scores.append((combined_score, pid))

        # Step D: Extract Top N using Max-Heap
        heap = MaxHeap()
        heap.build_heap(hybrid_scores)

        results = []
        for _ in range(min(top_n, heap.size())):
            pid, score = heap.pop()
            results.append((self.product_map[pid], score))
            
        return results

    def add_purchase(self, user_id: str, product_id: str) -> bool:
        """
        Logs a new purchase by a user, updates indices, and updates the purchase Graph.
        """
        user = self.user_map.get(user_id)
        product = self.product_map.get(product_id)
        
        if not user or not product:
            return False

        # Add to user record
        user.purchase_history.add(product_id)
        # Remove from cart if it was there
        user.cart.discard(product_id)
        # Add bidirectional edge to the Interaction Graph
        self.purchase_graph.add_edge(user_id, product_id)
        return True

    def add_to_cart(self, user_id: str, product_id: str) -> bool:
        """
        Adds a product to the user's shopping cart.
        """
        user = self.user_map.get(user_id)
        product = self.product_map.get(product_id)
        
        if not user or not product:
            return False

        user.cart.add(product_id)
        return True
