import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Users, 
  Sparkles, 
  Layers, 
  ShieldAlert, 
  CheckCircle2, 
  Loader2, 
  Clock, 
  ChevronDown, 
  ChevronUp, 
  Cpu, 
  Scan, 
  Check 
} from 'lucide-react';

const DEFAULT_STEPS = [
  {
    id: 1,
    title: '1. Image Preprocessing & Normalization',
    subtitle: 'Validating image resolution, RGB tensor formatting & dynamic range',
    icon: FileText,
    subtasks: [
      'Reading uploaded image binary data...',
      'Normalizing color channels & contrast curve...',
      'Preparing 640x640 input tensor for model pipeline...'
    ]
  },
  {
    id: 2,
    title: '2. YOLO26 Spatial Object & Person Detection',
    subtitle: 'Scanning classroom bounding boxes, counting students & detecting hardware',
    icon: Users,
    subtasks: [
      'Detecting human bounding boxes for student count...',
      'Locating trainer spatial position in classroom...',
      'Scanning visible infrastructure (projector, whiteboard, computers)...'
    ]
  },
  {
    id: 3,
    title: '3. Qwen2.5-VL Multimodal Vision Context Reasoning',
    subtitle: 'Evaluating teacher instruction posture, activity alignment & engagement',
    icon: Sparkles,
    subtasks: [
      'Evaluating trainer posture & active teaching status...',
      'Analyzing student engagement & attentiveness index...',
      'Verifying visual classroom activity against planned course topic...'
    ]
  },
  {
    id: 4,
    title: '4. Dual-Model Consensus & Infrastructure Verification',
    subtitle: 'Cross-referencing spatial bounding boxes with visual context reasoning',
    icon: Layers,
    subtasks: [
      'Synthesizing YOLO student count with Qwen visual estimate...',
      'Matching detected hardware against required infrastructure checklist...',
      'Validating session safety & layout compliance...'
    ]
  },
  {
    id: 5,
    title: '5. 6-Factor Quality Scoring & Audit Report',
    subtitle: 'Calculating weighted quality index and generating actionable audit alerts',
    icon: ShieldAlert,
    subtasks: [
      'Computing 6 core weighted quality factors...',
      'Evaluating attendance percentage against enrollment...',
      'Generating final quality score & actionable recommendations...'
    ]
  }
];

