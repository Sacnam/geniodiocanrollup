"""
Premium E-Reader component with AI features.
"""
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ChevronLeft, ChevronRight, Type, Sun, Moon, BookOpen,
  Highlighter, MessageSquare, Share2, Headphones, Brain,
  MoreVertical, X, Plus, Play, Pause, SkipForward, Settings,
  Maximize, Minimize, Search, Bookmark, List, Zap
} from 'lucide-react';
import { ereaderApi } from '../../services/api/ereader';
import { aiApi } from '../../services/api/ai';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import './ereader.css';

interface EReaderProps {
  documentId: string;
  onClose?: () => void;
}

const THEMES = {
  light: { bg: '#ffffff', text: '#1a1a1a', sidebar: '#f8f9fa' },
  dark: { bg: '#1a1a1a', text: '#e5e5e5', sidebar: '#2d2d2d' },
  sepia: { bg: '#f4ecd8', text: '#5b4636', sidebar: '#e8dec3' },
};

const FONTS = [
  { id: 'system', name: 'System' },
  { id: 'serif', name: 'Serif' },
  { id: 'sans', name: 'Sans Serif' },
  { id: 'mono', name: 'Monospace' },
  { id: 'opendyslexic', name: 'OpenDyslexic' },
];

export function EReader({ documentId, onClose }: EReaderProps) {
  const queryClient = useQueryClient();
  const containerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const [userBookId, setUserBookId] = useState<string | null>(null);
  const [currentChapter, setCurrentChapter] = useState(0);
  const [showSidebar, setShowSidebar] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<'toc' | 'highlights' | 'notes' | 'ai'>('toc');
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Reader settings
  const [settings, setSettings] = useState({
    fontFamily: 'system',
    fontSize: 18,
    lineHeight: 1.6,
    margin: 40,
    theme: 'light' as 'light' | 'dark' | 'sepia',
    textAlign: 'justify' as 'left' | 'justify',
  });
  
  // TTS state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTTS, setCurrentTTS] = useState<string | null>(null);
  const [ttsSpeed, setTtsSpeed] = useState(1.0);
  
  // Selection state
  const [selection, setSelection] = useState<{
    text: string;
    position: { x: number; y: number };
  } | null>(null);
  
  // AI Assistant
  const [showAIAssist, setShowAIAssist] = useState(false);
  const [aiAction, setAiAction] = useState<string | null>(null);
  
  // Initialize book
  useEffect(() => {
    const initBook = async () => {
      const result = await ereaderApi.openBook(documentId);
      setUserBookId(result.user_book_id);
    };
    initBook();
  }, [documentId]);
  
  // Keyboard shortcuts
  useKeyboardShortcuts({
    context: 'reader',
    onShortcut: (action) => {
      switch (action) {
        case 'navigation.next_item':
          setCurrentChapter(c => c + 1);
          break;
        case 'navigation.prev_item':
          setCurrentChapter(c => Math.max(0, c - 1));
          break;
        case 'reader.close_reader':
          onClose?.();
          break;
      }
    },
  });
  
  // Text selection handler
  const handleSelection = useCallback(() => {
    const sel = window.getSelection();
    if (sel && sel.toString().trim()) {
      const text = sel.toString();
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      
      setSelection({
        text,
        position: { x: rect.left + rect.width / 2, y: rect.top - 50 },
      });
    } else {
      setSelection(null);
    }
  }, []);
  
  // TTS functions
  const playTTS = async (text: string) => {
    try {
      const result = await ereaderApi.generateTTS({
        text: text.slice(0, 4000),
        speed: ttsSpeed,
      });
      
      if (result.audio_url) {
        setCurrentTTS(result.audio_url);
        setIsPlaying(true);
        if (audioRef.current) {
          audioRef.current.src = result.audio_url;
          audioRef.current.play();
        }
      }
    } catch (e) {
      console.error('TTS failed:', e);
    }
  };
  
  // AI Assistant functions
  const runAIAssist = async (action: string) => {
    if (!selection?.text) return;
    
    setAiAction(action);
    setShowAIAssist(true);
    
    try {
      const result = await aiApi.studyAssist({
        book_id: userBookId!,
        action,
        context: selection.text,
      });
      
      setSidebarTab('ai');
      setShowSidebar(true);
    } catch (e) {
      console.error('AI assist failed:', e);
    } finally {
      setAiAction(null);
    }
  };
  
  const theme = THEMES[settings.theme];
  
  return (
    <div
      ref={containerRef}
      className="ereader-container"
      style={{ backgroundColor: theme.bg, color: theme.text }}
      onMouseUp={handleSelection}
    >
      {/* Header Toolbar */}
      <header className="ereader-header" style={{ backgroundColor: theme.sidebar }}>
        <div className="flex items-center gap-4">
          <button onClick={onClose} className="p-2 rounded hover:bg-black/10">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <span className="font-medium">Book Title</span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => isPlaying ? setIsPlaying(false) : playTTS('Sample text')}
            className={`p-2 rounded flex items-center gap-2 ${isPlaying ? 'bg-primary text-white' : 'hover:bg-black/10'}`}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Headphones className="w-4 h-4" />}
          </button>
          
          <button onClick={() => setShowSidebar(!showSidebar)} className="p-2 rounded hover:bg-black/10">
            <List className="w-5 h-5" />
          </button>
          
          <SettingsMenu settings={settings} onChange={setSettings} />
        </div>
      </header>
      
      {/* Main Content */}
      <div className="ereader-main">
        {showSidebar && (
          <aside className="ereader-sidebar" style={{ backgroundColor: theme.sidebar }}>
            <div className="flex border-b">
              {(['toc', 'highlights', 'notes', 'ai'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setSidebarTab(tab)}
                  className={`flex-1 py-3 text-sm capitalize ${sidebarTab === tab ? 'border-b-2 border-primary font-medium' : ''}`}
                >
                  {tab}
                </button>
              ))}
            </div>
            <div className="p-4">
              {sidebarTab === 'ai' && <AIPanel action={aiAction} />}
            </div>
          </aside>
        )}
        
        <main
          className="ereader-content"
          style={{
            fontFamily: settings.fontFamily,
            fontSize: settings.fontSize,
            lineHeight: settings.lineHeight,
            padding: `40px ${settings.margin}px`,
          }}
        >
          <p>Book content goes here...</p>
        </main>
      </div>
      
      {/* Selection Toolbar */}
      {selection && (
        <div
          className="selection-toolbar"
          style={{
            position: 'fixed',
            left: selection.position.x,
            top: selection.position.y,
            transform: 'translateX(-50%)',
          }}
        >
          <div className="bg-popover border rounded-lg shadow-lg p-2 flex gap-1">
            {['#fef08a', '#bbf7d0', '#bfdbfe', '#fbcfe8'].map((color) => (
              <button
                key={color}
                className="w-8 h-8 rounded border-2"
                style={{ backgroundColor: color }}
              />
            ))}
            <button onClick={() => runAIAssist('explain_concept')} className="p-2">
              <Brain className="w-4 h-4" />
            </button>
            <button onClick={() => playTTS(selection.text)} className="p-2">
              <Headphones className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
      
      <audio ref={audioRef} onEnded={() => setIsPlaying(false)} />
    </div>
  );
}

