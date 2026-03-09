"""
Keyboard shortcuts help modal and cheatsheet.
"""
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, Keyboard, Search, Command } from 'lucide-react';
import { shortcutApi } from '../services/api/shortcuts';

interface KeyboardShortcutsHelpProps {
  isOpen: boolean;
  onClose: () => void;
}

export function KeyboardShortcutsHelp({ isOpen, onClose }: KeyboardShortcutsHelpProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const { data: cheatsheet, isLoading } = useQuery({
    queryKey: ['shortcuts', 'cheatsheet'],
    queryFn: () => shortcutApi.getCheatsheet(),
    enabled: isOpen,
  });
  
  if (!isOpen) return null;
  
  // Filter shortcuts based on search
  const filteredCheatsheet = cheatsheet?.map(section => ({
    ...section,
    shortcuts: section.shortcuts.filter(s =>
      s.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.key.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(section => section.shortcuts.length > 0);
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-background rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Keyboard className="w-5 h-5" />
            <h2 className="text-lg font-semibold">Keyboard Shortcuts</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Search */}
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search shortcuts..."
              className="input w-full pl-9"
              autoFocus
            />
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading shortcuts...
            </div>
          ) : filteredCheatsheet?.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No shortcuts found
            </div>
          ) : (
            <div className="space-y-6">
              {filteredCheatsheet?.map((section) => (
                <div key={section.category}>
                  <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    {formatCategoryName(section.category)}
                  </h3>
                  <div className="space-y-2">
                    {section.shortcuts.map((shortcut) => (
                      <div
                        key={shortcut.action}
                        className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50"
                      >
                        <span className="text-sm">{shortcut.description}</span>
                        <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono">
                          {formatKey(shortcut.key)}
                        </kbd>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t text-center text-sm text-muted-foreground">
          Press <kbd className="px-1 py-0.5 bg-muted rounded">?</kbd> to open this help anytime
        </div>
      </div>
    </div>
  );
}

function formatCategoryName(category: string): string {
  return category.charAt(0).toUpperCase() + category.slice(1);
}

function formatKey(key: string): string {
  // Format for display
  return key
    .replace('ctrl', 'Ctrl')
    .replace('shift', 'Shift')
    .replace('alt', 'Alt')
    .replace('meta', 'Cmd')
    .replace('ArrowUp', '↑')
    .replace('ArrowDown', '↓')
    .replace('ArrowLeft', '←')
    .replace('ArrowRight', '→')
    .replace('Enter', '↵');
}
