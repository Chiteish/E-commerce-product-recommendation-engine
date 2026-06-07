/* ==========================================================================
   MOCK DATABASES (MIRRORING THE PYTHON FILES)
   ========================================================================== */
const INITIAL_PRODUCTS = [
    { id: "P101", name: "Wireless Noise-Canceling Headphones", category: "Electronics", price: 199.99, tags: ["wireless", "audio", "noise-canceling", "bluetooth", "premium"], rating: 4.7 },
    { id: "P102", name: "Mechanical Gaming Keyboard", category: "Electronics", price: 89.99, tags: ["gaming", "keyboard", "rgb", "wired", "mechanical"], rating: 4.5 },
    { id: "P103", name: "Ergonomic Wireless Mouse", category: "Electronics", price: 49.99, tags: ["wireless", "mouse", "ergonomic", "bluetooth", "office"], rating: 4.3 },
    { id: "P104", name: "Ultra-Wide Gaming Monitor 34-inch", category: "Electronics", price: 449.99, tags: ["gaming", "monitor", "ultrawide", "display", "4k"], rating: 4.8 },
    { id: "P105", name: "USB-C Portable Power Bank", category: "Electronics", price: 29.99, tags: ["portable", "power", "usb-c", "charger", "travel"], rating: 4.4 },
    { id: "P201", name: "Slim-Fit Denim Jeans", category: "Fashion", price: 59.99, tags: ["denim", "jeans", "slim-fit", "casual", "apparel"], rating: 4.1 },
    { id: "P202", name: "Water-Resistant Windbreaker Jacket", category: "Fashion", price: 79.99, tags: ["jacket", "water-resistant", "windbreaker", "outerwear", "travel"], rating: 4.6 },
    { id: "P203", name: "Classic White Leather Sneakers", category: "Fashion", price: 69.99, tags: ["sneakers", "leather", "casual", "footwear", "white"], rating: 4.2 },
    { id: "P204", name: "Runners Athletic Sports Shoes", category: "Fashion", price: 89.99, tags: ["shoes", "running", "athletic", "footwear", "breathable"], rating: 4.5 },
    { id: "P205", name: "Stainless Steel Minimalist Watch", category: "Fashion", price: 129.99, tags: ["watch", "minimalist", "accessory", "steel", "analog"], rating: 4.4 },
    { id: "P301", name: "Data Structures & Algorithms Made Easy", category: "Books", price: 34.99, tags: ["dsa", "programming", "education", "textbook", "algorithms"], rating: 4.9 },
    { id: "P302", name: "The Pragmatic Programmer", category: "Books", price: 39.99, tags: ["programming", "career", "best-seller", "software", "development"], rating: 4.9 },
    { id: "P303", name: "Introduction to Artificial Intelligence", category: "Books", price: 49.99, tags: ["ai", "machine-learning", "textbook", "python", "education"], rating: 4.6 },
    { id: "P304", name: "Atomic Habits", category: "Books", price: 16.99, tags: ["self-help", "best-seller", "habits", "productivity", "psychology"], rating: 4.8 },
    { id: "P401", name: "Programmable Espresso Machine", category: "Home & Kitchen", price: 249.99, tags: ["espresso", "coffee", "machine", "kitchen", "premium"], rating: 4.7 },
    { id: "P402", name: "High-Speed Countertop Blender", category: "Home & Kitchen", price: 99.99, tags: ["blender", "smoothie", "juicer", "kitchen", "appliance"], rating: 4.3 },
    { id: "P403", name: "Electric Gooseneck Kettle", category: "Home & Kitchen", price: 54.99, tags: ["kettle", "electric", "tea", "coffee", "kitchen"], rating: 4.5 }
];

const INITIAL_USERS = [
    { id: "U001", name: "Alice Smith", search_history: ["headphones", "earbuds", "noise canceling"], cart: ["P103"], purchase_history: ["P101", "P105"] },
    { id: "U002", name: "Bob Johnson", search_history: ["gaming keyboard", "gaming monitor", "mouse"], cart: ["P102"], purchase_history: ["P104"] },
    { id: "U003", name: "Charlie Brown", search_history: ["programming books", "dsa", "python book"], cart: ["P302"], purchase_history: ["P301", "P303"] },
    { id: "U004", name: "Diana Prince", search_history: ["jacket", "sports shoes", "casual sneakers"], cart: [], purchase_history: ["P202", "P204"] },
    { id: "U005", name: "Ethan Hunt", search_history: ["coffee maker", "espresso machine", "electric kettle"], cart: ["P403"], purchase_history: ["P401", "P105"] },
    { id: "U006", name: "Fiona Gallagher", search_history: ["minimalist watch", "denim jeans", "sneakers"], cart: ["P203"], purchase_history: ["P201", "P205"] }
];

/* ==========================================================================
   DSA PORT: TRIE (PREFIX TREE)
   ========================================================================== */
