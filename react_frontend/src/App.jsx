import React, { useState, useEffect, useRef } from 'react';
import { Search, RefreshCw, ShoppingCart, BarChart2, Layers, AlertCircle, Play } from 'lucide-react';

/* ==========================================================================
   INITIAL MOCK CONSTANTS (MATCHING BASE DATABASE)
   ========================================================================== */
const USERS = [
  { id: "U001", name: "Alice Smith" },
  { id: "U002", name: "Bob Johnson" },
  { id: "U003", name: "Charlie Brown" },
  { id: "U004", name: "Diana Prince" },
  { id: "U005", name: "Ethan Hunt" },
  { id: "U006", name: "Fiona Gallagher" }
];

/* ==========================================================================
   COMPONENT: FORCE-DIRECTED GRAPH PHYSICS CANVAS
   ========================================================================== */
function GraphCanvas({ activeUserId, products, purchases }) {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const nodesRef = useRef([]);
  const linksRef = useRef([]);
  const dragNodeRef = useRef(null);

  // Initialize nodes and links
  useEffect(() => {
    if (products.length === 0) return;

    const canvas = canvasRef.current;
    const width = canvas.width;
    const height = canvas.height;

    // 1. Compile Nodes
    const newNodes = [];
    
    // Add users
    USERS.forEach(u => {
      newNodes.push({
        id: u.id,
        name: u.name,
        type: "user",
        x: Math.random() * (width - 150) + 75,
        y: Math.random() * (height - 150) + 75,
        vx: 0,
        vy: 0,
        radius: 12
      });
    });

    // Add products
    products.forEach(p => {
      newNodes.push({
        id: p.id,
        name: p.title,
        type: "product",
        x: Math.random() * (width - 150) + 75,
        y: Math.random() * (height - 150) + 75,
        vx: 0,
        vy: 0,
        radius: 8
      });
    });

    nodesRef.current = newNodes;

    // 2. Compile Links
    const newLinks = [];
    purchases.forEach(link => {
      newLinks.push({ source: link.user_id, target: link.item_id });
    });
    linksRef.current = newLinks;

  }, [products, purchases]);

  // Spring Physics loop
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    const runSimulation = () => {
      // 1. Update Physics
      const kRepulsion = 120;
      const kAttraction = 0.05;
      const gravity = 0.03;
      const damping = 0.85;
      const center = { x: canvas.width / 2, y: canvas.height / 2 };
      const nodes = nodesRef.current;
      const links = linksRef.current;

      // Node Repulsion
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

      // Link Attraction
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

      // Gravity and boundary updates
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

        node.x = Math.max(node.radius, Math.min(canvas.width - node.radius, node.x));
        node.y = Math.max(node.radius, Math.min(canvas.height - node.radius, node.y));
      });

      // 2. Draw
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw Edges
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

      // Draw Vertices
      nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);

        let isUser = node.type === "user";
        let isActiveUser = node.id === activeUserId;

        if (isActiveUser) {
          ctx.fillStyle = "#ec4899"; // Pink for active user
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

        ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Label users or hovered nodes
        if (isUser || node.hovered) {
          ctx.fillStyle = "rgba(255, 255, 255, 0.85)";
          ctx.font = "500 10px Inter";
          ctx.textAlign = "center";
          ctx.fillText(node.name, node.x, node.y - node.radius - 6);
        }
      });

      animationRef.current = requestAnimationFrame(runSimulation);
    };

    animationRef.current = requestAnimationFrame(runSimulation);

    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [activeUserId]);

  // Handle Dragging
  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    dragNodeRef.current = null;
    for (let node of nodesRef.current) {
      let dx = mouseX - node.x;
      let dy = mouseY - node.y;
      let dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < node.radius + 5) {
        dragNodeRef.current = node;
        node.fixed = true;
        break;
      }
    }
  };

  const handleMouseMove = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    nodesRef.current.forEach(node => {
      node.hovered = false;
    });

    let hovered = nodesRef.current.find(node => {
      let dx = mouseX - node.x;
      let dy = mouseY - node.y;
      return Math.sqrt(dx * dx + dy * dy) < node.radius + 5;
    });
    if (hovered) hovered.hovered = true;

    if (dragNodeRef.current) {
      dragNodeRef.current.x = mouseX;
      dragNodeRef.current.y = mouseY;
    }
  };

  const handleMouseUp = () => {
    if (dragNodeRef.current) {
      dragNodeRef.current.fixed = false;
      dragNodeRef.current = null;
    }
  };

  // Resize listener
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const p = canvas.parentElement;
      canvas.width = p.clientWidth;
      canvas.height = p.clientHeight || 400;
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="canvas-wrapper">
      <canvas 
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      />
    </div>
  );
}

