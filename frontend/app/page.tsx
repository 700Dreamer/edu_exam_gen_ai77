"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Sparkles, Settings, Database, BookOpen, Layers, CheckCircle2, AlertCircle, FileText, Download, Play, RefreshCw, Filter, Loader2, GitBranch, ArrowDown, ZoomIn, ZoomOut, Printer, Maximize, FileCheck, Eye, Columns, Square, Image as ImageIcon, Palette, Compass, Camera, X } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { NurseryASTViewer } from "./NurseryASTViewer";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ── CONNECTIVITY ──
// Empty string = relative URLs → Next.js proxy forwards /api/* to the FastAPI backend.
// This works correctly on Railway, in Docker, and locally without any env var required.
const API_BASE = "";
const STREAM_BASE = "";

// ── TYPES ──
type Page = "studio" | "ingestion" | "analytics" | "pkg" | "assessment";
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

const Header = ({ theme, setTheme, currentPage, setCurrentPage, isLeftSidebarOpen, setIsLeftSidebarOpen, isRightSidebarOpen, setIsRightSidebarOpen, parsedQuestionsLength, zoom, setZoom, viewMode, setViewMode, iframeRef }: any) => (
  <header className="bg-surface border-b border-border-main text-foreground px-8 py-2 shadow-sm flex justify-between items-center sticky top-0 z-50 transition-colors duration-500">
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
      <div className="flex gap-2 border-l border-border-main pl-6 items-center">
        <button 
          onClick={() => setCurrentPage("studio")}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition-all",
            currentPage === "studio" ? "bg-brand-800 text-white shadow-md" : "bg-transparent text-foreground opacity-50 hover:text-brand-800 hover:opacity-100",
            (theme === 'midnight' || theme === 'royal') && currentPage === "studio" && "neon-glow shadow-[0_0_15px_var(--glow-accent)]"
          )}
        >
          <Sparkles className="w-3.5 h-3.5" />
          Studio
        </button>
        <button 
          onClick={() => setCurrentPage("analytics")}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition-all",
            currentPage === "analytics" ? "bg-brand-800 text-white shadow-md" : "bg-transparent text-foreground opacity-50 hover:text-brand-800 hover:opacity-100",
            (theme === 'midnight' || theme === 'royal') && currentPage === "analytics" && "neon-glow shadow-[0_0_15px_var(--glow-accent)]"
          )}
        >
          <Layers className="w-3.5 h-3.5" />
          Analytics
        </button>
        <button 
          onClick={() => setCurrentPage("ingestion")}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition-all",
            currentPage === "ingestion" ? "bg-brand-800 text-white shadow-md" : "bg-transparent text-foreground opacity-50 hover:text-brand-800 hover:opacity-100",
            (theme === 'midnight' || theme === 'royal') && currentPage === "ingestion" && "neon-glow shadow-[0_0_15px_var(--glow-accent)]"
          )}
        >
          <Database className="w-3.5 h-3.5" />
          Data Digestion
        </button>
        <button 
          onClick={() => setCurrentPage("pkg")}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition-all",
            currentPage === "pkg" ? "bg-brand-800 text-white shadow-md" : "bg-transparent text-foreground opacity-50 hover:text-brand-800 hover:opacity-100",
            (theme === 'midnight' || theme === 'royal') && currentPage === "pkg" && "neon-glow shadow-[0_0_15px_var(--glow-accent)]"
          )}
        >
          <Compass className="w-3.5 h-3.5" />
          Pedagogical Graph
        </button>
        <button 
          onClick={() => setCurrentPage("assessment")}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition-all",
            currentPage === "assessment" ? "bg-brand-800 text-white shadow-md" : "bg-transparent text-foreground opacity-50 hover:text-brand-800 hover:opacity-100",
            (theme === 'midnight' || theme === 'royal') && currentPage === "assessment" && "neon-glow shadow-[0_0_15px_var(--glow-accent)]"
          )}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Assessment
        </button>
      </div>
    </div>
    {currentPage === "studio" && (
      <div className="flex items-center gap-1 bg-surface-soft p-1.5 rounded-2xl border border-border-main shadow-inner">
         <div className="flex items-center gap-0.5 border-r border-border-main pr-1.5 mr-1.5">
            <button onClick={() => setIsLeftSidebarOpen(!isLeftSidebarOpen)} className={cn("p-2 rounded-xl transition-all", isLeftSidebarOpen ? "bg-brand-500/10 text-brand-800" : "text-foreground/60 hover:text-brand-800 hover:bg-brand-500/10")} title="Toggle Settings"><Columns className="w-4 h-4" /></button>
         </div>
         
         <div className="flex items-center gap-0.5 border-r border-border-main pr-1.5 mr-1.5">
            <button onClick={() => setZoom(Math.max(50, zoom - 10))} className="p-2 hover:bg-brand-500/10 rounded-xl transition-all text-foreground/60 hover:text-brand-800" title="Zoom Out"><ZoomOut className="w-4 h-4" /></button>
            <div className="px-2 text-[10px] font-black text-brand-800 w-12 text-center">{zoom}%</div>
            <button onClick={() => setZoom(Math.min(200, zoom + 10))} className="p-2 hover:bg-brand-500/10 rounded-xl transition-all text-foreground/60 hover:text-brand-800" title="Zoom In"><ZoomIn className="w-4 h-4" /></button>
            <button onClick={() => setZoom(100)} className="p-2 hover:bg-brand-500/10 rounded-xl transition-all text-foreground/60 hover:text-brand-800" title="Reset Zoom"><Maximize className="w-3.5 h-3.5" /></button>
         </div>

         <div className="flex bg-surface p-1 rounded-xl gap-1 mr-1.5 shadow-sm border border-border-main">
            <button onClick={() => setViewMode("student")} className={cn("px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest flex items-center gap-2 transition-all", viewMode === "student" ? "bg-surface-soft text-brand-800 shadow-sm" : "text-foreground opacity-40 hover:opacity-100")}><Eye className="w-3 h-3" /> Question Paper</button>
            <button onClick={() => setViewMode("marking")} className={cn("px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest flex items-center gap-2 transition-all", viewMode === "marking" ? "bg-brand-800 text-white shadow-lg neon-glow" : "text-foreground opacity-40 hover:opacity-100")}><FileCheck className="w-3 h-3" /> Marking Guide</button>
            <button onClick={() => setViewMode("ref_map")} className={cn("px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest flex items-center gap-2 transition-all", viewMode === "ref_map" ? "bg-emerald-600 text-white shadow-lg neon-glow" : "text-foreground opacity-40 hover:opacity-100")}><Compass className="w-3 h-3" /> Reference Map</button>
          </div>

         <div className="flex items-center gap-1 pl-1.5 border-l border-border-main">
            <button onClick={() => iframeRef.current?.contentWindow?.print()} className="p-2 hover:bg-brand-500/10 rounded-xl transition-all text-foreground/60 hover:text-brand-800" title="Print Exam"><Printer className="w-4 h-4" /></button>
            {parsedQuestionsLength > 0 && (
              <>
                <div className="w-[1px] h-4 bg-border-main mx-1"></div>
                <button onClick={() => setIsRightSidebarOpen(!isRightSidebarOpen)} className={cn("p-2 rounded-xl transition-all", isRightSidebarOpen ? "bg-brand-500/10 text-brand-800" : "text-foreground/60 hover:text-brand-800 hover:bg-brand-500/10")} title="Toggle Illustrations"><ImageIcon className="w-4 h-4" /></button>
              </>
            )}
          </div>
      </div>
    )}
  </header>
);