function SettingsMenu({ settings, onChange }: { settings: any; onChange: (s: any) => void }) {
  const [isOpen, setIsOpen] = useState(false);
  
  if (!isOpen) {
    return (
      <button onClick={() => setIsOpen(true)} className="p-2 rounded hover:bg-black/10">
        <Type className="w-5 h-5" />
      </button>
    );
  }
  
  return (
    <div className="relative">
      <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
      <div className="absolute right-0 top-full mt-2 w-72 bg-popover border rounded-lg shadow-lg p-4 z-50">
        <h3 className="font-medium mb-3">Reader Settings</h3>
        
        <div className="mb-4">
          <label className="text-sm">Font Size: {settings.fontSize}px</label>
          <input
            type="range"
            min={12}
            max={32}
            value={settings.fontSize}
            onChange={(e) => onChange({ ...settings, fontSize: parseInt(e.target.value) })}
            className="w-full"
          />
        </div>
        
        <div className="mb-4">
          <label className="text-sm">Theme</label>
          <div className="flex gap-2 mt-1">
            {(['light', 'sepia', 'dark'] as const).map((theme) => (
              <button
                key={theme}
                onClick={() => onChange({ ...settings, theme })}
                className={`flex-1 py-2 rounded capitalize ${settings.theme === theme ? 'bg-primary text-white' : 'bg-muted'}`}
              >
                {theme}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function AIPanel({ action }: { action: string | null }) {
  return (
    <div className="space-y-3">
      {action ? (
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          Processing...
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2">
            <button className="p-3 bg-muted rounded text-sm">
              <Brain className="w-4 h-4 mx-auto mb-1" />
              Explain
            </button>
            <button className="p-3 bg-muted rounded text-sm">
              <Zap className="w-4 h-4 mx-auto mb-1" />
              Quiz Me
            </button>
          </div>
        </>
      )}
    </div>
  );
}