class TrieNode {
    constructor() {
        this.children = {}; // char -> TrieNode
        this.isEndOfWord = false;
        this.associatedTerm = null;
    }
}

class Trie {
    constructor() {
        this.root = new TrieNode();
    }

    insert(term) {
        term = term.trim().toLowerCase();
        if (!term) return;

        let current = this.root;
        for (let i = 0; i < term.length; i++) {
            let char = term[i];
            if (!current.children[char]) {
                current.children[char] = new TrieNode();
            }
            current = current.children[char];
        }
        current.isEndOfWord = true;
        current.associatedTerm = term;
    }

    getAutocompleteSuggestions(prefix) {
        prefix = prefix.trim().toLowerCase();
        let suggestions = [];
        if (!prefix) return suggestions;

        let current = this.root;
        for (let i = 0; i < prefix.length; i++) {
            let char = prefix[i];
            if (!current.children[char]) {
                return suggestions;
            }
            current = current.children[char];
        }

        this._dfsCollect(current, suggestions);
        return suggestions;
    }

    _dfsCollect(node, suggestions) {
        if (node.isEndOfWord && node.associatedTerm) {
            suggestions.push(node.associatedTerm);
        }
        let sortedKeys = Object.keys(node.children).sort();
        for (let char of sortedKeys) {
            this._dfsCollect(node.children[char], suggestions);
        }
    }
}

/* ==========================================================================
   DSA PORT: GRAPH (ADJACENCY LIST)
   ========================================================================== */
class Graph {
    constructor() {
        this.adjacencyList = {};
        this.nodeTypes = {}; // id -> 'user' | 'product'
    }

    addNode(nodeId, nodeType) {
        if (!this.adjacencyList[nodeId]) {
            this.adjacencyList[nodeId] = new Set();
            this.nodeTypes[nodeId] = nodeType;
        }
    }

    addEdge(userId, productId) {
        this.addNode(userId, "user");
        this.addNode(productId, "product");
        this.adjacencyList[userId].add(productId);
        this.adjacencyList[productId].add(userId);
    }

    getNeighbors(nodeId) {
        return this.adjacencyList[nodeId] || new Set();
    }

    getCoPurchasedProducts(productId) {
        let coPurchasedFreq = {};
        if (this.nodeTypes[productId] !== "product") return coPurchasedFreq;

        let buyerUsers = this.getNeighbors(productId);
        for (let userId of buyerUsers) {
            let otherProducts = this.getNeighbors(userId);
            for (let otherPid of otherProducts) {
                if (otherPid !== productId) {
                    coPurchasedFreq[otherPid] = (coPurchasedFreq[otherPid] || 0) + 1;
                }
            }
        }
        return coPurchasedFreq;
    }
}

/* ==========================================================================
   DSA PORT: CUSTOM MAX-HEAP
   ========================================================================== */
class MaxHeap {
    constructor() {
        this.heap = []; // Array of {score, item}
    }

    push(item, score) {
        this.heap.push({ score, item });
        this._heapifyUp(this.heap.length - 1);
    }

    pop() {
        if (this.heap.length === 0) return null;
        if (this.heap.length === 1) return this.heap.pop();

        let max = this.heap[0];
        this.heap[0] = this.heap.pop();
        this._heapifyDown(0);
        return max;
    }

    size() {
        return this.heap.length;
    }

    _heapifyUp(index) {
        let parentIdx = Math.floor((index - 1) / 2);
        if (index > 0 && this.heap[index].score > this.heap[parentIdx].score) {
            let temp = this.heap[index];
            this.heap[index] = this.heap[parentIdx];
            this.heap[parentIdx] = temp;
            this._heapifyUp(parentIdx);
        }
    }

    _heapifyDown(index) {
        let largest = index;
        let leftIdx = 2 * index + 1;
        let rightIdx = 2 * index + 2;
        let len = this.heap.length;

        if (leftIdx < len && this.heap[leftIdx].score > this.heap[largest].score) {
            largest = leftIdx;
        }
        if (rightIdx < len && this.heap[rightIdx].score > this.heap[largest].score) {
            largest = rightIdx;
        }

        if (largest !== index) {
            let temp = this.heap[index];
            this.heap[index] = this.heap[largest];
            this.heap[largest] = temp;
            this._heapifyDown(largest);
        }
    }

    buildHeap(itemsWithScores) {
        this.heap = itemsWithScores.map(x => ({ score: x.score, item: x.item }));
        let lastNonLeaf = Math.floor((this.heap.length - 2) / 2);
        for (let i = lastNonLeaf; i >= 0; i--) {
            this._heapifyDown(i);
        }
    }
}

/* ==========================================================================
   RECOMENDER SYSTEM ORCHESTRATOR
   ========================================================================== */
class RecommenderEngine {
    constructor() {
        this.productMap = {};
        this.userMap = {};
        this.categoryIndex = {};
        this.searchTrie = new Trie();
        this.purchaseGraph = new Graph();
    }

