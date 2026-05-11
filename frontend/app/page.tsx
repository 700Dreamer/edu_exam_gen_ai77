"use client";

import { useState, useEffect, useRef } from "react";
import { Sparkles, Settings, Database, BookOpen, Layers, CheckCircle2, AlertCircle, FileText, Download, Play, RefreshCw, Filter, Loader2, GitBranch } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import FlowView from "./FlowView";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ── CONNECTIVITY ──
const API_BASE = typeof window !== "undefined" ? "" : "http://127.0.0.1:8000";

// ── TYPES ──
type Page = "studio" | "ingestion" | "analytics";
type Mode = "Exams" | "Lesson Notes" | "Schemes of Work";

interface Project {
  id: string;
  title: string;
  mode: string;
  subject: string;
  level: string;
  term: string;
  timestamp: string;
  data: any;
}

// ── COMPONENTS ──

const Header = ({ theme, setTheme }: any) => (
  <header className="bg-surface border-b border-border-main text-foreground px-8 py-4 shadow-sm flex justify-between items-center sticky top-0 z-50 transition-colors duration-500">
    <div className="flex items-center gap-6">
      <div className="flex items-center gap-3 group px-4 py-2 hover:bg-foreground/5 rounded-2xl transition-all cursor-default">
        <div className="bg-brand-500/10 border border-brand-500/20 p-2 rounded-lg backdrop-blur-md relative overflow-hidden">
           <Database className="w-6 h-6 text-brand-500 relative z-10" />
           <div className="absolute inset-0 bg-brand-500/20 animate-pulse"></div>
        </div>
        <div>
           <h1 className="text-xl font-black tracking-widest leading-none">EDUQUEST <span className="font-light opacity-40 italic">STUDIO</span></h1>
           <p className="text-[9px] tracking-[0.3em] font-bold mt-1 uppercase text-brand-500 opacity-80">Enterprise Content Engine</p>
        </div>
      </div>
    </div>
    <div className="flex items-center gap-6">
      <div className="flex gap-1.5 bg-background p-1.5 rounded-full border border-border-main shadow-inner">
        {(['burgundy', 'midnight', 'emerald', 'royal', 'studio'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTheme(t)}
            className={cn(
              "w-6 h-6 rounded-full border-2 transition-all hover:scale-110",
              theme === t ? "border-brand-500 scale-110 shadow-lg" : "border-transparent opacity-60",
              t === 'burgundy' && "bg-[#800020]",
              t === 'midnight' && "bg-[#0f172a]",
              t === 'emerald' && "bg-[#064e3b]",
              t === 'royal' && "bg-[#4338ca]",
              t === 'studio' && "bg-[#181818]"
            )}
            title={`${t.charAt(0).toUpperCase() + t.slice(1)} Theme`}
          />
        ))}
      </div>

      <div className="flex items-center gap-3 border-l border-border-main pl-6 h-8">
        <div className="px-3 py-1 bg-surface-soft border border-border-main rounded-full text-[9px] font-bold tracking-widest uppercase text-foreground opacity-60">RAG-SYNAPSE v4</div>
        <div className="px-3 py-1 bg-surface-soft border border-border-main rounded-full text-[9px] font-bold tracking-widest uppercase text-foreground opacity-60">TIKZ-JAX DRAW</div>
      </div>
    </div>
  </header>
);

