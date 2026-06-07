import os
import sys
from src.recommender import RecommenderEngine

try:
    from prettytable import PrettyTable
    HAS_PRETTYTABLE = True
except ImportError:
    HAS_PRETTYTABLE = False

def print_and_write(f, text):
    """Prints to console and writes to file simultaneously."""
    print(text)
    f.write(text + "\n")

def print_table_to_file(f, headers, rows):
    """Prints a table to console and writes to file."""
    if HAS_PRETTYTABLE:
        table = PrettyTable(headers)
        for row in rows:
            table.add_row(row)
        table_str = str(table)
        print(table_str)
        f.write(table_str + "\n")
    else:
        widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(str(val)))
        
        row_format = " | ".join([f"{{:<{w}}}" for w in widths])
        separator = "-+-".join(["-" * w for w in widths])
        
        print_and_write(f, separator)
        print_and_write(f, row_format.format(*headers))
        print_and_write(f, separator)
        for row in rows:
            print_and_write(f, row_format.format(*[str(val) for val in row]))
        print_and_write(f, separator)

def main():
    engine = RecommenderEngine()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    products_path = os.path.join(base_dir, "data", "products.json")
    users_path = os.path.join(base_dir, "data", "users.json")
    
    try:
        engine.load_data_from_json(products_path, users_path)
    except FileNotFoundError:
        print(f"Error: Datasets not found at {products_path}")
        sys.exit(1)
        
    os.makedirs(os.path.join(base_dir, "outputs"), exist_ok=True)
    report_path = os.path.join(base_dir, "outputs", "similarity_scores.txt")
    
    with open(report_path, "w", encoding="utf-8") as f:
        print_and_write(f, "=====================================================================")
        print_and_write(f, "               E-COMMERCE RECO-ENGINE SIMILARITY REPORT              ")
        print_and_write(f, "        Content-Based Jaccard Index & Custom Max-Heap Scores        ")
        print_and_write(f, "=====================================================================\n")
        
        # Part 1: Pairwise Jaccard Similarity Matrix of Electronics
        print_and_write(f, "--- PART 1: JACCARD TAG SIMILARITY (INTERSECTION / UNION) ---")
        print_and_write(f, "Shows how overlapping feature tags compute similarity index:\n")
        
        electronics_ids = ["P101", "P102", "P103", "P104", "P105"]
        headers = ["Product A", "Product B", "Intersection Tags", "Union Tags", "Jaccard Score"]
        rows = []
        
        for i in range(len(electronics_ids)):
            for j in range(i + 1, len(electronics_ids)):
                prod_a = engine.product_map[electronics_ids[i]]
                prod_b = engine.product_map[electronics_ids[j]]
                
                intersection = prod_a.tags.intersection(prod_b.tags)
                union = prod_a.tags.union(prod_b.tags)
                score = len(intersection) / len(union) if union else 0.0
                
                rows.append([
                    f"{prod_a.name[:25]} ({prod_a.id})",
                    f"{prod_b.name[:25]} ({prod_b.id})",
                    f"{{{', '.join(intersection)}}}" if intersection else "{}",
                    f"{{{', '.join(union)}}}",
                    f"{score:.1%}"
                ])
                
        print_table_to_file(f, headers, rows)
        print_and_write(f, "\n")
        
        # Part 2: Top 3 Similar Products via Custom Max-Heap
        print_and_write(f, "--- PART 2: MAX-HEAP CONTENT-BASED RECOMMENDATIONS (TOP 3 SIMILAR) ---")
        print_and_write(f, "Calculated using: Score = 70% Jaccard Similarity + 30% Normalized Rating\n")
        
        target_ids = ["P101", "P102", "P201", "P301", "P401"]
        for target_id in target_ids:
            if target_id in engine.product_map:
                target_prod = engine.product_map[target_id]
                print_and_write(f, f"Target Product: {target_prod.name} ({target_prod.id})")
                print_and_write(f, f"Target Tags: {{{', '.join(target_prod.tags)}}}")
                print_and_write(f, "Top 3 Content-Similar Products:")
                
                sim_recs = engine.get_similar_products(target_id, top_n=3)
                
                sub_headers = ["Rank", "Similar Product ID", "Product Name", "Category", "Weighted Score"]
                sub_rows = []
                for rank, (prod, score) in enumerate(sim_recs, 1):
                    sub_rows.append([
                        rank,
                        prod.id,
                        prod.name,
                        prod.category,
                        f"{score:.4f}"
                    ])
                print_table_to_file(f, sub_headers, sub_rows)
                print_and_write(f, "-" * 69 + "\n")
                
        print_and_write(f, "=====================================================================")
        print_and_write(f, f"Similarity report successfully exported to: {report_path}")
        print_and_write(f, "=====================================================================")

if __name__ == "__main__":
    main()
