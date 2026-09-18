import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Activity, 
  Award, 
  AlertTriangle, 
  CheckCircle2, 
  Users, 
  Building2, 
  ArrowUpRight,
  TrendingUp,
  Camera,
  Layers,
  X,
  ExternalLink,
  Info
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { api } from '../api/client';
import { QualityRadarChart } from '../components/QualityRadarChart';
import { ScoreGauge } from '../components/ScoreGauge';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export const DashboardPage = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const data = await api.getSessions({ limit: 50 });
        setSessions(data);
      } catch (err) {
        console.error('Failed to load sessions:', err);
        setError('Could not connect to FastAPI backend. Please make sure uvicorn server is running on port 8000.');
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  // Compute metrics
  const totalSessions = sessions.length;
  const avgScore = totalSessions > 0 
    ? (sessions.reduce((acc, s) => acc + (s.quality_score || 0), 0) / totalSessions).toFixed(1)
    : 0;
  const excellentSessionsList = sessions.filter(s => (s.quality_score || 0) >= 90);
  const excellentSessions = excellentSessionsList.length;
  const needsMonitoringList = sessions.filter(s => (s.quality_score || 0) < 60);
  const needsMonitoring = needsMonitoringList.length;

  // Filter sessions for Modal based on clicked card
  const getFilteredSessions = () => {
    if (selectedFilter === 'excellent') return excellentSessionsList;
    if (selectedFilter === 'needs_monitoring') return needsMonitoringList;
    if (selectedFilter === 'avg') return [...sessions].sort((a, b) => b.quality_score - a.quality_score);
    return sessions;
  };

  const getModalTitle = () => {
    if (selectedFilter === 'excellent') return { title: 'Excellent Training Sessions (Score ≥ 90)', badge: 'High Performing', color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' };
    if (selectedFilter === 'needs_monitoring') return { title: 'Flagged Sessions - Needs Monitoring (Score < 60)', badge: 'Requires Inspection', color: 'text-rose-400 border-rose-500/30 bg-rose-500/10' };
    if (selectedFilter === 'avg') return { title: 'All Sessions Ranked by Quality Score', badge: `Avg QS: ${avgScore}`, color: 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10' };
    return { title: 'Total Analyzed Sessions Overview', badge: `${totalSessions} Sessions`, color: 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10' };
  };

  // Prepare Trend Data for Recharts Area Chart
  const trendData = [...sessions]
    .reverse()
    .slice(0, 10)
    .map((s, idx) => {
      const shortInst = (s.institution_name || 'NSTI').split(' ')[0];
      return {
        name: `S#${idx + 1}`,
        fullName: `${shortInst} (Session #${idx + 1})`,
        score: s.quality_score,
        institution: s.institution_name,
        course: s.course_name,
        date: s.date,
        label: s.quality_label,
      };
    });

  // Average radar breakdown mock/aggregate
  const avgBreakdown = {
    trainer_presence: 90,
    student_engagement: 82,
    classroom_activity: 85,
    infrastructure: 75,
    attendance: 88,
    curriculum_compliance: 80,
  };

  return (
    <div className="space-y-8">
      {/* Top Banner Header */}
      <div className="glass-card rounded-2xl p-6 sm:p-8 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 relative overflow-hidden">
        <div className="absolute -right-12 -top-12 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-3">
              <Activity className="w-3.5 h-3.5" /> AI Quality Analytics
            </div>
            <h1 className="text-3xl font-black text-white tracking-tight sm:text-4xl">
              Classroom Monitoring Dashboard
            </h1>
            <p className="mt-2 text-slate-400 max-w-2xl text-sm sm:text-base">
              Automated computer vision quality assessment for Skill Development Training Centers using YOLO26 & Qwen-2.5VL AI models.
            </p>
          </div>
          <Link
            to="/analyze"
            className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02] active:scale-95"
          >
            <Camera className="w-5 h-5" /> Analyze Classroom Image
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Interactive Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div 
          onClick={() => setSelectedFilter('all')}
          className="glass-card glass-card-hover rounded-xl p-5 border border-slate-800 cursor-pointer hover:border-indigo-500/50 hover:scale-[1.02] transition-all group relative"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-indigo-300 transition-colors">Total Analyzed Sessions</span>
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center group-hover:bg-indigo-500 group-hover:text-white transition-all">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white">{totalSessions}</span>
              <span className="text-xs text-slate-400">sessions</span>
            </div>
            <span className="text-[11px] text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity font-semibold flex items-center gap-1">
              View details <ArrowUpRight className="w-3 h-3" />
            </span>
          </div>
        </div>

        <div 
          onClick={() => setSelectedFilter('avg')}
          className="glass-card glass-card-hover rounded-xl p-5 border border-slate-800 cursor-pointer hover:border-emerald-500/50 hover:scale-[1.02] transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-emerald-300 transition-colors">Avg Quality Score</span>
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center group-hover:bg-emerald-500 group-hover:text-white transition-all">
              <Award className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white">{avgScore}</span>
              <span className="text-xs text-slate-400">/ 100</span>
            </div>
            <span className="text-[11px] text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity font-semibold flex items-center gap-1">
              View ranking <ArrowUpRight className="w-3 h-3" />
            </span>
          </div>
        </div>

        <div 
          onClick={() => setSelectedFilter('excellent')}
          className="glass-card glass-card-hover rounded-xl p-5 border border-slate-800 cursor-pointer hover:border-emerald-500/50 hover:scale-[1.02] transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-emerald-300 transition-colors">Excellent Training (≥90)</span>
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center group-hover:bg-emerald-500 group-hover:text-white transition-all">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-emerald-400">{excellentSessions}</span>
              <span className="text-xs text-slate-400">sessions</span>
            </div>
            <span className="text-[11px] text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity font-semibold flex items-center gap-1">
              View list <ArrowUpRight className="w-3 h-3" />
            </span>
          </div>
        </div>

        <div 
          onClick={() => setSelectedFilter('needs_monitoring')}
          className="glass-card glass-card-hover rounded-xl p-5 border border-slate-800 cursor-pointer hover:border-rose-500/50 hover:scale-[1.02] transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-rose-300 transition-colors">Needs Monitoring (&lt;60)</span>
            <div className="w-10 h-10 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center group-hover:bg-rose-500 group-hover:text-white transition-all">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-rose-400">{needsMonitoring}</span>
              <span className="text-xs text-slate-400">flagged</span>
            </div>
            <span className="text-[11px] text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity font-semibold flex items-center gap-1">
              Inspect flagged <ArrowUpRight className="w-3 h-3" />
            </span>
          </div>
        </div>
      </div>

      {/* Grid: Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quality Score Dimensions Breakdown Card */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800 lg:col-span-1 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Quality Score Dimensions</h3>
            <p className="text-xs text-slate-400 mb-4">6-Factor Quality Assessment Breakdown</p>
            <QualityRadarChart scoreBreakdown={avgBreakdown} />
          </div>
          <div className="text-xs text-slate-400 border-t border-slate-800/80 pt-3 mt-3 text-center font-medium leading-relaxed">
            Score Weights: Trainer (25%) • Engagement (20%) • Activity (20%) • Attendance (15%) • Equipment (10%) • Curriculum (10%)
          </div>
        </div>

        {/* Historical Quality Score Trend Area Chart */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-white">Quality Score History</h3>
              <p className="text-xs text-slate-400">Session Performance Trend Over Time</p>
            </div>
            <TrendingUp className="w-5 h-5 text-indigo-400" />
          </div>

          <div className="h-72 w-full">
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                    formatter={(val, name, props) => [`${val} pts (${props.payload?.label || 'Evaluated'})`, 'Score']}
                    labelFormatter={(label, items) => {
                      const item = items && items[0] ? items[0].payload : null;
                      return item ? `${item.fullName || label} • ${item.institution || ''}` : label;
                    }}
                  />
                  <Area type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorScore)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                No session data recorded yet. Upload a classroom image to see analytics!
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Sessions Table */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-bold text-white">Recent Classroom Analyses</h3>
            <p className="text-xs text-slate-400">Latest automated inspection results</p>
          </div>
          <Link to="/history" className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
            View All <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Session ID</th>
                <th className="py-3 px-4">Institution</th>
                <th className="py-3 px-4">Course</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Trainer Status</th>
                <th className="py-3 px-4">Students</th>
                <th className="py-3 px-4 text-right">Quality Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {sessions.slice(0, 5).map((session) => (
                <tr key={session.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-xs text-indigo-300">{session.session_id}</td>
                  <td className="py-3.5 px-4 font-medium text-white">{session.institution_name}</td>
                  <td className="py-3.5 px-4 text-slate-400">{session.course_name}</td>
                  <td className="py-3.5 px-4 text-slate-400">{session.date}</td>
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-200 capitalize">
                      {session.trainer_status?.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">{session.student_count}</td>
                  <td className="py-3.5 px-4 text-right font-bold">
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
                </tr>
              ))}
              {sessions.length === 0 && !loading && (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-slate-500">
                    No sessions analyzed yet. Click "Analyze Classroom Image" above to test the system!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Metric Filter Details Modal */}
      {selectedFilter && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
          <div className="glass-card rounded-2xl w-full max-w-4xl max-h-[85vh] border border-slate-700 bg-slate-900 shadow-2xl flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
              <div>
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-bold text-white">{getModalTitle().title}</h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getModalTitle().color}`}>
                    {getModalTitle().badge}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Showing {getFilteredSessions().length} matching session records with college/institution details
                </p>
              </div>
              <button
                onClick={() => setSelectedFilter(null)}
                className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body Table */}
            <div className="p-6 overflow-y-auto flex-grow space-y-3">
              {getFilteredSessions().length > 0 ? (
                <div className="grid grid-cols-1 gap-3">
                  {getFilteredSessions().map((session) => (
                    <div 
                      key={session.id || session.session_id} 
                      className="glass-card rounded-xl p-4 border border-slate-800 hover:border-indigo-500/40 bg-slate-950/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                          <span className="font-bold text-white text-base">{session.institution_name}</span>
                          <span className="text-xs font-mono text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                            {session.session_id}
                          </span>
                        </div>
                        <div className="text-xs text-slate-300 font-semibold flex items-center gap-2">
                          <span>Course: <strong className="text-white">{session.course_name}</strong></span>
                          <span>•</span>
                          <span className="text-slate-400">{session.date}</span>
                        </div>
                        <div className="text-xs text-slate-400 flex items-center gap-3 pt-1">
                          <span>Trainer: <strong className="text-slate-200 capitalize">{session.trainer_status?.replace('_', ' ')}</strong></span>
                          <span>•</span>
                          <span>Students: <strong className="text-slate-200">{session.student_count}</strong></span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 justify-between sm:justify-end border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-800">
                        <div className="text-right">
                          <div className={`text-lg font-black ${
                            session.quality_score >= 80 ? 'text-emerald-400' : session.quality_score >= 60 ? 'text-amber-400' : 'text-rose-400'
                          }`}>
                            {session.quality_score} <span className="text-xs font-normal text-slate-400">/ 100</span>
                          </div>
                          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                            {session.quality_label}
                          </div>
                        </div>

                        <button
                          onClick={() => {
                            setSelectedFilter(null);
                            navigate('/history');
                          }}
                          className="px-3.5 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-bold flex items-center gap-1.5 transition-all"
                        >
                          <span>Inspect</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400 text-sm glass-card rounded-xl p-8 border border-slate-800">
                  <Info className="w-8 h-8 text-indigo-400 mx-auto mb-2 opacity-60" />
                  <p>No sessions match the selected filter category.</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex justify-end">
              <button
                onClick={() => setSelectedFilter(null)}
                className="px-5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