export default function Home() {
  const [currentPage, setCurrentPage] = useState<Page>("studio");
  const [activeTab, setActiveTab] = useState<"gen" | "lib" | "insights" | "chat" | "scenario">("gen");
  const [previewHtml, setPreviewHtml] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [library, setLibrary] = useState<Project[]>([]);
  const [bridgedPrompt, setBridgedPrompt] = useState<string>("");
  const [lastRaw, setLastRaw] = useState<string>("");
  const [lastConfig, setLastConfig] = useState<any>(null);

  const [theme, setTheme] = useState<'burgundy' | 'midnight' | 'emerald' | 'royal' | 'studio'>('burgundy');

  // Persistence logic
  useEffect(() => {
    const saved = localStorage.getItem('eduquest-theme') as any;
    if (saved && ['burgundy', 'midnight', 'emerald', 'royal', 'studio'].includes(saved)) {
      setTheme(saved);
    }
  }, []);

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('eduquest-theme', theme);
  }, [theme]);

  // Fetch library on load
  const fetchLibrary = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/library`);
      const data = await res.json();
      setLibrary(data);
    } catch (e) {
      console.error("Library fetch failed", e);
    }
  };

  return (
    <div className="min-h-screen flex flex-col transition-colors duration-500">
      <Header theme={theme} setTheme={setTheme} />
      
      {/* ── TOP NAV bar ── */}
      <div className={cn("px-8 py-6 flex gap-4 border-b border-border-main z-10 transition-all duration-500", (theme === 'midnight' || theme === 'royal') ? "glass-premium" : "bg-surface/50 backdrop-blur-sm")}>
        <button 
          onClick={() => setCurrentPage("studio")}
          className={cn(
            "flex items-center gap-2 px-8 py-2.5 rounded-lg font-bold transition-all",
            currentPage === "studio" ? "bg-brand-800 text-white shadow-md" : "bg-surface text-foreground opacity-50 hover:text-brand-800 hover:opacity-100 border border-border-main",
            (theme === 'midnight' || theme === 'royal') && currentPage === "studio" && "neon-glow shadow-[0_0_15px_var(--glow-accent)]"
          )}
        >
          <Sparkles className="w-4 h-4" />
          Studio
        </button>
        <button 
          onClick={() => setCurrentPage("analytics")}
          className={cn(
            "flex items-center gap-2 px-8 py-2.5 rounded-lg font-bold transition-all",
            currentPage === "analytics" ? "bg-brand-800 text-white shadow-md" : "bg-surface text-foreground opacity-50 hover:text-brand-800 hover:opacity-100 border border-border-main",
            (theme === 'midnight' || theme === 'royal') && currentPage === "analytics" && "neon-glow shadow-[0_0_15px_var(--glow-accent)]"
          )}
        >
          <Layers className="w-4 h-4" />
          Analytics
        </button>
        <button 
          onClick={() => setCurrentPage("flow")}
          className={cn(
            "flex items-center gap-2 px-8 py-2.5 rounded-lg font-bold transition-all",
            currentPage === "flow" ? "bg-brand-800 text-white shadow-md" : "bg-surface text-foreground opacity-50 hover:text-brand-800 hover:opacity-100 border border-border-main",
            (theme === 'midnight' || theme === 'royal') && currentPage === "flow" && "neon-glow shadow-[0_0_15px_var(--glow-accent)]"
          )}
        >
          <GitBranch className="w-4 h-4" />
          Neural Flow
        </button>
        <button 
          onClick={() => setCurrentPage("ingestion")}
          className={cn(
            "flex items-center gap-2 px-8 py-2.5 rounded-lg font-bold transition-all",
            currentPage === "ingestion" ? "bg-brand-800 text-white shadow-md" : "bg-surface text-foreground opacity-50 hover:text-brand-800 hover:opacity-100 border border-border-main",
            (theme === 'midnight' || theme === 'royal') && currentPage === "ingestion" && "neon-glow shadow-[0_0_15px_var(--glow-accent)]"
          )}
        >
          <Database className="w-4 h-4" />
          Data Digestion
        </button>
      </div>

      {/* ── CONTENT AREA ── */}
      <main className="flex-1 overflow-hidden flex">
        {currentPage === "studio" ? (
          <StudioView 
            activeTab={activeTab} 
            setActiveTab={setActiveTab} 
            previewHtml={previewHtml} 
            setPreviewHtml={setPreviewHtml}
            isGenerating={isGenerating}
            setIsGenerating={setIsGenerating}
            library={library}
            onProjectLoad={(raw: string, html: string, subject: string, level: string) => {
              setPreviewHtml(html);
              setLastRaw(raw);
              setLastConfig({ subject, level });
              setActiveTab("gen");
            }}
            refreshLibrary={fetchLibrary}
            theme={theme}
            lastRaw={lastRaw}
            setLastRaw={setLastRaw}
            lastConfig={lastConfig}
            setLastConfig={setLastConfig}
            bridgedPrompt={bridgedPrompt}
            setBridgedPrompt={setBridgedPrompt}
          />
        ) : currentPage === "analytics" ? (
          <AnalyticsView 
            theme={theme} 
            onBridge={(topic: string) => {
               setBridgedPrompt(`I noticed '${topic}' is missing from the curriculum saturation map. Please generate 5 high-quality exam questions for this specific topic to bridge the gap.`);
               setCurrentPage("studio");
               setActiveTab("chat");
            }}
          />
        ) : currentPage === "flow" ? (
          <FlowView theme={theme} onBridge={(topic: string) => {
               setBridgedPrompt(`[Neural Flow Bridge] Topic: ${topic}`);
               setCurrentPage("studio");
               setActiveTab("chat");
          }} />
        ) : (
          <IngestionView theme={theme} />
        )}
      </main>
    </div>
  );
}

// ── STUDIO SUB-VIEW ──
function StudioView({ 
  activeTab, 
  setActiveTab, 
  previewHtml, 
  setPreviewHtml, 
  isGenerating, 
  setIsGenerating,
  library,
  onProjectLoad,
  refreshLibrary,
  theme,
  lastRaw,
  setLastRaw,
  lastConfig,
  setLastConfig,
  bridgedPrompt,
  setBridgedPrompt
}: any) {
  const [selection, setSelection] = useState("");
  const [selectionPos, setSelectionPos] = useState({ x: 0, y: 0 });
  const [isRefining, setIsRefining] = useState(false);
  const [isProcessingRefinement, setIsProcessingRefinement] = useState(false);

  // 📡 SELECTION RELAY: Listen for messages from the Document Iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'EDUQUEST_SELECTION') {
        const { text, rect } = event.data;
        const iframe = document.querySelector('iframe');
        if (iframe) {
          const iframeRect = iframe.getBoundingClientRect();
          setSelection(text);
          setSelectionPos({
            x: iframeRect.left + rect.left + (rect.width / 2),
            y: iframeRect.top + rect.top
          });
        }
      } else if (event.data.type === 'EDUQUEST_SELECTION_CLEAR') {
        if (!isRefining) {
           setSelection("");
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [isRefining]);


  const handleRefine = async (instruction: string) => {
    if (!selection) return;
    setIsProcessingRefinement(true);

    try {
      const resp = await fetch(`${API_BASE}/api/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selected_text: selection,
          instruction,
          subject: lastConfig?.subject || "Mathematics", 
          level: lastConfig?.level || "Primary 7",
          term: lastConfig?.term || "Term 1"
        })
      });
      
      if (!resp.ok) {
        const err = await resp.text();
        throw new Error(`API Error ${resp.status}: ${err}`);
      }

      const data = await resp.json();
      if (data.refined_text) {
        const newHtml = previewHtml.replace(selection, data.refined_text);
        setPreviewHtml(newHtml);
        setIsRefining(false);
        setSelection("");
      } else {
        alert("AI returned empty refinement. Try a different instruction.");
      }
    } catch (e: any) {
      console.error("Refine failed", e);
      alert(`Refinement Failed: ${e.message}\n\nCheck if the server is running and has the latest updates.`);
    } finally {
      setIsProcessingRefinement(false);
    }
  };

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Sidebar Controls */}
      <aside className={cn("w-[450px] border-r border-border-main overflow-y-auto p-6 flex flex-col gap-8 transition-all", theme === 'midnight' ? "glass" : "bg-surface")}>
        <div className="flex gap-1 bg-surface-soft p-1 rounded-xl">
           {(['gen', 'scenario', 'lib', 'insights', 'chat'] as const).map(tab => (
             <button 
               key={tab}
               onClick={() => setActiveTab(tab)}
               className={cn(
                 "flex-1 py-1.5 rounded-lg font-bold text-[10px] uppercase tracking-tighter transition-all",
                 activeTab === tab ? "bg-surface text-brand-800 shadow-sm" : "text-foreground opacity-40 hover:opacity-100"
               )}
             >
               {tab === 'gen' && 'Generator'}
               {tab === 'scenario' && 'Scenario-Based'}
               {tab === 'lib' && 'Library'}
               {tab === 'insights' && 'Insights'}
               {tab === 'chat' && 'Chat'}
             </button>
           ))}
        </div>

        {activeTab === 'gen' && (
          <GeneratorControls 
            setPreviewHtml={setPreviewHtml} 
            isGenerating={isGenerating} 
            setIsGenerating={setIsGenerating} 
            refreshLibrary={refreshLibrary}
            theme={theme}
            selection={selection}
            setIsRefining={setIsRefining}
            setLastRaw={setLastRaw}
            setLastConfig={setLastConfig}
            lastRaw={lastRaw}
            lastConfig={lastConfig}
          />
        )}
        {activeTab === 'scenario' && (
          <ScenarioView 
            setPreviewHtml={setPreviewHtml} 
            isGenerating={isGenerating} 
            setIsGenerating={setIsGenerating} 
            refreshLibrary={refreshLibrary}
            theme={theme}
            setLastRaw={setLastRaw}
            setLastConfig={setLastConfig}
            lastConfig={lastConfig}
          />
        )}
        {activeTab === 'lib' && <LibraryView library={library} onProjectLoad={onProjectLoad} theme={theme} />}
        {activeTab === 'insights' && (
          <InsightsView 
            theme={theme} 
            previewHtml={previewHtml} 
            lastRaw={lastRaw}
            lastConfig={lastConfig}
            onBridge={(topic: string) => {
              setBridgedPrompt(`I noticed '${topic}' is missing from the curriculum audit. Please generate 3 exam-ready questions for this topic to bridge the curriculum gap.`);
              setActiveTab('chat');
            }}
          />
        )}
        {activeTab === 'chat' && (
          <ChatView 
            theme={theme} 
            bridgedPrompt={bridgedPrompt} 
            setBridgedPrompt={setBridgedPrompt} 
          />
        )}
      </aside>

      {/* Preview Area */}
      <section id="preview-section" className="flex-1 bg-surface-soft/50 p-8 overflow-y-auto relative">
        <div className="absolute top-8 right-8 z-10 flex gap-2">
           {!selection && (
             <div className="px-4 py-1.5 bg-brand-800/10 border border-brand-800/20 rounded-full text-[9px] font-black text-brand-800 uppercase tracking-[0.2em] animate-pulse">
               💡 Pro Tip: Highlight text to Refine via AI
             </div>
           )}
           {['White', 'Cream', 'Recycled'].map(p => (
             <button key={p} className="px-3 py-1 bg-surface/80 backdrop-blur-md border border-border-main rounded-full text-[9px] font-black opacity-40 hover:text-brand-800 hover:opacity-100 transition-all uppercase tracking-widest">{p}</button>
           ))}
        </div>

        {selection && selectionPos && (
          <div 
            className="absolute z-[9999] animate-in fade-in zoom-in duration-200 pointer-events-auto"
            style={{ 
              top: selectionPos.y - 12, 
              left: selectionPos.x,
              transform: 'translate(-50%, -100%)' 
            }}
          >
            <div className="flex flex-col items-center">
              <button 
                onMouseDown={(e) => e.preventDefault()}
                onClick={(e) => {
                  e.stopPropagation();
                  setIsRefining(true);
                }}
                className="bg-brand-800 text-white px-5 py-2.5 rounded-full flex items-center gap-2 shadow-[0_10px_35px_rgba(0,0,0,0.4)] hover:scale-110 active:scale-95 transition-all text-[12px] font-black uppercase tracking-widest neon-glow border-2 border-brand-400"
              >
                <Sparkles className="w-4 h-4 text-brand-400" />
                REFINE FRAGMENT
              </button>
              <div className="w-4 h-4 bg-brand-800 rotate-45 -mt-2.5 border-r-2 border-b-2 border-brand-400"></div>
            </div>
          </div>
        )}

        {isRefining && (
          <div className="fixed inset-0 z-[60] bg-brand-900/60 backdrop-blur-sm flex items-center justify-center p-4">
             <div className="bg-surface w-full max-w-md rounded-2xl p-6 shadow-2xl border border-brand-500/30 neon-glow">
                <div className="flex items-center gap-2 mb-4">
                   <Sparkles className="w-5 h-5 text-brand-500" />
                   <h3 className="text-lg font-black text-brand-800 uppercase tracking-tight">Holographic Refiner</h3>
                </div>
                <p className="text-[10px] text-foreground opacity-40 font-bold uppercase mb-2">Selected Snippet:</p>
                <div className="bg-surface-soft p-3 rounded-xl border border-border-main text-[11px] text-foreground opacity-80 italic mb-4 max-h-32 overflow-y-auto">
                  "{selection}"
                </div>
                <input 
                  autoFocus
                  placeholder="e.g. 'Make it harder', 'Add a diagram hint', 'Simplify level'..."
                  className="refine-input w-full bg-surface-soft border-2 border-border-main rounded-xl p-3 text-xs font-bold outline-none focus:border-brand-500 transition-all mb-4"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRefine((e.target as HTMLInputElement).value);
                  }}
                />
                <div className="flex justify-end gap-2 text-right">
                   <button 
                     disabled={isProcessingRefinement}
                     onClick={() => { setIsRefining(false); setSelection(""); }} 
                     className="px-4 py-2 text-[10px] font-black uppercase text-foreground opacity-40 hover:opacity-100 disabled:opacity-50"
                   >
                     Cancel
                   </button>
                   <button 
                     disabled={isProcessingRefinement}
                     onClick={() => {
                        const inp = document.querySelector('.refine-input') as HTMLInputElement;
                        if (inp) handleRefine(inp.value);
                     }} 
                     className="px-6 py-2 bg-brand-800 text-white rounded-lg text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-brand-900 transition-all neon-glow"
                   >
                     {isProcessingRefinement ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                     {isProcessingRefinement ? "Synthesizing..." : "Execute Refinement"}
                   </button>
                </div>
             </div>
          </div>
        )}

        <div className="max-w-[850px] mx-auto bg-surface min-h-[1100px] shadow-2xl rounded-sm relative overflow-hidden transition-all duration-500">
           {isGenerating && (
             <div className="absolute inset-0 z-50 bg-surface/80 backdrop-blur-sm flex flex-col items-center justify-center gap-6">
                <div className="relative">
                  <Loader2 className="w-12 h-12 text-brand-800 animate-spin" />
                  <Sparkles className="w-5 h-5 text-brand-400 absolute -top-1 -right-1 animate-pulse" />
                </div>
                <div className="text-center">
                  <h3 className="font-black text-brand-800 tracking-widest uppercase text-sm">Synchronizing Neural Core</h3>
                  <p className="text-[10px] font-bold text-foreground opacity-40 mt-2 tracking-widest uppercase">Applying Bloom's Taxonomy & Pedagogical Logic...</p>
                </div>
                <div className="w-48 h-1 bg-surface-soft rounded-full overflow-hidden mt-4">
                  <div className="h-full bg-brand-800 animate-loading-bar"></div>
                </div>
             </div>
           )}

           {previewHtml ? (
             <iframe 
                srcDoc={previewHtml} 
                className="w-full h-full min-h-[1100px] border-none"
                title="Preview"
             />
           ) : (
             <div className="p-[16mm] h-full">
               <div className="flex justify-between items-end border-b-4 border-brand-800 pb-4 mb-8">
                 <div>
                   <h2 className="text-4xl font-black text-brand-800">EDUMERC</h2>
                   <p className="text-[10px] tracking-[0.5em] font-bold mt-1 uppercase text-foreground opacity-40">Examinations Services</p>
                 </div>
                 <div className="bg-brand-800 text-white text-center p-3 rounded-lg min-w-[80px]">
                   <div className="text-[9px] font-bold opacity-60">YEAR</div>
                   <div className="text-xl font-black italic">2026</div>
                 </div>
               </div>
               <div className="flex flex-col items-center justify-center h-[600px] text-foreground opacity-40 gap-4">
                  <FileText className="w-16 h-16 opacity-20" />
                  <p className="font-bold tracking-widest text-xs uppercase opacity-40">Ready to Generate Content</p>
               </div>
             </div>
           )}
        </div>
      </section>
    </div>
  );
}