function AssessmentView({ theme }: { theme: string }) {
  const [subject, setSubject] = useState("");
  const [level, setLevel] = useState("");
  const [configLocked, setConfigLocked] = useState(false);
  const [strictness, setStrictness] = useState(5);
  const [markingMode, setMarkingMode] = useState<"individual" | "class">("individual");
  const [uploadMode, setUploadMode] = useState<"file" | "camera">("file");
  const [cameraActive, setCameraActive] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processStep, setProcessStep] = useState(0);
  const [results, setResults] = useState<any[]>([]);
  const [scannedPages, setScannedPages] = useState<{file: File, url: string}[]>([]);
  const videoRef = useRef<HTMLVideoElement>(null);

  const startCamera = async () => {
    setCameraActive(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Error accessing camera: ", err);
    }
  };

  const stopCamera = () => {
    setCameraActive(false);
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach(t => t.stop());
    }
  };

  const [apiConfig, setApiConfig] = useState<any>({ subjects: [], levels: [], syllabus: {} });
  
  useEffect(() => {
    fetch(`${API_BASE}/api/syllabus/config?t=${Date.now()}`)
      .then(res => res.json())
      .then(data => setApiConfig(data))
      .catch(() => {});
  }, []);

  const subjects = apiConfig.subjects || [];
  const levels = apiConfig.levels || [];
  const aiSteps = ["Scanning Document Geometry...", "Extracting Handwriting Features...", "Semantic Evaluation via Marking Guide...", "Assigning Constructive Remarks..."];

  const handleDrag = (e: any) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const processMultiplePages = async () => {
    if (scannedPages.length === 0) return;
    setIsProcessing(true);
    setProcessStep(0);
    
    const interval = setInterval(() => {
      setProcessStep(prev => Math.min(prev + 1, aiSteps.length - 1));
    }, 1500);

    try {
      const formData = new FormData();
      for (const page of scannedPages) {
         formData.append("files", page.file);
      }
      formData.append("subject", subject);
      formData.append("level", level);
      formData.append("strictness", strictness.toString());

      const res = await fetch("/api/assess/vision", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Assessment API failed");
      const data = await res.json();
      
      clearInterval(interval);
      setProcessStep(aiSteps.length - 1);
      
      setTimeout(() => {
        setIsProcessing(false);
        setResults([data]);
        setScannedPages([]);
      }, 1000);
    } catch (e) {
      console.error(e);
      clearInterval(interval);
      setIsProcessing(false);
      alert("Failed to process images with Vision AI.");
    }
  };

  const handleDrop = (e: any) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
       const newPages = Array.from(e.dataTransfer.files).map((f: any) => ({
           file: f,
           url: URL.createObjectURL(f)
       }));
       setScannedPages(prev => [...prev, ...newPages]);
    }
  };

  const isSidebarMode = isProcessing || results.length > 0;

  return (
    <div className={cn(
      "flex-1 bg-[#F8FAFC] text-slate-900 overflow-hidden relative flex transition-all duration-700 ease-in-out",
      isSidebarMode ? "flex-col lg:flex-row" : "flex-col items-center overflow-y-auto py-12 lg:py-20"
    )}>
      {/* Configuration Panel */}
      <div className={cn(
        "bg-white z-20 flex flex-col transition-all duration-700 ease-in-out shadow-sm",
        isSidebarMode 
          ? "w-full lg:w-[320px] lg:min-w-[320px] border-r border-slate-200 h-full rounded-none" 
          : "w-full max-w-2xl border border-slate-200 rounded-xl mb-8 flex-none"
      )}>
         <div className={cn("p-5 border-b border-slate-100 bg-slate-50/50", isSidebarMode ? "" : "rounded-t-xl")}>
             <h2 className="text-base font-semibold tracking-tight text-slate-900 flex items-center gap-2">
               <Layers className="w-4 h-4 text-brand-600"/> Auto-Assessment Engine
             </h2>
             <p className="text-[11px] text-slate-500 mt-1">Enterprise Semantic Grading Pipeline</p>
         </div>
         
         <div className={cn("p-5 flex-1", isSidebarMode ? "space-y-6 overflow-y-auto" : "")}>
             {!configLocked ? (
               <div className="animate-in fade-in slide-in-from-left-4 duration-500">
                 <div className={cn("grid gap-6", isSidebarMode ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2")}>
                 <div>
                   <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2 block">Subject Taxonomy</label>
                   <select 
                     value={subject} 
                     onChange={(e) => setSubject(e.target.value)}
                     className="w-full text-sm border border-slate-200 rounded-md p-2.5 bg-slate-50 focus:bg-white focus:ring-1 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
                   >
                     <option value="" disabled>Select Subject...</option>
                     {subjects.map((s: string) => <option key={s} value={s}>{s}</option>)}
                   </select>
                 </div>
                 
                 <div>
                   <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2 block">Academic Level</label>
                   <select 
                     value={level} 
                     onChange={(e) => setLevel(e.target.value)}
                     className="w-full text-sm border border-slate-200 rounded-md p-2.5 bg-slate-50 focus:bg-white focus:ring-1 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
                   >
                     <option value="" disabled>Select Level...</option>
                     {levels.map((l: string) => <option key={l} value={l}>{l}</option>)}
                   </select>
                 </div>

                 <div className={cn(isSidebarMode ? "pt-4 border-t border-slate-100" : "md:col-span-2 pt-4 border-t border-slate-100")}>
                    <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2 block">Processing Mode</label>
                    <div className="flex bg-slate-100 p-1 rounded-md">
                      <button onClick={()=>setMarkingMode("individual")} className={cn("flex-1 text-[11px] font-semibold py-1.5 rounded transition-all", markingMode === "individual" ? "bg-white shadow-sm text-slate-900" : "text-slate-500 hover:text-slate-700")}><FileText className="w-3 h-3 inline mr-1"/> Individual</button>
                      <button onClick={()=>setMarkingMode("class")} className={cn("flex-1 text-[11px] font-semibold py-1.5 rounded transition-all", markingMode === "class" ? "bg-white shadow-sm text-slate-900" : "text-slate-500 hover:text-slate-700")}><Columns className="w-3 h-3 inline mr-1"/> Class Batch</button>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-2 leading-relaxed">
                      {markingMode === "individual" ? "Stitches all pages into a single student report." : "Grades each page independently for class analytics."}
                    </p>
                 </div>

                 <div className={cn(isSidebarMode ? "pt-4 border-t border-slate-100" : "md:col-span-2 pt-4 border-t border-slate-100")}>
                    <div className="flex justify-between items-center mb-2">
                       <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Strictness Index</label>
                       <span className="text-[10px] font-mono font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">{strictness}/10</span>
                    </div>
                    <input type="range" min="1" max="10" step="1" value={strictness} onChange={(e)=>setStrictness(parseInt(e.target.value))} className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-800" />
                    <div className="flex justify-between mt-1 text-[9px] font-bold uppercase tracking-widest text-slate-400">
                       <span>Lenient</span>
                       <span>Strict</span>
                    </div>
                 </div>
               </div>

                 <button onClick={()=>setConfigLocked(true)} disabled={!subject || !level} className="w-full mt-6 bg-slate-900 text-white text-[11px] uppercase tracking-wider font-bold py-3 rounded-md hover:bg-slate-800 disabled:opacity-50 transition-colors shadow-sm">
                   Initialize Engine
                 </button>
               </div>
             ) : (
               <div className="bg-slate-50 border border-slate-200 rounded-md p-4 animate-in fade-in slide-in-from-right-4 duration-300">
                 <div className="flex justify-between items-center mb-4 border-b border-slate-200 pb-2">
                   <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-600 flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5"/> Engine Active</span>
                   <button onClick={()=>{setConfigLocked(false); setResults([]); setScannedPages([]);}} className="text-[10px] uppercase font-bold text-slate-500 hover:text-slate-800 transition-colors">Edit Config</button>
                 </div>
                 <div className={cn("grid gap-3 text-xs", isSidebarMode ? "grid-cols-1" : "grid-cols-2 md:grid-cols-4")}>
                   <div className={cn("flex", isSidebarMode ? "justify-between" : "flex-col gap-1")}><span className="text-slate-400">Subject</span><span className="font-semibold text-slate-800">{subject}</span></div>
                   <div className={cn("flex", isSidebarMode ? "justify-between" : "flex-col gap-1")}><span className="text-slate-400">Level</span><span className="font-semibold text-slate-800">{level}</span></div>
                   <div className={cn("flex", isSidebarMode ? "justify-between" : "flex-col gap-1")}><span className="text-slate-400">Mode</span><span className="font-semibold text-slate-800">{markingMode === "individual" ? "Individual" : "Class Batch"}</span></div>
                   <div className={cn("flex", isSidebarMode ? "justify-between" : "flex-col gap-1")}><span className="text-slate-400">Strictness</span><span className="font-semibold text-slate-800">{strictness}/10</span></div>
                 </div>
               </div>
             )}
         </div>
      </div>

      {/* Main Workspace Panel */}
      <div className={cn(
        "transition-all duration-700 ease-in-out relative",
        isSidebarMode ? "flex-1 h-full overflow-y-auto p-6 lg:p-10" : "w-full max-w-3xl px-4 flex-none"
      )}>
        <div className="max-w-5xl mx-auto">
          {configLocked && results.length === 0 && !isProcessing && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
              
              <div className="flex items-center gap-2 border-b border-slate-200 pb-4 mb-6">
                 <button onClick={() => { setUploadMode("file"); stopCamera(); }} className={cn("px-4 py-1.5 rounded-md text-[11px] font-bold uppercase tracking-wider transition-all", uploadMode === "file" ? "bg-slate-800 text-white shadow-sm" : "text-slate-500 hover:bg-slate-100")}>File Import</button>
                 <button onClick={() => { setUploadMode("camera"); startCamera(); }} className={cn("px-4 py-1.5 rounded-md text-[11px] font-bold uppercase tracking-wider transition-all", uploadMode === "camera" ? "bg-slate-800 text-white shadow-sm" : "text-slate-500 hover:bg-slate-100")}>Live Camera</button>
              </div>

              {uploadMode === "file" && (
                <div 
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  className={cn(
                    "border border-dashed rounded-lg p-16 flex flex-col items-center justify-center text-center transition-all duration-300 cursor-pointer bg-white",
                    dragActive ? "border-brand-500 bg-brand-50" : "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
                  )}
                >
                  <div className="w-12 h-12 rounded bg-slate-100 flex items-center justify-center mb-4">
                    <Download className={cn("w-6 h-6", dragActive ? "text-brand-600" : "text-slate-400")} />
                  </div>
                  <h3 className="text-sm font-semibold text-slate-800">Drop Scans Here</h3>
                  <p className="text-xs text-slate-500 mt-1">Upload JPG or PDF formats.</p>
                </div>
              )}

              {uploadMode === "camera" && (
                <div className="border border-slate-200 rounded-lg p-4 bg-white shadow-sm">
                  <div className="flex flex-col items-center">
                    <div className="w-full max-w-2xl aspect-video bg-slate-900 rounded overflow-hidden relative shadow-inner">
                      {!cameraActive ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
                          <Camera className="w-8 h-8 mb-2 opacity-50" />
                          <p className="text-[10px] font-bold tracking-widest uppercase">Initializing Feed...</p>
                        </div>
                      ) : (
                        <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                      )}
                      
                      <div className="absolute inset-4 border border-white/20 rounded pointer-events-none flex items-center justify-center">
                         <div className="w-16 h-16 border border-white/40 border-dashed rounded-full pointer-events-none" />
                      </div>
                    </div>

                    <div className="mt-6 flex justify-center w-full">
                      <button 
                        onClick={() => {
                           if (!videoRef.current) return;
                           const canvas = document.createElement("canvas");
                           canvas.width = videoRef.current.videoWidth;
                           canvas.height = videoRef.current.videoHeight;
                           const ctx = canvas.getContext("2d");
                           if (!ctx) return;
                           ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
                           canvas.toBlob(async (blob) => {
                             if (!blob) return;
                             const file = new File([blob], `camera_capture_${scannedPages.length+1}.jpg`, { type: "image/jpeg" });
                             setScannedPages(prev => [...prev, { file, url: URL.createObjectURL(file) }]);
                           }, "image/jpeg", 0.9);
                        }}
                        className="px-8 py-2.5 bg-slate-900 text-white text-[11px] font-bold uppercase tracking-wider rounded-md hover:bg-slate-800 shadow-sm transition-all flex items-center gap-2"
                      >
                        <Camera className="w-4 h-4" /> Capture Document
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {scannedPages.length > 0 && (
                <div className="bg-white border border-slate-200 p-5 rounded-lg shadow-sm mt-6">
                  <div className="flex justify-between items-center mb-4">
                     <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">Document Queue</h3>
                     <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">{scannedPages.length} Pages</span>
                  </div>
                  <div className="flex gap-3 overflow-x-auto pb-2">
                     {scannedPages.map((page, idx) => (
                       <div key={idx} className="relative min-w-[100px] h-32 bg-slate-100 rounded border border-slate-200 overflow-hidden group">
                         <img src={page.url} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity" alt={`Page ${idx+1}`} />
                         <div className="absolute top-1 left-1 bg-slate-900/70 backdrop-blur-sm text-white text-[9px] font-bold px-1.5 py-0.5 rounded">PG {idx+1}</div>
                         <button onClick={() => setScannedPages(prev => prev.filter((_, i) => i !== idx))} className="absolute top-1 right-1 bg-red-500/90 text-white p-0.5 rounded hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity"><X className="w-3 h-3"/></button>
                       </div>
                     ))}
                  </div>
                  <button 
                    onClick={() => {
                      if(uploadMode === "camera") stopCamera();
                      processMultiplePages();
                    }}
                    className="w-full mt-5 py-3 bg-brand-600 text-white text-xs font-bold uppercase tracking-wider rounded-md hover:bg-brand-700 shadow-sm transition-all flex items-center justify-center gap-2"
                  >
                    <Layers className="w-4 h-4" /> Process {scannedPages.length} Documents
                  </button>
                </div>
              )}
            </div>
          )}

          {isProcessing && (
            <div className="bg-white border border-slate-200 rounded-lg p-12 flex flex-col items-center justify-center text-center shadow-sm">
              <Loader2 className="w-10 h-10 text-brand-500 animate-spin mb-6" />
              <h3 className="text-sm font-semibold text-slate-800 mb-1">Analyzing Documents...</h3>
              <p className="text-[11px] text-slate-500">Extracting syntax and performing semantic cross-referencing.</p>
              
              <div className="w-64 h-1 bg-slate-100 rounded-full mt-6 overflow-hidden">
                 <div className="h-full bg-brand-500 transition-all duration-1000" style={{ width: `${((processStep + 1) / aiSteps.length) * 100}%` }} />
              </div>
              <p className="text-[9px] uppercase tracking-widest text-slate-400 mt-3 font-bold">{aiSteps[processStep]}</p>
            </div>
          )}

          {results.length > 0 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
               <div className="flex justify-between items-center bg-white border border-slate-200 p-4 rounded-lg shadow-sm">
                  <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500"/> Pipeline Complete</h3>
                  <button onClick={() => { setResults([]); setScannedPages([]); }} className="text-[11px] font-bold uppercase tracking-wider text-slate-500 hover:text-slate-800 flex items-center gap-1.5"><RefreshCw className="w-3 h-3"/> New Batch</button>
               </div>
               
               <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-8 md:p-12 overflow-x-auto">
                  <div 
                     className="text-slate-800 text-sm leading-relaxed max-w-4xl mx-auto prose prose-slate"
                     dangerouslySetInnerHTML={{ __html: results[0].report_html || "<p>No report generated.</p>" }} 
                  />
               </div>
            </div>
          )}
          
          {!configLocked && (
            <div className="flex flex-col items-center justify-center text-center opacity-30 pointer-events-none mt-8 pb-12">
               <FileCheck className="w-16 h-16 mb-4 text-slate-400" />
               <h3 className="text-lg font-semibold text-slate-600">Awaiting Configuration</h3>
               <p className="text-xs text-slate-500 mt-2 max-w-sm">Lock the assessment context to initialize the engine workflow.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [currentPage, setCurrentPage] = useState<Page>("studio");
  const [activeTab, setActiveTab] = useState<"gen" | "lib" | "insights" | "chat" | "scenario" | "nursery">("gen");
  const [previewHtml, setPreviewHtml] = useState<string>("");
  const [examData, setExamData] = useState<any>(null);
  const [examImages, setExamImages] = useState<any>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [library, setLibrary] = useState<Project[]>([]);
  const [bridgedPrompt, setBridgedPrompt] = useState<string>("");
  const [lastRaw, setLastRaw] = useState<string>("");
  const [lastConfig, setLastConfig] = useState<any>(null);

  const [theme, setTheme] = useState<'burgundy' | 'midnight' | 'emerald' | 'royal' | 'studio'>('burgundy');

  // Responsive drawer/sidebar states
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(true);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(false);

  const [zoom, setZoom] = useState(100);
  const [viewMode, setViewMode] = useState<"student" | "marking" | "ref_map">("student");
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Compute parsed questions length for Header
  const parsedQuestionsLength = (() => {
    try {
      const raw = typeof lastRaw === 'string' ? JSON.parse(lastRaw) : lastRaw;
      const qs = raw?.questions || raw?.sections?.[0]?.questions || [];
      return qs.length;
    } catch { return 0; }
  })();

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
    <div className="h-screen overflow-hidden flex flex-col transition-colors duration-500">
      <Header theme={theme} setTheme={setTheme} currentPage={currentPage} setCurrentPage={setCurrentPage} isLeftSidebarOpen={isLeftSidebarOpen} setIsLeftSidebarOpen={setIsLeftSidebarOpen} isRightSidebarOpen={isRightSidebarOpen} setIsRightSidebarOpen={setIsRightSidebarOpen} parsedQuestionsLength={parsedQuestionsLength} zoom={zoom} setZoom={setZoom} viewMode={viewMode} setViewMode={setViewMode} iframeRef={iframeRef} />

      {/* ── CONTENT AREA ── */}
      <main className="flex-1 overflow-hidden flex flex-col relative">
        {currentPage === "studio" ? (
          <StudioView 
            activeTab={activeTab} 
            setActiveTab={setActiveTab} 
            previewHtml={previewHtml} 
            setPreviewHtml={setPreviewHtml}
            examData={examData}
            setExamData={setExamData}
            examImages={examImages}
            setExamImages={setExamImages}
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
            setTheme={setTheme}
            lastRaw={lastRaw}
            setLastRaw={setLastRaw}
            lastConfig={lastConfig}
            setLastConfig={setLastConfig}
            bridgedPrompt={bridgedPrompt}
            setBridgedPrompt={setBridgedPrompt}
            isLeftSidebarOpen={isLeftSidebarOpen}
            setIsLeftSidebarOpen={setIsLeftSidebarOpen}
            isRightSidebarOpen={isRightSidebarOpen}
            setIsRightSidebarOpen={setIsRightSidebarOpen}
            zoom={zoom}
            setZoom={setZoom}
            viewMode={viewMode}
            setViewMode={setViewMode}
            iframeRef={iframeRef}
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
        ) : currentPage === "pkg" ? (
          <SyllabusGraphView theme={theme} />
        ) : currentPage === "assessment" ? (
          <AssessmentView theme={theme} />
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
  examData,
  setExamData,
  examImages,
  setExamImages, 
  isGenerating, 
  setIsGenerating,
  library,
  onProjectLoad,
  refreshLibrary,
  theme,
  setTheme,
  lastRaw,
  setLastRaw,
  lastConfig,
  setLastConfig,
  bridgedPrompt,
  setBridgedPrompt,
  isLeftSidebarOpen,
  setIsLeftSidebarOpen,
  isRightSidebarOpen,
  setIsRightSidebarOpen,
  zoom,
  setZoom,
  viewMode,
  setViewMode,
  iframeRef
}: any) {
  const [illustratingWid, setIllustratingWid] = useState<string | null>(null);
  const [illustratedWids, setIllustratedWids] = useState<Set<string>>(new Set());
  const [expandedWids, setExpandedWids] = useState<Set<string>>(new Set());
  const [customPrompts, setCustomPrompts] = useState<Record<string, string>>({});
  const [imageStyles, setImageStyles] = useState<Record<string, string>>({});
  const [regenExpandedWids, setRegenExpandedWids] = useState<Set<string>>(new Set());
  const [regenInstructions, setRegenInstructions] = useState<Record<string, string>>({});
  const [regenTopics, setRegenTopics] = useState<Record<string, string>>({});
  const [regeneratingWid, setRegeneratingWid] = useState<string | null>(null);
  // ── IMAGE NEEDS AGENT ──
  const [imageNeededWids, setImageNeededWids] = useState<Set<string>>(new Set());
  const [isAnalyzingImageNeeds, setIsAnalyzingImageNeeds] = useState(false);
  const [serverProgress, setServerProgress] = useState<{title: string, sub: string} | null>(null);

  useEffect(() => {
    let es: EventSource | null = null;
    if (isGenerating) {
      // Connect to the new SSE endpoint for real-time progress
      es = new EventSource(`/api/progress`);
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          setServerProgress({ title: data.title, sub: data.detail });
        } catch (err) {}
      };
    } else {
      setServerProgress(null);
    }
    return () => {
      if (es) es.close();
    };
  }, [isGenerating]);



  const handlePrintPdf = useCallback(() => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      iframeRef.current.contentWindow.print();
    } else {
      alert("Please generate a document first to print/download as PDF.");
    }
  }, []);

  // Parse questions out of lastRaw for the Illustrations panel
  const parsedQuestions: { wid: string; num: string | number; text: string; hasDiagram: boolean }[] = (() => {
    try {
      const raw = typeof lastRaw === 'string' ? JSON.parse(lastRaw) : lastRaw;
      const qs = raw?.questions || raw?.sections?.[0]?.questions || [];
      return qs.map((q: any, i: number) => ({
        wid: `qw-${i}`,
        num: q.number ?? i + 1,
        text: q.text ?? '',
        hasDiagram: !!(q.tikz_code || q.diagram_url || q.diagram_description)
      }));
    } catch { return []; }
  })();

  const handleIllustrate = async (wid: string, qtext: string, custom_prompt?: string, style: string = "png") => {
    if (!iframeRef.current) return;
    setIllustratingWid(wid);
    try {
      const res = await fetch(`${API_BASE}/api/generate-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_text: qtext,
          subject: lastConfig?.subject || 'General',
          level: lastConfig?.level || 'Primary 4',
          custom_prompt: custom_prompt || '',
          style: style
        })
      });

      // Read body as text first — avoids JSON parse crash on plain-text HTTP errors
      const rawText = await res.text();
      if (!res.ok) {
        // Try to extract FastAPI's { detail: "..." } message, fall back to raw text
        let errMsg = rawText;
        try {
          const errJson = JSON.parse(rawText);
          errMsg = errJson.detail || errJson.message || rawText;
        } catch { /* rawText wasn't JSON, use as-is */ }
        throw new Error(errMsg);
      }

      const data = JSON.parse(rawText);
      iframeRef.current.contentWindow?.postMessage({
        type: 'INJECT_IMAGE',
        wid,
        image_html: data.image_html
      }, '*');
      setIllustratedWids(prev => new Set(prev).add(wid));
    } catch (e: any) {
      alert('Illustration failed: ' + e.message);
    } finally {
      setIllustratingWid(null);
    }
  };
  const handleRegenerateQuestion = async (wid: string, index: number, topic: string, instruction: string) => {
    setRegeneratingWid(wid);
    try {
      // 1. Fetch the new question
      const res = await fetch(`${API_BASE}/api/regenerate-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject: lastConfig?.subject || 'General',
          level: lastConfig?.level || 'Primary 4',
          topic: topic,
          instruction: instruction
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to regenerate');
      if (!data.question) throw new Error('Empty response from AI');

      // 2. Splice it into lastRaw
      const raw = typeof lastRaw === 'string' ? JSON.parse(lastRaw) : { ...lastRaw };
      if (raw.questions && raw.questions[index]) {
         raw.questions[index] = data.question;
      } else if (raw.sections?.[0]?.questions?.[index]) {
         raw.sections[0].questions[index] = data.question;
      }

      // 3. Re-generate HTML
      const rawStr = JSON.stringify(raw);
      const renderRes = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
           mode: lastConfig?.mode || 'Exams',
           subject: lastConfig?.subject || 'General',
           level: lastConfig?.level || 'Primary 4',
           term: lastConfig?.term || 'Term 1',
           paper_style: lastConfig?.paper_style || 'uneb_standard',
           content_override: rawStr,
           question_count: 0
        })
      });
      const renderData = await renderRes.json();
      if (!renderRes.ok) {
        const detail = typeof renderData.detail === 'object' ? JSON.stringify(renderData.detail) : renderData.detail;
        throw new Error(detail || 'Failed to render');
      }

      setLastRaw(renderData.raw);
      setPreviewHtml(renderData.html);
      setRegenExpandedWids(prev => {
        const next = new Set(prev);
        next.delete(wid);
        return next;
      });
    } catch (e: any) {
      const msg = e.message || String(e);
      alert('Regeneration failed: ' + msg);
      console.error(e);
    } finally {
      setRegeneratingWid(null);
    }
  };
  const loadingSequence = [
    { title: "Synchronizing Neural Core", sub: "Authenticating database connection..." },
    { title: "Retrieving Syllabus Context", sub: "Filtering vector database by subject and level..." },
    { title: "Analyzing Pedagogical Logic", sub: "Applying Bloom's Taxonomy constraints..." },
    { title: "Drafting Section A", sub: "Generating objective items..." },
    { title: "Drafting Section B", sub: "Constructing structured scenarios..." },
    { title: "Drawing Illustrations", sub: "Synthesizing AI cartography and diagrams..." },
    { title: "Finalizing Document", sub: "Enforcing UNEB formatting guidelines..." },
    { title: "Compiling Marking Guide", sub: "Generating the teacher's rubric..." }
  ];
  
  const [loadingMsgIdx, setLoadingMsgIdx] = useState(0);

  useEffect(() => {
    if (!isGenerating) {
      setLoadingMsgIdx(0);
      return;
    }
    const interval = setInterval(() => {
      setLoadingMsgIdx((prev) => (prev + 1 < loadingSequence.length ? prev + 1 : prev));
    }, 3500);
    
    return () => clearInterval(interval);
  }, [isGenerating]);

  // 📡 SELECTION RELAY: Listen for messages from the Document Iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'EDUQUEST_READY') {
        // Iframe is ready! Push the current view mode immediately
        const iframe = document.querySelector('iframe');
        if (iframe && iframe.contentWindow) {
          iframe.contentWindow.postMessage({
            type: 'EDUQUEST_VIEW_MODE',
            mode: viewMode
          }, '*');
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [viewMode]);

  const handleDownload = async () => {
    if (!lastRaw || !lastConfig) {
      alert("Please generate an exam first.");
      return;
    }
    
    setIsGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/export/docx`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...lastConfig,
          content_override: lastRaw
        })
      });
      
      if (!res.ok) throw new Error("Export failed");
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `EduQuest_${lastConfig.subject}_${lastConfig.level}.docx`.replace(/\s+/g, '_');
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Download failed. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  // 📡 VIEW MODE SYNC: Push view mode changes to the iframe
  useEffect(() => {
    const iframe = document.querySelector('iframe');
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.postMessage({
        type: 'EDUQUEST_VIEW_MODE',
        mode: viewMode
      }, '*');
    }
  }, [viewMode, previewHtml]);


  return (
    <div className="flex flex-col flex-1 overflow-hidden relative w-full h-full">
      


      <div className="flex flex-col lg:flex-row flex-1 overflow-hidden relative w-full h-full">
      {/* Sidebar Controls (Left Drawer) */}
      <aside className={cn(
        "border-r border-border-main overflow-y-auto flex flex-col gap-8 transition-all duration-300 absolute lg:relative h-full z-40 bg-surface",
        theme === 'midnight' ? "glass" : "bg-surface",
        isLeftSidebarOpen 
          ? "translate-x-0 w-[85%] sm:w-[450px] p-4 lg:p-6 opacity-100" 
          : "-translate-x-full lg:translate-x-0 lg:w-0 p-0 lg:opacity-0 lg:border-none"
      )}>
        <div className="flex gap-1 bg-surface-soft p-1 rounded-xl">
           {(['gen', 'scenario', 'nursery', 'lib', 'insights', 'chat'] as const).map(tab => (
             <button 
               key={tab}
               onClick={() => setActiveTab(tab)}
               className={cn(
                 "flex-1 py-1.5 rounded-lg font-bold text-[10px] uppercase tracking-tighter transition-all",
                 activeTab === tab ? "bg-surface text-brand-800 shadow-sm" : "text-foreground opacity-40 hover:opacity-100"
               )}
             >
               {tab === 'gen' && 'Generator'}
               {tab === 'scenario' && 'Scenario'}
               {tab === 'nursery' && '🧸 ECD'}
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
            setLastRaw={setLastRaw}
            setLastConfig={setLastConfig}
            lastRaw={lastRaw}
            lastConfig={lastConfig}
            onPrint={handlePrintPdf}
            iframeRef={iframeRef}
            setImageNeededWids={setImageNeededWids}
            setIsAnalyzingImageNeeds={setIsAnalyzingImageNeeds}
            setIsRightSidebarOpen={setIsRightSidebarOpen}
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
        {activeTab === 'nursery' && (
          <NurseryView
            setPreviewHtml={setPreviewHtml}
            setExamData={setExamData}
            setExamImages={setExamImages}
            isGenerating={isGenerating}
            setIsGenerating={setIsGenerating}
            iframeRef={iframeRef}
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

        <div className="mt-auto pt-6 border-t border-border-main flex flex-col gap-4">
           <div className="flex gap-1.5 bg-background p-1.5 rounded-full border border-border-main shadow-inner w-fit">
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
           <div className="flex flex-col gap-2">
              <div className="px-3 py-1 bg-surface-soft border border-border-main rounded-full text-[9px] font-bold tracking-widest uppercase text-foreground opacity-60 w-fit">RAG-SYNAPSE v4</div>
              <div className="px-3 py-1 bg-surface-soft border border-border-main rounded-full text-[9px] font-bold tracking-widest uppercase text-foreground opacity-60 w-fit">TIKZ-JAX DRAW</div>
           </div>
        </div>
      </aside>

      {/* Preview Area */}
      <section id="preview-section" className="flex-1 bg-surface-soft/50 p-4 lg:p-8 overflow-y-auto relative w-full">
        <div 
           className="mx-auto bg-surface shadow-2xl rounded-sm relative overflow-hidden transition-all duration-500 origin-top"
           style={{ 
             width: `${850 * (zoom / 100)}px`,
             minHeight: `${1100 * (zoom / 100)}px`
           }}
        >
           {/* Slim progress bar — visible during generation without blocking the preview */}
           {isGenerating && (
             <div className="absolute top-0 left-0 right-0 z-50 pointer-events-none">
               <div className="h-[3px] bg-brand-800/10 w-full">
                 <div className="h-full bg-brand-800 animate-loading-bar" />
               </div>
               <div className="flex items-center gap-2 px-4 py-1.5 bg-brand-800/5 border-b border-brand-800/10">
                 <Loader2 className="w-3 h-3 text-brand-800 animate-spin flex-shrink-0" />
                 <span className="text-[9px] font-black text-brand-800 tracking-widest uppercase animate-pulse">
                   {serverProgress ? serverProgress.title : loadingSequence[loadingMsgIdx].title}
                 </span>
                 <span className="text-[9px] font-bold text-foreground opacity-30 tracking-widest uppercase ml-1">
                   — {serverProgress ? serverProgress.sub : loadingSequence[loadingMsgIdx].sub}
                 </span>
               </div>
             </div>
           )}

           {activeTab === 'nursery' && examData ? (
             <NurseryASTViewer examData={examData} images={examImages} />
           ) : previewHtml ? (
             <iframe
               ref={iframeRef}
               srcDoc={previewHtml}
               className="w-full h-full min-h-[1100px] border-none"
               style={{ marginTop: isGenerating ? '28px' : '0' }}
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

      {/* ── RIGHT PANEL: Illustrations Studio ── */}
      {previewHtml && parsedQuestions.length > 0 && (
        <aside className={cn(
          "border-l border-border-main flex flex-col overflow-hidden transition-all duration-300 absolute lg:relative right-0 h-full z-40 shadow-2xl lg:shadow-none bg-surface",
          theme === 'midnight' ? "glass" : "bg-surface",
          isRightSidebarOpen 
            ? "translate-x-0 w-[85%] sm:w-[350px] opacity-100" 
            : "translate-x-full lg:translate-x-0 lg:w-0 lg:opacity-0 lg:border-none"
        )}>
          {/* Header */}
          <div className="px-4 py-3 border-b border-border-main flex items-center gap-2 flex-shrink-0">
            <div className="w-6 h-6 rounded-lg bg-brand-800 flex items-center justify-center">
              <ImageIcon className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <p className="text-[11px] font-black text-foreground uppercase tracking-widest">Illustration Studio</p>
              <p className="text-[9px] text-foreground opacity-40 font-bold">{illustratedWids.size}/{parsedQuestions.length} illustrated</p>
            </div>
            {/* Image Needs Agent status badge */}
            {isAnalyzingImageNeeds && (
              <div className="ml-auto flex items-center gap-1.5 px-2 py-1 bg-orange-50 border border-orange-200 rounded-lg">
                <Loader2 className="w-3 h-3 text-orange-500 animate-spin" />
                <span className="text-[9px] font-black text-orange-600 uppercase tracking-wider">Scanning...</span>
              </div>
            )}
            {!isAnalyzingImageNeeds && imageNeededWids.size > 0 && (
              <div className="ml-auto flex items-center gap-1.5 px-2 py-1 bg-red-50 border border-red-200 rounded-lg">
                <span className="text-[9px] font-black text-red-600 uppercase tracking-wider">{imageNeededWids.size} need image</span>
              </div>
            )}
          </div>

          {/* Progress bar */}
          <div className="h-1 bg-surface-soft flex-shrink-0">
            <div 
              className="h-full bg-brand-800 transition-all duration-500"
              style={{ width: `${parsedQuestions.length > 0 ? (illustratedWids.size / parsedQuestions.length) * 100 : 0}%` }}
            />
          </div>

          {/* Bulk action */}
          <div className="px-4 py-2 border-b border-border-main flex-shrink-0">
            <button
              onClick={() => {
                parsedQuestions
                  .filter(q => !illustratedWids.has(q.wid) && !q.hasDiagram)
                  .forEach((q, i) => {
                    setTimeout(() => handleIllustrate(q.wid, q.text), i * 800);
                  });
              }}
              disabled={illustratingWid !== null || illustratedWids.size === parsedQuestions.length}
              className="w-full py-2 rounded-xl bg-brand-800/10 border border-brand-800/20 text-brand-800 text-[10px] font-black uppercase tracking-wider hover:bg-brand-800/20 transition-all disabled:opacity-40 flex items-center justify-center gap-2"
            >
              <Sparkles className="w-3 h-3" />
              Illustrate All Remaining
            </button>
          </div>

          {/* Question list */}
          <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
            {parsedQuestions.map((q, i) => {
              const isDone = illustratedWids.has(q.wid);
              const isLoading = illustratingWid === q.wid;
              const isExpanded = expandedWids.has(q.wid);
              const isRegenExpanded = regenExpandedWids.has(q.wid);
              const customVal = customPrompts[q.wid] || '';
              const regenInst = regenInstructions[q.wid] || '';
              const regenTop = regenTopics[q.wid] || '';

              return (
                <div
                  key={q.wid}
                  className={cn(
                    "rounded-xl border-2 transition-all",
                    isDone
                      ? "border-green-200 bg-green-50"
                      : imageNeededWids.has(q.wid)
                        ? "border-red-400 bg-red-50 shadow-[0_0_0_1px_rgba(239,68,68,0.2)]"
                        : "border-border-main bg-surface-soft hover:border-brand-800/30"
                  )}
                >
                  {/* Card top — Q badge + question text */}
                  <div className="p-3">
                    <div className="flex items-start gap-2 mb-2">
                      <span className={cn(
                        "text-[9px] font-black px-2 py-0.5 rounded-full flex-shrink-0",
                        isDone ? "bg-green-100 text-green-700" 
                          : imageNeededWids.has(q.wid) && !isDone ? "bg-red-100 text-red-700 animate-pulse" 
                          : "bg-brand-800/10 text-brand-800"
                      )}>Q{q.num}</span>
                      <p className="text-[10px] text-foreground leading-relaxed line-clamp-2 opacity-70">
                        {q.text}
                      </p>
                    </div>

                    {/* Status row + action buttons */}
                    <div className="flex items-center justify-between gap-1">
                      <span className={cn(
                        "text-[9px] font-bold uppercase tracking-wider flex-1",
                        q.hasDiagram ? "text-blue-600"
                          : isDone ? "text-green-600" 
                          : imageNeededWids.has(q.wid) ? "text-red-500 font-black" 
                          : "text-foreground opacity-30"
                      )}>
                        {isLoading ? "Generating..." 
                          : q.hasDiagram ? "📐 Has Diagram"
                          : isDone ? "✓ Illustrated" 
                          : imageNeededWids.has(q.wid) ? "⚠ Needs Image" 
                          : "No image"}
                      </span>

                      {/* Toggle custom prompt */}
                      <button
                        onClick={() => setExpandedWids(prev => {
                          const next = new Set(prev);
                          next.has(q.wid) ? next.delete(q.wid) : next.add(q.wid);
                          if (next.has(q.wid)) setRegenExpandedWids(r => { const n = new Set(r); n.delete(q.wid); return n; });
                          return next;
                        })}
                        title="Illustration prompt"
                        className={cn(
                          "text-[9px] font-black px-2.5 py-1.5 rounded-lg transition-all flex items-center gap-1 border",
                          isExpanded
                            ? "bg-brand-800/10 border-brand-800/30 text-brand-800"
                            : "border-border-main text-foreground opacity-50 hover:opacity-100"
                        )}
                      >
                        <Palette className="w-3 h-3" />
                      </button>

                      {/* Toggle regenerate prompt */}
                      <button
                        onClick={() => setRegenExpandedWids(prev => {
                          const next = new Set(prev);
                          next.has(q.wid) ? next.delete(q.wid) : next.add(q.wid);
                          if (next.has(q.wid)) setExpandedWids(r => { const n = new Set(r); n.delete(q.wid); return n; });
                          return next;
                        })}
                        title="Regenerate question text"
                        className={cn(
                          "text-[9px] font-black px-2.5 py-1.5 rounded-lg transition-all flex items-center gap-1 border",
                          isRegenExpanded
                            ? "bg-brand-800/10 border-brand-800/30 text-brand-800"
                            : "border-border-main text-foreground opacity-50 hover:opacity-100"
                        )}
                      >
                        <RefreshCw className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Expandable custom prompt section */}
                  {isExpanded && (
                    <div className="px-3 pb-3 border-t border-border-main pt-2 animate-in slide-in-from-top-1 duration-150">
                      <p className="text-[9px] font-black text-foreground opacity-40 uppercase tracking-widest mb-1.5">
                        Custom Illustration Setup
                      </p>
                      <textarea
                        rows={3}
                        value={customVal}
                        onChange={(e) => setCustomPrompts(prev => ({ ...prev, [q.wid]: e.target.value }))}
                        placeholder={`e.g. "A labelled diagram of the human digestive system" or "A bar graph showing rainfall data"`}
                        className="w-full text-[10px] bg-surface border border-border-main rounded-lg p-2 outline-none focus:border-brand-800 transition-all resize-none font-medium placeholder:opacity-40 text-foreground mb-2"
                      />
                      <div className="flex gap-2 mb-2">
                        <select
                          value={imageStyles[q.wid] || "png"}
                          onChange={(e) => setImageStyles(prev => ({ ...prev, [q.wid]: e.target.value }))}
                          className="flex-1 text-[10px] font-bold bg-surface border border-border-main rounded-lg p-1.5 outline-none focus:border-brand-800 text-foreground"
                        >
                          <option value="png">Format: Academic (PNG)</option>
                          <option value="svg">Format: Vector Graph (SVG)</option>
                          <option value="tikz">Format: LaTeX TikZ (TikzJax)</option>
                          <option value="sketch">Style: Hand-Drawn Sketch</option>
                          <option value="realistic">Style: Realistic Photo</option>
                          <option value="3d">Style: 3D Render</option>
                          <option value="raw">Style: Raw Prompt (chatgpt-image)</option>
                        </select>
                      </div>
                      <button
                        onClick={() => {
                          handleIllustrate(q.wid, q.text, customVal.trim(), imageStyles[q.wid] || "png");
                        }}
                        disabled={isLoading || illustratingWid !== null}
                        className="w-full py-1.5 rounded-lg bg-brand-800 text-white text-[9px] font-black uppercase tracking-wider flex items-center justify-center gap-1.5 hover:bg-brand-900 transition-all disabled:opacity-40"
                      >
                        {isLoading ? (
                          <><Loader2 className="w-2.5 h-2.5 animate-spin" /> Generating...</>
                        ) : (
                          <><Sparkles className="w-2.5 h-2.5" /> Generate Image</>
                        )}
                      </button>
                    </div>
                  )}

                  {/* Expandable regenerate section */}
                  {isRegenExpanded && (
                    <div className="px-3 pb-3 border-t border-border-main pt-2 animate-in slide-in-from-top-1 duration-150">
                      <p className="text-[9px] font-black text-foreground opacity-40 uppercase tracking-widest mb-1.5">
                        Regenerate Question
                      </p>
                      <input
                        type="text"
                        value={regenTop}
                        onChange={(e) => setRegenTopics(prev => ({ ...prev, [q.wid]: e.target.value }))}
                        placeholder="Optional Topic (e.g. Algebra)"
                        className="w-full text-[10px] bg-surface border border-border-main rounded-lg p-2 outline-none focus:border-brand-800 transition-all font-medium placeholder:opacity-40 text-foreground mb-2"
                      />
                      <textarea
                        rows={2}
                        value={regenInst}
                        onChange={(e) => setRegenInstructions(prev => ({ ...prev, [q.wid]: e.target.value }))}
                        placeholder="Instruction (e.g. Make it harder, or use a scenario about apples)"
                        className="w-full text-[10px] bg-surface border border-border-main rounded-lg p-2 outline-none focus:border-brand-800 transition-all resize-none font-medium placeholder:opacity-40 text-foreground mb-2"
                      />
                      <button
                        onClick={() => handleRegenerateQuestion(q.wid, i, regenTop, regenInst)}
                        disabled={regeneratingWid !== null}
                        className="w-full py-1.5 rounded-lg border-2 border-brand-800 text-brand-800 text-[9px] font-black uppercase tracking-wider flex items-center justify-center gap-1.5 hover:bg-brand-800/10 transition-all disabled:opacity-40"
                      >
                        {regeneratingWid === q.wid ? (
                          <><Loader2 className="w-2.5 h-2.5 animate-spin" /> Rewriting...</>
                        ) : (
                          <><RefreshCw className="w-2.5 h-2.5" /> Confirm Rewrite</>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

        </aside>
      )}

      {/* Mobile Overlay Background (Dim) */}
      {(isLeftSidebarOpen || isRightSidebarOpen) && (
        <div 
          className="absolute inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm transition-opacity duration-300"
          onClick={() => { setIsLeftSidebarOpen(false); setIsRightSidebarOpen(false); }}
        />
      )}
      </div>
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
    fetch(`${API_BASE}/api/syllabus/config?t=${Date.now()}`)
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
  setLastRaw,
  setLastConfig,
  lastRaw,
  lastConfig,
  onPrint,
  iframeRef,
  setImageNeededWids,
  setIsAnalyzingImageNeeds,
  setIsRightSidebarOpen
}: any) {
  const [mode, setMode] = useState<Mode>("Exams");
  const [level, setLevel] = useState(lastConfig?.level || "Primary 7");
  const [subject, setSubject] = useState(lastConfig?.subject || "Mathematics");
  const [term, setTerm] = useState(lastConfig?.term || "Term 1");
  const [period, setPeriod] = useState("MOT");
  const [qCount, setQCount] = useState(20);
  const [duration, setDuration] = useState("2 HR");
  const [paperStyle, setPaperStyle] = useState("uneb_standard");
  const [topic, setTopic] = useState("");
  const [config, setConfig] = useState<any>({ subjects: [], levels: [], syllabus: {} });

  useEffect(() => {
    fetch(`${API_BASE}/api/syllabus/config?t=${Date.now()}`)
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(() => {});
  }, []);

  const availableSubjects = config.subjects.filter((s: string) =>
    config.syllabus?.[s]?.[level]
  );

  const availableTopics = config.syllabus?.[subject]?.[level] || [];

  // 📄 PAPER STANDARDS MAPPING
  useEffect(() => {
    if (mode !== "Exams") return;
    const standards: Record<string, Record<string, { count: number; duration: string }>> = {
      "Primary 7": {
        "Mathematics": { count: 32, duration: "2 HR 30 MIN" },
        "Integrated Science": { count: 55, duration: "2 HR 15 MIN" },
        "Social Studies with Religious Education": { count: 55, duration: "2 HR 15 MIN" },
        "English": { count: 55, duration: "2 HR 15 MIN" },
      },
      "Primary 6": {
        "Mathematics": { count: 30, duration: "2 HR 30 MIN" },
        "Integrated Science": { count: 55, duration: "2 HR 15 MIN" },
        "Social Studies with Religious Education": { count: 55, duration: "2 HR 15 MIN" },
        "English": { count: 55, duration: "2 HR 15 MIN" }
      },
      "Primary 5": {
        "Mathematics": { count: 30, duration: "2 HR 30 MIN" },
        "Integrated Science": { count: 55, duration: "2 HR 15 MIN" },
        "Social Studies with Religious Education": { count: 55, duration: "2 HR 15 MIN" },
        "English": { count: 55, duration: "2 HR 15 MIN" }
      },
      "Primary 4": {
        "Mathematics": { count: 30, duration: "2 HR 30 MIN" },
        "Integrated Science": { count: 55, duration: "2 HR 15 MIN" },
        "Social Studies with Religious Education": { count: 55, duration: "2 HR 15 MIN" },
        "English": { count: 55, duration: "2 HR 15 MIN" }
      },
    };
    const std = standards[level]?.[subject] || { count: 20, duration: "2 HR" };
    setQCount(std.count);
    setDuration(std.duration);
  }, [level, subject, mode]);

  useEffect(() => {
    if (availableSubjects.length > 0 && !availableSubjects.includes(subject)) {
      setSubject(availableSubjects[0]);
    }
  }, [level, availableSubjects]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setImageNeededWids(new Set());
    setIsAnalyzingImageNeeds(false);

    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode, level, subject,
          term: `${term} (${period})`,
          question_count: qCount,
          duration,
          paper_style: paperStyle,
          topic,
          brand_name: "EDUMERC"
        })
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();

      if (data.error) {
        alert("Generation error: " + data.error);
        return;
      }

      setPreviewHtml(data.html);
      setLastRaw(data.raw);
      setLastConfig({ mode, level, subject, term: `${term} (${period})`, paper_style: paperStyle });
      refreshLibrary();

      // ── IMAGE NEEDS AGENT: Auto-run after generation ──
      const finalQuestions = data.raw ? JSON.parse(data.raw)?.questions ?? [] : [];
      if (finalQuestions.length > 0) {
        setIsAnalyzingImageNeeds(true);
        try {
          const agentRes = await fetch(`${API_BASE}/api/analyze-image-needs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ questions: finalQuestions, subject, level })
          });
          const agentData = await agentRes.json();
          const flaggedNums: number[] = agentData.needs_image || [];

          const flaggedWids = new Set<string>(
            flaggedNums
              .map(num => finalQuestions.findIndex((q: any) => q.number === num))
              .filter(idx => idx >= 0)
              .map(idx => `qw-${idx}`)
          );
          setImageNeededWids(flaggedWids);

          if (iframeRef.current?.contentWindow && flaggedWids.size > 0) {
            iframeRef.current.contentWindow.postMessage({
              type: 'MARK_NEEDS_IMAGE',
              wids: Array.from(flaggedWids)
            }, '*');
          }

          if (flaggedWids.size > 0) setIsRightSidebarOpen(true);
        } catch (e) {
          console.warn('Image Needs Agent failed:', e);
        } finally {
          setIsAnalyzingImageNeeds(false);
        }
      }
    } catch (e) {
      alert("Generation failed. Please try again.");
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
            onChange={(e) => { setLevel(e.target.value); setTopic(""); }}
            className="w-full bg-surface-soft border border-border-main rounded-lg p-2.5 text-xs font-bold outline-none"
          >
            {config.levels.map((l: string) => <option key={l}>{l}</option>)}
          </select>
        </div>
        <div>
          <label className="sec-label">Subject</label>
          <select 
            value={subject}
            onChange={(e) => { setSubject(e.target.value); setTopic(""); }}
            className="w-full bg-surface-soft border border-border-main rounded-lg p-2.5 text-xs font-bold outline-none"
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
        <label className="sec-label">Target Topic (Optional)</label>
        <select 
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="w-full bg-surface-soft border border-border-main rounded-xl p-3 text-xs font-bold outline-none appearance-none cursor-pointer"
        >
          <option value="">Full Syllabus Coverage</option>
          {availableTopics.map((t: string) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      <div>
        <label className="sec-label">Paper Appearance</label>
        <div className="grid grid-cols-3 gap-2">
          {[
            { key: "elite_dark", label: "Elite Dark", color: "bg-brand-800" },
            { key: "pro_protocol", label: "Pro Protocol", color: "bg-slate-800" },
            { key: "uneb_standard", label: "UNEB Classic", color: "bg-black" }
          ].map(s => (
            <button
              key={s.key}
              onClick={() => setPaperStyle(s.key)}
              className={cn(
                "py-2.5 rounded-xl text-[9px] font-black uppercase tracking-tighter flex flex-col items-center gap-1.5 border-2 transition-all",
                paperStyle === s.key
                  ? "border-brand-800 bg-brand-800/10 text-brand-800"
                  : "border-border-main bg-surface-soft text-foreground opacity-50 hover:opacity-100"
              )}
            >
              <div className={`w-5 h-3 rounded-sm ${s.color}`} />
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <button 
        disabled={isGenerating}
        onClick={handleGenerate}
        className={cn(
          "w-full py-4 mt-2 rounded-2xl flex items-center justify-center gap-3 transition-all font-black uppercase tracking-[0.2em] text-sm disabled:opacity-50",
          theme === 'midnight' ? "bg-brand-500 text-black neon-glow hover:bg-brand-400" : "bg-brand-800 text-white hover:bg-brand-900 shadow-xl"
        )}
      >
        {isGenerating ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            GENERATE
          </>
        )}
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
                  a.download = `${subject}_${level}_Exam.docx`;
                  a.click();
                  window.URL.revokeObjectURL(url);
                } catch(e) {
                  alert("Export failed. Please try again.");
                }
             }}
             className="w-full py-2 bg-surface border border-border-main rounded-lg text-xs font-bold text-foreground opacity-50 hover:opacity-100 hover:border-brand-800 hover:text-brand-800 transition-all"
           >
             Download Microsoft Word (.docx)
           </button>
           <button 
             onClick={onPrint}
             className="w-full py-2 bg-brand-800 border border-brand-800 rounded-lg text-xs font-bold text-white shadow-lg hover:bg-brand-900 transition-all mt-1"
           >
             Download PDF (Print Format)
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
    fetch(`${API_BASE}/api/syllabus/config?t=${Date.now()}`)
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
                <div className="space-y-4">
                    {(() => {
                        const saturation = analysis.topic_saturation || {};
                        // Group topics by question count
                        const grouped: Record<number, string[]> = {};
                        Object.entries(saturation).forEach(([topic, count]: [string, any]) => {
                            const c = Number(count);
                            if (!grouped[c]) grouped[c] = [];
                            grouped[c].push(topic);
                        });

                        return Object.entries(grouped)
                            .sort((a, b) => Number(b[0]) - Number(a[0])) // Highest count first
                            .map(([count, topics]) => (
                                <div key={count} className="p-4 rounded-2xl bg-surface-soft border border-border-main flex justify-between items-start group">
                                    <div className="flex-1">
                                        <div className="flex flex-wrap gap-1.5">
                                            {topics.map((t, idx) => (
                                                <span key={t} className="text-[10px] font-black text-foreground opacity-60 uppercase tracking-tight">
                                                    {t}{idx < topics.length - 1 ? "," : ""}
                                                </span>
                                            ))}
                                        </div>
                                        <div className="text-[8px] font-bold text-foreground/40 mt-1 uppercase tracking-tighter">
                                            Curriculum Domain{topics.length > 1 ? 's' : ''}
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <div className="text-xl font-black text-brand-800">{count}</div>
                                        <div className="text-[7px] font-black opacity-40 uppercase tracking-tighter">Questions</div>
                                    </div>
                                </div>
                            ));
                    })()}

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
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Remote Connection. Please verify the API is online.' }]);
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

// ── NURSERY / ECD VIEW ──
function NurseryView({ setPreviewHtml, setExamData, setExamImages, isGenerating, setIsGenerating, iframeRef }: any) {
  const [classLevel, setClassLevel] = useState("Middle Class");
  const [learningArea, setLearningArea] = useState("LA4");
  const [term, setTerm] = useState("Term 1");
  const [period, setPeriod] = useState("EOT");
  const [schoolName, setSchoolName] = useState("EduQuest Academy");
  const [year, setYear] = useState("2025");
  const [integrity, setIntegrity] = useState<any>(null);
  const [isDeepChecking, setIsDeepChecking] = useState(false);
  const [localLastData, setLocalLastData] = useState<any>(null);

  const CLASS_LEVELS = ["Baby Class", "Middle Class", "Top Class"];
  const LEARNING_AREAS = [
    { id: "LA1", label: "LA 1: Relating with others in an acceptable way (Social Development)" },
    { id: "LA2", label: "LA 2: Interacting, exploring, knowing and using my environment (Environment / General Knowledge)" },
    { id: "LA3", label: "LA 3: Taking care of myself for proper growth and development (Health Habits & Psychomotor)" },
    { id: "LA4", label: "LA 4: Developing and using mathematical concepts in my day-to-day experiences (Numeracy)" },
    { id: "LA5", label: "LA 5: Developing and using my language appropriately (Literacy / Reading)" },
  ];
  const PERIODS = [
    { id: "BOT", label: "Beginning of Term" },
    { id: "MOT", label: "Mid Term" },
    { id: "EOT", label: "End of Term" },
  ];

  const handleGenerate = async () => {
    setIsGenerating(true);
    setIntegrity(null);
    try {
      const res = await fetch(`${API_BASE}/api/nursery-exam`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ class_level: classLevel, learning_area: learningArea, term, period, school_name: schoolName, year })
      });
      const rawText = await res.text();
      if (!res.ok) {
        let msg = rawText;
        try { msg = JSON.parse(rawText).detail || rawText; } catch {}
        alert("Generation failed: " + msg);
        return;
      }
      const data = JSON.parse(rawText);
      setPreviewHtml(data.html);
      if (data.integrity) setIntegrity(data.integrity);
      if (data.exam_data) {
          setLocalLastData(data.exam_data);
          if (setExamData) setExamData(data.exam_data);
      }
      if (data.images && setExamImages) setExamImages(data.images);
    } catch (e: any) {
      alert("Error: " + e.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeepCheck = async () => {
    if (!localLastData) return;
    setIsDeepChecking(true);
    try {
      const res = await fetch(`${API_BASE}/api/integrity-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exam_data: localLastData, ai_check: true, ai_sample_size: 3 }),
        signal: AbortSignal.timeout(120000),
      });
      const data = await res.json();
      setIntegrity(data);
    } catch (e: any) {
      alert("Deep check error: " + e.message);
    } finally {
      setIsDeepChecking(false);
    }
  };

  return (
    <div className="flex flex-col gap-5 animate-in fade-in slide-in-from-left-4 duration-300">
      <div className="flex items-center gap-3 p-4 bg-gradient-to-br from-pink-50 to-purple-50 border border-pink-100 rounded-2xl">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-xl shadow-lg">&#129528;</div>
        <div>
          <p className="text-[11px] font-black uppercase tracking-widest text-purple-700">ECD / Nursery Generator</p>
          <p className="text-[10px] text-foreground opacity-50 font-bold">Baby &middot; Middle &middot; Top Class</p>
        </div>
      </div>

      <div>
        <label className="sec-label">Class Level</label>
        <div className="flex flex-col gap-1.5">
          {CLASS_LEVELS.map(cl => (
            <button key={cl} onClick={() => setClassLevel(cl)}
              className={cn("py-2.5 px-4 rounded-xl border-2 text-[11px] font-black text-left transition-all",
                classLevel === cl ? "border-purple-400 bg-purple-50 text-purple-700" : "border-border-main bg-surface-soft text-foreground opacity-60 hover:opacity-100"
              )}>
              {cl === "Baby Class" && "Baby Class (3\u20134 years)"}
              {cl === "Middle Class" && "Middle Class (4\u20135 years)"}
              {cl === "Top Class" && "Top Class (5\u20136 years)"}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="sec-label">Learning Area</label>
        <div className="flex flex-col gap-1.5">
          {LEARNING_AREAS.map(la => (
            <button key={la.id} onClick={() => setLearningArea(la.id)}
              className={cn("py-2 px-4 rounded-xl border-2 text-[10px] font-bold text-left transition-all",
                learningArea === la.id ? "border-purple-400 bg-purple-50 text-purple-700" : "border-border-main bg-surface-soft text-foreground opacity-60 hover:opacity-100"
              )}>{la.label}</button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="sec-label">Term</label>
          <div className="flex flex-col gap-1">
            {["Term 1","Term 2","Term 3"].map(t => (
              <button key={t} onClick={() => setTerm(t)}
                className={cn("py-1.5 px-3 rounded-lg border text-[10px] font-bold transition-all",
                  term === t ? "border-purple-400 bg-purple-50 text-purple-700" : "border-border-main opacity-50 hover:opacity-100"
                )}>{t}</button>
            ))}
          </div>
        </div>
        <div>
          <label className="sec-label">Period</label>
          <div className="flex flex-col gap-1">
            {PERIODS.map(p => (
              <button key={p.id} onClick={() => setPeriod(p.id)}
                className={cn("py-1.5 px-3 rounded-lg border text-[10px] font-bold transition-all",
                  period === p.id ? "border-purple-400 bg-purple-50 text-purple-700" : "border-border-main opacity-50 hover:opacity-100"
                )}>{p.label}</button>
            ))}
          </div>
        </div>
      </div>

      <div>
        <label className="sec-label">School Name</label>
        <input value={schoolName} onChange={e => setSchoolName(e.target.value)}
          className="w-full text-[11px] bg-surface border border-border-main rounded-xl p-2.5 outline-none focus:border-purple-400 transition-all font-bold text-foreground" />
      </div>
      <div>
        <label className="sec-label">Year</label>
        <input value={year} onChange={e => setYear(e.target.value)}
          className="w-full text-[11px] bg-surface border border-border-main rounded-xl p-2.5 outline-none focus:border-purple-400 transition-all font-bold text-foreground" />
      </div>

      <button onClick={handleGenerate} disabled={isGenerating}
        className="w-full py-3.5 rounded-2xl bg-gradient-to-br from-pink-500 to-purple-600 text-white text-[11px] font-black uppercase tracking-widest shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
        {isGenerating ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Generating ECD Exam...</>
        ) : (
          <><Sparkles className="w-4 h-4" /> Generate Nursery Exam</>
        )}
      </button>

      <p className="text-[9px] text-foreground opacity-30 text-center font-bold tracking-wider uppercase">
        Authentic Ugandan ECD format &middot; LA1&ndash;LA5 support
      </p>

      {/* ── Integrity Report ── */}
      {integrity && (
        <div style={{ borderRadius: "14px", border: "1px solid var(--border-main)", overflow: "hidden", marginTop: "4px" }}>
          {/* Header */}
          <div style={{
            padding: "12px 16px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            background: integrity.overall_status === "PASS" ? "#22c55e15"
                      : integrity.overall_status === "WARN" ? "#f59e0b15" : "#ef444415",
            borderBottom: "1px solid var(--border-main)"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "24px" }}>
                {integrity.overall_status === "PASS" ? "✅" : integrity.overall_status === "WARN" ? "⚠️" : "❌"}
              </span>
              <div>
                <div style={{ fontWeight: 900, fontSize: "13px" }}>Integrity Report</div>
                <div style={{ fontSize: "11px", opacity: 0.6 }}>{integrity.summary}</div>
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "26px", fontWeight: 900,
                color: integrity.overall_score >= 80 ? "#22c55e" : integrity.overall_score >= 50 ? "#f59e0b" : "#ef4444" }}>
                {integrity.overall_score}
              </div>
              <div style={{ fontSize: "9px", fontWeight: 700, opacity: 0.5 }}>/ 100</div>
            </div>
          </div>

          {/* Per-question badges */}
          <div style={{ padding: "10px 16px" }}>
            <div style={{ fontSize: "10px", fontWeight: 700, opacity: 0.4, textTransform: "uppercase", marginBottom: "8px" }}>Questions</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
              {integrity.questions?.map((q: any, idx: number) => (
                <div key={idx} title={q.instruction + (q.rule_check?.issues?.length ? "\n⚠ " + q.rule_check.issues.join("\n⚠ ") : "")}
                  style={{
                    padding: "3px 8px", borderRadius: "20px", fontSize: "10px", fontWeight: 800, cursor: "default",
                    background: q.final_status === "PASS" ? "#22c55e20" : q.final_status === "WARN" ? "#f59e0b20" : "#ef444420",
                    color: q.final_status === "PASS" ? "#22c55e" : q.final_status === "WARN" ? "#f59e0b" : "#ef4444",
                    border: `1px solid ${q.final_status === "PASS" ? "#22c55e40" : q.final_status === "WARN" ? "#f59e0b40" : "#ef444440"}`,
                  }}>
                  Q{q.number} {q.final_status === "PASS" ? "✓" : q.final_status === "WARN" ? "△" : "✗"}
                </div>
              ))}
            </div>
          </div>

          {/* Critical issues */}
          {integrity.critical_issues?.length > 0 && (
            <div style={{ padding: "10px 16px", borderTop: "1px solid var(--border-main)" }}>
              <div style={{ fontSize: "10px", fontWeight: 700, color: "#ef4444", marginBottom: "6px" }}>⚠ Critical Issues</div>
              {integrity.critical_issues.map((ci: any, idx: number) => (
                <div key={idx} style={{ fontSize: "11px", opacity: 0.7, marginBottom: "4px" }}>
                  <span style={{ fontWeight: 800 }}>Q{ci.question} ({ci.type}):</span> {ci.issues.join(" · ")}
                </div>
              ))}
            </div>
          )}

          {/* VLM Visual Layout Audit (Option 2) */}
          <div style={{ padding: "10px 16px", borderTop: "1px solid var(--border-main)", background: "#3b82f60d" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
              <div style={{ fontSize: "10px", fontWeight: 800, color: "#3b82f6", display: "flex", alignItems: "center", gap: "4px" }}>
                <span>👁️</span> VLM VISUAL LAYOUT AUDITOR
              </div>
              <span style={{
                fontSize: "9px", fontWeight: 900, padding: "2px 6px", borderRadius: "10px",
                background: integrity.layout_status === "PASS" ? "#22c55e20" : integrity.layout_status === "WARN" ? "#f59e0b20" : "#ef444420",
                color: integrity.layout_status === "PASS" ? "#22c55e" : integrity.layout_status === "WARN" ? "#f59e0b" : "#ef4444",
                marginLeft: "auto"
              }}>
                {integrity.layout_status || "PASS"}
              </span>
            </div>
            {integrity.layout_warnings?.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                {integrity.layout_warnings.map((w: string, idx: number) => (
                  <div key={idx} style={{ fontSize: "10px", opacity: 0.75, color: "var(--foreground)" }}>
                    • {w}
                  </div>
                ))}
                {integrity.layout_css_patch && (
                  <div style={{ fontSize: "9px", color: "#22c55e", fontWeight: 700, marginTop: "4px", background: "#22c55e10", padding: "4px 8px", borderRadius: "6px" }}>
                    ✓ Layout Patch Auto-Applied to Print Preview
                  </div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: "10px", opacity: 0.6 }}>No visual pagination, scaling or overlap defects detected. Excellent print contrast.</div>
            )}
          </div>

          {/* Pedagogical Graph (PKG) Safeguards (Option 1) */}
          {integrity.pkg_warnings?.length > 0 && (
            <div style={{ padding: "10px 16px", borderTop: "1px solid var(--border-main)", background: "#f59e0b0d" }}>
              <div style={{ fontSize: "10px", fontWeight: 800, color: "#f59e0b", display: "flex", alignItems: "center", gap: "4px", marginBottom: "6px" }}>
                <span>🎓</span> CURRICULUM SCAFFOLDING WARNING
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                {integrity.pkg_warnings.map((w: string, idx: number) => (
                  <div key={idx} style={{ fontSize: "10px", opacity: 0.75 }}>
                    ⚠ {w}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Deep AI Check button */}
          <div style={{ padding: "10px 16px", borderTop: "1px solid var(--border-main)" }}>
            <button onClick={handleDeepCheck} disabled={isDeepChecking || !localLastData}
              style={{ width: "100%", padding: "8px", borderRadius: "8px", border: "1px solid var(--border-main)",
                background: "transparent", color: "var(--foreground)", fontSize: "12px", fontWeight: 800,
                cursor: isDeepChecking ? "wait" : "pointer", opacity: isDeepChecking ? 0.6 : 1 }}>
              {isDeepChecking ? "🔍 Running GPT-4o Vision Check..." : "🔍 Run Deep AI Check (GPT-4o Vision)"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
interface GraphNode {
  subject: string;
  level: string;
  topic: string;
  complexity: string;
  skills: string[];
  prereqs: { subject: string; level: string; topic: string }[];
}

function SyllabusGraphView({ theme }: { theme: string }) {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubj, setSelectedSubj] = useState("Mathematical Concepts");
  const [selectedLevel, setSelectedLevel] = useState("Top Class");

  useEffect(() => {
    fetch(`${API_BASE}/api/syllabus/graph`)
      .then((res) => res.json())
      .then((data) => {
        setNodes(data.nodes || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching PKG graph:", err);
        setLoading(false);
      });
  }, []);

  const subjects = Array.from(new Set(nodes.map((n) => n.subject)));
  const levels = Array.from(new Set(nodes.map((n) => n.level)));

  const filteredNodes = nodes.filter(
    (n) => n.subject === selectedSubj && n.level === selectedLevel
  );

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-background text-foreground transition-colors duration-500">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h2 className="text-3xl font-extrabold tracking-tight flex items-center gap-3">
              <span className="bg-brand-500/10 p-2 rounded-xl border border-brand-500/20 text-brand-500 inline-flex">
                <Compass className="w-7 h-7" />
              </span>
              Pedagogical Knowledge Graph (PKG)
            </h2>
            <p className="text-sm opacity-60 mt-1">
              Traverse hierarchical syllabus dependencies, skills, and prerequisite paths.
            </p>
          </div>

          {/* Filters */}
          <div className="flex gap-3 bg-surface border border-border-main p-2 rounded-xl shadow-sm">
            <select
              value={selectedSubj}
              onChange={(e) => setSelectedSubj(e.target.value)}
              className="bg-background border border-border-main rounded-lg px-3 py-1.5 text-xs font-bold outline-none text-foreground cursor-pointer"
            >
              {subjects.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="bg-background border border-border-main rounded-lg px-3 py-1.5 text-xs font-bold outline-none text-foreground cursor-pointer"
            >
              {levels.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 opacity-60">
            <Loader2 className="w-10 h-10 animate-spin text-brand-500 mb-4" />
            <p className="text-sm font-semibold">Resolving DAG Prerequisite Nodes...</p>
          </div>
        ) : filteredNodes.length === 0 ? (
          <div className="text-center py-20 bg-surface border border-border-main rounded-2xl opacity-60">
            <p className="text-sm">No knowledge nodes mapped for this selection yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredNodes.map((node, i) => (
              <div
                key={i}
                className={cn(
                  "p-6 rounded-2xl border border-border-main bg-surface transition-all duration-300 hover:shadow-lg hover:-translate-y-1 relative overflow-hidden group",
                  (theme === "midnight" || theme === "royal") && "glass-premium"
                )}
              >
                {/* Visual Accent Glow on Hover */}
                <div className="absolute -inset-px bg-gradient-to-r from-brand-500 to-accent-gradient opacity-0 group-hover:opacity-10 transition-opacity duration-300 blur-sm pointer-events-none" />

                <div className="relative z-10">
                  {/* Badges */}
                  <div className="flex justify-between items-center mb-4">
                    <span className="px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider rounded-full bg-brand-500/10 text-brand-500 border border-brand-500/20">
                      {node.complexity}
                    </span>
                    <span className="text-[10px] opacity-40 font-bold uppercase tracking-widest">
                      {node.level}
                    </span>
                  </div>

                  {/* Node Title */}
                  <h3 className="text-xl font-bold mb-4 text-foreground tracking-tight">
                    {node.topic}
                  </h3>

                  {/* Skills Grid */}
                  <div className="mb-6">
                    <h4 className="text-[10px] uppercase tracking-widest font-extrabold opacity-40 mb-2.5">
                      Targeted Learning Skills
                    </h4>
                    <div className="flex flex-col gap-2">
                      {node.skills.map((skill, si) => (
                        <div key={si} className="flex items-start gap-2.5 text-xs text-foreground/80 leading-relaxed">
                          <span className="text-brand-500 font-bold mt-0.5">✓</span>
                          <span>{skill}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Prerequisite paths */}
                  <div className="border-t border-border-main/50 pt-4">
                    <h4 className="text-[10px] uppercase tracking-widest font-extrabold opacity-40 mb-2.5">
                      Prerequisite Dependency Path
                    </h4>
                    {node.prereqs.length === 0 ? (
                      <p className="text-[11px] italic opacity-40">None (Foundational Outcome Node)</p>
                    ) : (
                      <div className="flex flex-wrap gap-2 items-center">
                        {node.prereqs.map((prereq, pi) => (
                          <div key={pi} className="flex items-center gap-1.5">
                            <span className="px-2 py-1 text-[10px] font-bold rounded bg-background border border-border-main text-foreground/70">
                              {prereq.topic}
                            </span>
                            {pi < node.prereqs.length - 1 && (
                              <span className="text-xs opacity-35 font-bold">➔</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

