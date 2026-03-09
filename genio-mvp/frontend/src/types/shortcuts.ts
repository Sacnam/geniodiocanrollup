"""
TypeScript types for keyboard shortcuts.
"""

export type ShortcutContext = 'global' | 'list' | 'reader' | 'navigation';

export interface ShortcutBinding {
  key: string;
  modifiers?: string[];
  then?: string;  // For chord shortcuts like 'g' then 'f'
  doubleTap?: boolean;
  description: string;
  enabled: boolean;
  context: ShortcutContext[];
}

export interface ShortcutCategory {
  [action: string]: ShortcutBinding;
}

export interface ShortcutsConfig {
  navigation: ShortcutCategory;
  actions: ShortcutCategory;
  reader: ShortcutCategory;
  application: ShortcutCategory;
}

export interface ShortcutConflict {
  category1: string;
  action1: string;
  category2: string;
  action2: string;
  conflictingKey: string;
}
