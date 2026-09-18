import React from 'react';
import { Cpu, ShieldCheck } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950/60 py-6 mt-12 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-400" />
          <span>Skill Development Training Program — Classroom Quality Monitoring System</span>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1 text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" /> Qwen2.5-VL & YOLO26 Vision Pipeline
          </span>
          <span>v1.0.0</span>
        </div>
      </div>
    </footer>
  );
};
