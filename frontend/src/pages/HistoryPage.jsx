import React, { useState, useEffect } from 'react';
import { 
  History, 
  Search, 
  Filter, 
  FileText, 
  Calendar, 
  Building2, 
  CheckCircle2, 
  AlertTriangle,
  X,
  Eye
} from 'lucide-react';
import { api } from '../api/client';
import { ScoreGauge } from '../components/ScoreGauge';
import { QualityRadarChart } from '../components/QualityRadarChart';

export const HistoryPage = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterInst, setFilterInst] = useState('');
  const [institutions, setInstitutions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [sessionList, instList] = await Promise.all([
          api.getSessions({ limit: 100 }),
          api.getInstitutions(),
        ]);
        setSessions(sessionList);
        setInstitutions(instList);
      } catch (err) {
        console.error('Failed to load history:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleOpenDetails = async (sessionId) => {
    try {
      const details = await api.getSessionDetails(sessionId);
      setSelectedSession(details);
    } catch (err) {
      console.error('Failed to fetch session details:', err);
    }
  };

  const filteredSessions = sessions.filter((s) => {
    const matchesSearch = 
      s.session_id.toLowerCase().includes(search.toLowerCase()) ||
      s.course_name?.toLowerCase().includes(search.toLowerCase()) ||
      s.institution_name?.toLowerCase().includes(search.toLowerCase());
    
    const matchesInst = filterInst ? s.institution_name === filterInst : true;
    return matchesSearch && matchesInst;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Session History & Logs</h1>
          <p className="mt-1 text-slate-400 text-sm">
            Searchable log of all classroom quality evaluations
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-card rounded-xl p-4 border border-slate-800 flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Session ID, Course, or Institution..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={filterInst}
            onChange={(e) => setFilterInst(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 w-full sm:w-auto"
          >
            <option value="">All Institutions</option>
            {institutions.map((inst) => (
              <option key={inst} value={inst}>{inst}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Session ID</th>
                <th className="py-3.5 px-4">Institution</th>
                <th className="py-3.5 px-4">Course</th>
                <th className="py-3.5 px-4">Date</th>
                <th className="py-3.5 px-4">Trainer</th>
                <th className="py-3.5 px-4">Students</th>
                <th className="py-3.5 px-4">Quality Score</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredSessions.map((session) => (
                <tr key={session.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-xs text-indigo-300">{session.session_id}</td>
                  <td className="py-3.5 px-4 font-medium text-white">{session.institution_name}</td>
                  <td className="py-3.5 px-4 text-slate-400">{session.course_name}</td>
                  <td className="py-3.5 px-4 text-slate-400">{session.date}</td>
                  <td className="py-3.5 px-4">
                    <span className="capitalize text-xs bg-slate-900 px-2 py-1 rounded text-slate-300">
                      {session.trainer_status?.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">{session.student_count}</td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                      session.quality_score >= 80 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                        : session.quality_score >= 60 
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {session.quality_score} ({session.quality_label})
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => handleOpenDetails(session.session_id)}
                      className="p-1.5 rounded-lg bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600 hover:text-white transition-all"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredSessions.length === 0 && !loading && (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-slate-500">
                    No sessions match your search criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Session Details Modal */}
      {selectedSession && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-card rounded-2xl border border-slate-700 max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto space-y-6 relative">
            <button
              onClick={() => setSelectedSession(null)}
              className="absolute top-4 right-4 p-2 rounded-full bg-slate-800 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-indigo-400">{selectedSession.session_id}</span>
                <h3 className="text-xl font-black text-white">{selectedSession.institution_name}</h3>
                <p className="text-xs text-slate-400">{selectedSession.course_name} • {selectedSession.date}</p>
              </div>
              <ScoreGauge score={selectedSession.quality_score} size="sm" />
            </div>

            <div className="border-t border-slate-800 pt-4">
              <h4 className="text-sm font-bold text-white mb-2">Detailed Observations</h4>
              <p className="text-xs text-slate-300 bg-slate-900 p-3 rounded-lg font-mono">
                {selectedSession.raw_description || 'No raw text description.'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-400 block">Trainer Status</span>
                <span className="font-bold text-white capitalize">{selectedSession.trainer_status}</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-400 block">Attendance Rate</span>
                <span className="font-bold text-white">{selectedSession.attendance_percentage}% ({selectedSession.student_count} students)</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