    initialize(products, users) {
        this.productMap = {};
        this.userMap = {};
        this.categoryIndex = {};
        this.searchTrie = new Trie();
        this.purchaseGraph = new Graph();

        // Load Products
        products.forEach(p => {
            let prod = {
                id: p.id,
                name: p.name,
                category: p.category,
                price: p.price,
                tags: new Set(p.tags.map(t => t.toLowerCase())),
                rating: p.rating
            };
            this.productMap[prod.id] = prod;

            if (!this.categoryIndex[prod.category]) {
                this.categoryIndex[prod.category] = [];
            }
            this.categoryIndex[prod.category].push(prod.id);

            this.searchTrie.insert(prod.name);
            this.searchTrie.insert(prod.category);
        });

        // Load Users
        users.forEach(u => {
            let user = {
                id: u.id,
                name: u.name,
                search_history: u.search_history.map(s => s.toLowerCase()),
                cart: new Set(u.cart),
                purchase_history: new Set(u.purchase_history)
            };
            this.userMap[user.id] = user;

            user.purchase_history.forEach(pid => {
                this.purchaseGraph.addEdge(user.id, pid);
            });
        });
    }

    calculateJaccardSimilarity(prodA, prodB) {
        let setA = prodA.tags;
        let setB = prodB.tags;
        let intersection = new Set([...setA].filter(x => setB.has(x)));
        let union = new Set([...setA, ...setB]);
        return union.size === 0 ? 0.0 : intersection.size / union.size;
    }

    getSimilarProducts(targetProductId, topN = 3) {
        let targetProd = this.productMap[targetProductId];
        if (!targetProd) return [];

        let candidates = [];
        for (let pid in this.productMap) {
            if (pid === targetProductId) continue;
            let prod = this.productMap[pid];
            let sim = this.calculateJaccardSimilarity(targetProd, prod);
            let score = sim * 0.7 + (prod.rating / 5.0) * 0.3;
            candidates.push({ score, item: pid });
        }

        let heap = new MaxHeap();
        heap.buildHeap(candidates);

        let results = [];
        let limit = Math.min(topN, heap.size());
        for (let i = 0; i < limit; i++) {
            let popped = heap.pop();
            results.push({ product: this.productMap[popped.item], score: popped.score });
        }
        return results;
    }

    getPersonalizedRecommendations(userId, topN = 5, onLoggedStep = null) {
        let user = this.userMap[userId];
        if (!user) return [];

        let excluded = new Set([...user.purchase_history, ...user.cart]);
        if (onLoggedStep) onLoggedStep(`Checking interaction exclusions: ${Array.from(excluded).join(", ") || 'None'}`);

        // A. Graph-Based Collaborative Filtering candidates
        let coPurchases = {};
        user.purchase_history.forEach(pid => {
            let matches = this.purchaseGraph.getCoPurchasedProducts(pid);
            for (let matchPid in matches) {
                if (!excluded.has(matchPid)) {
                    coPurchases[matchPid] = (coPurchases[matchPid] || 0) + matches[matchPid];
                }
            }
        });

        let maxCoCount = Math.max(...Object.values(coPurchases), 0) || 1;
        let collabScores = {};
        for (let pid in coPurchases) {
            collabScores[pid] = coPurchases[pid] / maxCoCount;
        }

        if (onLoggedStep) {
            onLoggedStep(`2-Hop Graph Collaborative Candidates extracted: ${Object.keys(collabScores).length} products found`);
        }

        // B. Content-Based Preferences Profile Vector
        let userPreferenceTags = new Set();
        let userInteracted = new Set([...user.purchase_history, ...user.cart]);
        userInteracted.forEach(pid => {
            let p = this.productMap[pid];
            if (p) p.tags.forEach(t => userPreferenceTags.add(t));
        });

        if (userPreferenceTags.size === 0) {
            user.search_history.forEach(q => {
                q.split(/\s+/).forEach(t => {
                    if (t.length > 2) userPreferenceTags.add(t);
                });
            });
        }

        if (onLoggedStep) {
            onLoggedStep(`User Preference profile vector tags: { ${Array.from(userPreferenceTags).join(", ")} }`);
        }

        // C. Calculate final hybrid scores
        let candidates = [];
        for (let pid in this.productMap) {
            if (excluded.has(pid)) continue;

            let product = this.productMap[pid];

            // Jaccard tags similarity
            let intersection = new Set([...product.tags].filter(x => userPreferenceTags.has(x)));
            let union = new Set([...product.tags, ...userPreferenceTags]);
            let contentScore = union.size === 0 ? 0.0 : intersection.size / union.size;

            let collabScore = collabScores[pid] || 0.0;
            let ratingScore = product.rating / 5.0;

            // Hybrid score formula
            let score = (contentScore * 0.4) + (collabScore * 0.4) + (ratingScore * 0.2);

            candidates.push({ score, item: pid });
        }

        if (onLoggedStep) {
            onLoggedStep(`Scored ${candidates.length} candidate products. Feeding into Max-Heap...`);
        }

        // D. Extract using MaxHeap
        let heap = new MaxHeap();
        heap.buildHeap(candidates);

        let results = [];
        let limit = Math.min(topN, heap.size());
        for (let i = 0; i < limit; i++) {
            let popped = heap.pop();
            results.push({ product: this.productMap[popped.item], score: popped.score });
        }

        if (onLoggedStep) {
            onLoggedStep(`Heap Popped top ${results.length} recommendations successfully.`);
        }

        return { recs: results, heapArray: heap.heap };
    }

