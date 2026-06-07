import os
import sys
from src.recommender import RecommenderEngine

# Try importing PrettyTable for clean terminal formatting. 
# Fall back to custom ASCII formatting if not installed yet.
try:
    from prettytable import PrettyTable
    HAS_PRETTYTABLE = True
except ImportError:
    HAS_PRETTYTABLE = False

def print_table(headers, rows):
    """
    Utility function to print tables. Uses PrettyTable if available,
    otherwise prints using formatted clean text rows.
    """
    if HAS_PRETTYTABLE:
        table = PrettyTable(headers)
        for row in rows:
            table.add_row(row)
        print(table)
    else:
        # Custom ASCII table formatting fallback
        widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(str(val)))
        
        # Format strings
        row_format = " | ".join([f"{{:<{w}}}" for w in widths])
        separator = "-+-".join(["-" * w for w in widths])
        
        print(separator)
        print(row_format.format(*headers))
        print(separator)
        for row in rows:
            print(row_format.format(*[str(val) for val in row]))
        print(separator)

def generate_report(engine: RecommenderEngine, user_id: str, recs: list) -> str:
    """
    Generates a formal recommendation report and saves it to the outputs directory.
    """
    user = engine.user_map[user_id]
    os.makedirs("outputs", exist_ok=True)
    report_path = os.path.join("outputs", f"report_{user_id}.txt")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=========================================================\n")
        f.write("       E-COMMERCE RECOMMENDATION ENGINE REPORT           \n")
        f.write("=========================================================\n")
        f.write(f"User ID:            {user.id}\n")
        f.write(f"Customer Name:      {user.name}\n")
        f.write(f"Current Cart:       {list(user.cart)}\n")
        f.write(f"Purchase History:   {list(user.purchase_history)}\n")
        f.write(f"Search Log:         {user.search_history}\n")
        f.write("---------------------------------------------------------\n")
        f.write("               TOP SUGGESTIONS FOR YOU                   \n")
        f.write("---------------------------------------------------------\n")
        f.write(f"{'Rank':<5} | {'ProdID':<8} | {'Product Name':<40} | {'Score':<6} | {'Price':<8}\n")
        f.write("-" * 75 + "\n")
        
        for idx, (prod, score) in enumerate(recs, 1):
            f.write(f"{idx:<5} | {prod.id:<8} | {prod.name[:40]:<40} | {score:.3f} | ${prod.price:.2f}\n")
            
        f.write("=========================================================\n")
        f.write(f"Report compiled successfully. Saved to: {report_path}\n")
        
    return report_path

