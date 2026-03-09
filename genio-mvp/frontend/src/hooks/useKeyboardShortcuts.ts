"""
Keyboard shortcuts hook with Vim-style navigation.
"""
import { useEffect, useRef, useCallback, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { shortcutApi } from '../services/api/shortcuts';
import type { ShortcutsConfig, ShortcutContext } from '../types/shortcuts';

interface UseKeyboardShortcutsOptions {
  context?: ShortcutContext;
  enabled?: boolean;
  onShortcut?: (action: string, event: KeyboardEvent) => void;
}

export function useKeyboardShortcuts(options: UseKeyboardShortcutsOptions = {}) {
  const { context = 'global', enabled = true, onShortcut } = options;
  const queryClient = useQueryClient();
  
  // Track chord sequences (e.g., 'g' then 'f')
  const chordBuffer = useRef<string[]>([]);
  const chordTimeout = useRef<NodeJS.Timeout | null>(null);
  const lastKeyTime = useRef<number>(0);
  
  // Fetch shortcuts config
  const { data: shortcuts } = useQuery({
    queryKey: ['shortcuts'],
    queryFn: () => shortcutApi.getAll(),
    staleTime: Infinity,
  });
  
  // Toggle Vim mode
  const [vimModeEnabled, setVimModeEnabled] = useState(true);
  
  const toggleVimMode = useMutation({
    mutationFn: (enabled: boolean) => shortcutApi.toggleVimMode(enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shortcuts'] });
    },
  });
  
  // Check if shortcut matches current context
  const matchesContext = useCallback((shortcutContext: string[]) => {
    return shortcutContext.includes('global') || shortcutContext.includes(context);
  }, [context]);
  
  // Execute shortcut action
  const executeShortcut = useCallback((category: string, action: string, event: KeyboardEvent) => {
    if (onShortcut) {
      onShortcut(`${category}.${action}`, event);
    }
    
    // Emit custom event for components to listen
    window.dispatchEvent(new CustomEvent('keyboard-shortcut', {
      detail: { category, action, context }
    }));
  }, [onShortcut, context]);
  
  // Process keyboard event
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled || !vimModeEnabled || !shortcuts) return;
    
    // Don't trigger shortcuts when typing in inputs
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.contentEditable === 'true' ||
      target.closest('[data-keyboard-shortcuts="disabled"]')
    ) {
      return;
    }
    
    const now = Date.now();
    const key = event.key;
    const modifiers: string[] = [];
    
    if (event.ctrlKey) modifiers.push('ctrl');
    if (event.altKey) modifiers.push('alt');
    if (event.shiftKey) modifiers.push('shift');
    if (event.metaKey) modifiers.push('meta');
    
    // Clear chord buffer if too much time passed
    if (now - lastKeyTime.current > 1000) {
      chordBuffer.current = [];
    }
    lastKeyTime.current = now;
    
    // Check for chord shortcuts
    const chordKey = chordBuffer.current.join(',');
    
    // Search through all shortcuts
    for (const [category, actions] of Object.entries(shortcuts)) {
      for (const [action, binding] of Object.entries(actions)) {
        if (!binding.enabled) continue;
        if (!matchesContext(binding.context)) continue;
        
        // Check for chord sequence
        if (binding.then) {
          if (chordBuffer.current.length === 1 && chordBuffer.current[0] === binding.key && key === binding.then) {
            event.preventDefault();
            chordBuffer.current = [];
            executeShortcut(category, action, event);
            return;
          }
          
          // First part of chord
          if (key === binding.key && !binding.modifiers?.length) {
            chordBuffer.current = [key];
            if (chordTimeout.current) clearTimeout(chordTimeout.current);
            chordTimeout.current = setTimeout(() => {
              chordBuffer.current = [];
            }, 1000);
            return;
          }
        }
        
        // Check double-tap (e.g., 'gg' for go to top)
        if (binding.doubleTap) {
          const recentBuffer = chordBuffer.current.slice(-1);
          if (recentBuffer[0] === binding.key && key === binding.key) {
            event.preventDefault();
            chordBuffer.current = [];
            executeShortcut(category, action, event);
            return;
          }
          
          chordBuffer.current.push(key);
          return;
        }
        
        // Check regular shortcut
        const bindingModifiers = binding.modifiers || [];
        const modifiersMatch = 
          modifiers.length === bindingModifiers.length &&
          modifiers.every(m => bindingModifiers.includes(m));
        
        if (binding.key === key && modifiersMatch) {
          event.preventDefault();
          executeShortcut(category, action, event);
          return;
        }
      }
    }
    
    // Add to chord buffer for single keys
    if (key.length === 1 && !modifiers.length) {
      chordBuffer.current.push(key);
      if (chordBuffer.current.length > 5) {
        chordBuffer.current = chordBuffer.current.slice(-5);
      }
    }
  }, [enabled, vimModeEnabled, shortcuts, matchesContext, executeShortcut]);
  
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      if (chordTimeout.current) clearTimeout(chordTimeout.current);
    };
  }, [handleKeyDown]);
  
  return {
    shortcuts,
    vimModeEnabled,
    setVimModeEnabled: (enabled: boolean) => {
      setVimModeEnabled(enabled);
      toggleVimMode.mutate(enabled);
    },
    isLoading: !shortcuts,
  };
}

// Hook for listening to specific shortcuts
export function useShortcut(action: string, handler: () => void, deps: any[] = []) {
  useEffect(() => {
    const [category, actionName] = action.split('.');
    
    const handleShortcut = (event: CustomEvent) => {
      const detail = event.detail;
      if (detail.category === category && detail.action === actionName) {
        handler();
      }
    };
    
    window.addEventListener('keyboard-shortcut', handleShortcut as EventListener);
    return () => {
      window.removeEventListener('keyboard-shortcut', handleShortcut as EventListener);
    };
  }, [action, ...deps]);
}

// Hook for list navigation (j/k)
export function useListNavigation(
  itemCount: number,
  options: { onSelect?: (index: number) => void; onAction?: (action: string) => void } = {}
) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const { onSelect, onAction } = options;
  
  useEffect(() => {
    const handleShortcut = (event: CustomEvent) => {
      const { category, action } = event.detail;
      
      if (category !== 'navigation' && category !== 'actions') return;
      
      switch (action) {
        case 'next_item':
          setSelectedIndex(prev => {
            const next = Math.min(itemCount - 1, prev + 1);
            onSelect?.(next);
            return next;
          });
          break;
        case 'prev_item':
          setSelectedIndex(prev => {
            const next = Math.max(0, prev - 1);
            onSelect?.(next);
            return next;
          });
          break;
        case 'go_to_top':
          setSelectedIndex(0);
          onSelect?.(0);
          break;
        case 'go_to_bottom':
          setSelectedIndex(itemCount - 1);
          onSelect?.(itemCount - 1);
          break;
        case 'open_reader':
        case 'mark_read':
        case 'mark_favorite':
        case 'archive':
          onAction?.(action);
          break;
      }
    };
    
    window.addEventListener('keyboard-shortcut', handleShortcut as EventListener);
    return () => {
      window.removeEventListener('keyboard-shortcut', handleShortcut as EventListener);
    };
  }, [itemCount, onSelect, onAction]);
  
  return { selectedIndex, setSelectedIndex };
}