    addPurchase(userId, productId) {
        let user = this.userMap[userId];
        if (!user || !this.productMap[productId]) return false;

        user.purchase_history.add(productId);
        user.cart.delete(productId);
        this.purchaseGraph.addEdge(userId, productId);
        return true;
    }

    addToCart(userId, productId) {
        let user = this.userMap[userId];
        if (!user || !this.productMap[productId]) return false;

        user.cart.add(productId);
        return true;
    }
}

/* ==========================================================================
   APPLICATION AND UI CONTROLLER
   ========================================================================== */
const engine = new RecommenderEngine();
let activeUserId = "U001";
let activeTab = "graph"; // "graph" | "heap"
let heapVisualizerData = []; // Array of {score, item} currently in the heap

// DOM Elements
const userSelect = document.getElementById("userSelect");
const searchInput = document.getElementById("searchInput");
const autocompleteDropdown = document.getElementById("autocompleteDropdown");
const simProductA = document.getElementById("simProductA");
const simProductB = document.getElementById("simProductB");
const btnCalcSimilarity = document.getElementById("btnCalcSimilarity");
const similarityResult = document.getElementById("similarityResult");
const jaccardScore = document.getElementById("jaccardScore");
const setIntersection = document.getElementById("setIntersection");
const setUnion = document.getElementById("setUnion");
const cartDisplayList = document.getElementById("cartDisplayList");
const cartTotalVal = document.getElementById("cartTotalVal");
const btnCheckout = document.getElementById("btnCheckout");
const btnGetRecs = document.getElementById("btnGetRecs");
const recsOutputList = document.getElementById("recsOutputList");
const terminalConsole = document.getElementById("terminalConsole");
const btnReset = document.getElementById("btnReset");

const tabGraph = document.getElementById("tabGraph");
const tabHeap = document.getElementById("tabHeap");
const graphContainer = document.getElementById("graphContainer");
const heapContainer = document.getElementById("heapContainer");

const graphCanvas = document.getElementById("graphCanvas");
const heapCanvas = document.getElementById("heapCanvas");

// Logger Utility
function logToConsole(message, type = "system") {
    const line = document.createElement("div");
    line.className = `terminal-line ${type}-line`;
    const now = new Date().toLocaleTimeString();
    line.textContent = `[${now}] ${message}`;
    terminalConsole.appendChild(line);
    terminalConsole.scrollTop = terminalConsole.scrollHeight;
}

/* ==========================================================================
   FORCE-DIRECTED NETWORK GRAPH SIMULATOR
   ========================================================================== */
let nodes = [];
let links = [];
let dragNode = null;
let graphAnimationId = null;

function initNetworkGraph() {
    nodes = [];
    links = [];

    // Add User Nodes
    for (let uid in engine.userMap) {
        let u = engine.userMap[uid];
        nodes.push({
            id: uid,
            name: u.name,
            type: "user",
            x: Math.random() * 400 + 100,
            y: Math.random() * 300 + 100,
            vx: 0,
            vy: 0,
            radius: 12
        });
    }

    // Add Product Nodes
    for (let pid in engine.productMap) {
        let p = engine.productMap[pid];
        nodes.push({
            id: pid,
            name: p.name,
            type: "product",
            x: Math.random() * 400 + 100,
            y: Math.random() * 300 + 100,
            vx: 0,
            vy: 0,
            radius: 8
        });
    }

    // Add Links based on Purchases (Undirected Graph edges)
    for (let uid in engine.userMap) {
        let u = engine.userMap[uid];
        u.purchase_history.forEach(pid => {
            links.push({ source: uid, target: pid });
        });
    }

    // Start force-directed loop
    if (graphAnimationId) cancelAnimationFrame(graphAnimationId);
    runNetworkSimulation();
}

function runNetworkSimulation() {
    updateGraphPhysics();
    drawGraph();
    graphAnimationId = requestAnimationFrame(runNetworkSimulation);
}

