import React, { useState } from 'react';
import { 
  Calculator, 
  Award, 
  CheckCircle2, 
  AlertTriangle, 
  Layers, 
  FileText, 
  HelpCircle,
  TrendingUp,
  Search,
  Sparkles,
  Info,
  ChevronDown,
  ChevronUp,
  Sliders
} from 'lucide-react';

const SESSION_FORMULA_INFO = {
  lecture: {
    title: 'Lecture Session Formula (QS_Lecture)',
    icon: '🎓',
    activityName: 'Lecture & Theory',
    assCount: 10,
    desc: 'Combines 8 Universal Common Parameters (40%) with 10 Lecture-Specific Pedagogical Parameters (60%).',
    formulaText: 'QS_Lecture = 0.4(CPS) + 0.6(ASS_Lecture)',
    assFormulaText: 'ASS_Lecture = Σ(W_i · L_i) / Σ(W_i)',
  },
  assessment: {
    title: 'Assessment & Exam Formula (QS_Assessment)',
    icon: '📝',
    activityName: 'Exam & Assessment',
    assCount: 10,
    desc: 'Combines 8 Universal Common Parameters (40%) with 10 Exam Integrity & Proctoring Parameters (60%).',
    formulaText: 'QS_Assessment = 0.4(CPS) + 0.6(ASS_Assessment)',
    assFormulaText: 'ASS_Assessment = Σ(W_i · A_i) / Σ(W_i)',
  },
  practical_session: {
    title: 'Practical / Lab Session Formula (QS_Practical)',
    icon: '🧪',
    activityName: 'Practical Lab & Workshop',
    assCount: 7,
    desc: 'Combines 8 Universal Common Parameters (40%) with 7 Hands-on Equipment & Lab Usage Parameters (60%).',
    formulaText: 'QS_Practical = 0.4(CPS) + 0.6(ASS_Practical)',
    assFormulaText: 'ASS_Practical = Σ(W_i · P_i) / Σ(W_i)',
  },
  group_discussion: {
    title: 'Group Discussion Formula (QS_GD)',
    icon: '👥',
    activityName: 'Group Discussion',
    assCount: 6,
    desc: 'Combines 8 Universal Common Parameters (40%) with 6 Peer Interaction & Group Dynamics Parameters (60%).',
    formulaText: 'QS_GD = 0.4(CPS) + 0.6(ASS_GD)',
    assFormulaText: 'ASS_GD = Σ(W_i · G_i) / Σ(W_i)',
  },
};

const PARAM_HUMAN_NAMES = {
  // Universal Common Parameters (CPS)
  student_attendance: 'Student Attendance Rate',
  mentor_presence: 'Mentor / Trainer Presence',
  student_attention: 'Student Visual Attention & Focus',
  student_participation: 'Student Active Participation',
  mentor_guidance: 'Mentor Active Guidance & Monitoring',
  seating_arrangement: 'Seating & Desk Arrangement Quality',
  classroom_discipline: 'Classroom Discipline (Freedom from Distractions)',
  classroom_organization: 'Overall Classroom Cleanliness & Order',

  // Lecture Specific (ASS_Lecture)
  student_occupancy: 'Classroom Student Occupancy',
  board_availability: 'Board Availability (White/Smartboard)',
  projector_availability: 'Projector & Screen Availability',
  laptop_availability: 'Laptop / Computer Availability',
  laptop_usage: 'Laptop Active Practical Usage',
  projector_usage: 'Projector / Screen Display Usage',
  students_facing_mentor_board: 'Students Facing Mentor / Board',
  board_utilization: 'Board Active Utilization',
  classroom_crowding: 'Classroom Spacing & Density Balance',
  proper_seating: 'Proper Seating Discipline',

  // Assessment Specific (ASS_Assessment)
  question_paper: 'Question Paper Distribution & Availability',
  answer_sheet: 'Answer Sheet / Exam Paper Availability',
  pen_writing_material: 'Pen & Writing Material Availability',
  looking_at_paper: 'Students Looking Down at Paper',
  writing_posture: 'Proper Exam Writing Posture',
  unauthorized_communication: 'Unauthorized Communication Prevention (Silence)',
  exam_environment: 'Strict Exam Environment Protocol',
  seating_distance: 'Inter-Student Seating Distance',
  students_leaving_seat: 'Seat Adherence (No Leaving Seat)',
  classroom_visibility: 'Exam Hall Lighting & Visibility',

  // Practical Specific (ASS_Practical)
  required_equipment: 'Required Equipment Availability',
  required_materials: 'Required Tools & Consumable Materials',
  equipment_usage: 'Equipment Active Utilization',
  student_activity: 'Student Practical Task Activity',
  hands_on_activity: 'Direct Hands-on Experimentation',
  workspace_usage: 'Workstation Space Utilization',
  proper_arrangement: 'Lab Tools & Bench Arrangement',

  // Group Discussion Specific (ASS_GD)
  groups_properly_formed: 'Groups Formed & Structured',
  group_size_balance: 'Balanced Group Size Distribution',
  student_interaction: 'Student-to-Student Interaction Rate',
  face_to_face_orientation: 'Face-to-Face Clustered Orientation',
  active_discussion: 'Active Brainstorming & Discussion',
  group_engagement: 'Collective Group Engagement',
};

