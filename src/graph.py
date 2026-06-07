class Graph:
    """
    An Adjacency List representing User-Product bipartite interactions.
    Nodes can represent either users (e.g. 'U001') or products (e.g. 'P101').
    """
    def __init__(self):
        # Maps node_id (str) -> Set of neighbor_node_ids
        self.adjacency_list = {}
        # Keep track of node categories/types ('user' or 'product')
        self.node_types = {}

    def add_node(self, node_id: str, node_type: str) -> None:
        """
        Adds a node to the graph if it doesn't already exist.
        node_type should be either 'user' or 'product'.
        """
        if node_id not in self.adjacency_list:
            self.adjacency_list[node_id] = set()
            self.node_types[node_id] = node_type

    def add_edge(self, user_id: str, product_id: str) -> None:
        """
        Creates an undirected edge between a user node and a product node,
        representing an interaction (like a purchase or a review rating).
        """
        # Ensure nodes exist
        self.add_node(user_id, "user")
        self.add_node(product_id, "product")

        # Create bidirectional links
        self.adjacency_list[user_id].add(product_id)
        self.adjacency_list[product_id].add(user_id)

    def get_neighbors(self, node_id: str) -> set:
        """
        Returns all nodes adjacent to the given node.
        If the node doesn't exist, returns an empty set.
        Time Complexity: O(1)
        """
        return self.adjacency_list.get(node_id, set())

    def get_purchased_products(self, user_id: str) -> set:
        """
        Retrieves all products purchased by a specific user node.
        """
        if user_id in self.node_types and self.node_types[user_id] == "user":
            return self.get_neighbors(user_id)
        return set()

    def get_co_purchased_products(self, product_id: str) -> dict:
        """
        Collaborative Filtering (2-Hop Traversal on Bipartite Graph):
        Finds other products purchased by users who also bought the target product.
        
        Step 1: Start at target Product node.
        Step 2: Traverse to all User nodes who bought this product (1-hop).
        Step 3: Traverse to all other Product nodes bought by these users (2-hop).
        Step 4: Accumulate count frequencies.
        
        Returns a dictionary: {other_product_id: frequency_count} sorted by frequency.
        Time Complexity: O(U * P_u) where U is users who bought product_id,
        and P_u is number of items bought by user u.
        """
        co_purchased_freq = {}
        if product_id not in self.node_types or self.node_types[product_id] != "product":
            return co_purchased_freq

        # Step 1: Find all users who bought this product
        buyer_users = self.get_neighbors(product_id)

        for user_id in buyer_users:
            # Step 2: Find all other products bought by this user
            other_products = self.get_neighbors(user_id)
            for other_prod_id in other_products:
                if other_prod_id != product_id:
                    # Increment frequency
                    co_purchased_freq[other_prod_id] = co_purchased_freq.get(other_prod_id, 0) + 1

        return co_purchased_freq