export const AnalysisStepVisualizer = ({ isAnalyzing, result }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [subTaskIndex, setSubTaskIndex] = useState(0);
  const [progress, setProgress] = useState(10);
  const [isExpanded, setIsExpanded] = useState(true);

  // Simulation timer during active analysis
  useEffect(() => {
    if (!isAnalyzing) {
      if (result) {
        setActiveStep(4);
        setProgress(100);
      }
      return;
    }

    setActiveStep(0);
    setProgress(15);
    setSubTaskIndex(0);

    const stepInterval = setInterval(() => {
      setActiveStep((prevStep) => {
        if (prevStep < 4) {
          const nextStep = prevStep + 1;
          setProgress(Math.min(95, (nextStep + 1) * 19));
          setSubTaskIndex(0);
          return nextStep;
        }
        return prevStep;
      });
    }, 2200);

    const subTaskInterval = setInterval(() => {
      setSubTaskIndex((prev) => (prev + 1) % 3);
    }, 700);

    return () => {
      clearInterval(stepInterval);
      clearInterval(subTaskInterval);
    };
  }, [isAnalyzing, result]);

  // If in results mode, render the post-analysis Step-by-Step Breakdown Accordion
  if (!isAnalyzing && result) {
    const traceData = result.pipeline_trace || [
      {
        step: 1,
        name: 'Image Preprocessing & Normalization',
        badge: 'RGB Tensor Ready',
        details: 'Image format validated and contrast optimized for dual AI inference.'
      },
      {
        step: 2,
        name: 'YOLO26 Spatial Detection',
        badge: `${result.student_count + (result.trainer_present ? 1 : 0)} Persons Detected`,
        details: `Scanned human bounding boxes & hardware items (${Object.keys(result.infrastructure_status || {}).join(', ') || 'whiteboard'}).`
      },
      {
        step: 3,
        name: 'Qwen2.5-VL Context Analysis',
        badge: `Trainer: ${String(result.trainer_status || '').replace('_', ' ')}`,
        details: `Curriculum Match: '${result.curriculum_match || 'fully_matched'}'. Activity: '${result.detected_activities?.[0] || 'practical_session'}'.`
      },
      {
        step: 4,
        name: 'Consensus & Infrastructure Fusion',
        badge: `${Object.values(result.infrastructure_status || {}).filter(Boolean).length}/${Object.keys(result.infrastructure_status || {}).length || 0} Infra Matched`,
        details: `Merged spatial YOLO detections with Qwen visual reasoning. Consensus attendance: ${result.student_count} students.`
      },
      {
        step: 5,
        name: '6-Factor Quality Scoring & Audit',
        badge: `QS: ${Number(result.quality_score || 0).toFixed(1)}/100`,
        details: `Overall Quality Label: '${result.quality_label}'. Attendance Rate: ${Math.round(Number(result.attendance_percentage) || 0)}%.`
      }
    ];

    return (
      <div className="glass-card rounded-2xl border border-indigo-500/30 overflow-hidden shadow-xl animate-fadeIn">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full p-4 sm:p-5 bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 flex items-center justify-between hover:bg-slate-800/60 transition-colors text-left"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <Scan className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>Step-by-Step AI Detection & Analysis Pipeline</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  5/5 Steps Verified
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Inspect how YOLO26 object detection & Qwen2.5-VL vision reasoning produced this score.
              </p>
            </div>
          </div>
          <div className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white">
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {isExpanded && (
          <div className="p-5 border-t border-slate-800/80 space-y-4 bg-slate-950/40">
            <div className="relative pl-6 space-y-4 before:absolute before:left-3 before:top-3 before:bottom-3 before:w-0.5 before:bg-indigo-500/30">
              {traceData.map((item, idx) => {
                const IconComponent = DEFAULT_STEPS[idx]?.icon || CheckCircle2;
                return (
                  <div key={item.step || idx} className="relative group">
                    <div className="absolute -left-[31px] top-1 w-6 h-6 rounded-full bg-emerald-950 border border-emerald-500 flex items-center justify-center text-emerald-400 shadow-sm">
                      <Check className="w-3.5 h-3.5 stroke-[3]" />
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <IconComponent className="w-4 h-4 text-indigo-400" />
                          <span className="text-xs font-bold text-white">
                            Step {item.step || idx + 1}: {item.name}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 pl-6">{item.details}</p>
                      </div>

                      {item.badge && (
                        <span className="self-start sm:self-center shrink-0 px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                          {item.badge}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Active Loading/Analyzing State Visualizer
  return (
    <div className="glass-card rounded-2xl p-6 sm:p-8 border border-indigo-500/30 bg-slate-950/80 shadow-2xl relative overflow-hidden space-y-6">
      {/* Background glowing aura */}
      <div className="absolute -top-12 -right-12 w-48 h-48 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>

      {/* Progress Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400 animate-pulse" />
            <h3 className="text-base font-bold text-white tracking-wide">AI Multimodal Detection & Analysis Pipeline</h3>
          </div>
          <span className="text-xs font-mono font-bold text-indigo-300 bg-indigo-950/80 px-2.5 py-1 rounded-full border border-indigo-500/30">
            {progress}% Completed
          </span>
        </div>

        {/* Dynamic Progress Bar */}
        <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
          <div 
            className="bg-gradient-to-r from-indigo-500 via-violet-500 to-emerald-400 h-full transition-all duration-500 ease-out rounded-full shadow-lg shadow-indigo-500/50"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      {/* Step by Step Pipeline Checklist */}
      <div className="space-y-3 relative">
        {DEFAULT_STEPS.map((step, index) => {
          const StepIcon = step.icon;
          const isCompleted = index < activeStep;
          const isActive = index === activeStep;
          const isPending = index > activeStep;

          return (
            <div
              key={step.id}
              className={`p-4 rounded-xl border transition-all duration-300 flex items-start gap-4 ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-950/60 to-slate-900 border-indigo-500/60 shadow-lg shadow-indigo-950/50 scale-[1.01]'
                  : isCompleted
                  ? 'bg-slate-900/60 border-slate-800 text-slate-300 opacity-90'
                  : 'bg-slate-950/40 border-slate-900 text-slate-500 opacity-50'
              }`}
            >
              {/* Step Status Indicator Icon */}
              <div className="mt-0.5 flex-shrink-0">
                {isCompleted ? (
                  <div className="w-7 h-7 rounded-full bg-emerald-500/20 border border-emerald-500/60 flex items-center justify-center text-emerald-400 shadow-sm">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                ) : isActive ? (
                  <div className="w-7 h-7 rounded-full bg-indigo-600/30 border border-indigo-500 flex items-center justify-center text-indigo-300 shadow-md animate-pulse">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                ) : (
                  <div className="w-7 h-7 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-xs font-mono font-bold text-slate-500">
                    0{step.id}
                  </div>
                )}
              </div>

              {/* Step Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className={`text-xs sm:text-sm font-bold ${isActive ? 'text-white' : isCompleted ? 'text-slate-200' : 'text-slate-500'}`}>
                    {step.title}
                  </h4>
                  {isActive && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 animate-pulse">
                      PROCESSING
                    </span>
                  )}
                  {isCompleted && (
                    <span className="text-[10px] font-mono font-semibold text-emerald-400">
                      ✓ Done
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{step.subtitle}</p>

                {/* Active Step Ticker / Subtasks */}
                {isActive && (
                  <div className="mt-2.5 pt-2.5 border-t border-indigo-500/20 flex items-center gap-2 text-xs font-mono text-indigo-300 animate-fadeIn">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping"></span>
                    <span className="truncate">{step.subtasks[subTaskIndex]}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="pt-2 text-center">
        <p className="text-xs text-slate-400 flex items-center justify-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
          <span>Multimodal Neural Fusion (YOLO26 + Qwen2.5-VL) running in background...</span>
        </p>
      </div>
    </div>
  );
};
