import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Filter,
  Search,
  X,
  Info,
  GitBranch,
  BookOpen,
  Lightbulb
} from 'lucide-react';
import { usePKGGraph } from '../../hooks/useLibrary';
import { PKGNode, PKGEdge } from '../../services/library';

interface ConceptMapProps {
  onNodeSelect?: (node: PKGNode) => void;
  height?: number;
}

interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  node_type: 'concept' | 'atom' | 'document';
  confidence: number;
  knowledge_state: 'known' | 'gap' | 'learning';
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  id: string;
  source: string | D3Node;
  target: string | D3Node;
  edge_type: string;
  confidence: number;
}

const nodeColors = {
  concept: { fill: '#3b82f6', stroke: '#1d4ed8' },      // Blue
  atom: { fill: '#10b981', stroke: '#047857' },         // Green
  document: { fill: '#f59e0b', stroke: '#b45309' },     // Orange
};

const knowledgeStateColors = {
  known: '#22c55e',
  learning: '#eab308',
  gap: '#ef4444',
};

const edgeTypePatterns = {
  depends_on: [5, 5],      // Dashed
  supports: [],            // Solid
  contradicts: [2, 2],     // Dotted
  extends: [10, 3, 3, 3],  // Dash-dot
  exemplifies: [2, 5],     // Short dash
  contains: [],            // Solid
};