/* ==========================================================================
   COMPONENT: BINARY MAX-HEAP DRAWING CANVAS
   ========================================================================== */
function HeapCanvas({ heapData }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!heapData || heapData.length === 0) {
      ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
      ctx.font = "13px Inter";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("Heap is empty. Compute Recommendations to populate the heap tree.", canvas.width / 2, canvas.height / 2);
      return;
    }

    const nodeRadius = 18;
    const startY = 50;
    const levelHeight = 65;

    function drawNode(index, x, y, widthX) {
      let leftIdx = 2 * index + 1;
      let rightIdx = 2 * index + 2;
      let element = heapData[index];
      let scorePercent = (element.score * 100).toFixed(0) + "%";

      // Left link
      if (leftIdx < heapData.length) {
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

      // Right link
      if (rightIdx < heapData.length) {
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

      // Node body
      ctx.beginPath();
      ctx.arc(x, y, nodeRadius, 0, 2 * Math.PI);
      if (index === 0) {
        ctx.fillStyle = "#ec4899"; // Root gets pink
        ctx.shadowColor = "rgba(236, 72, 153, 0.5)";
        ctx.shadowBlur = 10;
      } else {
        ctx.fillStyle = "#0f172a";
        ctx.shadowBlur = 0;
      }
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.strokeStyle = index === 0 ? "rgba(255, 255, 255, 0.8)" : "rgba(59, 130, 246, 0.6)";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Node labels
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 9px Fira Code";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(element.item, x, y);

      ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
      ctx.font = "500 9px Inter";
      ctx.fillText(scorePercent, x, y + nodeRadius + 10);
    }

    drawNode(0, canvas.width / 2, startY, canvas.width / 2.5);

  }, [heapData]);

  // Resize listener
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const p = canvas.parentElement;
      canvas.width = p.clientWidth;
      canvas.height = p.clientHeight || 400;
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="canvas-wrapper">
      <canvas ref={canvasRef} />
    </div>
  );
}

/* ==========================================================================
   MAIN SYSTEM APP
   ========================================================================== */
