/**
 * Dynamic Concept Map Component
 * From LIBRARY_PRD.md §3.4
 */
import React, { useEffect, useRef, useState } from 'react';

interface Node {
  id: string;
  name: string;
  type: 'root' | 'thesis' | 'evidence' | 'gap';
  x?: number;
  y?: number;
}

interface Edge {
  source: string;
  target: string;
  type: string;
}

interface ConceptMapProps {
  nodes: Node[];
  edges: Edge[];
  onNodeClick?: (node: Node) => void;
  width?: number;
  height?: number;
}

export const ConceptMap: React.FC<ConceptMapProps> = ({
  nodes,
  edges,
  onNodeClick,
  width = 600,
  height = 400,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Calculate node positions (simple force layout simulation)
    const nodePositions = calculateLayout(nodes, edges, width, height);

    // Draw edges
    edges.forEach(edge => {
      const source = nodePositions[edge.source];
      const target = nodePositions[edge.target];
      if (source && target) {
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = getEdgeColor(edge.type);
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    });

    // Draw nodes
    nodes.forEach(node => {
      const pos = nodePositions[node.id];
      if (!pos) return;

      const radius = getNodeRadius(node.type);
      
      // Node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = getNodeColor(node.type);
      ctx.fill();
      
      // Hover effect
      if (hoveredNode === node.id) {
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 3;
        ctx.stroke();
      }

      // Label
      ctx.fillStyle = '#333';
      ctx.font = node.type === 'root' ? 'bold 12px sans-serif' : '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(node.name, pos.x, pos.y + radius + 15);
    });
  }, [nodes, edges, width, height, hoveredNode]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Find hovered node
    const nodePositions = calculateLayout(nodes, edges, width, height);
    const hovered = nodes.find(node => {
      const pos = nodePositions[node.id];
      if (!pos) return false;
      const radius = getNodeRadius(node.type);
      const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      return dist <= radius;
    });

    setHoveredNode(hovered?.id || null);
  };

  const handleClick = () => {
    if (hoveredNode) {
      const node = nodes.find(n => n.id === hoveredNode);
      if (node) onNodeClick?.(node);
    }
  };

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      className="border rounded-lg bg-white cursor-pointer"
      onMouseMove={handleMouseMove}
      onClick={handleClick}
    />
  );
};

// Simple force-directed layout
function calculateLayout(nodes: Node[], edges: Edge[], width: number, height: number): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {};
  
  // Initialize with random positions
  nodes.forEach((node, i) => {
    const angle = (i / nodes.length) * Math.PI * 2;
    const radius = Math.min(width, height) * 0.3;
    positions[node.id] = {
      x: width / 2 + Math.cos(angle) * radius,
      y: height / 2 + Math.sin(angle) * radius,
    };
  });

  // Simple force simulation (5 iterations)
  for (let iter = 0; iter < 5; iter++) {
    // Repulsion
    nodes.forEach((nodeA, i) => {
      nodes.forEach((nodeB, j) => {
        if (i >= j) return;
        const posA = positions[nodeA.id];
        const posB = positions[nodeB.id];
        const dx = posA.x - posB.x;
        const dy = posA.y - posB.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = 1000 / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        posA.x += fx;
        posA.y += fy;
        posB.x -= fx;
        posB.y -= fy;
      });
    });

    // Attraction (edges)
    edges.forEach(edge => {
      const posA = positions[edge.source];
      const posB = positions[edge.target];
      if (!posA || !posB) return;
      const dx = posB.x - posA.x;
      const dy = posB.y - posA.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = dist * 0.01;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      posA.x += fx;
      posA.y += fy;
      posB.x -= fx;
      posB.y -= fy;
    });

    // Center gravity
    nodes.forEach(node => {
      const pos = positions[node.id];
      pos.x += (width / 2 - pos.x) * 0.1;
      pos.y += (height / 2 - pos.y) * 0.1;
    });
  }

  return positions;
}

function getNodeColor(type: Node['type']): string {
  switch (type) {
    case 'root': return '#22c55e';
    case 'thesis': return '#3b82f6';
    case 'evidence': return '#9ca3af';
    case 'gap': return '#eab308';
    default: return '#9ca3af';
  }
}

function getNodeRadius(type: Node['type']): number {
  switch (type) {
    case 'root': return 20;
    case 'thesis': return 15;
    case 'evidence': return 8;
    case 'gap': return 12;
    default: return 10;
  }
}

function getEdgeColor(type: string): string {
  switch (type) {
    case 'DEPENDS_ON': return '#3b82f6';
    case 'SUPPORTS': return '#22c55e';
    case 'CONTRADICTS': return '#ef4444';
    case 'EXTENDS': return '#a855f7';
    default: return '#9ca3af';
  }
}
