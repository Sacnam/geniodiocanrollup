"""
Unified settings panel integrating all features.
"""
import React, { useState } from 'react';
import {
  User, Bell, Shield, Keyboard, Palette, Database,
  Share2, CreditCard
} from 'lucide-react';
import { TagManager } from '../TagManager';
import { SavedViewManager } from '../SavedViewManager';
import { BriefTemplateManager } from '../BriefTemplateManager';
import { KeyboardShortcutsHelp } from '../KeyboardShortcutsHelp';

interface SettingsPanelProps {
  className?: string;
}

export function SettingsPanel({ className = '' }: SettingsPanelProps) {
  const [activeSection, setActiveSection] = useState('profile');
  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false);

  const sections = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'tags', label: 'Tags', icon: Database },
    { id: 'views', label: 'Saved Views', icon: Database },
    { id: 'briefs', label: 'Brief Templates', icon: Database },
    { id: 'shortcuts', label: 'Keyboard Shortcuts', icon: Keyboard },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security & 2FA', icon: Shield },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'integrations', label: 'Integrations', icon: Share2 },
  ];

  return (
    <div className={`flex gap-6 ${className}`}>
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0">
        <nav className="space-y-1">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                activeSection === section.id
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              }`}
            >
              <section.icon className="w-4 h-4" />
              {section.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="card">
          {activeSection === 'profile' && <ProfileSettings />}
          {activeSection === 'tags' && <TagManager mode="manager" />}
          {activeSection === 'views' && <SavedViewManager />}
          {activeSection === 'briefs' && <BriefTemplateManager />}
          {activeSection === 'shortcuts' && <ShortcutsSettings onShowHelp={() => setShowShortcutsHelp(true)} />}
          {activeSection === 'notifications' && <NotificationSettings />}
          {activeSection === 'security' && <SecuritySettings />}
          {activeSection === 'appearance' && <AppearanceSettings />}
          {activeSection === 'billing' && <BillingSettings />}
          {activeSection === 'integrations' && <IntegrationsSettings />}
        </div>
      </div>

      {/* Help Modal */}
      <KeyboardShortcutsHelp
        isOpen={showShortcutsHelp}
        onClose={() => setShowShortcutsHelp(false)}
      />
    </div>
  );
}

function ProfileSettings() {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Profile Settings</h2>
      
      <div className="space-y-4">
        <div>
          <label className="label">Display Name</label>
          <input type="text" className="input w-full" placeholder="Your name" />
        </div>
        
        <div>
          <label className="label">Email</label>
          <input type="email" className="input w-full" disabled />
          <p className="text-xs text-muted-foreground mt-1">
            Email cannot be changed
          </p>
        </div>
        
        <div>
          <label className="label">Bio</label>
          <textarea className="input w-full" rows={3} placeholder="Tell us about yourself" />
        </div>
        
        <div>
          <label className="label">Timezone</label>
          <select className="input w-full">
            <option>UTC</option>
            <option>America/New_York</option>
            <option>Europe/London</option>
            <option>Asia/Tokyo</option>
          </select>
        </div>
      </div>
      
      <div className="pt-4 border-t">
        <button className="btn btn-primary">Save Changes</button>
      </div>
    </div>
  );
}

function ShortcutsSettings({ onShowHelp }: { onShowHelp: () => void }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Keyboard Shortcuts</h2>
        <button onClick={onShowHelp} className="btn btn-secondary btn-sm">
          View Cheatsheet
        </button>
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
          <div>
            <div className="font-medium">Vim Mode</div>
            <div className="text-sm text-muted-foreground">
              Enable j/k navigation and Vim-style shortcuts
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" className="sr-only peer" defaultChecked />
            <div className="w-11 h-6 bg-muted rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>
      </div>
      
      <div className="text-sm text-muted-foreground">
        Press <kbd className="px-1 bg-muted rounded">?</kbd> anywhere to view shortcuts
      </div>
    </div>
  );
}

function NotificationSettings() {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Notification Preferences</h2>
      
      <div className="space-y-4">
        {[
          { id: 'daily_brief', label: 'Daily Brief', desc: 'Receive your daily brief email' },
          { id: 'mentions', label: 'Mentions', desc: 'When someone mentions you in comments' },
          { id: 'team_invites', label: 'Team Invites', desc: 'When you are invited to a team' },
          { id: 'digest', label: 'Weekly Digest', desc: 'Weekly summary of your reading' },
        ].map((item) => (
          <div key={item.id} className="flex items-start gap-3">
            <input
              type="checkbox"
              id={item.id}
              className="mt-1"
              defaultChecked={item.id !== 'digest'}
            />
            <div>
              <label htmlFor={item.id} className="font-medium cursor-pointer">
                {item.label}
              </label>
              <p className="text-sm text-muted-foreground">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SecuritySettings() {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Security</h2>
      
      <div className="p-4 bg-muted rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-medium">Password</h3>
            <p className="text-sm text-muted-foreground">Last changed 3 months ago</p>
          </div>
          <button className="btn btn-secondary btn-sm">Change Password</button>
        </div>
      </div>
      
      <div className="p-4 bg-muted rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-medium">Two-Factor Authentication</h3>
            <p className="text-sm text-muted-foreground">Add extra security to your account</p>
          </div>
          <span className="text-xs px-2 py-1 rounded bg-yellow-100 text-yellow-700">
            Not Enabled
          </span>
        </div>
        <button className="btn btn-primary btn-sm">Enable 2FA</button>
      </div>
    </div>
  );
}

function AppearanceSettings() {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Appearance</h2>
      
      <div>
        <label className="label">Theme</label>
        <div className="grid grid-cols-3 gap-2">
          {['Light', 'Dark', 'System'].map((theme) => (
            <button
              key={theme}
              className={`p-3 rounded-lg border text-center transition-colors ${
                theme === 'Dark' ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
              }`}
            >
              {theme}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function BillingSettings() {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Billing</h2>
      
      <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-muted-foreground">Current Plan</div>
            <div className="text-2xl font-bold">Professional</div>
          </div>
          <button className="btn btn-primary">Upgrade</button>
        </div>
      </div>
    </div>
  );
}

function IntegrationsSettings() {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Integrations</h2>
      
      <div className="space-y-3">
        {[
          { name: 'Slack', desc: 'Get notifications in Slack', connected: false },
          { name: 'Discord', desc: 'Share articles to Discord', connected: true },
        ].map((integration) => (
          <div
            key={integration.name}
            className="flex items-center justify-between p-3 bg-muted rounded-lg"
          >
            <div>
              <div className="font-medium">{integration.name}</div>
              <div className="text-sm text-muted-foreground">{integration.desc}</div>
            </div>
            {integration.connected ? (
              <button className="text-sm text-destructive hover:underline">
                Disconnect
              </button>
            ) : (
              <button className="btn btn-secondary btn-sm">Connect</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