const COMMON_KEYS = new Set([
  'student_attendance',
  'mentor_presence',
  'student_attention',
  'student_participation',
  'mentor_guidance',
  'seating_arrangement',
  'classroom_discipline',
  'classroom_organization',
]);

export const SessionQualityBreakdown = ({ result }) => {
  const [filter, setFilter] = useState('');
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'cps' | 'ass'
  const [showVivaNotes, setShowVivaNotes] = useState(false);

  const sessionType = result.session_type || 'lecture';
  const formulaInfo = SESSION_FORMULA_INFO[sessionType] || SESSION_FORMULA_INFO.lecture;

  const commonData = result.common_parameters || {};
  const activityData = result.activity_parameters || {};

  // CPS & ASS values
  const cpsScore = Number(result.cps ?? commonData.cps ?? 82.5);
  const assScore = Number(result.ass ?? activityData.ass ?? 85.0);
  const alpha = Number(result.alpha ?? 0.4);
  const beta = Number(result.beta ?? 0.6);
  const finalQS = Number(result.quality_score ?? ((alpha * cpsScore) + (beta * assScore)));

  const paramScores = result.parameter_scores || {};
  const paramWeights = result.parameter_weights || {};
  const paramContributions = result.parameter_contributions || {};

  // Build unified list of parameters with category classification
  const entries = Object.keys(paramWeights).map((key) => {
    const isCommon = COMMON_KEYS.has(key);
    const score = Number(paramScores[key] ?? 80);
    const weight = Number(paramWeights[key] ?? 10);
    const contribution = Number(paramContributions[key] ?? ((score * weight) / 100));
    const name = PARAM_HUMAN_NAMES[key] || key.replace(/_/g, ' ');

    return {
      key,
      name,
      category: isCommon ? 'common' : 'activity',
      score: Math.round(score * 10) / 10,
      weight,
      contribution: Math.round(contribution * 100) / 100,
    };
  });

  const commonEntries = entries.filter((e) => e.category === 'common');
  const activityEntries = entries.filter((e) => e.category === 'activity');

  const visibleEntries = entries.filter((e) => {
    if (activeTab === 'cps') return e.category === 'common';
    if (activeTab === 'ass') return e.category === 'activity';
    return true;
  }).filter((e) =>
    e.name.toLowerCase().includes(filter.toLowerCase()) ||
    e.key.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800 animate-fadeIn space-y-6">
      {/* ── Top Header & Formula Title ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="text-2xl p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20">{formulaInfo.icon}</span>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                {formulaInfo.title}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {formulaInfo.desc}
              </p>
            </div>
          </div>
        </div>

        {/* Viva / Viva Notes Toggle Button */}
        <button
          type="button"
          onClick={() => setShowVivaNotes(!showVivaNotes)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-indigo-300 border border-slate-700 transition-all self-start md:self-auto"
        >
          <HelpCircle className="w-4 h-4 text-indigo-400" />
          <span>Viva / Defense Formulation</span>
          {showVivaNotes ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* ── Collapsible Viva / Mathematical Explanation Card ── */}
      {showVivaNotes && (
        <div className="p-4 rounded-xl bg-slate-900/90 border border-indigo-500/30 text-xs text-slate-300 space-y-2.5 animate-fadeIn">
          <div className="flex items-center gap-2 text-indigo-300 font-bold">
            <Calculator className="w-4 h-4 text-indigo-400" />
            <span>Modular Formulation Architecture for Project Review</span>
          </div>
          <p className="text-slate-400 leading-relaxed">
            The Quality Score (QS) decouples universal classroom indicators from activity-specific requirements:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-[11px] pt-1">
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-indigo-400 font-bold block mb-1">1. Common Parameter Score (CPS):</span>
              <span className="text-slate-200">CPS = Σ(W_Ci · C_i) / Σ(W_Ci)</span>
              <span className="block text-[10px] text-slate-400 mt-1">Weight: 40% (α = 0.4) • 8 Universal Metrics</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-cyan-400 font-bold block mb-1">2. Activity-Specific Score (ASS):</span>
              <span className="text-slate-200">{formulaInfo.assFormulaText}</span>
              <span className="block text-[10px] text-slate-400 mt-1">Weight: 60% (β = 0.6) • {formulaInfo.assCount} Mode Metrics</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-emerald-500/30 bg-emerald-950/10">
              <span className="text-emerald-400 font-bold block mb-1">3. Final Synthesized Quality Score:</span>
              <span className="text-emerald-300 font-bold">QS = 0.4(CPS) + 0.6(ASS)</span>
              <span className="block text-[10px] text-slate-400 mt-1">Where α + β = 1.0 (Strict 0–100 Scale)</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Dual Component Synthesis Hero Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Component 1: Common Parameters (CPS) */}
        <div className="p-4 rounded-xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-indigo-950/40 border border-indigo-500/30 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-indigo-300 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              Common Score (CPS)
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-bold">
              Weight: 40% (α = 0.4)
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <div className="text-2xl font-black text-white">{cpsScore.toFixed(1)}</div>
            <span className="text-xs text-slate-400 font-mono">/ 100</span>
          </div>
          <div className="text-[11px] text-slate-400 flex items-center justify-between font-mono pt-1 border-t border-slate-800">
            <span>Contribution to QS:</span>
            <strong className="text-indigo-300 font-bold">+{(cpsScore * alpha).toFixed(2)} pts</strong>
          </div>
        </div>

        {/* Component 2: Activity-Specific (ASS) */}
        <div className="p-4 rounded-xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-cyan-950/40 border border-cyan-500/30 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-cyan-300 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              Activity Score (ASS)
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-bold">
              Weight: 60% (β = 0.6)
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <div className="text-2xl font-black text-white">{assScore.toFixed(1)}</div>
            <span className="text-xs text-slate-400 font-mono">/ 100</span>
          </div>
          <div className="text-[11px] text-slate-400 flex items-center justify-between font-mono pt-1 border-t border-slate-800">
            <span>Contribution to QS:</span>
            <strong className="text-cyan-300 font-bold">+{(assScore * beta).toFixed(2)} pts</strong>
          </div>
        </div>

        {/* Final Quality Score (QS) */}
        <div className="p-4 rounded-xl bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/40 border border-emerald-500/40 space-y-2 shadow-lg shadow-emerald-950/20">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-emerald-300 flex items-center gap-1.5">
              <Award className="w-4 h-4 text-emerald-400" />
              Final Quality Score (QS)
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
              0.4·CPS + 0.6·ASS
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <div className="text-3xl font-black text-emerald-400">{finalQS.toFixed(1)}</div>
            <span className="text-xs text-slate-400 font-mono">/ 100</span>
          </div>
          <div className="text-[11px] text-slate-400 flex items-center justify-between font-mono pt-1 border-t border-slate-800">
            <span>Performance Index:</span>
            <strong className="text-emerald-300 font-bold">{result.quality_label || 'Good Session'}</strong>
          </div>
        </div>
      </div>

      {/* ── Interactive Tab Filter & Search Bar ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
        {/* Tabs */}
        <div className="flex items-center bg-slate-900/90 p-1 rounded-xl border border-slate-800 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'all'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            All Parameters ({entries.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('cps')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'cps'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>Common (CPS)</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-indigo-950 border border-indigo-400/40 text-indigo-200">
              {commonEntries.length}
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('ass')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'ass'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>Activity (ASS)</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-cyan-950 border border-cyan-400/40 text-cyan-200">
              {activityEntries.length}
            </span>
          </button>
        </div>

        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search parameter..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* ── Parameter Breakdown Table ── */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-900/90 border-b border-slate-800 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              <th className="py-2.5 px-3 w-10 text-center">#</th>
              <th className="py-2.5 px-3">Session Parameter</th>
              <th className="py-2.5 px-3 w-28 text-center">Component</th>
              <th className="py-2.5 px-3 w-24 text-center">Weight (w_i)</th>
              <th className="py-2.5 px-3 w-40">Visual Evaluation (S_i)</th>
              <th className="py-2.5 px-3 w-32 text-right">Contribution</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {visibleEntries.map((item, idx) => {
              const scorePercent = item.score;
              const isHigh = scorePercent >= 75;
              const isMed = scorePercent >= 50 && scorePercent < 75;
              const isCommon = item.category === 'common';

              return (
                <tr key={item.key} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 px-3 text-center text-slate-500 font-mono text-[11px]">
                    {idx + 1}
                  </td>
                  <td className="py-2.5 px-3">
                    <div className="font-semibold text-white capitalize">{item.name}</div>
                    <div className="text-[10px] text-slate-400 font-mono opacity-70">{item.key}</div>
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                      isCommon
                        ? 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30'
                        : 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                    }`}>
                      {isCommon ? 'Common (CPS)' : 'Activity (ASS)'}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-center font-mono">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 font-bold border border-slate-700">
                      {item.weight}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            isHigh ? 'bg-emerald-400' : isMed ? 'bg-amber-400' : 'bg-rose-400'
                          }`}
                          style={{ width: `${scorePercent}%` }}
                        />
                      </div>
                      <span className={`text-[11px] font-mono font-bold w-10 text-right ${
                        isHigh ? 'text-emerald-400' : isMed ? 'text-amber-400' : 'text-rose-400'
                      }`}>
                        {item.score}%
                      </span>
                    </div>
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono font-bold text-white">
                    <span className={isCommon ? 'text-indigo-300' : 'text-cyan-300'}>
                      +{item.contribution.toFixed(2)}
                    </span>
                    <span className="text-[10px] text-slate-500 font-normal"> / {item.weight}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className="bg-slate-900 border-t-2 border-slate-700 text-xs font-bold text-white">
              <td colSpan={2} className="py-3 px-3 uppercase tracking-wider text-slate-300">
                Formula Synthesis:
              </td>
              <td className="py-3 px-3 text-center font-mono text-cyan-300 text-[11px]">
                α=0.4, β=0.6
              </td>
              <td className="py-3 px-3 text-center font-mono text-indigo-300 text-[11px]">
                ΣW = 100%
              </td>
              <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                QS = 0.4({cpsScore.toFixed(1)}) + 0.6({assScore.toFixed(1)})
              </td>
              <td className="py-3 px-3 text-right font-mono text-emerald-400 text-sm">
                {finalQS.toFixed(2)} / 100.00
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};
