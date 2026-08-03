import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Loader2, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';

export const AnalysisBanner = () => {
  const { isAnalyzing, result, activeInstitution } = useAnalysis();
  const location = useLocation();
  const navigate = useNavigate();

  // Show banner only when user is NOT on the analyze page
  if (location.pathname === '/analyze') {
    return null;
  }

  if (isAnalyzing) {
    return (
      <div className="bg-indigo-600/90 text-white px-4 py-2.5 shadow-lg flex items-center justify-between gap-4 border-b border-indigo-400/30 animate-pulse">
        <div className="flex items-center gap-3 text-xs font-semibold">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-200" />
          <span>AI Multimodal Processing running in background for <strong>{activeInstitution}</strong>...</span>
        </div>
        <button
          onClick={() => navigate('/analyze')}
          className="px-3 py-1 bg-white/20 hover:bg-white/30 text-white rounded-lg text-xs font-bold flex items-center gap-1 transition-all"
        >
          <span>View Progress</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  if (result) {
    return (
      <div className="bg-emerald-600/90 text-white px-4 py-2.5 shadow-lg flex items-center justify-between gap-4 border-b border-emerald-400/30">
        <div className="flex items-center gap-3 text-xs font-semibold">
          <CheckCircle2 className="w-4 h-4 text-emerald-200" />
          <span>Analysis Complete! Quality Score: <strong>{Number(result.quality_score || 0).toFixed(1)}/100</strong> ({result.quality_label || 'Evaluated'})</span>
        </div>
        <button
          onClick={() => navigate('/analyze')}
          className="px-3 py-1 bg-white/20 hover:bg-white/30 text-white rounded-lg text-xs font-bold flex items-center gap-1 transition-all"
        >
          <span>View Report</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  return null;
};
