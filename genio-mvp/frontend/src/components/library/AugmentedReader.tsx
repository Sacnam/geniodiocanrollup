import React, { useState, useRef, useCallback, useEffect } from 'react';
import { 
  Highlighter, 
  MessageSquare, 
  BookOpen, 
  Share2, 
  ChevronLeft,
  ChevronRight,
  X,
  Sparkles,
  Link2,
  Lightbulb
} from 'lucide-react';
import { useOverlays, useCreateHighlight, useHighlights } from '../../hooks/useLibrary';
import { Highlight } from '../../services/library';

interface AugmentedReaderProps {
  documentId: string;
  title: string;
  content: string;
  onClose: () => void;
}

interface SelectionInfo {
  text: string;
  startOffset: number;
  endOffset: number;
  rect: DOMRect;
}

interface Overlay {
  id: string;
  type: 'concept' | 'definition' | 'connection' | 'insight';
  title: string;
  content: string;
  position: 'left' | 'right' | 'inline';
  relatedConcepts?: string[];
}

const HighlightColors = [
  { name: 'Yellow', bg: 'bg-yellow-200', border: 'border-yellow-400' },
  { name: 'Green', bg: 'bg-green-200', border: 'border-green-400' },
  { name: 'Blue', bg: 'bg-blue-200', border: 'border-blue-400' },
  { name: 'Pink', bg: 'bg-pink-200', border: 'border-pink-400' },
];

