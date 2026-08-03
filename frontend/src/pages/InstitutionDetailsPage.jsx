import React, { useState, useEffect } from 'react';
import { Building2, Award, AlertTriangle, Layers, BarChart3 } from 'lucide-react';
import { api } from '../api/client';

export const InstitutionDetailsPage = () => {
  const [institutions, setInstitutions] = useState([]);
  const [selectedInst, setSelectedInst] = useState('');
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchInsts = async () => {
      try {
        const list = await api.getInstitutions();
        setInstitutions(list);
        if (list.length > 0) {
          setSelectedInst(list[0]);
        }
      } catch (err) {
        console.error('Failed to load institutions:', err);
      }
    };
    fetchInsts();
  }, []);

  useEffect(() => {
    if (!selectedInst) return;
    const fetchSummary = async () => {
      try {
        setLoading(true);
        const data = await api.getInstitutionSummary(selectedInst);
        setSummary(data);
      } catch (err) {
        console.error('Failed to fetch institution summary:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, [selectedInst]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Institution Insights</h1>
          <p className="mt-1 text-slate-400 text-sm">
            Aggregate quality analytics and compliance performance per training center
          </p>
        </div>

        {/* Institution Selector */}
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-indigo-400" />
          <select
            value={selectedInst}
            onChange={(e) => setSelectedInst(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 font-semibold"
          >
            {institutions.map((inst) => (
              <option key={inst} value={inst}>{inst}</option>
            ))}
          </select>
        </div>
      </div>

      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="glass-card rounded-xl p-5 border border-slate-800">
            <span className="text-xs font-semibold uppercase text-slate-400">Total Inspected Sessions</span>
            <div className="mt-3 text-3xl font-bold text-white">{summary.total_sessions}</div>
          </div>

          <div className="glass-card rounded-xl p-5 border border-slate-800">
            <span className="text-xs font-semibold uppercase text-slate-400">Avg Quality Score</span>
            <div className="mt-3 text-3xl font-bold text-indigo-400">{summary.avg_quality_score} / 100</div>
          </div>

          <div className="glass-card rounded-xl p-5 border border-slate-800">
            <span className="text-xs font-semibold uppercase text-slate-400">Excellent Sessions</span>
            <div className="mt-3 text-3xl font-bold text-emerald-400">{summary.excellent_count}</div>
          </div>

          <div className="glass-card rounded-xl p-5 border border-slate-800">
            <span className="text-xs font-semibold uppercase text-slate-400">Flagged Sessions</span>
            <div className="mt-3 text-3xl font-bold text-rose-400">{summary.needs_monitoring_count}</div>
          </div>
        </div>
      )}

      {!selectedInst && (
        <div className="glass-card rounded-2xl p-12 text-center text-slate-500 border border-slate-800">
          Select an institution from the dropdown above to view performance analytics.
        </div>
      )}
    </div>
  );
};