def main():
    # Initialize engine and load files
    engine = RecommenderEngine()
    
    # Resolve relative paths for data files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    products_path = os.path.join(base_dir, "data", "products.json")
    users_path = os.path.join(base_dir, "data", "users.json")
    
    try:
        engine.load_data_from_json(products_path, users_path)
    except FileNotFoundError:
        print(f"Error: Required datasets not found.\nMake sure data/products.json and data/users.json exist under {base_dir}")
        sys.exit(1)

    # Default active user
    active_user_id = "U001"
    
    print("\n" + "=" * 60)
    print("      Welcome to the E-Commerce Recommendation Engine     ")
    print("      Custom DSA Implementation (Trie, Graph, Max-Heap)  ")
    print("=" * 60)

    while True:
        user = engine.user_map[active_user_id]
        print(f"\n[ACTIVE] Active Customer: \033[92m{user.name} ({user.id})\033[0m")
        print("1. View Full Product Catalog")
        print("2. Search Bar Autocomplete (Trie Simulation)")
        print("3. View Product Details & Content-Based Similar Items")
        print("4. Get Personalized Recommendations (Hybrid Engine)")
        print("5. View Current Shopping Cart")
        print("6. Add Product to Cart")
        print("7. Purchase Items in Cart")
        print("8. Switch Active Customer")
        print("9. Generate & Export Recommendations Report")
        print("10. Exit")
        
        try:
            choice = input("\nSelect an option (1-10): ").strip()
            if not choice:
                continue
                
            if choice == "1":
                # Print Product Catalog
                print("\n--- PRODUCT CATALOG ---")
                headers = ["ID", "Product Name", "Category", "Price", "Rating", "Key Tags"]
                rows = []
                for pid, prod in engine.product_map.items():
                    rows.append([prod.id, prod.name, prod.category, f"${prod.price:.2f}", prod.rating, ", ".join(list(prod.tags)[:3])])
                print_table(headers, rows)
                
            elif choice == "2":
                # Trie Autocomplete search simulation
                prefix = input("\nType a search keyword (e.g. 'la', 'sho', 'game', 'co'): ").strip()
                suggestions = engine.search_trie.get_autocomplete_suggestions(prefix)
                print(f"\n[TRIE] [Trie Prefix Search] Prefix: '{prefix}'")
                if suggestions:
                    print("Suggestions found in tree path:")
                    for idx, sug in enumerate(suggestions, 1):
                        print(f"  {idx}. {sug}")
                else:
                    print("[INFO] No matching autocomplete patterns found in Trie nodes.")
                    
            elif choice == "3":
                # Product details & Similar Items
                pid = input("\nEnter Product ID (e.g., P101, P201, P301): ").strip().upper()
                if pid in engine.product_map:
                    prod = engine.product_map[pid]
                    print(f"\n[CARD] [Product Card]")
                    print(f"  Name:     {prod.name}")
                    print(f"  Category: {prod.category}")
                    print(f"  Price:    ${prod.price:.2f}")
                    print(f"  Rating:   {prod.rating}/5.0")
                    print(f"  Tags:     {', '.join(prod.tags)}")
                    
                    # Run similarity check
                    print(f"\n[HEAP] [Heap Ranking] Top 3 Similar Products (Content-Based):")
                    sim_recs = engine.get_similar_products(pid, top_n=3)
                    
                    headers = ["ID", "Similar Product", "Similarity Match Score", "Price"]
                    rows = []
                    for item, score in sim_recs:
                        rows.append([item.id, item.name, f"{score:.3%}", f"${item.price:.2f}"])
                    print_table(headers, rows)
                else:
                    print("[ERROR] Invalid Product ID.")
                    
            elif choice == "4":
                # Personalized hybrid recommendations
                print(f"\n[HEAP] Calculating Hybrid Score (40% Content Similarity + 40% Graph Co-Purchases + 20% Ratings)...")
                recs = engine.get_personalized_recommendations(active_user_id, top_n=4)
                
                print(f"\n[SUGGESTIONS] Top Personalized Recommendations for {user.name}:")
                if recs:
                    headers = ["Rank", "ID", "Product Name", "Category", "Match Strength", "Price"]
                    rows = []
                    for idx, (prod, score) in enumerate(recs, 1):
                        rows.append([idx, prod.id, prod.name, prod.category, f"{score:.1%}", f"${prod.price:.2f}"])
                    print_table(headers, rows)
                else:
                    print("No recommendations found. Try buying some products first to build the user profile!")

            elif choice == "5":
                # View Cart
                print(f"\n[CART] Shopping Cart for {user.name}:")
                if user.cart:
                    headers = ["ID", "Product Name", "Price"]
                    rows = []
                    total = 0.0
                    for pid in user.cart:
                        if pid in engine.product_map:
                            prod = engine.product_map[pid]
                            rows.append([prod.id, prod.name, f"${prod.price:.2f}"])
                            total += prod.price
                    print_table(headers, rows)
                    print(f"Total Cart Value: \033[93m${total:.2f}\033[0m")
                else:
                    print("Your cart is empty.")

            elif choice == "6":
                # Add to cart
                pid = input("\nEnter Product ID to add to cart: ").strip().upper()
                if pid in engine.product_map:
                    if pid in user.purchase_history:
                        print("[WARNING] You have already purchased this item. Adding to cart anyway...")
                    if engine.add_to_cart(active_user_id, pid):
                        print(f"[OK] Added '{engine.product_map[pid].name}' to your cart.")
                    else:
                        print("[ERROR] Failed to add to cart.")
                else:
                    print("[ERROR] Invalid Product ID.")

            elif choice == "7":
                # Checkout/Purchase items in cart
                if not user.cart:
                    print("\n[CART] Your cart is empty. Nothing to checkout.")
                    continue
                
                print(f"\n[CHECKOUT] Checking out {len(user.cart)} items...")
                cart_items = list(user.cart)
                for pid in cart_items:
                    engine.add_purchase(active_user_id, pid)
                    print(f"  - Successfully purchased '{engine.product_map[pid].name}'!")
                
                print("\n[OK] Purchases complete! User-Product interaction graph updated dynamically.")
                
            elif choice == "8":
                # Switch active customer
                print("\nAvailable Customers:")
                for uid, cust in engine.user_map.items():
                    print(f"  [{uid}] {cust.name}")
                new_uid = input("\nEnter User ID to switch to: ").strip().upper()
                if new_uid in engine.user_map:
                    active_user_id = new_uid
                    print(f"[OK] Switched to customer: {engine.user_map[new_uid].name}")
                else:
                    print("[ERROR] Invalid User ID.")
                    
            elif choice == "9":
                # Export Report
                recs = engine.get_personalized_recommendations(active_user_id, top_n=5)
                if recs:
                    report_path = generate_report(engine, active_user_id, recs)
                    print(f"\n[REPORT] Recommendation report generated and saved successfully!")
                    print(f"  Location: \033[96m{report_path}\033[0m")
                else:
                    print("[ERROR] Cannot generate report: no recommendations available for this user.")

            elif choice == "10":
                print("\nThank you for using the E-Commerce Recommendation Engine! Goodbye.")
                break
            else:
                print("[ERROR] Invalid choice. Please enter a number between 1 and 10.")
                
        except KeyboardInterrupt:
            print("\nExiting engine. Goodbye!")
            break
        except Exception as e:
            print(f"[WARNING] An error occurred: {e}")

if __name__ == "__main__":
    main()