export const AugmentedReader: React.FC<AugmentedReaderProps> = ({
  documentId,
  title,
  content,
  onClose,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [selection, setSelection] = useState<SelectionInfo | null>(null);
  const [showHighlightToolbar, setShowHighlightToolbar] = useState(false);
  const [activeHighlights, setActiveHighlights] = useState<Highlight[]>([]);
  const [overlays, setOverlays] = useState<Overlay[]>([]);
  const [activeOverlay, setActiveOverlay] = useState<string | null>(null);
  const [semanticZoom, setSemanticZoom] = useState(false);

  const { data: savedHighlights } = useHighlights(documentId);
  const createHighlight = useCreateHighlight();

  // Load overlays for current visible content
  const visibleText = content.slice(0, 2000); // First 2000 chars
  const { data: fetchedOverlays } = useOverlays(documentId, visibleText);

  useEffect(() => {
    if (fetchedOverlays) {
      const formattedOverlays: Overlay[] = fetchedOverlays.map((item, idx) => ({
        id: item.id || `overlay-${idx}`,
        type: item.type as Overlay['type'],
        title: item.type === 'concept' ? 'Key Concept' : 
               item.type === 'definition' ? 'Definition' : 'Insight',
        content: item.text,
        position: idx % 2 === 0 ? 'left' : 'right',
        relatedConcepts: item.related_nodes,
      }));
      setOverlays(formattedOverlays);
    }
  }, [fetchedOverlays]);

  // Handle text selection
  const handleSelection = useCallback(() => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !contentRef.current) {
      setShowHighlightToolbar(false);
      return;
    }

    const text = sel.toString().trim();
    if (text.length < 3) return;

    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    // Calculate offsets relative to content
    const preCaretRange = range.cloneRange();
    preCaretRange.selectNodeContents(contentRef.current);
    preCaretRange.setEnd(range.startContainer, range.startOffset);
    const startOffset = preCaretRange.toString().length;

    setSelection({
      text,
      startOffset,
      endOffset: startOffset + text.length,
      rect,
    });
    setShowHighlightToolbar(true);
  }, []);

  // Create highlight
  const handleCreateHighlight = async (colorIndex: number) => {
    if (!selection) return;

    const color = HighlightColors[colorIndex].name.toLowerCase();
    
    await createHighlight.mutateAsync({
      document_id: documentId,
      start_offset: selection.startOffset,
      end_offset: selection.endOffset,
      text: selection.text,
      color,
    });

    setActiveHighlights(prev => [...prev, {
      id: `temp-${Date.now()}`,
      document_id: documentId,
      start_offset: selection.startOffset,
      end_offset: selection.endOffset,
      text: selection.text,
      color,
      created_at: new Date().toISOString(),
    }]);

    setShowHighlightToolbar(false);
    window.getSelection()?.removeAllRanges();
  };

  // Add note to highlight
  const [activeNote, setActiveNote] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');

  const handleSaveNote = () => {
    // Would save note to backend
    setActiveNote(null);
    setNoteText('');
  };

  // Render content with highlights
  const renderContent = () => {
    const allHighlights = [...(savedHighlights || []), ...activeHighlights];
    if (allHighlights.length === 0) return content;

    // Sort highlights by start offset
    const sorted = [...allHighlights].sort((a, b) => a.start_offset - b.start_offset);
    
    let result = [];
    let lastEnd = 0;

    sorted.forEach((highlight, idx) => {
      // Text before highlight
      if (highlight.start_offset > lastEnd) {
        result.push(
          <span key={`text-${idx}`}>{content.slice(lastEnd, highlight.start_offset)}</span>
        );
      }

      // Highlighted text
      const colorClass = HighlightColors.find(c => 
        c.name.toLowerCase() === highlight.color
      )?.bg || 'bg-yellow-200';

      result.push(
        <mark
          key={`highlight-${highlight.id}`}
          className={`${colorClass} cursor-pointer hover:opacity-80 rounded px-0.5`}
          onClick={() => setActiveNote(highlight.id)}
          title={highlight.note || 'Click to add note'}
        >
          {content.slice(highlight.start_offset, highlight.end_offset)}
        </mark>
      );

      lastEnd = highlight.end_offset;
    });

    // Remaining text
    if (lastEnd < content.length) {
      result.push(<span key="text-end">{content.slice(lastEnd)}</span>);
    }

    return result;
  };

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="font-semibold text-lg">{title}</h1>
            <p className="text-sm text-gray-500">Augmented Reader</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setSemanticZoom(!semanticZoom)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
              semanticZoom ? 'bg-purple-100 text-purple-700' : 'hover:bg-gray-100'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span className="text-sm">Semantic Zoom</span>
          </button>
          
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Share2 className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full flex">
          {/* Left Sidebar - Overlays */}
          <aside className={`
            w-80 border-r bg-gray-50 overflow-y-auto transition-all
            ${semanticZoom ? 'translate-x-0' : '-translate-x-full absolute'}
          `}>
            <div className="p-4">
              <h3 className="font-medium mb-4 flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Insights & Connections
              </h3>
              
              {overlays.map(overlay => (
                <div
                  key={overlay.id}
                  onClick={() => setActiveOverlay(activeOverlay === overlay.id ? null : overlay.id)}
                  className={`
                    mb-3 p-3 rounded-lg cursor-pointer transition-all
                    ${activeOverlay === overlay.id 
                      ? 'bg-white shadow-md border-2 border-purple-200' 
                      : 'bg-white hover:shadow-sm border border-gray-200'
                    }
                  `}
                >
                  <div className="flex items-start gap-2">
                    {overlay.type === 'concept' && <BookOpen className="w-4 h-4 text-blue-500 mt-0.5" />}
                    {overlay.type === 'definition' && <MessageSquare className="w-4 h-4 text-green-500 mt-0.5" />}
                    {overlay.type === 'connection' && <Link2 className="w-4 h-4 text-purple-500 mt-0.5" />}
                    {overlay.type === 'insight' && <Lightbulb className="w-4 h-4 text-yellow-500 mt-0.5" />}
                    
                    <div className="flex-1">
                      <p className="text-xs font-medium text-gray-500 uppercase">{overlay.title}</p>
                      <p className="text-sm mt-1">{overlay.content}</p>
                      
                      {overlay.relatedConcepts && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {overlay.relatedConcepts.map((concept, i) => (
                            <span key={i} className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                              {concept}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </aside>

          {/* Main Reading Area */}
          <main 
            className="flex-1 overflow-y-auto relative"
            onMouseUp={handleSelection}
          >
            <div className="max-w-3xl mx-auto py-8 px-8">
              <article 
                ref={contentRef}
                className="prose prose-lg max-w-none leading-relaxed"
              >
                {renderContent()}
              </article>
            </div>
          </main>

          {/* Right Sidebar - Highlights */}
          <aside className="w-64 border-l bg-gray-50 overflow-y-auto">
            <div className="p-4">
              <h3 className="font-medium mb-4">Highlights</h3>
              
              {savedHighlights?.map(highlight => (
                <div 
                  key={highlight.id}
                  className="mb-3 p-3 bg-white rounded-lg border border-gray-200 text-sm"
                >
                  <p className="line-clamp-3 italic text-gray-700">"{highlight.text}"</p>
                  {highlight.note && (
                    <p className="mt-2 text-xs text-gray-500">{highlight.note}</p>
                  )}
                </div>
              ))}
              
              {(!savedHighlights || savedHighlights.length === 0) && (
                <p className="text-sm text-gray-500 text-center py-8">
                  Select text to add highlights
                </p>
              )}
            </div>
          </aside>
        </div>
      </div>

      {/* Highlight Toolbar */}
      {showHighlightToolbar && selection && (
        <div 
          className="fixed z-50 bg-white rounded-lg shadow-lg border p-2 flex gap-1"
          style={{
            top: selection.rect.top - 50,
            left: selection.rect.left + selection.rect.width / 2 - 80,
          }}
        >
          {HighlightColors.map((color, idx) => (
            <button
              key={color.name}
              onClick={() => handleCreateHighlight(idx)}
              className={`w-8 h-8 rounded ${color.bg} border-2 ${color.border} hover:scale-110 transition-transform`}
              title={color.name}
            />
          ))}
          <div className="w-px bg-gray-200 mx-1" />
          <button 
            onClick={() => setShowHighlightToolbar(false)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Note Modal */}
      {activeNote && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl w-96 p-4">
            <h3 className="font-medium mb-3">Add Note</h3>
            <textarea
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              className="w-full h-24 p-3 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500"
              placeholder="Write your thoughts..."
            />
            <div className="flex justify-end gap-2 mt-3">
              <button 
                onClick={() => setActiveNote(null)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button 
                onClick={handleSaveNote}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
