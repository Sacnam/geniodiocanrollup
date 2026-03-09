import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  Rss, 
  FileText, 
  BookOpen, 
  FlaskConical, 
  Settings, 
  LogOut,
  Menu,
  X,
  Bookmark,
  Telescope,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { NotificationBell } from './NotificationBell';

export const Navigation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navItems = [
    { path: '/feeds', label: 'Feeds', icon: Rss },
    { path: '/articles', label: 'Articles', icon: FileText },
    { path: '/brief', label: 'Daily Brief', icon: BookOpen },
    { path: '/library', label: 'Library', icon: BookOpen },
    { path: '/reading-list', label: 'Reading List', icon: Bookmark },
    { path: '/scout', label: 'Scout', icon: Telescope },
    { path: '/lab', label: 'Lab', icon: FlaskConical },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      {/* Mobile Header */}
      <header className="md:hidden fixed top-0 left-0 right-0 h-16 bg-white border-b z-50 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold">G</span>
          </div>
          <span className="font-bold text-lg">Genio</span>
        </div>
        <button 
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 hover:bg-gray-100 rounded-lg"
        >
          {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </header>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black/50 z-40 mt-16"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <nav className={`
        fixed md:fixed left-0 top-0 bottom-0 bg-white border-r z-50
        transition-all duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        ${isCollapsed ? 'md:w-20' : 'md:w-64'}
        w-64
      `}>
        {/* Desktop Logo */}
        <div className="hidden md:flex items-center justify-between h-16 px-4 border-b">
          <Link to="/feeds" className={`flex items-center gap-3 ${isCollapsed && 'justify-center w-full'}`}>
            <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">G</span>
            </div>
            {!isCollapsed && <span className="font-bold text-lg">Genio</span>}
          </Link>
          <div className="flex items-center gap-2">
            {!isCollapsed && <NotificationBell />}
            <button 
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="hidden md:block p-1 hover:bg-gray-100 rounded"
            >
              {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Close Button */}
        <div className="md:hidden flex justify-end p-4">
          <button onClick={() => setIsOpen(false)}>
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Nav Items */}
        <div className="py-4 px-3 space-y-1 overflow-y-auto h-[calc(100vh-8rem)]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors
                  ${isCollapsed && 'md:justify-center'}
                  ${isActive 
                    ? 'bg-purple-100 text-purple-700' 
                    : 'text-gray-600 hover:bg-gray-100'
                  }
                `}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {!isCollapsed && <span className="font-medium">{item.label}</span>}
              </Link>
            );
          })}
        </div>

        {/* Bottom Section */}
        <div className="absolute bottom-0 left-0 right-0 border-t bg-white p-3">
          <Link
            to="/settings"
            onClick={() => setIsOpen(false)}
            className={`
              flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 hover:bg-gray-100
              ${isCollapsed && 'md:justify-center'}
            `}
          >
            <Settings className="w-5 h-5" />
            {!isCollapsed && <span>Settings</span>}
          </Link>
          
          <button
            onClick={handleLogout}
            className={`
              w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-red-600 hover:bg-red-50 mt-1
              ${isCollapsed && 'md:justify-center'}
            `}
          >
            <LogOut className="w-5 h-5" />
            {!isCollapsed && <span>Logout</span>}
          </button>

          {/* User info */}
          {!isCollapsed && user && (
            <div className="mt-3 pt-3 border-t">
              <p className="px-3 text-sm text-gray-500 truncate">{user.email}</p>
            </div>
          )}
        </div>
      </nav>

      {/* Spacer for mobile header */}
      <div className="md:hidden h-16" />
    </>
  );
};