function updateGraphPhysics() {
    const kRepulsion = 120;  // Force pushing nodes apart
    const kAttraction = 0.05; // Force pulling linked nodes together
    const gravity = 0.03;    // Pull nodes to center
    const damping = 0.85;     // Slow down node velocity over time
    const center = { x: graphCanvas.width / 2, y: graphCanvas.height / 2 };

    // 1. Repulsion force between all node pairs
    for (let i = 0; i < nodes.length; i++) {
        let nodeA = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
            let nodeB = nodes[j];
            let dx = nodeB.x - nodeA.x;
            let dy = nodeB.y - nodeA.y;
            let dist = Math.sqrt(dx * dx + dy * dy) || 1;
            
            if (dist < 220) {
                let force = (kRepulsion * kRepulsion) / dist;
                let fx = (dx / dist) * force * 0.08;
                let fy = (dy / dist) * force * 0.08;

                if (!nodeA.fixed) {
                    nodeA.vx -= fx;
                    nodeA.vy -= fy;
                }
                if (!nodeB.fixed) {
                    nodeB.vx += fx;
                    nodeB.vy += fy;
                }
            }
        }
    }

    // 2. Attraction force along links
    links.forEach(link => {
        let nodeA = nodes.find(n => n.id === link.source);
        let nodeB = nodes.find(n => n.id === link.target);
        if (!nodeA || !nodeB) return;

        let dx = nodeB.x - nodeA.x;
        let dy = nodeB.y - nodeA.y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;
        
        let force = dist * kAttraction;
        let fx = (dx / dist) * force;
        let fy = (dy / dist) * force;

        if (!nodeA.fixed) {
            nodeA.vx += fx;
            nodeA.vy += fy;
        }
        if (!nodeB.fixed) {
            nodeB.vx -= fx;
            nodeB.vy -= fy;
        }
    });

    // 3. Gravity pulling to center and updating node coordinates
    nodes.forEach(node => {
        if (node.fixed) return;

        let dx = center.x - node.x;
        let dy = center.y - node.y;
        node.vx += dx * gravity;
        node.vy += dy * gravity;

        node.vx *= damping;
        node.vy *= damping;

        node.x += node.vx;
        node.y += node.vy;

        // Boundaries
        node.x = Math.max(node.radius, Math.min(graphCanvas.width - node.radius, node.x));
        node.y = Math.max(node.radius, Math.min(graphCanvas.height - node.radius, node.y));
    });
}

function drawGraph() {
    const ctx = graphCanvas.getContext("2d");
    ctx.clearRect(0, 0, graphCanvas.width, graphCanvas.height);

    // Draw Links
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1.2;
    links.forEach(link => {
        let nodeA = nodes.find(n => n.id === link.source);
        let nodeB = nodes.find(n => n.id === link.target);
        if (!nodeA || !nodeB) return;

        ctx.beginPath();
        ctx.moveTo(nodeA.x, nodeA.y);
        ctx.lineTo(nodeB.x, nodeB.y);
        ctx.stroke();
    });

    // Draw Nodes
    nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
        
        // Coloring logic
        let isUser = node.type === "user";
        let isActiveUser = node.id === activeUserId;
        
        if (isActiveUser) {
            ctx.fillStyle = "#ec4899"; // Hot pink for active user
            ctx.shadowColor = "rgba(236, 72, 153, 0.5)";
            ctx.shadowBlur = 12;
        } else if (isUser) {
            ctx.fillStyle = "#3b82f6"; // Blue for other users
            ctx.shadowColor = "rgba(59, 130, 246, 0.3)";
            ctx.shadowBlur = 6;
        } else {
            ctx.fillStyle = "#10b981"; // Green for products
            ctx.shadowBlur = 0;
        }

        ctx.fill();
        ctx.shadowBlur = 0; // reset shadow

        // Add node border
        ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Node labels for users or hovered nodes
        if (isUser || node.hovered) {
            ctx.fillStyle = "rgba(255, 255, 255, 0.85)";
            ctx.font = "500 10px Inter";
            ctx.textAlign = "center";
            ctx.fillText(node.name, node.x, node.y - node.radius - 6);
        }
    });
}

