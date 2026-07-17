"use client";

import { useState, useEffect } from "react";
import {
  Database, Loader2, Plus, CheckCircle2, ArrowRight, X, Trash2, Upload, FileSpreadsheet, Keyboard
} from "lucide-react";
import { cn, authFetch } from "../lib/utils";


export default function SchoolOnboardingView({ theme, setActiveTab }: { theme: string, setActiveTab: any }) {
  const [step, setStep] = useState(1);
  const [schoolName, setSchoolName] = useState("");
  const [groups, setGroups] = useState<{level: string, stream: string, students: {full_name: string, index_number: string}[]}[]>([]);
  
  const [currentLevel, setCurrentLevel] = useState("P.1");
  const [currentStream, setCurrentStream] = useState("");
  const [importMode, setImportMode] = useState<"manual" | "csv">("manual");
  const [studentRows, setStudentRows] = useState<{ name: string; index: string }[]>([
    { name: "", index: "" },
    { name: "", index: "" },
    { name: "", index: "" },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const levels = ["P.1", "P.2", "P.3", "P.4", "P.5", "P.6", "P.7"];

  const updateRow = (idx: number, field: "name" | "index", value: string) => {
    const updated = [...studentRows];
    updated[idx][field] = value;
    setStudentRows(updated);
  };

  const addRow = () => {
    setStudentRows([...studentRows, { name: "", index: "" }]);
  };

  const removeRow = (idx: number) => {
    if (studentRows.length === 1) {
      setStudentRows([{ name: "", index: "" }]);
    } else {
      setStudentRows(studentRows.filter((_, i) => i !== idx));
    }
  };

  const handleCsvUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      const lines = text.split("\n");
      const parsedRows: { name: string; index: string }[] = [];
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        if (trimmed.includes(",")) {
          const firstCommaIdx = trimmed.indexOf(",");
          const name = trimmed.substring(0, firstCommaIdx).trim();
          const idx = trimmed.substring(firstCommaIdx + 1).trim();
          parsedRows.push({ name, index: idx });
        } else {
          parsedRows.push({ name: trimmed, index: "" });
        }
      }
      if (parsedRows.length > 0) {
        setStudentRows(parsedRows);
        setImportMode("manual");
      }
    };
    reader.readAsText(file);
    e.target.value = ""; // Reset file input
  };

  const handleAddGroup = () => {
     if(!currentStream) return;
     const newStudents = studentRows
        .map(r => ({ full_name: r.name.trim(), index_number: r.index.trim() }))
        .filter(s => s.full_name.length > 0);
        
     if (newStudents.length === 0) return;
        
     setGroups([...groups, { level: currentLevel, stream: currentStream, students: newStudents }]);
     setCurrentStream("");
     setStudentRows([
       { name: "", index: "" },
       { name: "", index: "" },
       { name: "", index: "" },
     ]);
  };

  const removeGroup = (idx: number) => {
     setGroups(groups.filter((_, i) => i !== idx));
  };

  const submitOnboarding = async () => {
    if(!schoolName || groups.length === 0) return;
    setIsSubmitting(true);
    try {
      const res = await authFetch("/api/v1/tenant/onboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          school_name: schoolName,
          groups: groups
        })
      });
      if(res.ok) {
         setActiveTab("assessment");
      } else {
         alert("Failed to onboard school. Please try again.");
         setIsSubmitting(false);
      }
    } catch(e) {
      alert("Network error during onboarding.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex-1 bg-surface-soft/30 text-foreground overflow-y-auto py-12 px-4 flex flex-col items-center justify-center min-h-screen">
      <div className="w-full max-w-4xl bg-surface border border-border-main rounded-none shadow-none overflow-hidden animate-in fade-in zoom-in-95 duration-500 font-outfit">
        <div className="flex flex-col md:flex-row">
          
          <div className="md:w-1/3 bg-brand-900 text-white p-10 flex flex-col justify-between relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-brand-600/20 to-transparent pointer-events-none" />
            <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-brand-500/20 rounded-none blur-3xl pointer-events-none" />
            
            <div className="relative z-10">
               <div className="flex items-center gap-3 mb-12">
                 <div className="w-10 h-10 bg-white/10 rounded-none flex items-center justify-center backdrop-blur-md border border-white/20">
                   <Database className="w-5 h-5 text-brand-300" />
                 </div>
                 <h2 className="text-xl font-bold tracking-tight text-white">Edulytics Setup</h2>
               </div>
               
               <div className="space-y-8">
                 <div className={cn("transition-all duration-300", step === 1 ? "opacity-100" : "opacity-40")}>
                   <div className="text-xs font-bold uppercase tracking-widest text-brand-300 mb-1">Step 1</div>
                   <div className="text-lg font-semibold text-white">School Identity</div>
                 </div>
                 <div className={cn("transition-all duration-300", step === 2 ? "opacity-100" : "opacity-40")}>
                   <div className="text-xs font-bold uppercase tracking-widest text-brand-300 mb-1">Step 2</div>
                   <div className="text-lg font-semibold text-white">Academic Roster</div>
                 </div>
                 <div className={cn("transition-all duration-300", step === 3 ? "opacity-100" : "opacity-40")}>
                   <div className="text-xs font-bold uppercase tracking-widest text-brand-300 mb-1">Step 3</div>
                   <div className="text-lg font-semibold text-white">Final Review</div>
                 </div>
               </div>
            </div>
          </div>
          
          <div className="md:w-2/3 p-10 relative">
            {step === 1 && (
              <div className="animate-in slide-in-from-right-4 duration-500">
                 <h3 className="text-2xl font-black text-foreground mb-2">Welcome to Edulytics</h3>
                 <p className="text-sm text-foreground/60 mb-8">Let's set up your institution's central intelligence hub. Enter your school name to begin.</p>
                 
                 <div className="space-y-6">
                   <div>
                     <label className="text-xs font-bold uppercase tracking-widest text-foreground/60 mb-3 block">Registered School Name</label>
                     <input 
                       type="text" 
                       value={schoolName}
                       onChange={(e) => setSchoolName(e.target.value)}
                       placeholder="e.g. Greenhill Academy"
                       className="w-full bg-surface-soft border border-border-main rounded-none p-4 text-foreground focus:ring-2 focus:ring-brand-500 outline-none transition-all shadow-none text-lg font-medium"
                     />
                   </div>
                 </div>
                 
                 <div className="mt-12 flex justify-end">
                   <button 
                     onClick={() => setStep(2)} 
                     disabled={!schoolName.trim()}
                     className="px-8 py-4 bg-brand-600 text-white text-sm font-bold rounded-none hover:bg-brand-700 disabled:opacity-50 transition-all flex items-center gap-2 group shadow-none cursor-pointer"
                   >
                     Next Step <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                   </button>
                 </div>
              </div>
            )}

            {step === 2 && (
              <div className="animate-in slide-in-from-right-4 duration-500 flex flex-col">
                 <h3 className="text-2xl font-black text-foreground mb-2">Academic Roster</h3>
                 <p className="text-sm text-foreground/60 mb-6">Build your classes, streams, and inject the student index mapping for AI resolution.</p>
                 
                 <div className="bg-surface-soft border border-border-main p-5 rounded-none mb-6 shadow-none">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                         <label className="text-xs font-bold text-foreground/60 mb-2 block">Level / Class</label>
                         <select value={currentLevel} onChange={(e)=>setCurrentLevel(e.target.value)} className="w-full bg-surface border border-border-main p-3 rounded-none text-sm outline-none focus:ring-2 focus:ring-brand-500 cursor-pointer">
                           {levels.map(l => <option key={l} value={l}>{l}</option>)}
                         </select>
                      </div>
                      <div>
                         <label className="text-xs font-bold text-foreground/60 mb-2 block">Stream (e.g. Blue, North)</label>
                         <input type="text" value={currentStream} onChange={(e)=>setCurrentStream(e.target.value)} className="w-full bg-surface border border-border-main p-3 rounded-none text-sm outline-none focus:ring-2 focus:ring-brand-500" placeholder="Stream Name"/>
                      </div>
                    </div>
                    {/* Input Mode Selector */}
                    <div className="flex gap-2 p-1 bg-surface-soft border border-border-main rounded-none mb-3">
                       <button
                         type="button"
                         onClick={() => setImportMode("manual")}
                         className={cn(
                           "flex-1 flex items-center justify-center gap-2 py-2 text-xs font-bold transition-all cursor-pointer rounded-none",
                           importMode === "manual"
                             ? "bg-foreground text-surface"
                             : "text-foreground/60 hover:bg-foreground/5"
                         )}
                       >
                         <Keyboard className="w-3.5 h-3.5" /> Manual Entry Grid
                       </button>
                       <button
                         type="button"
                         onClick={() => setImportMode("csv")}
                         className={cn(
                           "flex-1 flex items-center justify-center gap-2 py-2 text-xs font-bold transition-all cursor-pointer rounded-none",
                           importMode === "csv"
                             ? "bg-foreground text-surface"
                             : "text-foreground/60 hover:bg-foreground/5"
                         )}
                       >
                         <FileSpreadsheet className="w-3.5 h-3.5" /> CSV File Import
                       </button>
                    </div>

                    {importMode === "manual" ? (
                       <div className="space-y-3">
                          <label className="text-xs font-bold text-foreground/60 block">Roster Entry Table</label>
                          <div className="border border-border-main overflow-hidden bg-surface max-h-60 overflow-y-auto custom-scrollbar">
                             <table className="w-full text-left text-xs border-collapse">
                                <thead>
                                   <tr className="border-b border-border-main bg-surface-soft/40 text-foreground/50 font-bold uppercase tracking-wider">
                                      <th className="px-4 py-2.5">No.</th>
                                      <th className="px-4 py-2.5">Full Name</th>
                                      <th className="px-4 py-2.5">Index (Optional)</th>
                                      <th className="px-4 py-2.5 text-center">Delete</th>
                                   </tr>
                                </thead>
                                <tbody className="divide-y divide-border-main/50">
                                   {studentRows.map((row, idx) => (
                                      <tr key={idx} className="hover:bg-surface-soft/10 transition-colors">
                                         <td className="px-4 py-2 font-mono text-foreground/40">{idx + 1}</td>
                                         <td className="px-2 py-1">
                                            <input
                                               type="text"
                                               value={row.name}
                                               onChange={(e) => updateRow(idx, "name", e.target.value)}
                                               placeholder="Student Full Name"
                                               className="w-full bg-transparent border-0 px-2 py-1.5 text-xs text-foreground focus:ring-0 outline-none"
                                            />
                                         </td>
                                         <td className="px-2 py-1">
                                            <input
                                               type="text"
                                               value={row.index}
                                               onChange={(e) => updateRow(idx, "index", e.target.value)}
                                               placeholder="e.g. 001"
                                               className="w-full bg-transparent border-0 px-2 py-1.5 text-xs text-foreground focus:ring-0 outline-none font-mono"
                                            />
                                         </td>
                                         <td className="px-4 py-2 text-center">
                                            <button
                                               type="button"
                                               onClick={() => removeRow(idx)}
                                               className="text-foreground/40 hover:text-red-500 transition-colors p-1 cursor-pointer"
                                            >
                                               <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                         </td>
                                      </tr>
                                   ))}
                                </tbody>
                             </table>
                          </div>
                          <button
                             type="button"
                             onClick={addRow}
                             className="w-full py-2 border border-dashed border-border-main hover:border-foreground/30 hover:bg-surface-soft/20 text-xs font-bold text-foreground/60 hover:text-foreground transition-all cursor-pointer rounded-none flex items-center justify-center gap-1.5"
                          >
                             <Plus className="w-3.5 h-3.5" /> Add New Row
                          </button>
                       </div>
                    ) : (
                       <div className="border border-dashed border-border-main p-6 text-center bg-surface-soft/10 flex flex-col items-center justify-center gap-3">
                          <div className="w-10 h-10 bg-brand-500/10 text-brand-600 rounded-none flex items-center justify-center">
                             <Upload className="w-5 h-5" />
                          </div>
                          <div>
                             <h4 className="text-xs font-bold text-foreground mb-1">Select CSV File</h4>
                             <p className="text-[10px] text-foreground/50 max-w-[280px] mx-auto leading-relaxed">
                                Upload a `.csv` where each line is formatted as `Student Name, Index Number` (e.g. `John Doe, 001`).
                             </p>
                          </div>
                          <label className="px-4 py-2 bg-foreground text-surface hover:bg-foreground/90 transition-all text-xs font-bold cursor-pointer rounded-none">
                             Browse Files
                             <input
                                type="file"
                                accept=".csv"
                                onChange={handleCsvUpload}
                                className="hidden"
                             />
                          </label>
                       </div>
                    )}

                    <button 
                       onClick={handleAddGroup} 
                       disabled={!currentStream || studentRows.filter(r => r.name.trim()).length === 0} 
                       className="w-full mt-4 py-3 bg-foreground text-surface text-sm font-bold rounded-none flex items-center justify-center gap-2 disabled:opacity-50 transition-all hover:bg-foreground/90 cursor-pointer"
                    >
                       <Plus className="w-4 h-4" /> Add Academic Group
                    </button>
                 </div>

                 <div className="max-h-40 overflow-y-auto custom-scrollbar space-y-3">
                   {groups.length === 0 ? (
                     <div className="text-center text-xs text-foreground/40 py-4 font-bold uppercase tracking-widest border border-dashed border-border-main rounded-none">No Groups Added</div>
                   ) : groups.map((g, idx) => (
                     <div key={idx} className="bg-surface border border-border-main p-4 rounded-none flex items-center justify-between group-item transition-all hover:border-brand-300">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-brand-500/10 text-brand-600 rounded-none flex items-center justify-center font-black text-sm">
                            {g.level}
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-foreground">{g.stream} Stream</h4>
                            <p className="text-xs text-foreground/60">{g.students.length} Student(s) Enrolled</p>
                          </div>
                        </div>
                        <button onClick={()=>removeGroup(idx)} className="text-red-500/50 hover:text-red-500 transition-colors p-2 cursor-pointer"><X className="w-4 h-4"/></button>
                     </div>
                   ))}
                 </div>
                 
                 <div className="mt-6 flex justify-between items-center pt-4 border-t border-border-main">
                   <button onClick={() => setStep(1)} className="px-6 py-3 text-foreground/60 text-sm font-bold hover:text-foreground transition-colors cursor-pointer">Back</button>
                   <button 
                     onClick={() => setStep(3)} 
                     disabled={groups.length === 0}
                     className="px-8 py-3 bg-brand-600 text-white text-sm font-bold rounded-none hover:bg-brand-700 disabled:opacity-50 transition-all shadow-none cursor-pointer"
                   >
                     Review Settings
                   </button>
                 </div>
              </div>
            )}

            {step === 3 && (
              <div className="animate-in slide-in-from-right-4 duration-500">
                 <div className="flex items-center justify-center mb-6">
                   <div className="w-16 h-16 bg-emerald-500/10 rounded-none flex items-center justify-center text-emerald-500">
                     <CheckCircle2 className="w-8 h-8" />
                   </div>
                 </div>
                 <h3 className="text-2xl font-black text-foreground mb-2 text-center">Ready for Provisioning</h3>
                 <p className="text-sm text-foreground/60 mb-8 text-center max-w-sm mx-auto">Please confirm the multi-tenant architecture details below before initializing the database.</p>
                 
                 <div className="bg-surface-soft border border-border-main rounded-none p-6 mb-8 shadow-none font-outfit">
                   <div className="flex justify-between items-center mb-4 pb-4 border-b border-border-main/50">
                     <span className="text-xs font-bold text-foreground/60 uppercase tracking-widest">Institution</span>
                     <span className="text-sm font-black text-foreground">{schoolName}</span>
                   </div>
                   <div className="flex justify-between items-center mb-4 pb-4 border-b border-border-main/50">
                     <span className="text-xs font-bold text-foreground/60 uppercase tracking-widest">Total Classes</span>
                     <span className="text-sm font-black text-foreground">{new Set(groups.map(g => g.level)).size} Levels</span>
                   </div>
                   <div className="flex justify-between items-center mb-4 pb-4 border-b border-border-main/50">
                     <span className="text-xs font-bold text-foreground/60 uppercase tracking-widest">Total Streams</span>
                     <span className="text-sm font-black text-foreground">{groups.length} Streams</span>
                   </div>
                   <div className="flex justify-between items-center">
                     <span className="text-xs font-bold text-foreground/60 uppercase tracking-widest">Total Students</span>
                     <span className="text-sm font-black text-foreground">{groups.reduce((acc, g) => acc + g.students.length, 0)} Profiles</span>
                   </div>
                 </div>
                 
                 <div className="flex justify-between items-center">
                   <button onClick={() => setStep(2)} className="px-6 py-4 text-foreground/60 text-sm font-bold hover:text-foreground transition-colors cursor-pointer">Edit Details</button>
                   <button 
                     onClick={submitOnboarding}
                     disabled={isSubmitting}
                     className="px-8 py-4 bg-emerald-600 text-white text-sm font-bold rounded-none hover:bg-emerald-700 disabled:opacity-50 transition-all flex items-center gap-2 shadow-none cursor-pointer"
                   >
                     {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Database className="w-5 h-5" />}
                     {isSubmitting ? "Provisioning..." : "Provision Engine Database"}
                   </button>
                 </div>
              </div>
            )}
          </div>
          
        </div>
      </div>
    </div>
  );
}
