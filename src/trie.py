class TrieNode:
    """
    A single node in the prefix tree (Trie).
    """
    def __init__(self):
        # Maps character (str) -> TrieNode
        self.children = {}
        # Flag indicating if this node represents the end of a valid search term
        self.is_end_of_word = False
        # Optional: store complete term to avoid walking back up to reconstruct it
        self.associated_term = None


class Trie:
    """
    Trie (Prefix Tree) for efficient prefix matching and search autocomplete.
    """
    def __init__(self):
        self.root = TrieNode()

    def insert(self, term: str) -> None:
        """
        Inserts a search term into the Trie.
        Time Complexity: O(L) where L is the length of the term.
        Space Complexity: O(L) in the worst-case (all new nodes).
        """
        term = term.strip().lower()
        if not term:
            return

        current = self.root
        for char in term:
            if char not in current.children:
                current.children[char] = TrieNode()
            current = current.children[char]
        
        current.is_end_of_word = True
        current.associated_term = term

    def search(self, term: str) -> bool:
        """
        Searches for an exact term in the Trie.
        Time Complexity: O(L) where L is the length of the term.
        """
        term = term.strip().lower()
        current = self._traverse_to_node(term)
        return current is not None and current.is_end_of_word

    def get_autocomplete_suggestions(self, prefix: str) -> list:
        """
        Retrieves all search terms starting with the given prefix.
        Time Complexity: O(L + S)
          - O(L) to traverse to the prefix node (L = length of prefix).
          - O(S) to perform DFS search to collect all terms (S = size of matching subtree).
        """
        prefix = prefix.strip().lower()
        suggestions = []
        if not prefix:
            return suggestions

        # Step 1: Navigate to the end of the prefix prefix path
        prefix_node = self._traverse_to_node(prefix)
        if not prefix_node:
            return suggestions  # No terms share this prefix

        # Step 2: DFS from the prefix node to gather all complete terms
        self._dfs_collect_terms(prefix_node, suggestions)
        return suggestions

    def _traverse_to_node(self, text: str) -> TrieNode:
        """
        Helper method to walk the trie characters and return the node of the final character.
        Returns None if the path breaks.
        """
        current = self.root
        for char in text:
            if char not in current.children:
                return None
            current = current.children[char]
        return current

    def _dfs_collect_terms(self, node: TrieNode, suggestions: list) -> None:
        """
        Helper method performing Depth-First Search to collect all matching words.
        """
        if node.is_end_of_word and node.associated_term:
            suggestions.append(node.associated_term)

        # Recursively visit children in alphabetical order (sorting dictionary keys)
        for char in sorted(node.children.keys()):
            self._dfs_collect_terms(node.children[char], suggestions)