// Mouse dragging setup
function setupCanvasInteractions() {
    function resizeCanvas() {
        const p = graphCanvas.parentElement;
        graphCanvas.width = p.clientWidth;
        graphCanvas.height = p.clientHeight;
        heapCanvas.width = p.clientWidth;
        heapCanvas.height = p.clientHeight;
        drawGraph();
    }
    window.addEventListener("resize", resizeCanvas);
    setTimeout(resizeCanvas, 100);

    // Mouse events on Graph Canvas
    graphCanvas.addEventListener("mousedown", e => {
        let rect = graphCanvas.getBoundingClientRect();
        let mouseX = e.clientX - rect.left;
        let mouseY = e.clientY - rect.top;

        dragNode = null;
        for (let node of nodes) {
            let dx = mouseX - node.x;
            let dy = mouseY - node.y;
            let dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < node.radius + 5) {
                dragNode = node;
                node.fixed = true;
                break;
            }
        }
    });

    graphCanvas.addEventListener("mousemove", e => {
        let rect = graphCanvas.getBoundingClientRect();
        let mouseX = e.clientX - rect.left;
        let mouseY = e.clientY - rect.top;

        // Hover labels
        nodes.forEach(node => node.hovered = false);
        let hovered = nodes.find(n => {
            let dx = mouseX - n.x;
            let dy = mouseY - n.y;
            return Math.sqrt(dx*dx + dy*dy) < n.radius + 5;
        });
        if (hovered) hovered.hovered = true;

        if (dragNode) {
            dragNode.x = mouseX;
            dragNode.y = mouseY;
        }
    });

    graphCanvas.addEventListener("mouseup", () => {
        if (dragNode) {
            dragNode.fixed = false;
            dragNode = null;
        }
    });

    graphCanvas.addEventListener("mouseleave", () => {
        if (dragNode) {
            dragNode.fixed = false;
            dragNode = null;
        }
    });

    // Double-click product to select it and trigger recommendations
    graphCanvas.addEventListener("dblclick", e => {
        let rect = graphCanvas.getBoundingClientRect();
        let mouseX = e.clientX - rect.left;
        let mouseY = e.clientY - rect.top;

        let node = nodes.find(n => {
            let dx = mouseX - n.x;
            let dy = mouseY - n.y;
            return Math.sqrt(dx*dx + dy*dy) < n.radius + 5;
        });

        if (node && node.type === "product") {
            logToConsole(`Double-clicked product node: [${node.id}] ${node.name}. Searching details...`, "alg");
            // Set similar item values
            simProductA.value = node.id;
            btnCalcSimilarity.click();
            
            // Populate Trie search bar
            searchInput.value = node.name;
            searchInput.dispatchEvent(new Event("input"));
        } else if (node && node.type === "user") {
            logToConsole(`Switched user node context to: ${node.name}`, "system");
            userSelect.value = node.id;
            userSelect.dispatchEvent(new Event("change"));
        }
    });
}

/* ==========================================================================
   BINARY MAX-HEAP RENDERER
   ========================================================================== */
function drawHeapTree() {
    const ctx = heapCanvas.getContext("2d");
    ctx.clearRect(0, 0, heapCanvas.width, heapCanvas.height);

    if (heapVisualizerData.length === 0) {
        ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
        ctx.font = "14px Inter";
        ctx.textAlign = "center";
        ctx.fillText("Heap is empty. Compute Recommendations to populate the heap tree.", heapCanvas.width / 2, heapCanvas.height / 2);
        return;
    }

    const nodeRadius = 18;
    const startY = 50;
    const levelHeight = 65;

    // Helper function to draw connections and nodes recursively
    function drawNode(index, x, y, widthX) {
        let leftIdx = 2 * index + 1;
        let rightIdx = 2 * index + 2;
        let heapElement = heapVisualizerData[index];
        let scorePercent = (heapElement.score * 100).toFixed(1) + "%";

        // Draw line to left child
        if (leftIdx < heapVisualizerData.length) {
            let childX = x - widthX / 2;
            let childY = y + levelHeight;
            ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(childX, childY);
            ctx.stroke();
            drawNode(leftIdx, childX, childY, widthX / 2);
        }

        // Draw line to right child
        if (rightIdx < heapVisualizerData.length) {
            let childX = x + widthX / 2;
            let childY = y + levelHeight;
            ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(childX, childY);
            ctx.stroke();
            drawNode(rightIdx, childX, childY, widthX / 2);
        }

        // Draw the circular node
        ctx.beginPath();
        ctx.arc(x, y, nodeRadius, 0, 2 * Math.PI);
        
        if (index === 0) {
            ctx.fillStyle = "#ec4899"; // Root (highest priority score) gets Accent Pink
            ctx.shadowColor = "rgba(236, 72, 153, 0.5)";
            ctx.shadowBlur = 10;
        } else {
            ctx.fillStyle = "#0f172a";
            ctx.shadowBlur = 0;
        }
        ctx.fill();
        ctx.shadowBlur = 0; // reset shadow

        ctx.strokeStyle = index === 0 ? "rgba(255, 255, 255, 0.8)" : "rgba(59, 130, 246, 0.6)";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Print item labels
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 9px Fira Code";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(heapElement.item, x, y);

        // Print score metadata above/below node
        ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
        ctx.font = "500 9px Inter";
        ctx.fillText(scorePercent, x, y + nodeRadius + 10);
    }

    // Start drawing from root
    drawNode(0, heapCanvas.width / 2, startY, heapCanvas.width / 2.5);
}

/* ==========================================================================
   UI DATA-BINDINGS & EVENT REGISTRATIONS
   ========================================================================== */
