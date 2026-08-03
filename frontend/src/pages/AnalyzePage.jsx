import React, { useState } from 'react';
import { 
  Upload, 
  Camera, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  FileText, 
  Sparkles, 
  Layers, 
  Users, 
  Monitor, 
  BookOpen, 
  ShieldAlert,
  Zap
} from 'lucide-react';
import { api } from '../api/client';
import { QualityRadarChart } from '../components/QualityRadarChart';
import { ScoreGauge } from '../components/ScoreGauge';
import { ErrorBoundary } from '../components/ErrorBoundary';

import { useAnalysis } from '../context/AnalysisContext';

const DEFAULT_INFRASTRUCTURE = [
  'whiteboard',
  'projector',
  'computer',
  'smartboard',
  'benches_tables',
  'chart_papers',
];

export const AnalyzePage = () => {
  const {
    file,
    setFile,
    preview,
    setPreview,
    isAnalyzing,
    error,
    setError,
    result,
    setResult,
    runAnalysis,
  } = useAnalysis();

  // Form Metadata State
  const [formData, setFormData] = useState({
    institution_name: 'NSTI Bangalore',
    course_name: 'Python Web Development',
    job_role: 'Software Engineer Trainee',
    registered_students: 30,
    date: new Date().toISOString().split('T')[0],
    time: '10:30 AM',
    planned_activity: 'Practical Hands-on Coding Session',
    topic: 'FastAPI and Database Integration',
    activity_type: 'practical_session',
  });

  const [selectedInfra, setSelectedInfra] = useState(['whiteboard', 'projector', 'computer']);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const url = URL.createObjectURL(selectedFile);
      setFile(selectedFile);
      setPreview(url);
      setResult(null);
      setError(null);
    }
  };

  const handleInfraToggle = (item) => {
    if (selectedInfra.includes(item)) {
      setSelectedInfra(selectedInfra.filter((i) => i !== item));
    } else {
      setSelectedInfra([...selectedInfra, item]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select or drag a classroom image to analyze.');
      return;
    }

    try {
      const payload = new FormData();
      payload.append('image', file);
      payload.append('institution_name', formData.institution_name);
      payload.append('course_name', formData.course_name);
      payload.append('job_role', formData.job_role);
      payload.append('registered_students', formData.registered_students);
      payload.append('date', formData.date);
      payload.append('time', formData.time);
      payload.append('infrastructure_items', JSON.stringify(selectedInfra));
      payload.append('planned_activity', formData.planned_activity);
      payload.append('topic', formData.topic);
      payload.append('activity_type', formData.activity_type);

      await runAnalysis(payload, file, preview, formData.institution_name);
      // Auto-scroll to results section when response arrives
      setTimeout(() => {
        document.getElementById('analysis-result-section')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      console.error('Analysis submission error:', err);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-white tracking-tight">Classroom AI Vision Inspection</h1>
        <p className="mt-1 text-slate-400 text-sm">
          Upload a classroom photo for dual YOLOv8 object detection & Qwen2.5-VL quality assessment.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Input Form Column */}
        <div className="lg:col-span-6 space-y-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Image Upload Box */}
            <div className="glass-card rounded-2xl p-6 border border-slate-800">
              <label className="block text-sm font-bold text-slate-200 mb-3">Classroom Image *</label>
              
              <div 
                className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all ${
                  preview ? 'border-indigo-500/50 bg-indigo-950/10' : 'border-slate-700 hover:border-indigo-500/60 bg-slate-900/40'
                }`}
              >
                {preview ? (
                  <div className="relative group">
                    <img 
                      src={preview} 
                      alt="Classroom Preview" 
                      className="max-h-64 mx-auto rounded-lg object-cover shadow-lg border border-slate-700" 
                    />
                    <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity rounded-lg">
                      <label className="cursor-pointer bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-xs font-semibold shadow">
                        Change Image
                        <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
                      </label>
                    </div>
                  </div>
                ) : (
                  <label className="cursor-pointer flex flex-col items-center justify-center py-6">
                    <Upload className="w-10 h-10 text-indigo-400 mb-3 animate-bounce" />
                    <span className="text-sm font-semibold text-slate-200">Click to upload or drag & drop</span>
                    <span className="text-xs text-slate-400 mt-1">Supports JPG, PNG, WEBP (Max 10MB)</span>
                    <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
                  </label>
                )}
              </div>
            </div>

            {/* Metadata Form */}
            <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
              <h3 className="text-base font-bold text-white mb-4 border-b border-slate-800 pb-2">Session Metadata</h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Institution Name</label>
                  <input
                    type="text"
                    value={formData.institution_name}
                    onChange={(e) => setFormData({ ...formData, institution_name: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Course Name</label>
                  <input
                    type="text"
                    value={formData.course_name}
                    onChange={(e) => setFormData({ ...formData, course_name: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Job Role</label>
                  <input
                    type="text"
                    value={formData.job_role}
                    onChange={(e) => setFormData({ ...formData, job_role: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Registered Students</label>
                  <input
                    type="number"
                    value={formData.registered_students}
                    onChange={(e) => setFormData({ ...formData, registered_students: parseInt(e.target.value) || 0 })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Date</label>
                  <input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Activity Type</label>
                  <select
                    value={formData.activity_type}
                    onChange={(e) => setFormData({ ...formData, activity_type: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="practical_session">Practical Session</option>
                    <option value="trainer_teaching">Trainer Lecture / Teaching</option>
                    <option value="group_discussion">Group Discussion</option>
                    <option value="assessment">Assessment / Test</option>
                  </select>
                </div>
              </div>

              {/* Infrastructure chips */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-2">Planned Infrastructure Checklist</label>
                <div className="flex flex-wrap gap-2">
                  {DEFAULT_INFRASTRUCTURE.map((item) => (
                    <button
                      type="button"
                      key={item}
                      onClick={() => handleInfraToggle(item)}
                      className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                        selectedInfra.includes(item)
                          ? 'bg-indigo-600/30 text-indigo-300 border-indigo-500/50'
                          : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      {selectedInfra.includes(item) ? '✓ ' : '+ '}{item.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Action Button */}
              <button
                type="submit"
                disabled={isAnalyzing || !file}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white font-bold shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition-all"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin text-white" />
                    <span>Running Qwen2.5-VL & YOLOv8 Analysis...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5 fill-current" />
                    <span>Generate Quality Score Report</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Output Column */}
        <div className="lg:col-span-6 space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block">Inspection Error</span>
                <span className="text-xs">{error}</span>
              </div>
            </div>
          )}

          {!result && !isAnalyzing && !error && (
            <div className="glass-card rounded-2xl p-12 border border-slate-800 text-center flex flex-col items-center justify-center min-h-[400px]">
              <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-indigo-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Ready to Inspect</h3>
              <p className="text-slate-400 text-xs max-w-sm mt-1">
                Upload a classroom photo and click "Generate Quality Score Report" to inspect trainer presence, attendance, and activity compliance.
              </p>
            </div>
          )}

          {isAnalyzing && (
            <div className="glass-card rounded-2xl p-12 border border-slate-800 text-center flex flex-col items-center justify-center min-h-[400px]">
              <div className="relative mb-6">
                <div className="w-20 h-20 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin"></div>
                <Sparkles className="w-8 h-8 text-indigo-400 absolute inset-0 m-auto animate-pulse" />
              </div>
              <h3 className="text-lg font-bold text-white">AI Multimodal Processing</h3>
              <p className="text-xs text-indigo-300 mt-2 font-mono">1. Running YOLOv8 person & object detector...</p>
              <p className="text-xs text-slate-400 mt-1 font-mono">2. Evaluating visual context with Qwen2.5-VL...</p>
            </div>
          )}

          {result && (
            <ErrorBoundary>
              <div id="analysis-result-section" className="space-y-6 animate-fadeIn">
                {/* Overall Quality Score Header Card */}
                <div className="glass-card rounded-2xl p-6 border border-emerald-500/30 bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 shadow-xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none"></div>
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-6 relative z-10">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span className="text-xs font-mono uppercase text-emerald-400 font-bold tracking-wider">Analysis Complete • {result.session_id || 'SESSION'}</span>
                      </div>
                      <h2 className="text-2xl font-black text-white mt-1">{result.institution_name || 'Institution'}</h2>
                      <p className="text-xs text-slate-400">{result.course_name} • {result.date}</p>
                      
                      <div className="mt-4 flex flex-wrap items-center gap-2">
                        <div className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          {result.quality_label || 'Evaluated'}
                        </div>
                        {result.curriculum_match && (
                          <div className="px-3 py-1 rounded-full text-xs font-bold bg-violet-500/20 text-violet-300 border border-violet-500/30 capitalize">
                            Curriculum: {String(result.curriculum_match).replace('_', ' ')}
                          </div>
                        )}
                      </div>
                    </div>

                    <ScoreGauge score={result.quality_score ?? 0} label="Overall QS" />
                  </div>
                </div>

                {/* Radar Score Breakdown */}
                <div className="glass-card rounded-2xl p-6 border border-slate-800">
                  <h3 className="text-base font-bold text-white mb-4 flex items-center justify-between">
                    <span>6-Factor Quality Radar</span>
                    <span className="text-xs font-normal text-indigo-400">QS Score: {Number(result.quality_score || 0).toFixed(1)}/100</span>
                  </h3>
                  <QualityRadarChart scoreBreakdown={result.score_breakdown || {}} />
                </div>

                {/* Detections Summary Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="glass-card rounded-xl p-4 border border-slate-800">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase">
                      <Users className="w-4 h-4 text-indigo-400" /> Attendance & Count
                    </div>
                    <div className="mt-2 text-xl font-bold text-white">
                      {result.student_count ?? 0} <span className="text-xs font-normal text-slate-400">students ({Math.round(Number(result.attendance_percentage) || 0)}%)</span>
                    </div>
                  </div>

                  <div className="glass-card rounded-xl p-4 border border-slate-800">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Trainer Status
                    </div>
                    <div className="mt-2 text-sm font-bold text-emerald-400 capitalize">
                      {String(result.trainer_status || 'Unknown').replace('_', ' ')}
                    </div>
                  </div>
                </div>

                {/* Infrastructure Checklist Verification */}
                {result.infrastructure_status && typeof result.infrastructure_status === 'object' && (
                  <div className="glass-card rounded-2xl p-6 border border-slate-800">
                    <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                      <Monitor className="w-4 h-4 text-indigo-400" /> Infrastructure Verification
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {Object.entries(result.infrastructure_status).map(([item, detected]) => (
                        <div
                          key={item}
                          className={`p-2.5 rounded-lg border text-xs font-semibold flex items-center gap-2 ${
                            detected
                              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                              : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
                          }`}
                        >
                          {detected ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                          ) : (
                            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                          )}
                          <span className="capitalize">{String(item).replace('_', ' ')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Raw AI Reasoning Description */}
                {result.raw_description && (
                  <div className="glass-card rounded-2xl p-6 border border-slate-800">
                    <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400" /> AI Visual Observations
                    </h3>
                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/80 p-4 rounded-xl font-mono border border-slate-800">
                      {result.raw_description}
                    </p>
                  </div>
                )}

                {/* Alerts & Recommendations */}
                {Array.isArray(result.alerts) && result.alerts.length > 0 && (
                  <div className="glass-card rounded-2xl p-6 border border-slate-800">
                    <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-amber-400" /> Compliance Alerts
                    </h3>
                    <ul className="space-y-2">
                      {result.alerts.map((alert, idx) => {
                        const alertMsg = typeof alert === 'object' && alert !== null
                          ? (alert.message || alert.alert || JSON.stringify(alert))
                          : String(alert);
                        const isCritical = typeof alert === 'object' && (alert.severity === 'critical' || alert.severity === 'HIGH');
                        
                        return (
                          <li
                            key={idx}
                            className={`p-3 rounded-lg border text-xs flex items-center gap-2 ${
                              isCritical
                                ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                                : 'bg-amber-500/10 border-amber-500/20 text-amber-300'
                            }`}
                          >
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            <span>{alertMsg}</span>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </div>
            </ErrorBoundary>
          )}
        </div>
      </div>
    </div>
  );
};
