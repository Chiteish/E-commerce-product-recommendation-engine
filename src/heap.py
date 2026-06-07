class MaxHeap:
    """
    A custom hand-crafted Binary Max-Heap (Priority Queue) to rank recommendation scores.
    Stores tuples of (score, item) where elements are sorted by score.
    """
    def __init__(self):
        self.heap = []

    def push(self, item, score: float) -> None:
        """
        Inserts a new item with its score into the heap.
        Time Complexity: O(log N)
        """
        # Append to the end of the array
        self.heap.append((score, item))
        # Bubble up to maintain the max-heap property
        self._heapify_up(len(self.heap) - 1)

    def pop(self):
        """
        Extracts and returns the item with the highest score.
        Returns None if the heap is empty.
        Time Complexity: O(log N)
        """
        if not self.heap:
            return None

        # If there's only one element, pop and return it
        if len(self.heap) == 1:
            score, item = self.heap.pop()
            return item, score

        # Save the root (max element)
        max_score, max_item = self.heap[0]
        
        # Move the last element to the root
        last_score, last_item = self.heap.pop()
        self.heap[0] = (last_score, last_item)
        
        # Bubble down to restore the heap property
        self._heapify_down(0)
        
        return max_item, max_score

    def peek(self):
        """
        Returns the highest score item without removing it.
        Time Complexity: O(1)
        """
        if not self.heap:
            return None
        return self.heap[0][1], self.heap[0][0]

    def size(self) -> int:
        return len(self.heap)

    def is_empty(self) -> bool:
        return len(self.heap) == 0

    def _heapify_up(self, index: int) -> None:
        """
        Moves the element at the given index up until it satisfies the max-heap property.
        """
        parent_idx = (index - 1) // 2
        
        # If we are not at root and current value is greater than parent value, swap
        if index > 0 and self.heap[index][0] > self.heap[parent_idx][0]:
            self.heap[index], self.heap[parent_idx] = self.heap[parent_idx], self.heap[index]
            self._heapify_up(parent_idx)

    def _heapify_down(self, index: int) -> None:
        """
        Moves the element at the given index down until it satisfies the max-heap property.
        """
        largest = index
        left_idx = 2 * index + 1
        right_idx = 2 * index + 2
        heap_len = len(self.heap)

        # Check if left child exists and is greater than root
        if left_idx < heap_len and self.heap[left_idx][0] > self.heap[largest][0]:
            largest = left_idx

        # Check if right child exists and is greater than current largest
        if right_idx < heap_len and self.heap[right_idx][0] > self.heap[largest][0]:
            largest = right_idx

        # If the largest is not the root, swap and continue heapifying down
        if largest != index:
            self.heap[index], self.heap[largest] = self.heap[largest], self.heap[index]
            self._heapify_down(largest)

    def build_heap(self, items_with_scores: list) -> None:
        """
        Builds a Max-Heap from an arbitrary list of tuples (score, item) in-place.
        Time Complexity: O(N) where N is the number of elements.
        """
        self.heap = [(score, item) for score, item in items_with_scores]
        # Start from the last non-leaf node and heapify down to the root
        last_non_leaf = (len(self.heap) - 2) // 2
        for i in range(last_non_leaf, -1, -1):
            self._heapify_down(i)