function initDropdowns() {
    // 1. Switch User Dropdown
    userSelect.innerHTML = "";
    for (let uid in engine.userMap) {
        let u = engine.userMap[uid];
        let opt = document.createElement("option");
        opt.value = uid;
        opt.textContent = `${u.name} (${uid})`;
        userSelect.appendChild(opt);
    }
    userSelect.value = activeUserId;

    // 2. Similarity Dropdowns
    simProductA.innerHTML = "";
    simProductB.innerHTML = "";
    for (let pid in engine.productMap) {
        let p = engine.productMap[pid];
        let opt1 = document.createElement("option");
        opt1.value = pid;
        opt1.textContent = `${pid} - ${p.name}`;
        let opt2 = opt1.cloneNode(true);
        simProductA.appendChild(opt1);
        simProductB.appendChild(opt2);
    }
    
    // Choose distinct defaults
    simProductA.selectedIndex = 0;
    simProductB.selectedIndex = 1;
}

function updateCartView() {
    let user = engine.userMap[activeUserId];
    cartDisplayList.innerHTML = "";

    if (!user || user.cart.size === 0) {
        cartDisplayList.innerHTML = `<p class="empty-text">Cart is empty.</p>`;
        cartTotalVal.textContent = "$0.00";
        return;
    }

    let total = 0.0;
    user.cart.forEach(pid => {
        let p = engine.productMap[pid];
        if (p) {
            let itemDiv = document.createElement("div");
            itemDiv.className = "cart-item";
            itemDiv.innerHTML = `
                <span class="cart-item-name" title="${p.name}">${p.name}</span>
                <span class="cart-item-price">$${p.price.toFixed(2)}</span>
            `;
            cartDisplayList.appendChild(itemDiv);
            total += p.price;
        }
    });

    cartTotalVal.textContent = `$${total.toFixed(2)}`;
}

// Bind switch active customer actions
userSelect.addEventListener("change", () => {
    activeUserId = userSelect.value;
    logToConsole(`Context shifted to Customer: ${engine.userMap[activeUserId].name}`, "system");
    updateCartView();
    initNetworkGraph();
    
    // Clear old recommendations lists
    recsOutputList.innerHTML = `<p class="info-text">Click the Compute Recommendations button above to recalculate.</p>`;
});

// Autocomplete inputs
searchInput.addEventListener("input", () => {
    let prefix = searchInput.value;
    let suggestions = engine.searchTrie.getAutocompleteSuggestions(prefix);

    if (suggestions.length === 0 || !prefix) {
        autocompleteDropdown.classList.add("hidden");
        return;
    }

    autocompleteDropdown.innerHTML = "";
    suggestions.slice(0, 5).forEach(sug => {
        let div = document.createElement("div");
        div.className = "autocomplete-item";
        div.textContent = sug;
        div.addEventListener("click", () => {
            searchInput.value = sug;
            autocompleteDropdown.classList.add("hidden");
            
            // Execute details lookup based on match
            handleSearchTermSelected(sug);
        });
        autocompleteDropdown.appendChild(div);
    });
    autocompleteDropdown.classList.remove("hidden");
});

// Close autocomplete dropdown when clicking outside
document.addEventListener("click", e => {
    if (!e.target.closest(".search-input-group")) {
        autocompleteDropdown.classList.add("hidden");
    }
});

function handleSearchTermSelected(term) {
    logToConsole(`Trie query match: searched autocomplete term: "${term}"`, "alg");
    
    // Check if the term matches a product name exactly
    let matchedProd = null;
    for (let pid in engine.productMap) {
        if (engine.productMap[pid].name.toLowerCase() === term.toLowerCase()) {
            matchedProd = engine.productMap[pid];
            break;
        }
    }

    if (matchedProd) {
        logToConsole(`Exact product identified: [${matchedProd.id}] ${matchedProd.name}`, "success");
        simProductA.value = matchedProd.id;
        btnCalcSimilarity.click();
        
        // Push this query to search history logs
        let activeUser = engine.userMap[activeUserId];
        activeUser.search_history.unshift(term);
    } else {
        // Search category match check
        let isCat = Object.keys(engine.categoryIndex).find(c => c.toLowerCase() === term.toLowerCase());
        if (isCat) {
            logToConsole(`Matches catalog category: "${isCat}". Loading index products...`, "success");
        } else {
            logToConsole(`Autocomplete term: "${term}" mapped.`, "system");
        }
    }
}

// Calculate tag similarities
btnCalcSimilarity.addEventListener("click", () => {
    let pidA = simProductA.value;
    let pidB = simProductB.value;
    let prodA = engine.productMap[pidA];
    let prodB = engine.productMap[pidB];

    if (!prodA || !prodB) return;

    let score = engine.calculateJaccardSimilarity(prodA, prodB);
    jaccardScore.textContent = (score * 100).toFixed(1) + "%";

    // Set intersections detailings
    let intersection = [...prodA.tags].filter(x => prodB.tags.has(x));
    let union = [...new Set([...prodA.tags, ...prodB.tags])];

    setIntersection.textContent = intersection.length > 0 ? `{ ${intersection.join(", ")} }` : "{ empty }";
    setUnion.textContent = `{ ${union.join(", ")} }`;
    
    similarityResult.classList.remove("hidden");
    logToConsole(`Calculated Jaccard similarity between [${pidA}] and [${pidB}] = ${score.toFixed(4)}`, "alg");
});