function ScenarioView({ 
  setPreviewHtml, 
  isGenerating, 
  setIsGenerating, 
  refreshLibrary,
  theme,
  setLastRaw,
  setLastConfig,
  lastConfig
}: any) {
  const [themeInput, setThemeInput] = useState("");
  const [level, setLevel] = useState(lastConfig?.level || "Primary 7");
  const [subject, setSubject] = useState(lastConfig?.subject || "Mathematics");
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("Standard");
  const [term, setTerm] = useState(lastConfig?.term || "Term 1");
  const [period, setPeriod] = useState("MOT");
  const [config, setConfig] = useState<any>({ subjects: [], levels: [], syllabus: {} });

  useEffect(() => {
    fetch(`${API_BASE}/api/syllabus/config`)
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(() => {});
  }, []);

  const availableSubjects = config.subjects.filter((s: string) => 
    config.syllabus?.[s]?.[level]
  );

  useEffect(() => {
    if (availableSubjects.length > 0 && !availableSubjects.includes(subject)) {
      setSubject(availableSubjects[0]);
    }
  }, [level, availableSubjects]);

  // Filter topics based on subject and level
  const availableTopics = config.syllabus?.[subject]?.[level] || [];

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/scenario`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          theme: themeInput,
          topic,
          difficulty,
          level,
          subject,
          term: `${term} (${period})`,
          brand_name: "EDUMERC"
        })
      });
      const data = await res.json();
      setPreviewHtml(data.html);
      setLastRaw(data.raw);
      setLastConfig({ subject, level, term: `${term} (${period})` });
      refreshLibrary();
    } catch (e) {
      alert("Scenario generation failed.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-left-4 duration-300">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="sec-label">Grade / Level</label>
          <select 
            value={level}
            onChange={(e) => { setLevel(e.target.value); setTopic(""); }}
            className="w-full bg-surface-soft border border-border-main rounded-xl p-3 text-xs font-bold outline-none appearance-none cursor-pointer"
          >
            {config.levels.map((l: string) => <option key={l}>{l}</option>)}
          </select>
        </div>
        <div>
          <label className="sec-label">Subject</label>
          <select 
            value={subject}
            onChange={(e) => { setSubject(e.target.value); setTopic(""); }}
            className="w-full bg-surface-soft border border-border-main rounded-xl p-3 text-xs font-bold outline-none appearance-none cursor-pointer"
          >
             {availableSubjects.map((s: string) => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="sec-label">Academic Term</label>
          <div className="flex gap-1 bg-surface-soft p-1 rounded-xl border border-border-main">
             {["Term 1", "Term 2", "Term 3"].map(t => (
               <button 
                 key={t} 
                 onClick={() => setTerm(t)}
                 className={cn(
                   "flex-1 py-1.5 rounded-lg text-[9px] font-black transition-all",
                   term === t ? "bg-surface shadow-md text-brand-800" : "text-foreground opacity-40 hover:opacity-100"
                 )}
               >
                 T{t.split(' ')[1]}
               </button>
             ))}
          </div>
        </div>
        <div>
          <label className="sec-label">Exam Period</label>
          <div className="flex gap-1 bg-brand-800/5 p-1 rounded-xl border border-brand-800/10">
             {["BOT", "MOT", "EOT"].map(p => (
               <button 
                 key={p} 
                 onClick={() => setPeriod(p)}
                 className={cn(
                   "flex-1 py-1.5 rounded-lg text-[9px] font-black transition-all",
                   period === p ? "bg-brand-800 text-white shadow-md" : "text-brand-800 opacity-40 hover:opacity-100"
                 )}
               >
                 {p}
               </button>
             ))}
          </div>
        </div>
      </div>

      <div>
        <label className="sec-label">Target Pedagogical Topic</label>
        <select 
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="w-full bg-surface-soft border border-border-main rounded-xl p-3 text-xs font-bold outline-none appearance-none cursor-pointer"
        >
          <option value="">Select Topic from Syllabus...</option>
          {availableTopics.map((t: string) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      <div>
        <label className="sec-label">Target Complexity</label>
        <div className="flex gap-1 bg-surface-soft p-1 rounded-xl border border-border-main">
           {["Basic", "Standard", "Complex", "Integrated"].map(d => (
             <button 
               key={d} 
               onClick={() => setDifficulty(d)}
               className={cn(
                 "flex-1 py-2 rounded-lg text-[9px] font-bold transition-all uppercase tracking-tighter",
                 difficulty === d ? "bg-surface text-brand-800 shadow-sm" : "text-foreground opacity-40 hover:opacity-100"
               )}
             >
               {d}
             </button>
           ))}
        </div>
      </div>

      <div>
        <label className="sec-label">Narrative Context (Optional)</label>
        <textarea 
          value={themeInput}
          onChange={(e) => setThemeInput(e.target.value)}
          placeholder="e.g. A busy town market, construction site, farming scenario..."
          className="w-full bg-surface-soft border-2 border-border-main rounded-2xl p-4 text-xs font-bold font-main outline-none focus:border-brand-500 transition-all min-h-[100px]"
        />
      </div>

      <button 
        disabled={isGenerating}
        onClick={handleGenerate}
        className="w-full py-4 bg-brand-800 text-white rounded-2xl font-black uppercase tracking-[0.2em] shadow-xl hover:bg-brand-900 transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2 group"
      >
        {isGenerating ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Synthesizing Scenario...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5 group-hover:animate-pulse" />
            GENERATE TARGETED SCENARIO
          </>
        )}
      </button>

      <div className="p-4 bg-surface-soft border border-border-main rounded-2xl flex items-start gap-3 transition-opacity duration-500">
         <div className="p-2 bg-brand-800/10 rounded-lg">
           <AlertCircle className="w-4 h-4 text-brand-800" />
         </div>
         <p className="text-[10px] text-foreground opacity-60 font-medium leading-relaxed">
           Targeted scenarios use <span className="font-black text-brand-800">Topic Saturation</span> data to bridge knowledge gaps. Higher complexity levels require synthetic evaluation and multi-concept integration.
         </p>
      </div>
    </div>
  );
}

function GeneratorControls({ 
  setPreviewHtml, 
  isGenerating, 
  setIsGenerating, 
  refreshLibrary, 
  theme,
  selection,
  setIsRefining,
  setLastRaw,
  setLastConfig,
  lastRaw,
  lastConfig
}: any) {
  const [mode, setMode] = useState<Mode>("Exams");
  const [level, setLevel] = useState("Primary 7");
  const [subject, setSubject] = useState("Mathematics");
  const [term, setTerm] = useState("Term 1");
  const [period, setPeriod] = useState("MOT");
  const [qCount, setQCount] = useState(20);
  const [topic, setTopic] = useState("");
  const [config, setConfig] = useState<any>({ subjects: [], levels: [] });

  useEffect(() => {
    fetch(`${API_BASE}/api/syllabus/config`)
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(() => {});
  }, []);

  const availableSubjects = config.subjects.filter((s: string) => 
    config.syllabus?.[s]?.[level]
  );

  useEffect(() => {
    if (availableSubjects.length > 0 && !availableSubjects.includes(subject)) {
      setSubject(availableSubjects[0]);
    }
  }, [level, availableSubjects]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode, level, subject,
          term: `${term} (${period})`,
          question_count: qCount,
          topic,
          brand_name: "EDUMERC"
        })
      });
      const data = await res.json();
      setPreviewHtml(data.html);
      setLastRaw(data.raw);
      setLastConfig({ subject, level });
      refreshLibrary();
    } catch (e) {
      alert("Generation failed.");
    } finally {
      setIsGenerating(false);
    }
  };
  
  return (
    <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-left-4 duration-300">
      <div>
        <label className="sec-label">Generation Mode</label>
        <div className="grid grid-cols-3 gap-2">
          {["Exams", "Lesson Notes", "Schemes of Work"].map((m) => (
            <button 
              key={m}
              onClick={() => setMode(m as Mode)}
              className={cn(
                "py-2 px-2 rounded-lg text-[10px] font-bold border transition-all shadow-sm",
                mode === m ? "bg-brand-800 text-white border-brand-800 shadow-brand-800/20" : "bg-surface-soft text-foreground opacity-50 border-border-main hover:border-brand-800 hover:opacity-100"
              )}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="sec-label">Grade / Level</label>
          <select 
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="w-full bg-surface-soft border border-border-main rounded-lg p-2.5 text-xs font-bold outline-none"
          >
            {config.levels.map((l: string) => <option key={l}>{l}</option>)}
          </select>
        </div>
        <div>
          <label className="sec-label">Subject</label>
          <select 
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full bg-surface-soft border border-border-main rounded-lg p-2.5 text-xs font-bold outline-none cursor-pointer"
          >
             {availableSubjects.map((s: string) => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="sec-label">Academic Term</label>
          <div className="flex gap-1 bg-surface-soft p-1 rounded-lg border border-border-main">
             {["Term 1", "Term 2", "Term 3"].map(t => (
               <button 
                 key={t} 
                 onClick={() => setTerm(t)}
                 className={cn(
                   "flex-1 py-1.5 rounded-md text-[9px] font-black transition-all",
                   term === t ? "bg-surface shadow-md text-brand-800" : "text-foreground opacity-40 hover:opacity-100"
                 )}
               >
                 T{t.split(' ')[1]}
               </button>
             ))}
          </div>
        </div>
        <div>
          <label className="sec-label">Exam Period</label>
          <div className="flex gap-1 bg-brand-800/5 p-1 rounded-lg border border-brand-800/10">
             {["BOT", "MOT", "EOT"].map(p => (
               <button 
                 key={p} 
                 onClick={() => setPeriod(p)}
                 className={cn(
                   "flex-1 py-1.5 rounded-md text-[9px] font-black transition-all",
                   period === p ? "bg-brand-800 text-white shadow-md" : "text-brand-800 opacity-40 hover:opacity-100"
                 )}
               >
                 {p}
               </button>
             ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="sec-label">Question Count</label>
          <input 
            type="number" 
            value={qCount} 
            onChange={(e) => setQCount(parseInt(e.target.value))}
            className="w-full bg-surface-soft border border-border-main rounded-lg p-2.5 text-xs font-bold outline-none focus:border-brand-500 transition-all" 
          />
        </div>
        <div>
           <label className="sec-label">Topic Focus (Optional)</label>
           <input 
            type="text" 
            value={topic} 
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Algebra, Fractions..."
            className="w-full bg-surface-soft border border-border-main rounded-lg p-2.5 text-xs font-bold outline-none focus:border-brand-500 transition-all" 
          />
        </div>
      </div>

      <button 
        disabled={isGenerating}
        onClick={handleGenerate}
        className={cn(
          "w-full py-4 mt-6 rounded-2xl flex items-center justify-center gap-3 transition-all",
          theme === 'midnight' ? "bg-brand-500 text-black neon-glow hover:bg-brand-400" : "bg-brand-800 text-white hover:bg-brand-900 shadow-xl"
        )}
      >
        {isGenerating ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Play className="w-4 h-4 fill-current" />
        )}
        GENERATE {mode.toUpperCase()}
      </button>

      <button 
        disabled={!selection || isGenerating}
        onClick={() => setIsRefining(true)}
        className={cn(
          "w-full py-3 rounded-xl border-2 font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 transition-all mt-4",
          selection 
            ? "border-brand-500/50 text-brand-800 hover:bg-brand-500/5" 
            : "border-border-main text-foreground cursor-not-allowed opacity-30"
        )}
      >
        <Sparkles className="w-3.5 h-3.5" />
        {selection ? "Refine Selection" : "Select Text to Refine"}
      </button>

      <div className="p-4 rounded-xl bg-surface-soft border border-border-main border-dashed">
         <div className="flex items-center gap-2 mb-2 px-1">
           <Download className="w-4 h-4 text-brand-800" />
           <span className="text-[10px] font-black text-foreground opacity-60 uppercase">Export Options</span>
         </div>
         <div className="flex flex-col gap-2">
           <button 
             onClick={async () => {
                if (!lastRaw) {
                  alert("Please generate a document first.");
                  return;
                }
                try {
                  const res = await fetch(`${API_BASE}/api/export/docx`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      mode: mode,
                      level: level,
                      subject: subject,
                      term: term,
                      question_count: qCount,
                      content_override: typeof lastRaw === 'string' ? lastRaw : JSON.stringify(lastRaw),
                      brand_name: "EDUMERC"
                    })
                  });
                  if (!res.ok) throw new Error("Export failed");
                  const blob = await res.blob();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `EduQuest_${subject}_${level}.docx`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                } catch (e) {
                  console.error(e);
                  alert("DOCX Export failed.");
                }
              }}
             className="w-full py-2 bg-surface border border-border-main rounded-lg text-xs font-bold text-foreground opacity-50 hover:opacity-100 hover:border-brand-800 hover:text-brand-800 transition-all"
           >
             Download Microsoft Word (.docx)
           </button>
         </div>
      </div>
    </div>
  )
}

function LibraryView({ library, onProjectLoad, theme }: any) {
  return (
    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-left-4 duration-300">
      <label className="sec-label">Recent Generations</label>
      {library.length === 0 ? (
        <div className="text-[10px] text-foreground opacity-40 text-center py-8 font-bold uppercase tracking-widest">Library is empty</div>
      ) : library.map((proj: any, i: number) => (
          <div 
            key={proj.id} 
            style={{ animationDelay: `${i * 0.05}s` }}
            onClick={async () => {
               try {
                 const res = await fetch(`${API_BASE}/api/generate`, {
                   method: "POST",
                   headers: { "Content-Type": "application/json" },
                   body: JSON.stringify({
                     mode: proj.mode,
                     subject: proj.subject,
                     level: proj.level || "Primary 7",
                     term: proj.term || "Term 1",
                     question_count: 20,
                     content_override: proj.data
                   })
                 });
                 const data = await res.json();
                 onProjectLoad(data.raw, data.html, proj.subject, proj.level || "Primary 7");
               } catch(e) {
                 alert("Could not rebuild document from library.");
               }
            }}
            className={cn(
              "group p-4 rounded-xl border transition-all cursor-pointer shadow-sm hover:shadow-lg flex justify-between items-start animate-stagger",
              theme === 'midnight' 
                ? "bg-surface/50 border-border-main hover:border-brand-500 hover:neon-glow" 
                : "bg-surface-soft/50 border-border-main hover:bg-surface hover:border-brand-800/30"
            )}
          >
           <div className="flex-1 min-w-0 pr-2">
             <div className="text-[11px] font-black text-foreground truncate">{proj.title}</div>
             <div className="text-[9px] font-bold text-foreground opacity-40 mt-0.5 tracking-wider uppercase">{proj.timestamp}</div>
           </div>
           <BookOpen className="w-4 h-4 text-foreground opacity-20 group-hover:text-brand-800 group-hover:opacity-100 transition-all flex-shrink-0" />
        </div>
      ))}
    </div>
  )
}

function RadarChart({ data, theme }: { data: any, theme: string }) {
  const points = [
    { label: 'recall', x: 50, y: 20 },
    { label: 'comprehension', x: 85, y: 45 },
    { label: 'application', x: 75, y: 85 },
    { label: 'analysis', x: 25, y: 85 },
    { label: 'evaluation', x: 15, y: 45 }
  ];

  return (
    <div className="w-full flex justify-center">
      <svg viewBox="0 0 100 100" className="w-full h-48 drop-shadow-xl">
        {/* Polygons */}
        {[0.2, 0.4, 0.6, 0.8, 1].map((r) => (
          <polygon
            key={r}
            points={points.map(p => `${50 + (p.x-50)*r},${50 + (p.y-50)*r}`).join(' ')}
            fill="none"
            stroke="var(--border-color)"
            strokeWidth="0.5"
            strokeDasharray="2,2"
          />
        ))}

        {/* Radar Area */}
        <polygon
          points={points.map(p => `${50 + (p.x-50)*(data[p.label]||0)/100},${50 + (p.y-50)*(data[p.label]||0)/100}`).join(' ')}
          fill="url(#radarGradient)"
          fillOpacity={theme === 'midnight' ? "0.4" : "0.6"}
          stroke="var(--brand-500)"
          strokeWidth="1.5"
          className="transition-all duration-1000"
        />

        {/* Axis Lines */}
        {points.map((p, i) => (
          <g key={i}>
            <line 
              x1="50" y1="50" x2={p.x} y2={p.y} 
              stroke="var(--border-color)" 
              strokeWidth="0.5" 
            />
            <text
              x={50 + (p.x-50)*1.25}
              y={50 + (p.y-50)*1.25}
              textAnchor="middle"
              className="text-[9px] font-black uppercase tracking-widest fill-foreground opacity-50"
            >
              {p.label}
            </text>
          </g>
        ))}

        <defs>
          <linearGradient id="radarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--brand-500)" />
            <stop offset="100%" stopColor="var(--brand-800)" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
}

function InsightsView({ theme, previewHtml, lastRaw, lastConfig, onBridge }: { theme: string, previewHtml: string, lastRaw?: string, lastConfig?: any, onBridge?: (topic: string) => void }) {
  const [data, setData] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [subject, setSubject] = useState(lastConfig?.subject || "Mathematics");
  const [level, setLevel] = useState(lastConfig?.level || "Primary 7");
  const [config, setConfig] = useState<any>({ subjects: [], levels: [] });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [drilldownData, setDrilldownData] = useState<{topic: string, fragments: {content: string, source: string, page: string|number}[]} | null>(null);
  const [isDrilling, setIsDrilling] = useState(false);

  const fetchDrilldown = async (topic: string) => {
    if (selectedTopic === topic) {
      setSelectedTopic(null);
      setDrilldownData(null);
      return;
    }
    setSelectedTopic(topic);
    setIsDrilling(true);
    setDrilldownData(null);
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/drilldown?topic=${encodeURIComponent(topic)}&subject=${subject}&level=${level}`);
      const d = await res.json();
      setDrilldownData(d);
    } catch (e) {
      setDrilldownData({ topic, fragments: [] });
    } finally {
      setIsDrilling(false);
    }
  };

  const [isQuickIndexing, setIsQuickIndexing] = useState(false);
  const [quickIndexResult, setQuickIndexResult] = useState<string | null>(null);

  const handleQuickIndex = async (topic: string) => {
    setIsQuickIndexing(true);
    setQuickIndexResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/quick-index`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, subject, level })
      });
      const d = await res.json();
      setQuickIndexResult(d.preview || "Indexed successfully.");
      // Refresh coverage data to update the heatmap
      const cov = await fetch(`${API_BASE}/api/insights/coverage?subject=${subject}&level=${level}`);
      setData(await cov.json());
    } catch (e) {
      setQuickIndexResult("❌ Indexing failed. Please check your API connection.");
    } finally {
      setIsQuickIndexing(false);
    }
  };

  useEffect(() => {
    fetch(`${API_BASE}/api/syllabus/config`)
      .then(res => res.json())
      .then(d => setConfig(d))
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/api/insights/coverage?subject=${subject}&level=${level}`)
      .then(res => res.json())
      .then(json => setData(json))
      .catch(() => {});
  }, [subject, level]);

  const [auditError, setAuditError] = useState<string | null>(null);

  const handleDeepAudit = async () => {
    setAuditError(null);

    // Use lastRaw if available (much cleaner for AI), otherwise fallback to stripping previewHtml
    let contentToAudit = lastRaw;
    
    // If lastRaw is an object (common from API responses), stringify it
    if (contentToAudit && typeof contentToAudit === 'object') {
        contentToAudit = JSON.stringify(contentToAudit);
    }
    
    if (!contentToAudit) contentToAudit = previewHtml;

    if (!contentToAudit || contentToAudit.trim().length < 50) {
      setAuditError("Insufficient content detected. Please generate or load a document first.");
      return;
    }

    // If we only have HTML, try to strip noise
    if (typeof contentToAudit === 'string' && contentToAudit.includes("<html")) {
        contentToAudit = contentToAudit.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
                                     .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
                                     .replace(/<[^>]+>/g, ' ')
                                     .replace(/\s+/g, ' ')
                                     .trim();
    }

    setIsAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: contentToAudit, subject, level })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `Server error ${res.status}`);
      }
      const d = await res.json();
      setAnalysis(d);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setAuditError(msg);
      console.error("[DeepAudit]", msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-left-4 duration-300 pb-20">
      <div className="flex flex-col gap-2">
        <label className="sec-label">Institutional Context</label>
        <div className="grid grid-cols-2 gap-2">
           <select 
             value={subject} 
             onChange={e => setSubject(e.target.value)}
             className="bg-surface-soft border border-border-main rounded-xl p-3 text-[10px] font-black outline-none appearance-none cursor-pointer"
           >
             {config.subjects.map((s: string) => <option key={s}>{s}</option>)}
           </select>
           <select 
             value={level} 
             onChange={e => setLevel(e.target.value)}
             className="bg-surface-soft border border-border-main rounded-xl p-3 text-[10px] font-black outline-none appearance-none cursor-pointer"
           >
             {config.levels.map((l: string) => <option key={l}>{l}</option>)}
           </select>
        </div>
      </div>

      {/* CORE SYLLABUS ALIGNMENT */}
      <div className={cn("p-6 rounded-3xl border transition-all relative overflow-hidden", theme === 'midnight' ? "glass neon-glow" : "bg-surface border-border-main shadow-sm")}>
         <div className="flex justify-between items-end mb-8 relative z-10">
            <div>
              <div className="text-[10px] font-black opacity-40 uppercase tracking-widest mb-2">Syllabus Saturation</div>
              <div className="text-4xl font-black text-brand-800">{data?.coverage_percent || 0}%</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] font-black opacity-40 uppercase tracking-widest mb-2">Module Pulse</div>
              <div className="text-xs font-black">{data?.found_count || 0} / {data?.total_count || 0} Indexed</div>
            </div>
         </div>

         <div className="h-4 w-full bg-surface-soft rounded-full overflow-hidden relative mb-4 border border-border-main">
            <div 
              className="h-full transition-all duration-1000 bg-brand-800" 
              style={{ width: `${data?.coverage_percent || 0}%` }}
            >
               <div className="w-full h-full animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent bg-[length:200%_100%]"></div>
            </div>
         </div>
         <p className="text-[9px] font-bold text-foreground opacity-40 leading-tight">National Standards compliance verified against Ministry Syllabus v2026.</p>
         
         {/* Decorative Grid */}
         <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 0)', backgroundSize: '20px 20px' }}></div>
      </div>

      {/* KNOWLEDGE BANK HEATMAP */}
      <div className="flex flex-col gap-4">
        <label className="sec-label">Institutional Knowledge Bank <span className="font-normal opacity-50 normal-case">— click a topic to inspect</span></label>
        <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
          {data?.topic_density && Object.entries(data.topic_density).map(([topic, count]: [string, any]) => (
            <div
              key={topic}
              onClick={() => fetchDrilldown(topic)}
              title={count > 0 ? `Click to inspect ${topic}` : `Click to AI-index ${topic}`}
              className={cn(
                "h-12 rounded-xl border flex flex-col items-center justify-center transition-all p-2 relative overflow-hidden select-none cursor-pointer",
                count > 0
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.1)] hover:scale-105 active:scale-95"
                  : "bg-surface-soft border-border-main text-foreground opacity-50 hover:scale-105 active:scale-95",
                selectedTopic === topic && "ring-2 ring-brand-500 scale-105 opacity-100"
              )}
            >
              <div className={cn("text-[7px] font-black uppercase text-center leading-[1.1] z-10", count === 0 && "opacity-40")}>
                {topic}
              </div>
              <div className={cn("absolute top-0 right-0 px-1 py-0.5 text-[6px] font-black rounded-bl-md", theme === 'midnight' ? "bg-white/10" : "bg-white/20")}>
                {count > 0 ? `${count} ✦` : "+ AI"}
              </div>
            </div>
          ))}
        </div>

        {/* DRILL-DOWN / QUICK-INDEX PANEL */}
        {selectedTopic && (
          <div className={cn(
            "mt-2 rounded-2xl border overflow-hidden animate-in slide-in-from-top-2 duration-300 shadow-2xl glass-premium",
            data?.topic_density?.[selectedTopic] > 0
              ? "border-emerald-500/20"
              : "border-amber-500/20"
          )}>
            {/* Panel Header */}
            <div className={cn(
              "flex items-center justify-between px-4 py-3 text-white transition-colors duration-500",
              data?.topic_density?.[selectedTopic] > 0 ? "bg-emerald-600" : "bg-brand-800"
            )}>
              <div className="flex items-center gap-2">
                {data?.topic_density?.[selectedTopic] > 0
                  ? <BookOpen className="w-3.5 h-3.5" />
                  : <Sparkles className="w-3.5 h-3.5" />
                }
                <span className="text-[10px] font-black uppercase tracking-widest text-white/90">
                  {data?.topic_density?.[selectedTopic] > 0
                    ? `${selectedTopic} — Knowledge Fragments`
                    : `${selectedTopic} — Not Indexed`
                  }
                </span>
              </div>
              <button onClick={() => { setSelectedTopic(null); setDrilldownData(null); setQuickIndexResult(null); }} className="text-white/70 hover:text-white text-xs font-black transition-colors">✕</button>
            </div>

            <div className="p-4">
              {/* INDEXED TOPIC: show fragments */}
              {data?.topic_density?.[selectedTopic] > 0 ? (
                isDrilling ? (
                  <div className="flex items-center gap-3 justify-center py-6">
                    <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
                    <span className="text-[10px] font-black text-brand-500 uppercase tracking-widest animate-pulse">Scanning knowledge base...</span>
                  </div>
                ) : drilldownData?.fragments?.length === 0 ? (
                  <div className="text-center py-4">
                    <p className="text-[10px] font-black text-foreground opacity-40 uppercase tracking-widest">No fragments found for exact keyword match.</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-64 overflow-y-auto custom-scroll pr-1">
                    {drilldownData?.fragments?.map((frag, i) => (
                      <div key={i} className="rounded-xl p-3 shadow-sm border border-border-main transition-all card-premium">
                        <div className="flex justify-between items-center mb-2">
                          <div className="flex items-center gap-2">
                            <FileText className="w-3 h-3 text-brand-500" />
                            <span className="text-[9px] font-black text-foreground opacity-60 uppercase truncate max-w-[200px]">{frag.source}</span>
                          </div>
                          <span className="text-[8px] font-bold text-foreground opacity-40 whitespace-nowrap tabular-nums">Pg. {frag.page}</span>
                        </div>
                        <p className="text-[10px] text-foreground opacity-60 leading-relaxed font-medium">{frag.content}</p>
                      </div>
                    ))}
                  </div>
                )
              ) : (
                /* UNINDEXED TOPIC: show Quick Index option */
                <div className="flex flex-col items-center gap-4 py-4 text-center">
                  {quickIndexResult ? (
                    <>
                      <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 animate-bounce" />
                      </div>
                      <div>
                        <p className="text-[10px] font-black uppercase tracking-widest mb-1 text-emerald-500">Indexed Successfully!</p>
                        <p className="text-[9px] text-foreground opacity-40 leading-relaxed max-w-[300px] font-medium">{quickIndexResult}</p>
                      </div>
                      <button
                        onClick={() => { setSelectedTopic(null); setQuickIndexResult(null); }}
                        className="px-4 py-1.5 bg-brand-800 text-white text-[9px] font-black rounded-full uppercase tracking-widest hover:scale-105 transition-all shadow-lg"
                      >
                        Done
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center">
                        <AlertCircle className="w-4 h-4 text-amber-500" />
                      </div>
                      <div>
                        <p className="text-[10px] font-black uppercase tracking-widest mb-1 text-amber-500">No content indexed for &apos;{selectedTopic}&apos;</p>
                        <p className="text-[9px] text-foreground opacity-40 leading-relaxed max-w-[280px] font-medium">Push to Neural Ingestion for automated resource synthesis.</p>
                      </div>
                      <button
                        onClick={() => handleQuickIndex(selectedTopic)}
                        disabled={isQuickIndexing}
                        className="flex items-center gap-2 px-5 py-2 bg-brand-800 text-white text-[9px] font-black rounded-full uppercase tracking-widest hover:scale-105 active:scale-95 transition-all disabled:opacity-50 shadow-xl neon-glow"
                      >
                        {isQuickIndexing ? <><Loader2 className="w-3 h-3 animate-spin" /> Neural Ingest...</> : <><Sparkles className="w-3 h-3" /> AI Quick Ingest</>}
                      </button>
                      <p className="text-[8px] text-foreground opacity-40 font-bold uppercase tracking-tighter">Synthesizing benchmark data · ~10s</p>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        <p className="text-[8px] font-bold text-foreground opacity-40 uppercase tracking-widest text-center">
          🟢 Green = Indexed (click to inspect) &nbsp;·&nbsp; Gray = Not indexed (click to AI-index)
        </p>
      </div>

      {/* PEDAGOGICAL DEEP AUDIT */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
           <label className="sec-label">Pedagogical X-Ray</label>
            <button 
              onClick={handleDeepAudit}
              disabled={isAnalyzing}
              className="px-3 py-1 bg-brand-800 text-white text-[9px] font-black rounded-full uppercase tracking-widest hover:scale-105 active:scale-95 transition-all"
           >
             {isAnalyzing ? 'Analyzing...' : 'Trigger Deep Audit'}
           </button>
        </div>

        {auditError && (
          <div className="p-4 bg-rose-50 border border-rose-100 rounded-2xl animate-in shake duration-500">
             <div className="flex items-center gap-2 mb-1">
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                <span className="text-[10px] font-black text-rose-700 uppercase tracking-widest">Audit Restriction</span>
             </div>
             <p className="text-[9px] text-rose-500 font-bold">{auditError}</p>
          </div>
        )}

        {!analysis ? (
           <div className="p-12 rounded-3xl border-2 border-dashed border-border-main flex flex-col items-center justify-center text-center gap-3">
              <Sparkles className="w-8 h-8 text-foreground opacity-20" />
              <div className="text-[10px] font-black text-foreground opacity-40 uppercase tracking-widest">Awaiting Content Sample</div>
              <p className="text-[9px] text-foreground opacity-50 max-w-[200px] font-bold">Generate or load curriculum to perform a pedagogical audit.</p>
           </div>
        ) : (
           <div className="space-y-6 animate-in zoom-in-95 duration-500">
              {/* BLOOM'S RADAR */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 <div className="p-5 rounded-3xl border transition-all card-premium">
                    <div className="text-[9px] font-black uppercase mb-4 tracking-widest text-brand-500">Pedagogical Balance (Bloom's Taxonomy)</div>
                    <RadarChart data={analysis.bloom} theme={theme} />
                 </div>

                 <div className="grid grid-rows-2 gap-4">
                    <div className="p-5 rounded-3xl border transition-all flex flex-col justify-center card-premium">
                       <div className="text-[9px] font-black uppercase text-foreground opacity-40 mb-2 tracking-widest">Readability Index</div>
                       <div className="text-2xl font-black text-brand-500">{analysis.readability}%</div>
                       <div className="text-[8px] font-bold text-foreground opacity-50 uppercase mt-1">Level {level} Precision</div>
                    </div>
                    <div className="p-5 rounded-3xl border transition-all flex flex-col justify-center card-premium">
                       <div className="text-[9px] font-black uppercase text-foreground opacity-40 mb-2 tracking-widest">Completion Time</div>
                       <div className="text-2xl font-black text-brand-500">~{analysis.time_estimate}m</div>
                       <div className="text-[8px] font-bold text-foreground opacity-50 uppercase mt-1">Est. Student Duration</div>
                    </div>
                 </div>
              </div>

              {/* STRESS CURVE */}
              <div className={cn("p-6 rounded-3xl border transition-all", theme === 'midnight' ? "glass-premium border-white/5" : "bg-surface-soft border-border-main")}>
                 <div className="text-[9px] font-black uppercase text-foreground opacity-40 mb-6 tracking-widest">Student Stress Mapping (Difficulty Map)</div>
                 <div className="h-24 w-full flex items-end gap-1">
                    {analysis.difficulty_distribution.map((val: number, i: number) => (
                      <div key={i} className="flex-1 flex flex-col items-center group">
                         <div 
                           className={cn(
                             "w-full rounded-t-lg transition-all duration-700 shadow-sm",
                             val > 70 ? "bg-rose-500 mb-1" : val > 40 ? (theme === 'midnight' ? "bg-cyan-500" : "bg-brand-800") : "bg-emerald-500"
                           )} 
                           style={{ height: `${val}%` }}
                         ></div>
                         <div className="text-[6px] font-black mt-2 opacity-30">Q{i+1}</div>
                      </div>
                    ))}
                 </div>
              </div>

              {/* AUDITOR SUMMARY */}
              <div className="p-6 rounded-3xl shadow-xl relative overflow-hidden transition-all bg-brand-800 text-white neon-glow">
                 <Sparkles className="absolute -top-4 -right-4 w-24 h-24 rotate-12 text-white opacity-10" />
                 <div className="text-[9px] font-black uppercase tracking-widest mb-3 text-white/60">Chief Auditor’s Verdict</div>
                 <p className="text-xs font-bold leading-relaxed pr-8 italic text-white/90">"{analysis.summary}"</p>
              </div>

              {/* GRANULAR SYLLABUS AUDIT */}
              <div className="p-6 rounded-3xl border shadow-sm transition-all card-premium">
                <div className="flex justify-between items-center mb-6">
                    <div className="text-[10px] font-black uppercase text-foreground opacity-40 tracking-widest">Syllabus Saturation Audit</div>
                    <div className="px-2 py-0.5 text-white text-[8px] font-black rounded uppercase tracking-tighter bg-brand-800">
                       {Object.keys(analysis.topic_saturation || {}).length} Domains Indexed
                    </div>
                </div>
                <div className="space-y-5">
                    {Object.entries(analysis.topic_saturation || {}).map(([topic, pct]: [string, any]) => (
                      <div key={topic} className="space-y-2">
                        <div className="flex justify-between items-end">
                            <span className="text-[10px] font-black text-foreground opacity-60 uppercase tracking-tight truncate max-w-[80%]">{topic}</span>
                            <span className={cn(
                               "text-[10px] font-black tabular-nums",
                               pct > 80 ? "text-emerald-500" : pct > 40 ? "text-brand-500" : "text-rose-500"
                            )}>
                               {pct}%
                            </span>
                        </div>
                        <div className="h-1.5 w-full rounded-full overflow-hidden border relative bg-surface-soft border-border-main">
                            <div 
                              className={cn(
                                "h-full transition-all duration-1000",
                                pct > 80 ? "bg-emerald-500" : pct > 40 ? "bg-brand-500" : "bg-rose-500"
                              )}
                              style={{ width: `${pct}%` }}
                            >
                               <div className="w-full h-full animate-pulse bg-white/10"></div>
                            </div>
                        </div>
                      </div>
                    ))}

                    {analysis.missing_critical_topics?.length > 0 && (
                      <div className="mt-8 pt-6 border-t border-dashed border-border-main">
                        <div className="flex items-center gap-2 mb-3">
                           <AlertCircle className="w-3.5 h-3.5 text-red-500" />
                           <div className="text-[9px] font-black text-red-500 uppercase tracking-widest">High-Priority Subject Voids</div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {analysis.missing_critical_topics.map((t: string) => (
                              <div key={t} className="px-3 py-1 bg-red-50 text-red-600 text-[9px] font-black rounded-lg border border-red-100 hover:bg-red-100 transition-colors cursor-help">
                                 {t}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                </div>
              </div>
           </div>
        )}
      </div>

      <div className="flex flex-col gap-4">
        <label className="sec-label">Institutional Gap Analysis</label>
        {data?.gaps?.length > 0 ? (
          <div className="flex flex-col gap-2">
            {data.gaps.map((gap: string) => (
              <div key={gap} className="p-4 rounded-2xl border flex items-center justify-between group transition-all bg-rose-500/10 border-rose-500/20 hover:border-rose-500/50">
                <div className="flex items-center gap-3">
                   <div className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></div>
                   <span className="text-[10px] font-black text-rose-500 uppercase tracking-widest">{gap}</span>
                </div>
                <button 
                  onClick={() => onBridge?.(gap)}
                  className="text-[8px] font-black text-brand-800 hover:underline uppercase tracking-tighter"
                >
                  Bridge Now
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center gap-3 text-emerald-500">
             <CheckCircle2 className="w-4 h-4" />
             <span className="text-[10px] font-black uppercase tracking-widest">No Curriculum Voids Detected</span>
          </div>
        )}
      </div>
    </div>
  )
}

// ── INGESTION SUB-VIEW ──
function IngestionView({ theme }: any) {
  const [stats, setStats] = useState<any>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [extractResults, setExtractResults] = useState<any[]>([]);
  const [currentFile, setCurrentFile] = useState<string>("");
  const [resources, setResources] = useState<any>(null);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/ingestion/stats`);
      const data = await res.json();
      setStats(data);
    } catch (e) {}
  };

  const fetchResources = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/health/resources`);
      const data = await res.json();
      setResources(data);
    } catch (e) {}
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchResources, 2000); 
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsExtracting(true);
    setExtractResults([]);
    setCurrentFile("Initializing engine...");

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
       formData.append("files", files[i]);
    }

    try {
      const response = await fetch(`${API_BASE}/api/ingestion/extract`, {
        method: "POST",
        body: formData,
      });

      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.trim()) {
            try {
              const res = JSON.parse(line);
              setExtractResults(prev => [res, ...prev]);
              if (res.filename) setCurrentFile(res.filename);
            } catch (e) {}
          }
        }
      }
      fetchStats();
      setCurrentFile("");
    } catch (e) {
      alert("Extraction failed.");
    } finally {
      setIsExtracting(false);
    }
  };

  const [currentProgress, setCurrentProgress] = useState<{chunk: number, total: number} | null>(null);

  const handleEmbed = async () => {
    setIsEmbedding(true);
    setExtractResults([]); 
    setCurrentFile("Starting Neural Training...");
    setCurrentProgress(null);
    try {
      const response = await fetch(`${API_BASE}/api/ingestion/embed`, { method: "POST" });
      
      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.trim()) {
            if (line.startsWith("CHUNK:")) {
               const [curr, tot] = line.replace("CHUNK:", "").split("/").map(Number);
               setCurrentProgress({ chunk: curr, total: tot });
            } else {
               try {
                 const res = JSON.parse(line);
                 setExtractResults(prev => [res, ...prev]);
                 if (res.filename) setCurrentFile(res.filename);
               } catch (e) {}
            }
          }
        }
      }
      fetchStats();
      setCurrentFile("");
      setCurrentProgress(null);
    } catch (e) {
      alert("Embedding failed.");
    } finally {
      setIsEmbedding(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 custom-scroll animate-in fade-in duration-700">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <div className="lg:col-span-2 flex flex-col gap-8">
          <div className="card-premium rounded-3xl p-10 flex flex-col items-center justify-center text-center border-dashed border-2 relative overflow-hidden min-h-[300px]">
             <div className="absolute inset-0 bg-brand-500/5 animate-pulse" />
             <div className={cn("w-20 h-20 rounded-2xl flex items-center justify-center mb-6 shadow-2xl transition-colors", (isExtracting || isEmbedding) ? "bg-brand-500 animate-spin" : "bg-brand-800")}>
                {isExtracting ? <RefreshCw className="w-10 h-10 text-white" /> : <Database className="w-10 h-10 text-white" />}
             </div>
             <h2 className="text-2xl font-black text-foreground uppercase tracking-widest mb-2">Neural Ingestion Portal</h2>
             <p className="text-xs text-foreground opacity-40 max-w-[320px] mb-8 font-bold leading-relaxed uppercase tracking-tighter">
                Drop curriculum PDFs or structured data to expand the institutional knowledge base.
             </p>

             <div className="flex gap-4">
               <label className="btn-primary flex items-center gap-2 cursor-pointer shadow-xl">
                 <Download className="w-4 h-4" />
                 <span>Upload Documents</span>
                 <input type="file" multiple className="hidden" onChange={(e) => handleFileUpload(e.target.files)} />
               </label>
               <button className="btn-secondary">Advanced Sync</button>
             </div>
          </div>

          <div className="card-premium rounded-3xl p-8 shadow-sm">
            <div className="flex justify-between items-center mb-6">
               <label className="sec-label m-0 border-none">Active Ingest Stream</label>
               {currentFile && (
                 <div className="flex items-center gap-2 px-3 py-1 bg-brand-500/10 rounded-full animate-pulse border border-brand-500/20">
                    <Loader2 className="w-3 h-3 text-brand-500 animate-spin" />
                    <span className="text-[9px] font-black text-brand-500 uppercase tracking-widest">{currentFile}</span>
                 </div>
               )}
            </div>
            
            {!isExtracting && !isEmbedding && extractResults.length === 0 ? (
               <div className="py-20 flex flex-col items-center justify-center text-foreground opacity-30">
                  <Layers className="w-12 h-12 mb-4 opacity-10" />
                  <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Stream Standby</span>
               </div>
            ) : (
              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scroll">
                {currentProgress && (
                  <div className="p-4 bg-brand-500/10 rounded-xl border border-brand-500/30 mb-4 animate-in slide-in-from-top-2">
                     <div className="flex justify-between items-center mb-2">
                        <span className="text-[10px] font-black text-brand-500 uppercase">Training Progress</span>
                        <span className="text-[10px] font-black text-brand-500">{Math.round((currentProgress.chunk / currentProgress.total) * 100)}%</span>
                     </div>
                     <div className="w-full h-1.5 bg-brand-500/20 rounded-full overflow-hidden">
                        <div className="h-full bg-brand-500 transition-all duration-300" style={{ width: `${(currentProgress.chunk / currentProgress.total) * 100}%` }}></div>
                     </div>
                  </div>
                )}
                {extractResults.map((r, i) => (
                  <div 
                    key={i} 
                    style={{ animationDelay: `${i * 0.1}s` }}
                    className="flex items-center justify-between p-4 bg-surface-soft border border-border-main rounded-xl group hover:border-brand-500 transition-all animate-stagger"
                  >
                     <div className="flex flex-col gap-1">
                        <div className="text-[11px] font-black text-foreground flex items-center gap-2">
                           <FileText className="w-3 h-3 text-brand-500" />
                           {r.filename}
                        </div>
                        {r.status === 'error' && r.error && (
                          <span className="text-[9px] text-rose-500 font-medium hidden group-hover:block animate-in fade-in slide-in-from-left-1">
                            Reason: {r.error}
                          </span>
                        )}
                     </div>
                     <button 
                       onClick={() => r.error && alert(`Document Error Diagnostics:\n\nFile: ${r.filename}\nIssue: ${r.error}\n\nRecommendation: Check if the PDF is corrupt or encrypted.`)}
                       className={cn(
                         "text-[9px] font-black uppercase px-2 py-0.5 rounded transition-transform active:scale-95 shadow-sm",
                         r.status === 'ok' ? "bg-emerald-500/20 text-emerald-500" : 
                         r.status === 'error' ? "bg-rose-500/20 text-rose-500 cursor-pointer hover:bg-rose-500/30" : 
                         "bg-surface-soft text-foreground opacity-40"
                       )}
                     >
                       {r.status}
                     </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card-premium rounded-3xl p-8 shadow-sm">
            <label className="sec-label mb-6">Step 2 · Neural Training</label>
            <div className="flex items-center justify-between gap-6">
               <div className="flex-1">
                  <h3 className="font-extrabold text-foreground">Vector Embeddings</h3>
                  <p className="text-xs text-foreground opacity-40 mt-1 leading-relaxed">Only new documents in the dataset will be processed. Powered by OpenAI text-embedding-3-small.</p>
               </div>
               <button 
                 disabled={isEmbedding}
                 onClick={handleEmbed}
                 className="btn-primary flex items-center gap-2 whitespace-nowrap min-w-[160px] justify-center"
               >
                 {isEmbedding ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : <RefreshCw className="w-4 h-4 text-white" />}
                 <span>{isEmbedding ? "Embedding..." : "Embed Dataset"}</span>
               </button>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <div className="card-premium rounded-3xl p-6 shadow-sm">
             <label className="sec-label mb-6 leading-none">Live System Monitor</label>
             <div className="grid grid-cols-2 gap-3">
                <div className="p-4 rounded-xl bg-surface-soft border border-border-main flex flex-col justify-center transition-all hover:border-brand-500">
                   <div className="text-[10px] font-black text-foreground opacity-40 uppercase leading-none mb-2 text-center">RAM Used</div>
                   <div className="text-xl font-black text-brand-500 flex items-end justify-center gap-1">
                     {resources?.memory_mb || '0'} <span className="text-[10px] font-bold text-foreground opacity-20 italic">MB</span>
                   </div>
                </div>
                <div className="p-4 rounded-xl bg-surface-soft border border-border-main flex flex-col justify-center transition-all hover:border-brand-500">
                   <div className="text-[10px] font-black text-foreground opacity-40 uppercase leading-none mb-2 text-center">CPU Load</div>
                   <div className="text-xl font-black text-foreground flex items-end justify-center gap-1">
                     {resources?.cpu_percent || '0'}<span className="text-[10px] font-bold text-foreground opacity-20 italic">%</span>
                   </div>
                </div>
             </div>
             <div className="mt-4 flex items-center justify-center gap-2 px-1">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
                <span className="text-[9px] font-black text-foreground opacity-40 uppercase tracking-widest">Active Thread Heartbeat</span>
             </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <StatSmall label="Chunks in DB" value={stats?.total_chunks || "—"} color="var(--brand-800)" icon={<Database className="w-4 h-4" />} />
            <StatSmall label="Files Embedded" value={stats?.total_files || "—"} color="#10b981" icon={<CheckCircle2 className="w-4 h-4" />} />
          </div>

          <div className="card-premium rounded-3xl p-6 shadow-sm flex-1 flex flex-col min-h-0">
             <div className="flex justify-between items-center mb-6">
                <label className="sec-label m-0 border-none">Vector DB Registry</label>
                <div className="flex gap-2">
                   {stats?.error_count > 0 && (
                     <div className="flex items-center gap-1.5 px-2 py-0.5 bg-rose-500/10 border border-rose-500/20 rounded text-rose-500 animate-pulse">
                        <AlertCircle className="w-3 h-3" />
                        <span className="text-[9px] font-black uppercase tracking-tight">{stats.error_count} Failures</span>
                     </div>
                   )}
                   <Filter className="w-4 h-4 text-foreground opacity-20" />
                </div>
             </div>
             
             <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scroll">
                {/* Errors Section */}
                {stats?.errors?.length > 0 && (
                  <div className="mb-6 space-y-2">
                     <div className="text-[10px] font-black text-rose-500 uppercase tracking-widest px-1">Critical Failures</div>
                     {stats.errors.map((err: any, i: number) => (
                       <div 
                         key={err.filename} 
                         style={{ animationDelay: `${i * 0.05}s` }}
                         onClick={() => alert(`Persistent Failure Diagnostic:\n\nFile: ${err.filename}\nIssue: ${err.error}\n\nStatus: Error Logged to Registry.`)}
                         className="p-3 border border-rose-500/10 bg-rose-500/5 rounded-lg flex flex-col gap-1 border-l-4 border-l-rose-500 cursor-pointer hover:bg-rose-500/10 transition-colors group animate-stagger"
                       >
                         <div className="text-[11px] font-black text-rose-500 truncate group-hover:underline">{err.filename}</div>
                         <div className="text-[9px] font-bold text-rose-500 opacity-60 leading-tight italic">{err.error}</div>
                       </div>
                     ))}
                  </div>
                )}

                {/* Successful Files */}
                <div className="text-[10px] font-black text-foreground opacity-40 uppercase tracking-widest px-1">Successfully Staged</div>
                {(!stats?.filenames || stats.filenames.length === 0) ? (
                  <div className="text-[10px] text-foreground opacity-20 text-center py-12 italic uppercase font-bold tracking-widest">No documents found</div>
                ) : stats.filenames.map((fname: string, i: number) => (
                  <div 
                    key={fname} 
                    style={{ animationDelay: `${i * 0.02}s` }}
                    className="p-3 border border-border-main bg-surface-soft/30 rounded-lg flex flex-col gap-1 transition-all hover:bg-surface-soft hover:border-brand-500 group animate-stagger"
                  >
                    <div className="text-[11px] font-black text-foreground flex items-center gap-2">
                       <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]"></div>
                       <span className="truncate group-hover:text-brand-500 transition-colors">{fname}</span>
                    </div>
                    <div className="text-[9px] font-bold text-foreground opacity-30 uppercase tracking-wider ml-3.5">Metadata Verified</div>
                  </div>
                ))}
             </div>
          </div>
        </div>

      </div>
    </div>
  );
}

function StatSmall({ label, value, color, icon }: any) {
  return (
    <div className="bg-surface rounded-2xl p-5 shadow-sm border border-border-main flex items-center gap-4 transition-all duration-300 card-premium">
       <div className="p-3 rounded-xl" style={{ backgroundColor: `${color}10`, color: color }}>
         {icon}
       </div>
       <div className="min-w-0">
         <div className="text-[8px] font-black text-foreground opacity-40 uppercase tracking-widest leading-none mb-1">{label}</div>
         <div className="text-xl font-black truncate" style={{ color: color }}>{value}</div>
       </div>
    </div>
  )
}

function renderChatContent(text: string = "") {
  if (!text) return <div />;
  // Simple MD to HTML
  let html = text
    .replace(/^### (.*)$/gm, '<h3 class="text-brand-800 font-extrabold text-sm mt-3 mb-1 uppercase tracking-tight">$1</h3>')
    .replace(/^## (.*)$/gm, '<h2 class="text-brand-800 font-black text-base mt-4 mb-2 border-b border-border-main pb-1">$1</h2>')
    .replace(/^# (.*)$/gm, '<h1 class="text-brand-800 font-black text-lg mt-5 mb-3">$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-brand-800 font-black">$1</strong>')
    .replace(/^- (.*)$/gm, '<li class="ml-4 list-disc">$1</li>')
    .replace(/\n\n/g, '<div class="h-2"></div>')
    .replace(/\n/g, '<br/>');

  // 🛡️ Neural Safeguard: Protection for block math from <br/> interference
  html = html.replace(/(\$\$|\\\[)([\s\S]*?)(\$\$|\\\])/g, (match) => {
    return match.replace(/<br\/>/g, '\n');
  });

  return (
    <div 
      className="math-container"
      dangerouslySetInnerHTML={{ __html: html }} 
    />
  );
}

function ChatView({ theme, bridgedPrompt, setBridgedPrompt }: { theme: string, bridgedPrompt?: string, setBridgedPrompt?: (s: string) => void }) {
  const [messages, setMessages] = useState<any[]>([
    { role: 'assistant', content: 'Hello! I am your EduQuest Assistant. How can I help you refine your curriculum today?' }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleSend = async (customInput?: string) => {
    const textToSend = customInput || input;
    if (!textToSend.trim()) return;
    
    const userMsg = { role: 'user', content: textToSend };
    setMessages(prev => [...prev, userMsg]);
    if (!customInput) setInput("");
    setIsTyping(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
          subject: "Mathematics",
          level: "Primary 7"
        })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Remote Connection Error. Please verify the API is online.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  useEffect(() => {
    if (bridgedPrompt) {
      handleSend(bridgedPrompt);
      setBridgedPrompt?.("");
    }
  }, [bridgedPrompt]);

  useEffect(() => {
    if (scrollRef.current) {
       scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
    
    const triggerMath = () => {
      const area = document.getElementById('chat-scroll-area');
      const win = window as any;
      if (area && typeof win.renderMathInElement === 'function') {
        win.renderMathInElement(area, {
          delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
            {left: '\\(', right: '\\)', display: false},
            {left: '\\[', right: '\\]', display: true}
          ],
          throwOnError: false
        });
        return true;
      }
      return false;
    };

    triggerMath();
    const interval = setInterval(() => {
       if (triggerMath()) clearInterval(interval);
    }, 300);

    const timer = setTimeout(triggerMath, 1000);
    return () => {
      clearInterval(interval);
      clearTimeout(timer);
    };
  }, [messages, isTyping]);

  return (
    <div className="flex flex-col h-[700px] animate-in fade-in slide-in-from-left-4 duration-300">
      <div 
        id="chat-scroll-area"
        ref={scrollRef}
        className="flex-1 overflow-y-auto pr-2 custom-scroll mb-4 space-y-4"
      >
        {messages.map((m, i) => (
          <div key={i} className={cn("flex flex-col", m.role === 'user' ? "items-end" : "items-start")}>
            <div className={cn(
              "max-w-[85%] p-4 rounded-2xl text-[13px] leading-relaxed shadow-sm",
              m.role === 'user' 
                ? "bg-brand-800 text-white rounded-tr-none" 
                : "bg-surface-soft border border-border-main text-foreground rounded-tl-none"
            )}>
              {renderChatContent(m.content)}
            </div>
            <div className="text-[9px] font-black text-foreground opacity-40 mt-1 uppercase tracking-widest px-1">
              {m.role === 'user' ? 'You' : 'EduQuest AI'}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex items-start gap-2 animate-pulse">
            <div className="w-8 h-4 rounded bg-surface-soft border border-border-main flex items-center justify-center">
              <div className="w-1 h-1 bg-foreground opacity-40 rounded-full animate-bounce" />
              <div className="w-1 h-1 bg-foreground opacity-40 rounded-full animate-bounce [animation-delay:0.2s] mx-0.5" />
              <div className="w-1 h-1 bg-foreground opacity-40 rounded-full animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        )}
      </div>

      <div className="relative group">
        <input 
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask me anything..."
          className={cn(
            "w-full bg-surface-soft border-2 border-border-main rounded-xl p-4 text-xs font-bold outline-none transition-all",
            theme === 'midnight' ? "focus:border-brand-500 glass" : "focus:border-brand-800"
          )}
        />
        <button 
           onClick={() => handleSend()}
           disabled={isTyping}
           className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-brand-800 text-white rounded-lg hover:scale-110 active:scale-95 transition-all disabled:opacity-50"
        >
          <Play className="w-3 h-3 fill-current rotate-0" />
        </button>
      </div>
      <div className="mt-4 p-4 rounded-xl border border-dashed border-border-main bg-surface-soft/30">
         <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-3.5 h-3.5 text-brand-800" />
            <span className="text-[10px] font-black text-foreground opacity-60 uppercase tracking-widest leading-none">Powered by Neural Core v3.1</span>
         </div>
         <p className="text-[9px] text-foreground opacity-40 leading-tight">Expert advice grounded in National Curriculum Standards.</p>
      </div>
    </div>
  );
}

function SaturationMap({ found, missing, foundSources, onSuggest, theme }: { found: string[], missing: string[], foundSources: any, onSuggest: (t: string) => void, theme: string }) {
  const [activeTopic, setActiveTopic] = useState<any>(null);
  
  const all = [
    ...found.map(t => ({ name: t, status: 'found', sources: foundSources?.[t] || [] })),
    ...missing.map(t => ({ name: t, status: 'missing', sources: [] }))
  ].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-3 px-1">
        <label className="text-[9px] font-black uppercase text-foreground opacity-40 tracking-widest">Knowledge Saturation Map</label>
        <div className="flex gap-3">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
            <span className="text-[7px] font-bold text-foreground opacity-40 uppercase">Verified</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-surface-soft border border-border-main"></div>
            <span className="text-[7px] font-bold text-foreground opacity-40 uppercase">Missing</span>
          </div>
        </div>
      </div>

      <div className="bg-surface-soft/50 p-3 rounded-2xl border border-border-main flex flex-wrap gap-1.5 justify-center">
        {all.map((item, i) => (
          <button
            key={i}
            onMouseEnter={() => setActiveTopic(item)}
            onClick={() => item.status === 'missing' && onSuggest(item.name)}
            className={cn(
              "w-4 h-4 rounded-[4px] transition-all duration-300 hover:scale-125 relative group animate-stagger",
              item.status === 'found' 
                ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]" 
                : "bg-surface-soft border border-border-main hover:bg-rose-500/20",
              activeTopic?.name === item.name && "ring-2 ring-brand-800 ring-offset-2 scale-110"
            )}
            style={{ animationDelay: `${i * 0.01}s` }}
          />
        ))}
      </div>

      {/* TOPIC INSPECTOR PANE */}
      <div className="mt-4 min-h-[60px] p-4 bg-surface rounded-2xl border border-border-main animate-in fade-in slide-in-from-top-2">
        {activeTopic ? (
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-start">
               <div>
                  <div className="text-[10px] font-black text-foreground">{activeTopic.name}</div>
                  <div className={cn(
                    "text-[8px] font-black uppercase mt-0.5",
                    activeTopic.status === 'found' ? "text-emerald-500" : "text-rose-500"
                  )}>
                    {activeTopic.status === 'found' ? 'Knowledge Verified' : 'Curriculum Gap Detected'}
                  </div>
               </div>
               {activeTopic.status === 'missing' && (
                 <button 
                   onClick={() => onSuggest(activeTopic.name)}
                   className="flex items-center gap-1 px-2 py-1 bg-brand-800 text-white rounded-md hover:bg-brand-900 transition-all"
                 >
                    <Sparkles className="w-2.5 h-2.5" />
                    <span className="text-[8px] font-black uppercase">Bridge Gap</span>
                 </button>
               )}
            </div>
            {activeTopic.status === 'found' && activeTopic.sources.length > 0 && (
              <div className="flex flex-col gap-1 mt-1">
                 <div className="text-[7px] font-black text-foreground opacity-40 uppercase tracking-widest">Verification Sources:</div>
                 <div className="flex flex-wrap gap-1">
                    {activeTopic.sources.map((s: string, idx: number) => (
                      <div key={idx} className="px-1.5 py-0.5 bg-surface-soft rounded text-[7px] font-bold text-foreground opacity-50 border border-border-main truncate max-w-[150px]">
                        {s}
                      </div>
                    ))}
                 </div>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-[9px] font-bold text-foreground opacity-30 uppercase tracking-widest">
            Hover over blocks to inspect curriculum state
          </div>
        )}
      </div>
    </div>
  );
}

function AnalyticsView({ theme, onBridge }: { theme: string, onBridge?: (t: string) => void }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeSubject, setActiveSubject] = useState<string | null>(null);
  const [levelAudits, setLevelAudits] = useState<any>({});
  const [auditingLevels, setAuditingLevels] = useState<any>({});

  useEffect(() => {
    fetch(`${API_BASE}/api/analytics/global`)
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
        const subjects = Object.keys(json);
        if (subjects.length > 0) setActiveSubject(subjects[0]);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleLevelAudit = async (subject: string, level: string) => {
    setAuditingLevels((prev: any) => ({ ...prev, [`${subject}-${level}`]: true }));
    try {
      const res = await fetch(`${API_BASE}/api/analytics/audit?subject=${subject}&level=${level}`);
      const d = await res.json();
      setLevelAudits((prev: any) => ({ ...prev, [`${subject}-${level}`]: d }));
    } catch (e) {}
    finally {
      setAuditingLevels((prev: any) => ({ ...prev, [`${subject}-${level}`]: false }));
    }
  };

  if (loading) return (
    <div className="flex-1 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-brand-800/20 border-t-brand-800 rounded-full animate-spin"></div>
        <p className="text-xs font-black text-foreground opacity-40 uppercase tracking-widest">Aggregating Institutional Data...</p>
      </div>
    </div>
  );

  return (
    <div className="flex-1 overflow-auto p-12 bg-surface-soft/30">
      <div className="max-w-6xl mx-auto">
        <div className="mb-12">
          <h1 className="text-4xl font-black text-foreground mb-2">Pedagogical Coverage</h1>
          <p className="text-foreground opacity-50 font-bold">Comprehensive audit of syllabus saturation across all subjects and levels.</p>
        </div>

        {/* Subject Selection Tabs */}
        <div className="flex gap-2 mb-8 p-1.5 bg-surface border border-border-main rounded-2xl w-fit shadow-sm overflow-x-auto max-w-full">
          {Object.keys(data || {}).map(s => (
            <button
              key={s}
              onClick={() => setActiveSubject(s)}
              className={cn(
                "px-6 py-3 rounded-xl font-black text-xs uppercase tracking-wider transition-all",
                activeSubject === s 
                  ? "bg-brand-800 text-white shadow-lg scale-105" 
                  : "text-foreground opacity-40 hover:text-brand-800 hover:bg-brand-800/10"
              )}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Global Stats Grid */}
        {activeSubject && data[activeSubject] && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(data[activeSubject]).map(([level, stats]: [string, any], i: number) => (
              <div 
                key={level} 
                style={{ animationDelay: `${i * 0.05}s` }}
                className="p-8 rounded-[32px] border border-border-main transition-all hover:shadow-2xl group animate-stagger card-premium"
              >
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className="text-lg font-black text-foreground">{level}</h3>
                    <div className="text-[10px] font-bold text-foreground opacity-40 uppercase tracking-widest mt-1">Status: {stats.coverage >= 80 ? 'Optimal' : stats.coverage >= 50 ? 'Developing' : 'Critical Gap'}</div>
                  </div>
                  <div className={cn(
                    "w-12 h-12 rounded-2xl flex items-center justify-center text-xl font-black shadow-inner",
                    stats.coverage >= 80 ? "bg-emerald-500/10 text-emerald-500" : stats.coverage >= 50 ? "bg-amber-500/10 text-amber-500" : "bg-rose-500/10 text-rose-500"
                  )}>
                    {Math.round(stats.coverage)}%
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="h-3 w-full bg-surface-soft rounded-full overflow-hidden mb-6 shadow-inner border border-border-main">
                  <div 
                    className={cn(
                      "h-full transition-all duration-1000 ease-out rounded-full",
                      stats.coverage >= 80 ? "bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.3)]" : 
                      stats.coverage >= 50 ? "bg-amber-500" : 
                      "bg-rose-500"
                    )}
                    style={{ width: `${stats.coverage}%` }}
                  ></div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-surface-soft p-4 rounded-2xl border border-border-main">
                    <div className="text-[9px] font-black text-foreground opacity-40 uppercase tracking-widest mb-1">Saturation</div>
                    <div className="text-xl font-black text-foreground">{stats.topics_found} <span className="text-xs text-foreground opacity-20 font-bold">/ {stats.topics_total}</span></div>
                  </div>
                  <div className="bg-surface-soft p-4 rounded-2xl border border-border-main">
                    <div className="text-[9px] font-black text-foreground opacity-40 uppercase tracking-widest mb-1">Next Action</div>
                    <div className={cn(
                      "text-[10px] font-black uppercase tracking-wider",
                      stats.coverage < 100 ? "text-brand-800" : "text-emerald-500"
                    )}>
                      {stats.coverage < 100 ? 'Bridge Gaps' : 'Saturated'}
                    </div>
                  </div>
                </div>

                {/* Interactive Saturation Map */}
                <SaturationMap 
                  found={stats.found_list || []} 
                  missing={stats.missing_list || []} 
                  foundSources={stats.found_sources || {}}
                  theme={theme}
                  onSuggest={(t) => onBridge && onBridge(t)}
                />

                {/* Pedagogy Profile Integration */}
                <div className="mt-8 pt-6 border-t border-dashed border-border-main">
                  {levelAudits[`${activeSubject}-${level}`] ? (
                    <div className="animate-in zoom-in-95 duration-700">
                      <div className="flex items-center justify-between mb-4">
                        <div className="text-[9px] font-black uppercase text-foreground opacity-40 tracking-widest leading-none">Aggregated Profile</div>
                        <div className="px-2 py-0.5 bg-brand-800 text-white text-[7px] font-black rounded uppercase">Verified</div>
                      </div>
                      <RadarChart key={`${activeSubject}-${level}`} data={levelAudits[`${activeSubject}-${level}`]?.bloom} theme={theme} />
                      <div className="mt-4 flex flex-wrap gap-1">
                         <div className="px-2 py-1 bg-surface-soft rounded-md text-[8px] font-black text-foreground opacity-50 border border-border-main uppercase">RD: {levelAudits[`${activeSubject}-${level}`]?.readability}%</div>
                         <div className="px-2 py-1 bg-surface-soft rounded-md text-[8px] font-black text-foreground opacity-50 border border-border-main uppercase">Q: {levelAudits[`${activeSubject}-${level}`]?.time_estimate}m Avg</div>
                      </div>
                    </div>
                  ) : (
                    <button 
                      onClick={() => handleLevelAudit(activeSubject!, level)}
                      disabled={auditingLevels[`${activeSubject}-${level}`] || stats.chunk_count === 0}
                      title={stats.chunk_count === 0 ? "No pedagogical fragments ingested for this level yet." : "Perform deep institutional audit"}
                      className="w-full py-4 rounded-2xl border-2 border-dashed border-border-main text-[10px] font-black uppercase tracking-widest text-foreground opacity-40 hover:opacity-100 hover:text-brand-800 hover:border-brand-800/30 hover:bg-brand-50 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
                    >
                      {auditingLevels[`${activeSubject}-${level}`] ? (
                        <Loader2 className="w-4 h-4 animate-spin text-brand-800" />
                      ) : (
                        <Sparkles className="w-4 h-4 group-hover:scale-110 transition-transform" />
                      )}
                      {auditingLevels[`${activeSubject}-${level}`] ? "Scanning Neural Pattern..." : 
                       stats.chunk_count === 0 ? "No Data to Audit" : "Deep Level Pedagogy Audit"}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
