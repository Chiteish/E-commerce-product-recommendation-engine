class Product:
    """
    Represents an E-Commerce Product and its metadata.
    """
    def __init__(self, product_id: str, name: str, category: str, price: float, tags: list, rating: float):
        self.id = product_id
        self.name = name
        self.category = category
        self.price = price
        # Convert tags to a Python set for O(1) membership lookups and fast set operations (Jaccard similarity)
        self.tags = set(tag.lower() for tag in tags)
        self.rating = rating

    @classmethod
    def from_dict(cls, data: dict):
        """
        Factory method to create a Product object from a dictionary.
        """
        return cls(
            product_id=data["id"],
            name=data["name"],
            category=data["category"],
            price=float(data["price"]),
            tags=data["tags"],
            rating=float(data["rating"])
        )

    def to_dict(self) -> dict:
        """
        Serializes the Product object back to a standard dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "tags": list(self.tags),
            "rating": self.rating
        }

    def __repr__(self):
        return f"Product(ID={self.id}, Name='{self.name}', Category='{self.category}', Price=${self.price:.2f}, Rating={self.rating})"


class User:
    """
    Represents an E-Commerce User profile, shopping cart, and transaction histories.
    """
    def __init__(self, user_id: str, name: str, search_history: list, cart: list, purchase_history: list):
        self.id = user_id
        self.name = name
        # Store histories in standard lists to maintain chronological order
        self.search_history = [search.lower() for search in search_history]
        self.cart = set(cart)  # Set representation for fast O(1) checks
        self.purchase_history = set(purchase_history)  # Set representation for fast checks

    @classmethod
    def from_dict(cls, data: dict):
        """
        Factory method to create a User object from a dictionary.
        """
        return cls(
            user_id=data["id"],
            name=data["name"],
            search_history=data.get("search_history", []),
            cart=data.get("cart", []),
            purchase_history=data.get("purchase_history", [])
        )

    def to_dict(self) -> dict:
        """
        Serializes the User object back to a standard dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "search_history": self.search_history,
            "cart": list(self.cart),
            "purchase_history": list(self.purchase_history)
        }

    def __repr__(self):
        return f"User(ID={self.id}, Name='{self.name}', CartItems={len(self.cart)}, Purchased={len(self.purchase_history)})"
