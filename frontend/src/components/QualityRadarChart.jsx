import React, { useState } from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { UserCheck, Users, Activity, Monitor, CalendarCheck, BookOpen, Table as TableIcon, PieChart as PieIcon, BarChart2 } from 'lucide-react';

const PIE_COLORS = ['#10b981', '#6366f1', '#8b5cf6', '#3b82f6', '#f59e0b', '#0ea5e9'];

export const QualityRadarChart = ({ scoreBreakdown = {} }) => {
  const [viewType, setViewType] = useState('table'); // 'table' | 'pie' | 'bars'
  const sb = scoreBreakdown && typeof scoreBreakdown === 'object' ? scoreBreakdown : {};

  const dimensions = [
    { 
      key: 'trainer_presence', 
      label: 'Trainer Presence', 
      weight: '25%', 
      score: Number(sb.trainer_presence) || 0, 
      icon: UserCheck,
      color: 'bg-emerald-500',
      hex: '#10b981',
      text: 'text-emerald-400'
    },
    { 
      key: 'student_engagement', 
      label: 'Student Engagement', 
      weight: '20%', 
      score: Number(sb.student_engagement) || 0, 
      icon: Users,
      color: 'bg-indigo-500',
      hex: '#6366f1',
      text: 'text-indigo-400'
    },
    { 
      key: 'classroom_activity', 
      label: 'Classroom Activity', 
      weight: '20%', 
      score: Number(sb.classroom_activity) || 0, 
      icon: Activity,
      color: 'bg-violet-500',
      hex: '#8b5cf6',
      text: 'text-violet-400'
    },
    { 
      key: 'attendance', 
      label: 'Student Attendance', 
      weight: '15%', 
      score: Number(sb.attendance) || 0, 
      icon: CalendarCheck,
      color: 'bg-blue-500',
      hex: '#3b82f6',
      text: 'text-blue-400'
    },
    { 
      key: 'infrastructure', 
      label: 'Infrastructure Equipment', 
      weight: '10%', 
      score: Number(sb.infrastructure) || 0, 
      icon: Monitor,
      color: 'bg-amber-500',
      hex: '#f59e0b',
      text: 'text-amber-400'
    },
    { 
      key: 'curriculum_compliance', 
      label: 'Curriculum Match', 
      weight: '10%', 
      score: Number(sb.curriculum_compliance) || 0, 
      icon: BookOpen,
      color: 'bg-sky-500',
      hex: '#0ea5e9',
      text: 'text-sky-400'
    },
  ];

  const getStatusBadge = (val) => {
    if (val >= 90) return { label: 'Excellent', style: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
    if (val >= 75) return { label: 'Good', style: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' };
    if (val >= 60) return { label: 'Average', style: 'bg-amber-500/10 text-amber-400 border-amber-500/30' };
    return { label: 'Low', style: 'bg-rose-500/10 text-rose-400 border-rose-500/30' };
  };

  const pieData = dimensions.map(d => ({
    name: d.label,
    value: Math.round(d.score),
    weight: d.weight,
    color: d.hex
  }));

  return (
    <div className="space-y-4">
      {/* View Switcher Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800">
        <span className="text-xs font-semibold text-slate-400">View Format:</span>
        <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setViewType('table')}
            className={`px-3 py-1 rounded-md font-bold flex items-center gap-1.5 transition-all ${
              viewType === 'table' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <TableIcon className="w-3.5 h-3.5" /> Table View
          </button>
          <button
            onClick={() => setViewType('pie')}
            className={`px-3 py-1 rounded-md font-bold flex items-center gap-1.5 transition-all ${
              viewType === 'pie' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <PieIcon className="w-3.5 h-3.5" /> Pie Chart
          </button>
          <button
            onClick={() => setViewType('bars')}
            className={`px-3 py-1 rounded-md font-bold flex items-center gap-1.5 transition-all ${
              viewType === 'bars' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" /> Progress Bars
          </button>
        </div>
      </div>

      {/* View Mode 1: Table Format (DEFAULT) */}
      {viewType === 'table' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Quality Dimension</th>
                <th className="py-2.5 px-3">Weight</th>
                <th className="py-2.5 px-3">Score & Progress</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {dimensions.map((item) => {
                const Icon = item.icon;
                const badge = getStatusBadge(item.score);
                return (
                  <tr key={item.key} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className={`p-1 rounded bg-slate-800 ${item.text}`}>
                          <Icon className="w-3.5 h-3.5" />
                        </div>
                        <span className="font-semibold text-white">{item.label}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400">{item.weight}</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-3">
                        <div className="w-24 sm:w-32 h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                          <div 
                            className={`h-full ${item.color} rounded-full`} 
                            style={{ width: `${Math.min(Math.max(item.score, 0), 100)}%` }}
                          ></div>
                        </div>
                        <span className="font-bold font-mono text-white text-xs">{Math.round(item.score)}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold border inline-block ${badge.style}`}>
                        {badge.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* View Mode 2: Pie / Donut Chart View */}
      {viewType === 'pie' && (
        <div className="w-full flex flex-col items-center justify-center py-2">
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                  formatter={(val, name, props) => [`${val}% (Weight: ${props.payload?.weight})`, name]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Pie Chart Legend */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 w-full pt-2 text-xs">
            {dimensions.map((item) => (
              <div key={item.key} className="flex items-center gap-2 p-1.5 rounded bg-slate-900/60 border border-slate-800">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: item.hex }}></span>
                <span className="text-slate-300 text-[11px] truncate">{item.label}</span>
                <span className="font-mono text-white text-[11px] font-bold ml-auto">{Math.round(item.score)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View Mode 3: Simple Progress Bars */}
      {viewType === 'bars' && (
        <div className="space-y-3.5 py-1">
          {dimensions.map((item) => {
            const Icon = item.icon;
            const badge = getStatusBadge(item.score);
            return (
              <div key={item.key} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className={`p-1 rounded bg-slate-800 ${item.text}`}>
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="font-semibold text-slate-200">{item.label}</span>
                    <span className="text-[10px] text-slate-500 font-mono">({item.weight})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${badge.style}`}>
                      {badge.label}
                    </span>
                    <span className="font-bold text-white font-mono w-10 text-right">
                      {Math.round(item.score)}%
                    </span>
                  </div>
                </div>

                <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800/80">
                  <div 
                    className={`h-full ${item.color} rounded-full transition-all duration-700 ease-out`}
                    style={{ width: `${Math.min(Math.max(item.score, 0), 100)}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