// Checkout Cart
btnCheckout.addEventListener("click", () => {
    let user = engine.userMap[activeUserId];
    if (!user || user.cart.size === 0) return;

    logToConsole(`Beginning checkout process for ${user.name}...`, "system");
    let cartPids = Array.from(user.cart);
    cartPids.forEach(pid => {
        engine.addPurchase(activeUserId, pid);
        logToConsole(`  [OK] Purchased: ${engine.productMap[pid].name}. Edge added User(${activeUserId}) <--> Prod(${pid})`, "success");
    });

    logToConsole(`Checkout successfully committed. Bipartite purchase graph updated!`, "success");
    updateCartView();
    initNetworkGraph();
});

// Compute Recommendations
btnGetRecs.addEventListener("click", () => {
    logToConsole(`Starting personalized recommendations execution for User: ${activeUserId}`, "alg");
    
    // Call engine and track logging output
    let output = engine.getPersonalizedRecommendations(activeUserId, 5, msg => {
        logToConsole(`  - [ENGINE] ${msg}`, "alg");
    });

    let recs = output.recs;
    
    // Save heap visualizer state
    heapVisualizerData = output.heapArray;
    if (activeTab === "heap") {
        drawHeapTree();
    }

    recsOutputList.innerHTML = "";
    if (recs.length === 0) {
        recsOutputList.innerHTML = `<p class="info-text">No recommendations available. Update your purchase graph context.</p>`;
        return;
    }

    recs.forEach((rec, idx) => {
        let recDiv = document.createElement("div");
        recDiv.className = "rec-item";
        let rankClass = idx < 3 ? `rank-${idx+1}` : "";
        recDiv.innerHTML = `
            <div class="rec-rank ${rankClass}">${idx + 1}</div>
            <div class="rec-details">
                <span class="rec-name" title="${rec.product.name}">${rec.product.name}</span>
                <div class="rec-meta">
                    <span>Category: <strong>${rec.product.category}</strong></span>
                    <span>Match Score: <strong class="rec-score">${(rec.score * 100).toFixed(1)}%</strong></span>
                </div>
            </div>
        `;
        
        // Add "Buy/Add to Cart" interactions inline inside recommendation lists
        recDiv.addEventListener("click", () => {
            let add = confirm(`Do you want to add "${rec.product.name}" to your cart?`);
            if (add) {
                engine.addToCart(activeUserId, rec.product.id);
                logToConsole(`Added recommended item [${rec.product.id}] to cart.`, "success");
                updateCartView();
            }
        });
        
        recsOutputList.appendChild(recDiv);
    });

    logToConsole(`Personalized recommendations loaded successfully. Max-Heap compiled.`, "success");
});

// Switch Visualizer Tabs
tabGraph.addEventListener("click", () => {
    activeTab = "graph";
    tabGraph.classList.add("active");
    tabHeap.classList.remove("active");
    graphContainer.classList.remove("hidden");
    heapContainer.classList.add("hidden");
    initNetworkGraph();
});

tabHeap.addEventListener("click", () => {
    activeTab = "heap";
    tabHeap.classList.add("active");
    tabGraph.classList.remove("active");
    heapContainer.classList.remove("hidden");
    graphContainer.classList.add("hidden");
    drawHeapTree();
});

// Reset visualizer data
btnReset.addEventListener("click", () => {
    logToConsole("Resetting user interactions and purchase graph...", "system");
    engine.initialize(INITIAL_PRODUCTS, INITIAL_USERS);
    initDropdowns();
    updateCartView();
    initNetworkGraph();
    
    // Clear old displays
    similarityResult.classList.add("hidden");
    recsOutputList.innerHTML = `<p class="info-text">Click the Compute Recommendations button above to recalculate.</p>`;
    heapVisualizerData = [];
    if (activeTab === "heap") {
        drawHeapTree();
    }
});

// Page load initialization
window.addEventListener("DOMContentLoaded", () => {
    // Boot the recommendation engine with initial mock values
    engine.initialize(INITIAL_PRODUCTS, INITIAL_USERS);
    
    // Initialize UI Dropdowns & Lists
    initDropdowns();
    updateCartView();
    
    // Configure canvasses and load Force-directed graph
    setupCanvasInteractions();
    initNetworkGraph();
    
    logToConsole("Welcome to the E-Commerce Recommendation Engine DSA Visualizer!");
    logToConsole("Trie prefix tree initialized with all product catalog names.");
    logToConsole("Bipartite user-product transaction graph populated from checkout logs.");
});
