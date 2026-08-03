import React from 'react';

export const ScoreGauge = ({ score = 0, label = 'Quality Score', size = 'md' }) => {
  const safeScore = typeof score === 'number' && !isNaN(score) ? score : (Number(score) || 0);

  // Determine color theme based on score
  const getBadgeColor = (val) => {
    if (val >= 90) return { text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', ring: '#10b981' };
    if (val >= 80) return { text: 'text-indigo-400', bg: 'bg-indigo-500/10', border: 'border-indigo-500/30', ring: '#6366f1' };
    if (val >= 70) return { text: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30', ring: '#3b82f6' };
    if (val >= 60) return { text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', ring: '#f59e0b' };
    return { text: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/30', ring: '#f43f5e' };
  };

  const theme = getBadgeColor(safeScore);
  const strokeDashoffset = 283 - (283 * Math.min(Math.max(safeScore, 0), 100)) / 100;

  return (
    <div className="flex flex-col items-center justify-center p-2">
      <div className="relative flex items-center justify-center w-28 h-28">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            className="stroke-slate-800"
            strokeWidth="8"
            fill="transparent"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke={theme.ring}
            strokeWidth="8"
            strokeDasharray="283"
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className={`text-2xl font-extrabold ${theme.text}`}>{safeScore.toFixed(1)}</span>
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">/ 100</span>
        </div>
      </div>
      {label && <span className="mt-2 text-xs font-semibold text-slate-300 text-center">{label}</span>}
    </div>
  );
};
