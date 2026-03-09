/**
 * Augmented Reader Component
 * From LIBRARY_PRD.md §3.5
 * 
 * Features:
 * - Semantic Zoom (3 levels)
 * - Augmented TOC
 * - Concept Map
 * - JIT Context Injection
 * - Non-Linear Navigation
 */
import React, { useState, useCallback } from 'react';
import { ZoomIn, ZoomOut, Map, List, Highlighter } from 'lucide-react';
import { ConceptMap } from './ConceptMap';
import { AugmentedTOC } from './AugmentedTOC';

interface ReaderProps {
  document: {
    id: string;
    title: string;
    author?: string;
    content: string;
    chapters: Array<{
      title: string;
      content: string;
      concept_density?: number;
      is_core_thesis?: boolean;
    }>;
  };
  pkgData?: {
    nodes: Array<{
      id: string;
      name: string;
      type: 'root' | 'thesis' | 'evidence' | 'gap';
    }>;
    edges: Array<{
      source: string;
      target: string;
      type: string;
    }>;
  };
}

type ZoomLevel = 'summary' | 'theses' | 'full';

export const Reader: React.FC<ReaderProps> = ({ document, pkgData }) => {
  const [zoomLevel, setZoomLevel] = useState<ZoomLevel>('full');
  const [showConceptMap, setShowConceptMap] = useState(false);
  const [currentChapter, setCurrentChapter] = useState(0);
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null);
  const [highlights, setHighlights] = useState<Array<{start: number; end: number; text: string}>>([]);

  // Transform chapters for TOC
  const tocChapters = document.chapters.map((ch, i) => ({
    title: ch.title,
    position: i / document.chapters.length,
    concept_density: ch.concept_density || 0.5,
    atom_count: Math.ceil(ch.content.length / 1000),
    is_core_thesis: ch.is_core_thesis || false,
  }));

  // Semantic zoom content filter
  const getZoomedContent = useCallback((content: string) => {
    switch (zoomLevel) {
      case 'summary':
        // Return first paragraph + key sentences
        const sentences = content.match(/[^.!?]+[.!?]+/g) || [content];
        return sentences.slice(0, 3).join(' ');
      
      case 'theses':
        // Return paragraphs with high semantic density
        const paragraphs = content.split('\n\n');
        return paragraphs
          .filter((_, i) => i % 2 === 0) // Simplified: every other paragraph
          .join('\n\n');
      
      case 'full':
      default:
        return content;
    }
  }, [zoomLevel]);

  // Handle text selection for highlighting
  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      const text = selection.toString();
      const range = selection.getRangeAt(0);
      
      setHighlights(prev => [...prev, {
        start: range.startOffset,
        end: range.endOffset,
        text,
      }]);
    }
  };

  // Non-linear navigation: jump to concept mentions
  const handleConceptClick = (concept: { id: string; name: string }) => {
    setSelectedConcept(concept.id);
    
    // Find all mentions in document
    const mentions = document.chapters.filter(ch => 
      ch.content.toLowerCase().includes(concept.name.toLowerCase())
    );
    
    if (mentions.length > 0) {
      const firstMention = document.chapters.findIndex(ch => ch === mentions[0]);
      setCurrentChapter(firstMention);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left sidebar - TOC */}
      <div className="w-80 p-4 overflow-y-auto">
        <AugmentedTOC
          chapters={tocChapters}
          currentPosition={currentChapter / document.chapters.length}
          onChapterClick={(pos) => setCurrentChapter(Math.floor(pos * document.chapters.length))}
          documentProgress={0.35}
        />
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="bg-white border-b p-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">{document.title}</h1>
            {document.author && (
              <p className="text-sm text-gray-500">by {document.author}</p>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Semantic Zoom controls */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setZoomLevel('summary')}
                className={`px-3 py-1 rounded text-sm ${
                  zoomLevel === 'summary' ? 'bg-white shadow' : 'text-gray-600'
                }`}
              >
                Summary
              </button>
              <button
                onClick={() => setZoomLevel('theses')}
                className={`px-3 py-1 rounded text-sm ${
                  zoomLevel === 'theses' ? 'bg-white shadow' : 'text-gray-600'
                }`}
              >
                Theses
              </button>
              <button
                onClick={() => setZoomLevel('full')}
                className={`px-3 py-1 rounded text-sm ${
                  zoomLevel === 'full' ? 'bg-white shadow' : 'text-gray-600'
                }`}
              >
                Full
              </button>
            </div>

            {/* View toggle */}
            <button
              onClick={() => setShowConceptMap(!showConceptMap)}
              className={`p-2 rounded-lg flex items-center gap-2 ${
                showConceptMap ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'
              }`}
            >
              <Map className="w-5 h-5" />
              <span className="text-sm">Concept Map</span>
            </button>
          </div>
        </div>

        {/* Content area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Text content */}
          <div 
            className={`flex-1 p-8 overflow-y-auto ${showConceptMap ? 'w-1/2' : 'w-full'}`}
            onMouseUp={handleTextSelection}
          >
            <article className="prose prose-lg max-w-none">
              <h2 className="text-2xl font-bold mb-4">
                {document.chapters[currentChapter]?.title}
              </h2>
              
              <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                {getZoomedContent(document.chapters[currentChapter]?.content || '')}
              </div>
            </article>

            {/* Chapter navigation */}
            <div className="flex justify-between mt-8 pt-8 border-t">
              <button
                onClick={() => setCurrentChapter(Math.max(0, currentChapter - 1))}
                disabled={currentChapter === 0}
                className="px-4 py-2 text-blue-600 disabled:text-gray-400"
              >
                ← Previous
              </button>
              <button
                onClick={() => setCurrentChapter(Math.min(document.chapters.length - 1, currentChapter + 1))}
                disabled={currentChapter === document.chapters.length - 1}
                className="px-4 py-2 text-blue-600 disabled:text-gray-400"
              >
                Next →
              </button>
            </div>
          </div>

          {/* Concept Map sidebar */}
          {showConceptMap && pkgData && (
            <div className="w-1/2 p-4 bg-white border-l overflow-y-auto">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Map className="w-5 h-5" />
                Concept Map
              </h3>
              
              <ConceptMap
                nodes={pkgData.nodes}
                edges={pkgData.edges}
                onNodeClick={handleConceptClick}
                width={500}
                height={400}
              />

              {/* Legend */}
              <div className="mt-4 space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-green-500" />
                  <span>Axiomatic Root (known)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-blue-500" />
                  <span>Derivative Thesis</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-yellow-500" />
                  <span>Knowledge Gap</span>
                </div>
              </div>

              {/* Selected concept info */}
              {selectedConcept && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium">Selected Concept</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Click on concepts in the map to navigate to their mentions in the text.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Highlights sidebar */}
      {highlights.length > 0 && (
        <div className="w-64 bg-white border-l p-4 overflow-y-auto">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Highlighter className="w-5 h-5" />
            Highlights ({highlights.length})
          </h3>
          <div className="space-y-2">
            {highlights.map((hl, i) => (
              <div key={i} className="p-2 bg-yellow-50 rounded text-sm">
                {hl.text.slice(0, 100)}...
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