export const ConceptMap: React.FC<ConceptMapProps> = ({ 
  onNodeSelect,
  height = 600,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const simulationRef = useRef<d3.Simulation<D3Node, D3Link> | null>(null);
  
  const { data: graphData, isLoading } = usePKGGraph();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNode, setSelectedNode] = useState<PKGNode | null>(null);
  const [filterType, setFilterType] = useState<string | null>(null);
  const [showLabels, setShowLabels] = useState(true);
  const [zoom, setZoom] = useState(1);

  // Transform data for D3
  const transformData = useCallback((nodes: PKGNode[], edges: PKGEdge[]) => {
    const nodeMap = new Map<string, D3Node>();
    
    const d3Nodes: D3Node[] = nodes.map(n => {
      const node: D3Node = {
        id: n.id,
        name: n.name,
        node_type: n.node_type,
        confidence: n.confidence,
        knowledge_state: n.knowledge_state,
      };
      nodeMap.set(n.id, node);
      return node;
    });

    const d3Links: D3Link[] = edges.map(e => ({
      id: e.id,
      source: e.source_id,
      target: e.target_id,
      edge_type: e.edge_type,
      confidence: e.confidence,
    }));

    return { nodes: d3Nodes, links: d3Links };
  }, []);

  // Initialize D3 visualization
  useEffect(() => {
    if (!svgRef.current || !graphData || isLoading) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous

    const width = containerRef.current?.clientWidth || 800;
    const { nodes, links } = transformData(graphData.nodes, graphData.edges);

    // Filter nodes if search or type filter active
    let filteredNodes = nodes;
    let filteredLinks = links;

    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filteredNodes = nodes.filter(n => 
        n.name.toLowerCase().includes(searchLower)
      );
      const nodeIds = new Set(filteredNodes.map(n => n.id));
      filteredLinks = links.filter(l => 
        nodeIds.has(typeof l.source === 'string' ? l.source : l.source.id) &&
        nodeIds.has(typeof l.target === 'string' ? l.target : l.target.id)
      );
    }

    if (filterType) {
      filteredNodes = filteredNodes.filter(n => n.node_type === filterType);
    }

    // Create container group with zoom
    const g = svg.append('g');

    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoom(event.transform.k);
      });

    svg.call(zoomBehavior);

    // Create arrow markers for directed edges
    const defs = svg.append('defs');
    
    Object.keys(edgeTypePatterns).forEach(edgeType => {
      defs.append('marker')
        .attr('id', `arrow-${edgeType}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#6b7280');
    });

    // Create force simulation
    const simulation = d3.forceSimulation<D3Node>(filteredNodes)
      .force('link', d3.forceLink<D3Node, D3Link>(filteredLinks)
        .id(d => d.id)
        .distance(100)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    simulationRef.current = simulation;

    // Create links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(filteredLinks)
      .join('line')
      .attr('stroke', '#6b7280')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.confidence) * 2)
      .attr('stroke-dasharray', d => edgeTypePatterns[d.edge_type as keyof typeof edgeTypePatterns] || [])
      .attr('marker-end', d => `url(#arrow-${d.edge_type})`);

    // Create link labels
    const linkLabel = g.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(filteredLinks)
      .join('text')
      .attr('font-size', '10px')
      .attr('fill', '#6b7280')
      .attr('text-anchor', 'middle')
      .text(d => d.edge_type.replace('_', ' '))
      .style('opacity', showLabels ? 0.7 : 0);

    // Create nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(filteredNodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag<SVGGElement, D3Node>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // Node circles
    node.append('circle')
      .attr('r', d => d.node_type === 'concept' ? 20 : d.node_type === 'document' ? 15 : 10)
      .attr('fill', d => nodeColors[d.node_type].fill)
      .attr('stroke', d => nodeColors[d.node_type].stroke)
      .attr('stroke-width', 2)
      .attr('stroke-opacity', d => d.knowledge_state === 'known' ? 1 : 0.3);

    // Knowledge state indicator (inner circle)
    node.append('circle')
      .attr('r', 6)
      .attr('fill', d => knowledgeStateColors[d.knowledge_state]);

    // Node labels
    const nodeLabel = g.append('g')
      .attr('class', 'node-labels')
      .selectAll('text')
      .data(filteredNodes)
      .join('text')
      .attr('dy', 35)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', '500')
      .attr('fill', '#374151')
      .style('pointer-events', 'none')
      .style('opacity', showLabels ? 1 : 0)
      .text(d => d.name.length > 20 ? d.name.slice(0, 20) + '...' : d.name);

    // Node click handler
    node.on('click', (event, d) => {
      event.stopPropagation();
      const fullNode = graphData?.nodes.find(n => n.id === d.id);
      if (fullNode) {
        setSelectedNode(fullNode);
        onNodeSelect?.(fullNode);
      }
    });

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as D3Node).x!)
        .attr('y1', d => (d.source as D3Node).y!)
        .attr('x2', d => (d.target as D3Node).x!)
        .attr('y2', d => (d.target as D3Node).y!);

      node.attr('transform', d => `translate(${d.x},${d.y})`);

      nodeLabel
        .attr('x', d => d.x!)
        .attr('y', d => d.y!);

      linkLabel
        .attr('x', d => ((d.source as D3Node).x! + (d.target as D3Node).x!) / 2)
        .attr('y', d => ((d.source as D3Node).y! + (d.target as D3Node).y!) / 2);
    });

    return () => {
      simulation.stop();
    };
  }, [graphData, isLoading, height, transformData, searchTerm, filterType, showLabels, onNodeSelect]);

  const handleZoomIn = () => {
    if (svgRef.current) {
      d3.select(svgRef.current)
        .transition()
        .call(d3.zoom().transform, d3.zoomIdentity.scale(zoom * 1.2));
    }
  };

  const handleZoomOut = () => {
    if (svgRef.current) {
      d3.select(svgRef.current)
        .transition()
        .call(d3.zoom().transform, d3.zoomIdentity.scale(zoom * 0.8));
    }
  };

  const handleReset = () => {
    if (svgRef.current) {
      d3.select(svgRef.current)
        .transition()
        .call(d3.zoom().transform, d3.zoomIdentity);
      simulationRef.current?.alpha(1).restart();
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Toolbar */}
      <div className="p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="font-semibold flex items-center gap-2">
            <GitBranch className="w-5 h-5" />
            Concept Map
          </h3>
          
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search concepts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-2 border rounded-lg text-sm w-64 focus:ring-2 focus:ring-blue-500"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 -translate-y-1/2"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            )}
          </div>

          {/* Type Filter */}
          <select
            value={filterType || ''}
            onChange={(e) => setFilterType(e.target.value || null)}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="">All Types</option>
            <option value="concept">Concepts</option>
            <option value="atom">Atoms</option>
            <option value="document">Documents</option>
          </select>

          {/* Show Labels Toggle */}
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showLabels}
              onChange={(e) => setShowLabels(e.target.checked)}
              className="rounded"
            />
            Labels
          </label>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 rounded-lg"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-sm text-gray-500 w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 rounded-lg"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="p-2 hover:bg-gray-100 rounded-lg"
            title="Reset View"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div ref={containerRef} className="relative">
        <svg
          ref={svgRef}
          width="100%"
          height={height}
          className="bg-gray-50"
        />

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur rounded-lg shadow p-3 text-sm">
          <p className="font-medium mb-2">Legend</p>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500" />
              <span>Concept</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-green-500" />
              <span>Atom</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-orange-500" />
              <span>Document</span>
            </div>
          </div>
          <div className="mt-3 pt-2 border-t">
            <p className="text-xs text-gray-500 mb-1">Knowledge State</p>
            <div className="flex gap-2">
              <span className="w-3 h-3 rounded-full bg-green-500" title="Known" />
              <span className="w-3 h-3 rounded-full bg-yellow-500" title="Learning" />
              <span className="w-3 h-3 rounded-full bg-red-500" title="Gap" />
            </div>
          </div>
        </div>

        {/* Node Details Panel */}
        {selectedNode && (
          <div className="absolute top-4 right-4 w-72 bg-white rounded-lg shadow-lg border p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                {selectedNode.node_type === 'concept' && <BookOpen className="w-5 h-5 text-blue-500" />}
                {selectedNode.node_type === 'atom' && <Lightbulb className="w-5 h-5 text-green-500" />}
                <span className="font-medium capitalize">{selectedNode.node_type}</span>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <h4 className="font-semibold text-lg mt-3">{selectedNode.name}</h4>
            
            {selectedNode.definition && (
              <p className="text-sm text-gray-600 mt-2">{selectedNode.definition}</p>
            )}

            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Confidence</span>
                <span className="font-medium">{Math.round(selectedNode.confidence * 100)}%</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">State</span>
                <span 
                  className="px-2 py-0.5 rounded text-xs font-medium capitalize"
                  style={{ 
                    backgroundColor: knowledgeStateColors[selectedNode.knowledge_state] + '20',
                    color: knowledgeStateColors[selectedNode.knowledge_state]
                  }}
                >
                  {selectedNode.knowledge_state}
                </span>
              </div>
            </div>

            {selectedNode.relationships && selectedNode.relationships.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium mb-2">Relationships</p>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {selectedNode.relationships.map((rel, idx) => (
                    <div key={idx} className="text-xs p-2 bg-gray-50 rounded">
                      <span className="capitalize text-gray-500">{rel.type.replace('_', ' ')}</span>
                      <span className="mx-1">→</span>
                      <span>{rel.target_id.slice(0, 8)}...</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