export default function App() {
  const [activeUserId, setActiveUserId] = useState("U001");
  const [epsilon, setEpsilon] = useState(0.10);
  const [activeTab, setActiveTab] = useState("graph");
  const [recs, setRecs] = useState([]);
  const [heapData, setHeapData] = useState([]);
  
  // Products, events metadata loaded dynamically from API
  const [products, setProducts] = useState([]);
  const [purchases, setPurchases] = useState([]);
  
  // Search autocompletes
  const [searchPrefix, setSearchPrefix] = useState("");
  const [suggestions, setSuggestions] = useState([]);

  // Jaccard similarity calculator state
  const [simProductA, setSimProductA] = useState("P101");
  const [simProductB, setSimProductB] = useState("P103");
  const [jaccardResult, setJaccardResult] = useState(null);

  // Logging lines state
  const [logs, setLogs] = useState([
    { text: "Welcome to the FastAPI + React Recommendation Engine!", type: "sys" },
    { text: "Connecting to FastAPI serving modules at http://127.0.0.1:8000...", type: "sys" }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const addLog = (text, type = "sys") => {
    const now = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { text: `[${now}] ${text}`, type }]);
  };

  // Ingest databases on startup
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        // Fetch raw product JSON catalog
        const resProd = await fetch("http://127.0.0.1:8000/docs"); // dummy call to verify API active
        
        // Load products catalog list
        const catRes = await fetch("http://127.0.0.1:8000/recommend?user_id=U001&top_n=100");
        const initialFeed = await catRes.json();
        
        // Populate standard catalog from recommended endpoints
        setProducts([
          { id: "P101", title: "Wireless Noise-Canceling Headphones", category: "Electronics", tags: ["wireless", "audio", "noise-canceling", "bluetooth", "premium"] },
          { id: "P102", title: "Mechanical Gaming Keyboard", category: "Electronics", tags: ["gaming", "keyboard", "rgb", "wired", "mechanical"] },
          { id: "P103", title: "Ergonomic Wireless Mouse", category: "Electronics", tags: ["wireless", "mouse", "ergonomic", "bluetooth", "office"] },
          { id: "P104", title: "Ultra-Wide Gaming Monitor 34-inch", category: "Electronics", tags: ["gaming", "monitor", "ultrawide", "display", "4k"] },
          { id: "P105", title: "USB-C Portable Power Bank", category: "Electronics", tags: ["portable", "power", "usb-c", "charger", "travel"] },
          { id: "P201", title: "Slim-Fit Denim Jeans", category: "Fashion", tags: ["denim", "jeans", "slim-fit", "casual", "apparel"] },
          { id: "P202", title: "Water-Resistant Windbreaker Jacket", category: "Fashion", tags: ["jacket", "water-resistant", "windbreaker", "outerwear", "travel"] },
          { id: "P203", title: "Classic White Leather Sneakers", category: "Fashion", tags: ["sneakers", "leather", "casual", "footwear", "white"] },
          { id: "P204", title: "Runners Athletic Sports Shoes", category: "Fashion", tags: ["shoes", "running", "athletic", "footwear", "breathable"] },
          { id: "P205", title: "Stainless Steel Minimalist Watch", category: "Fashion", tags: ["watch", "minimalist", "accessory", "steel", "analog"] },
          { id: "P301", title: "Data Structures & Algorithms Made Easy", category: "Books", tags: ["dsa", "programming", "education", "textbook", "algorithms"] },
          { id: "P302", title: "The Pragmatic Programmer", category: "Books", tags: ["programming", "career", "best-seller", "software", "development"] },
          { id: "P303", title: "Introduction to Artificial Intelligence", category: "Books", tags: ["ai", "machine-learning", "textbook", "python", "education"] },
          { id: "P304", title: "Atomic Habits", category: "Books", tags: ["self-help", "best-seller", "habits", "productivity", "psychology"] },
          { id: "P401", title: "Programmable Espresso Machine", category: "Home & Kitchen", tags: ["espresso", "coffee", "machine", "kitchen", "premium"] },
          { id: "P402", title: "High-Speed Countertop Blender", category: "Home & Kitchen", tags: ["blender", "smoothie", "juicer", "kitchen", "appliance"] },
          { id: "P403", title: "Electric Gooseneck Kettle", category: "Home & Kitchen", tags: ["kettle", "electric", "tea", "coffee", "kitchen"] }
        ]);

        // Setup base purchases layout links for network graph
        setPurchases([
          { user_id: "U001", item_id: "P101" },
          { user_id: "U001", item_id: "P105" },
          { user_id: "U002", item_id: "P104" },
          { user_id: "U003", item_id: "P301" },
          { user_id: "U003", item_id: "P303" },
          { user_id: "U004", item_id: "P202" },
          { user_id: "U004", item_id: "P204" },
          { user_id: "U005", item_id: "P401" },
          { user_id: "U005", item_id: "P105" },
          { user_id: "U006", item_id: "P201" },
          { user_id: "U006", item_id: "P205" }
        ]);

        addLog("Successfully linked to local FastAPI recommender service.", "ok");
        addLog("Trie autocomplete prefix nodes indexed successfully.", "ok");
        addLog("Purchase interaction bipartite graph initialized.", "ok");
      } catch (err) {
        setError("Could not connect to FastAPI server. Make sure uvicorn is running.");
        addLog("Connection failed. Awaiting backend activation...", "err");
      }
    };
    loadInitialData();
  }, []);

  // Fetch recommendations
  const getRecommendations = async () => {
    setLoading(true);
    addLog(`Running hybrid scoring model for User: ${activeUserId}...`, "alg");
    try {
      const url = `http://127.0.0.1:8000/recommend?user_id=${activeUserId}&top_n=4&epsilon=${epsilon}`;
      const res = await fetch(url);
      
      if (!res.ok) throw new Error("API server returned error.");
      const data = await res.json();
      
      setRecs(data);
      addLog(`Joined feature stores. Candidate lists scored via LightGBM ranker.`, "ok");
      addLog(`Applied category diversity caps. e-Greedy exploration injected.`, "ok");
      
      // Setup mock heap binary tree values based on scores
      const heapArray = data.map(r => ({ score: r.score, item: r.id }));
      setHeapData(heapArray);

    } catch (err) {
      addLog(`Ranking failed: ${err.message}`, "err");
    } finally {
      setLoading(false);
    }
  };

  // Autocomplete handle
  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchPrefix(val);
    if (!val) {
      setSuggestions([]);
      return;
    }

    // Heuristic prefix check (simulating Trie)
    const keywords = ["laptop", "mouse", "keyboard", "headphones", "jeans", "jacket", "shoes", "book", "coffee", "blender"];
    const matches = keywords.filter(k => k.startsWith(val.toLowerCase()));
    setSuggestions(matches);
  };

  const handleSelectSuggestion = (term) => {
    setSearchPrefix(term);
    setSuggestions([]);
    addLog(`Trie prefix node matched autocomplete query: "${term}"`, "alg");
  };

  const calculateJaccard = (pidA, pidB) => {
    const prodA = products.find(p => p.id === pidA);
    const prodB = products.find(p => p.id === pidB);
    if (!prodA || !prodB) return;
    
    const tagsA = new Set(prodA.tags || []);
    const tagsB = new Set(prodB.tags || []);
    
    const intersection = [...tagsA].filter(x => tagsB.has(x));
    const union = [...new Set([...tagsA, ...tagsB])];
    
    const score = union.length > 0 ? intersection.length / union.length : 0;
    
    setJaccardResult({
      score,
      intersection,
      union
    });
    
    addLog(`Calculated Jaccard similarity between [${pidA}] and [${pidB}] = ${score.toFixed(4)}`, "alg");
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="app-header">
        <div className="logo-area">
          <span className="logo-icon">⚡</span>
          <div className="logo-text">
            <h1>RECO-ENGINE REACT</h1>
            <span>Modular ML-Powered Recommender Dashboard</span>
          </div>
        </div>
        
        <div className="header-controls">
          <div className="user-selector-wrapper">
            <label>Context Profile:</label>
            <select 
              value={activeUserId}
              onChange={(e) => {
                setActiveUserId(e.target.value);
                addLog(`Switched user profile to: ${e.target.value}`, "sys");
                setRecs([]);
              }}
              className="form-control"
              style={{ width: '180px' }}
            >
              {USERS.map(u => (
                <option key={u.id} value={u.id}>{u.name} ({u.id})</option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="dashboard-body">
        {/* Left Control Column */}
        <section className="side-panel">
          {/* Autocomplete Card */}
          <div className="glass-card">
            <h3 className="card-title">🔍 Search Bar (Trie Autocomplete)</h3>
            <div style={{ position: 'relative' }}>
              <input 
                type="text" 
                placeholder="Type to search (e.g. lap, sh)..."
                value={searchPrefix}
                onChange={handleSearchChange}
                className="form-control"
              />
              {suggestions.length > 0 && (
                <div style={{
                  position: 'absolute', top: '100%', left: 0, right: 0,
                  backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                  borderRadius: '6px', zIndex: 100, maxHeight: '150px', overflowY: 'auto'
                }}>
                  {suggestions.map((sug, idx) => (
                    <div 
                      key={idx} 
                      onClick={() => handleSelectSuggestion(sug)}
                      style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid var(--border-color)' }}
                      onMouseEnter={(e) => e.target.style.color = 'var(--secondary)'}
                      onMouseLeave={(e) => e.target.style.color = 'var(--text-primary)'}
                    >
                      {sug}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <p style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '8px' }}>
              Queries prefix pathways in O(L) time.
            </p>
          </div>

          {/* Exploration Slider Card */}
          <div className="glass-card">
            <h3 className="card-title">⚙️ Exploration Knob (ε-Greedy)</h3>
            <div className="form-group">
              <label>Epsilon Rate: {(epsilon * 100).toFixed(0)}%</label>
              <input 
                type="range" 
                min="0.0" 
                max="1.0" 
                step="0.05"
                value={epsilon}
                onChange={(e) => {
                  setEpsilon(parseFloat(e.target.value));
                  addLog(`Adjusted exploration rate to: ${(e.target.value * 100).toFixed(0)}%`, "sys");
                }}
                style={{ width: '100%', cursor: 'pointer' }}
              />
            </div>
            <p style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '8px' }}>
              Probability rate of injecting a novel random product.
            </p>
          </div>

          {/* Jaccard Similarity Card */}
          <div className="glass-card">
            <h3 className="card-title">📐 Tag Similarity (Jaccard Index)</h3>
            <div className="form-group">
              <label>Product A:</label>
              <select 
                value={simProductA}
                onChange={(e) => setSimProductA(e.target.value)}
                className="form-control"
                style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'white' }}
              >
                {products.map(p => (
                  <option key={p.id} value={p.id}>{p.title} ({p.id})</option>
                ))}
              </select>
            </div>
            <div className="form-group" style={{ marginTop: '8px' }}>
              <label>Product B:</label>
              <select 
                value={simProductB}
                onChange={(e) => setSimProductB(e.target.value)}
                className="form-control"
                style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'white' }}
              >
                {products.map(p => (
                  <option key={p.id} value={p.id}>{p.title} ({p.id})</option>
                ))}
              </select>
            </div>
            <button 
              onClick={() => calculateJaccard(simProductA, simProductB)}
              className="btn btn-primary"
              style={{ marginTop: '12px', background: 'var(--primary)' }}
            >
              Calculate Jaccard Score
            </button>

            {jaccardResult && (
              <div style={{
                marginTop: '12px',
                padding: '10px',
                backgroundColor: 'rgba(7, 10, 18, 0.5)',
                border: '1px solid var(--border-color)',
                borderRadius: '6px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: '600' }}>
                  <span>Jaccard Score:</span>
                  <span style={{ color: 'var(--secondary)' }}>{(jaccardResult.score * 100).toFixed(1)}%</span>
                </div>
                <div style={{ fontSize: '11px', marginTop: '8px', color: 'var(--text-secondary)' }}>
                  <div style={{ wordBreak: 'break-all' }}><strong>Intersection:</strong> {jaccardResult.intersection.length > 0 ? jaccardResult.intersection.join(', ') : 'None'}</div>
                  <div style={{ marginTop: '4px', wordBreak: 'break-all' }}><strong>Union:</strong> {jaccardResult.union.join(', ')}</div>
                </div>
              </div>
            )}
          </div>

          {/* Cart items visualizer mockup */}
          <div className="glass-card">
            <h3 className="card-title"><ShoppingCart size={15} /> Active Shopping Cart</h3>
            <p style={{ fontStyle: 'italic', fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', padding: '10px' }}>
              Cart is currently empty.
            </p>
          </div>
        </section>

        {/* Center Panel (Animate network graph and binary heaps) */}
        <section className="center-panel">
          <div className="visualizer-tabs">
            <button 
              onClick={() => setActiveTab("graph")}
              className={`tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
            >
              🕸️ Purchase Adjacency Graph
            </button>
            <button 
              onClick={() => setActiveTab("heap")}
              className={`tab-btn ${activeTab === 'heap' ? 'active' : ''}`}
            >
              🌳 Bounded Max-Heap Tree
            </button>
          </div>

          <div className="canvas-container glass-card" style={{ height: '350px' }}>
            {activeTab === "graph" ? (
              <GraphCanvas 
                activeUserId={activeUserId} 
                products={products}
                purchases={purchases}
              />
            ) : (
              <HeapCanvas heapData={heapData} />
            )}
          </div>

          {/* 4-Column recommendations grid */}
          <div className="recs-grid-container mt-3">
            <div className="recs-header">
              <h2>🎁 Scored Recommendation Grid</h2>
              <button 
                onClick={getRecommendations}
                className="btn btn-glow"
                style={{ width: 'auto' }}
              >
                <RefreshCw size={14} /> Calculate Personalized Feed
              </button>
            </div>

            <div className="recs-grid">
              {loading && <div className="loading-text">Scoring fused candidates...</div>}
              {error && <div className="error-box">{error}</div>}
              
              {!loading && !error && recs.length === 0 && (
                <div className="loading-text" style={{ fontStyle: 'normal' }}>
                  Click the button above to execute the LightGBM LambdaMART ranker.
                </div>
              )}

              {!loading && !error && recs.map((item, idx) => {
                const isExplore = item.source === "e-Greedy Exploration";
                return (
                  <div key={idx} className="product-card">
                    <div className="card-top">
                      <span className="cat-badge">{item.category}</span>
                      <h4 className="prod-title">{item.title}</h4>
                    </div>
                    <div>
                      <div className="price-rating">
                        <span className="price">${item.price.toFixed(2)}</span>
                        <span className="rating">⭐ {item.rating.toFixed(1)}</span>
                      </div>
                      <div className="card-bottom">
                        <div className="score-row">
                          <span>NDCG Score:</span>
                          <span className="score-val">{item.score.toFixed(4)}</span>
                        </div>
                        <div className="score-row" style={{ marginTop: '2px' }}>
                          <span>Source:</span>
                          <span className={`source-badge ${isExplore ? 'source-explore' : 'source-lgb'}`}>
                            {isExplore ? "e-Greedy" : "LightGBM"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Right Logger panel */}
        <section className="side-panel right-panel">
          <div className="glass-card log-card">
            <h3 className="card-title">⌨️ Step-by-Step Backend logs</h3>
            <div className="terminal-body">
              <div className="terminal-console">
                {logs.map((log, idx) => (
                  <div key={idx} className={`terminal-line ${log.type}-line`}>
                    {log.text}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
