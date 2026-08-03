import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Camera, 
  History, 
  Building2, 
  Cpu, 
  CheckCircle2, 
  AlertCircle,
  Activity
} from 'lucide-react';
import { api } from '../api/client';

export const Navbar = () => {
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await api.getHealth();
        setBackendStatus('online');
      } catch (err) {
        setBackendStatus('offline');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/analyze', label: 'Analyze Classroom', icon: Camera },
    { to: '/history', label: 'Session Logs', icon: History },
    { to: '/institutions', label: 'Institutions', icon: Building2 },
  ];

  return (
    <header className="sticky top-0 z-50 glass-card border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-extrabold text-lg text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-indigo-300">
                Classroom AI
              </span>
              <span className="text-xs block text-slate-400 font-medium">
                Skill Quality Monitoring System
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-inner'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>

          {/* System Status Indicator */}
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${
              backendStatus === 'online' 
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                : backendStatus === 'checking'
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
            }`}>
              <span className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  backendStatus === 'online' ? 'bg-emerald-400' : 'bg-amber-400'
                }`}></span>
                <span className={`relative inline-flex rounded-full h-2 w-2 ${
                  backendStatus === 'online' ? 'bg-emerald-500' : 'bg-rose-500'
                }`}></span>
              </span>
              <span className="capitalize">{backendStatus === 'online' ? 'FastAPI Online' : backendStatus}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
