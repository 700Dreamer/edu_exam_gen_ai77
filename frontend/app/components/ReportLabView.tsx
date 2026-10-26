"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  FileText, Printer, Download, Share2, Layers, Search, CheckCircle2,
  ChevronDown, ArrowUpRight, BarChart2, TrendingUp, Sparkles, Clock,
  RefreshCw, Check, X, ArrowLeft, Eye, Award, BookOpen, Users,
  ExternalLink, SlidersHorizontal, UserCheck, HelpCircle
} from "lucide-react";
import { cn, authFetch } from "../lib/utils";

export type ReportScope = "student_exam" | "student_history" | "class_exam" | "class_all_subjects";
export type ReportTemplate = "standard" | "report_card" | "detailed_analysis";

interface ReportSectionToggles {
  header: boolean;
  kpiStrip: boolean;
  visualCharts: boolean;
  questionBreakdown: boolean;
  aiRemarks: boolean;
  gradeMatrix: boolean;
  signatures: boolean;
}

export default function ReportLabView({
  theme
}: {
  theme?: string;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Navigation query params
  const paramScope = searchParams.get("scope") as ReportScope | null;
  const paramResultId = searchParams.get("result") || searchParams.get("result_id");
  const paramStudentId = searchParams.get("student") || searchParams.get("student_id");
  const paramBatchId = searchParams.get("run") || searchParams.get("batch") || searchParams.get("batch_id");
  const paramGroupId = searchParams.get("group") || searchParams.get("group_id");

  // State
  const [scope, setScope] = useState<ReportScope>(paramScope || "student_exam");
  const [template, setTemplate] = useState<ReportTemplate>("standard");
  const [metadata, setMetadata] = useState<{ groups: any[]; batches: any[]; subjects: string[] }>({
    groups: [],
    batches: [],
    subjects: []
  });

  const [selectedBatchId, setSelectedBatchId] = useState<string>(paramBatchId || "");
  const [selectedGroupId, setSelectedGroupId] = useState<string>(paramGroupId || "");
  const [selectedStudentId, setSelectedStudentId] = useState<string>(paramStudentId || "");
  const [selectedResultId, setSelectedResultId] = useState<string>(paramResultId || "");

  const [reportData, setReportData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchFilter, setSearchFilter] = useState<string>("");

  // Accordion expansion states
  const [isSectionsOpen, setIsSectionsOpen] = useState(true);
  const [isTemplateOpen, setIsTemplateOpen] = useState(true);
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);

  // Section visibility toggles
  const [sections, setSections] = useState<ReportSectionToggles>({
    header: true,
    kpiStrip: true,
    visualCharts: true,
    questionBreakdown: true,
    aiRemarks: true,
    gradeMatrix: true,
    signatures: true
  });

  // Report canvas reference for printing
  const reportCanvasRef = useRef<HTMLDivElement>(null);

  // Load metadata on mount
  useEffect(() => {
    const fetchMeta = async () => {
      try {
        const res = await authFetch("/api/v1/reports/meta");
        if (res.ok) {
          const data = await res.json();
          setMetadata({
            groups: Array.isArray(data.groups) ? data.groups : [],
            batches: Array.isArray(data.batches) ? data.batches : [],
            subjects: Array.isArray(data.subjects) ? data.subjects : []
          });

          // Set sensible defaults if none provided in params
          if (!selectedBatchId && data.batches?.length > 0) {
            setSelectedBatchId(data.batches[0].id);
          }
          if (!selectedGroupId && data.groups?.length > 0) {
            setSelectedGroupId(data.groups[0].id);
          }
        }
      } catch (e) {
        console.error("Failed to load Report Lab metadata:", e);
      }
    };
    fetchMeta();
  }, []);

  // Sync state if query params change
  useEffect(() => {
    if (paramScope && paramScope !== scope) setScope(paramScope);
    if (paramResultId && paramResultId !== selectedResultId) setSelectedResultId(paramResultId);
    if (paramStudentId && paramStudentId !== selectedStudentId) setSelectedStudentId(paramStudentId);
    if (paramBatchId && paramBatchId !== selectedBatchId) setSelectedBatchId(paramBatchId);
    if (paramGroupId && paramGroupId !== selectedGroupId) setSelectedGroupId(paramGroupId);
  }, [paramScope, paramResultId, paramStudentId, paramBatchId, paramGroupId]);

  // Fetch report data on scope or selector changes
  useEffect(() => {
    let isMounted = true;
    const fetchReport = async () => {
      setIsLoading(true);
      try {
        const params = new URLSearchParams();
        params.append("scope", scope);
        if (selectedResultId) params.append("result_id", selectedResultId);
        if (selectedStudentId) params.append("student_id", selectedStudentId);
        if (selectedBatchId) params.append("batch_id", selectedBatchId);
        if (selectedGroupId) params.append("academic_group_id", selectedGroupId);

        const res = await authFetch(`/api/v1/reports/query?${params.toString()}`);
        if (res.ok && isMounted) {
          const data = await res.json();
          setReportData(data);
        }
      } catch (err) {
        console.error("Failed to load report data:", err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchReport();
    return () => {
      isMounted = false;
    };
  }, [scope, selectedResultId, selectedStudentId, selectedBatchId, selectedGroupId]);

  // Trigger WYSIWYG Print / PDF
  const handlePrint = () => {
    window.print();
  };

  // Switch to results view for this batch
  const handleOpenInResults = () => {
    const targetBatchId = reportData?.exam?.batch_id || selectedBatchId;
    if (targetBatchId) {
      router.push(`/?view=gradebook&run=${targetBatchId}`);
    } else {
      router.push("/?view=gradebook");
    }
  };

  // Color coding helper for grades and marks (no heavy borders or bgs per Grade View design)
  const getScoreColor = (score: number | null | undefined) => {
    if (score === null || score === undefined) return "text-foreground/40";
    if (score >= 80) return "text-emerald-700 dark:text-emerald-400 font-bold";
    if (score >= 70) return "text-brand-700 dark:text-brand-400 font-bold";
    if (score >= 60) return "text-amber-700 dark:text-amber-400 font-semibold";
    if (score >= 50) return "text-yellow-700 dark:text-yellow-400 font-medium";
    return "text-red-600 dark:text-red-400 font-semibold";
  };

  const activeSectionsCount = Object.values(sections).filter(Boolean).length;

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden font-outfit text-foreground p-3 sm:p-4 gap-3">
      {/* ───────────────────────────────────────────────────────────── */}
      {/* PRINT STYLESHEET (WYSIWYG: hides sidebars during print/PDF)   */}
      {/* ───────────────────────────────────────────────────────────── */}
      <style jsx global>{`
        @media print {
          body, html {
            background: #ffffff !important;
            color: #000000 !important;
            margin: 0 !important;
            padding: 0 !important;
          }
          header, nav, .print-hide, .no-print {
            display: none !important;
          }
          .print-full-width {
            width: 100% !important;
            max-width: 100% !important;
            box-shadow: none !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
          }
          .print-page-break {
            page-break-before: always;
          }
        }
      `}</style>

      {/* 3-Pane Studio Workspace Grid */}
      <div className="grid grid-cols-12 gap-3 flex-1 min-h-0 overflow-hidden">
        
        {/* ─────────────────────────────────────────────────────────── */}
        {/* PANE 1: Left Query & Scope Navigator                        */}
        {/* ─────────────────────────────────────────────────────────── */}
        <div className="col-span-12 lg:col-span-3 bg-surface border border-border-main rounded-[10px] shadow-none flex flex-col h-full overflow-hidden print-hide">
          {/* Header */}
          <div className="p-3 border-b border-border-main/60 flex items-center justify-between shrink-0 bg-surface">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-surface-soft rounded-[5px] border border-border-main/50">
                <FileText className="w-4 h-4 text-foreground/70" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">
                  Report Lab
                </h3>
                <p className="text-[10px] text-foreground/50">
                  Analytics, Visuals &amp; Transcripts
                </p>
              </div>
            </div>
            <span className="text-[9px] font-bold uppercase tracking-wider bg-brand-500/10 text-brand-700 border border-brand-500/20 px-2 py-0.5 rounded-[4px]">
              Read-Only
            </span>
          </div>

          {/* Segmented Scope Bar (Templates | Layers design from Grade View) */}
          <div className="p-3 pb-2.5 border-b border-border-main/60 shrink-0 bg-surface">
            <label className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block mb-1.5">
              Report Scope
            </label>
            <div className="grid grid-cols-2 gap-1 p-1 bg-surface-soft rounded-[8px]">
              <button
                type="button"
                onClick={() => setScope("student_exam")}
                className={cn(
                  "py-1.5 px-2 text-xs rounded-[4px] transition-all text-center cursor-pointer truncate",
                  scope === "student_exam"
                    ? "bg-white dark:bg-neutral-900 text-foreground font-semibold shadow-xs border border-border-main/50"
                    : "text-foreground/60 hover:text-foreground font-medium bg-transparent"
                )}
              >
                Student Exam
              </button>
              <button
                type="button"
                onClick={() => setScope("student_history")}
                className={cn(
                  "py-1.5 px-2 text-xs rounded-[4px] transition-all text-center cursor-pointer truncate",
                  scope === "student_history"
                    ? "bg-white dark:bg-neutral-900 text-foreground font-semibold shadow-xs border border-border-main/50"
                    : "text-foreground/60 hover:text-foreground font-medium bg-transparent"
                )}
              >
                History
              </button>
              <button
                type="button"
                onClick={() => setScope("class_exam")}
                className={cn(
                  "py-1.5 px-2 text-xs rounded-[4px] transition-all text-center cursor-pointer truncate",
                  scope === "class_exam"
                    ? "bg-white dark:bg-neutral-900 text-foreground font-semibold shadow-xs border border-border-main/50"
                    : "text-foreground/60 hover:text-foreground font-medium bg-transparent"
                )}
              >
                Class Exam
              </button>
              <button
                type="button"
                onClick={() => setScope("class_all_subjects")}
                className={cn(
                  "py-1.5 px-2 text-xs rounded-[4px] transition-all text-center cursor-pointer truncate",
                  scope === "class_all_subjects"
                    ? "bg-white dark:bg-neutral-900 text-foreground font-semibold shadow-xs border border-border-main/50"
                    : "text-foreground/60 hover:text-foreground font-medium bg-transparent"
                )}
              >
                All Subjects
              </button>
            </div>
          </div>

          {/* Filter / Pickers Form */}
          <div className="p-3 border-b border-border-main/60 space-y-2.5 shrink-0 bg-surface">
            {/* Class / Academic Group Selector */}
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block mb-1">
                Class / Stream
              </label>
              <div className="relative">
                <select
                  value={selectedGroupId}
                  onChange={(e) => setSelectedGroupId(e.target.value)}
                  className="w-full appearance-none bg-surface-soft border border-border-main rounded-[6px] px-2.5 py-1.5 pr-7 text-xs font-medium text-foreground focus:outline-none cursor-pointer"
                >
                  {metadata.groups.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.level} {g.stream} ({g.tenant_name})
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-foreground/40 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            {/* Exam / Run Selector (for exam-focused scopes) */}
            {(scope === "student_exam" || scope === "class_exam") && (
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block mb-1">
                  Examination Run
                </label>
                <div className="relative">
                  <select
                    value={selectedBatchId}
                    onChange={(e) => {
                      setSelectedBatchId(e.target.value);
                      setSelectedResultId(""); // reset focused result
                    }}
                    className="w-full appearance-none bg-surface-soft border border-border-main rounded-[6px] px-2.5 py-1.5 pr-7 text-xs font-medium text-foreground focus:outline-none cursor-pointer"
                  >
                    {metadata.batches.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.subject} - {b.exam_type} ({b.level} {b.stream})
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-foreground/40 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>
            )}
          </div>

          {/* Query Results / Student Roster in Left Pane */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2">
            <div className="flex items-center justify-between pb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50">
                {scope === "student_exam" || scope === "student_history" ? "Select Student" : "Class Examinations"}
              </span>
              <span className="text-[10px] text-foreground/40 font-mono">
                {metadata.batches.length} items
              </span>
            </div>

            {/* Search filter for roster */}
            <div className="relative mb-2">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-foreground/40 pointer-events-none" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Filter by name..."
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-surface-soft border border-border-main/50 text-foreground placeholder:text-foreground/40 rounded-[6px] focus:outline-none focus:border-border-main"
              />
              {searchFilter && (
                <button
                  type="button"
                  onClick={() => setSearchFilter("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-foreground/40 hover:text-foreground"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* List items (matching Grade View link button style) */}
            <div className="space-y-1.5">
              {metadata.batches.slice(0, 10).map((batch) => (
                <button
                  key={batch.id}
                  type="button"
                  onClick={() => {
                    setSelectedBatchId(batch.id);
                    if (batch.academic_group_id) setSelectedGroupId(batch.academic_group_id);
                  }}
                  className={cn(
                    "w-full group px-3 py-2 text-left rounded-[6px] transition-all flex items-center justify-between cursor-pointer border",
                    selectedBatchId === batch.id
                      ? "bg-surface-soft border-border-main text-foreground font-semibold"
                      : "bg-surface-soft/40 hover:bg-surface-soft border-border-main/50 text-foreground/80 hover:text-foreground"
                  )}
                >
                  <div className="min-w-0 pr-2">
                    <span className="text-xs font-semibold block truncate">
                      {batch.subject} - {batch.exam_type}
                    </span>
                    <span className="text-[10px] text-foreground/50 font-mono block">
                      {batch.level} {batch.stream} · {batch.date_formatted}
                    </span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-foreground/40 group-hover:text-foreground shrink-0 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ─────────────────────────────────────────────────────────── */}
        {/* PANE 2: Center Live WYSIWYG Report Canvas                   */}
        {/* ─────────────────────────────────────────────────────────── */}
        <div className="col-span-12 lg:col-span-6 bg-surface border border-border-main rounded-[10px] shadow-none flex flex-col h-full overflow-hidden print-full-width">
          {/* Canvas Toolbar (Controls & Quick Print) */}
          <div className="p-3 border-b border-border-main/60 flex items-center justify-between shrink-0 bg-surface print-hide">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-foreground/70">
                WYSIWYG Canvas
              </span>
              <span className="text-foreground/40">·</span>
              <span className="text-xs text-foreground/50 capitalize">
                {scope.replace("_", " ")} ({template.replace("_", " ")})
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handlePrint}
                className="px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-[6px] transition-all flex items-center gap-1.5 cursor-pointer shadow-xs"
                title="Download / Print WYSIWYG PDF"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Export PDF</span>
              </button>
            </div>
          </div>

          {/* Scrollable Printable Canvas Body */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-4 sm:p-6 bg-surface-soft/20">
            {isLoading ? (
              <div className="h-96 flex flex-col items-center justify-center gap-3 text-foreground/50">
                <RefreshCw className="w-6 h-6 animate-spin text-foreground/40" />
                <span className="text-xs font-medium">Generating Report Canvas...</span>
              </div>
            ) : !reportData || reportData.error ? (
              <div className="h-96 flex flex-col items-center justify-center gap-2 text-foreground/50 text-center p-6 border border-dashed border-border-main rounded-[8px]">
                <HelpCircle className="w-8 h-8 text-foreground/30" />
                <h4 className="text-sm font-bold text-foreground">No Report Available</h4>
                <p className="text-xs text-foreground/50 max-w-sm">
                  {reportData?.error || "Select an examination batch or student from the left panel to generate a report."}
                </p>
              </div>
            ) : (
              <div
                ref={reportCanvasRef}
                className="max-w-2xl mx-auto bg-surface border border-border-main rounded-[8px] p-6 sm:p-8 space-y-6 shadow-xs print-full-width font-outfit"
              >
                {/* 1. Header Section */}
                {sections.header && (
                  <div className="border-b border-border-main/70 pb-5 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 bg-brand-500/10 border border-brand-500/20 rounded-[5px]">
                          <BookOpen className="w-5 h-5 text-brand-600" />
                        </div>
                        <div>
                          <h1 className="text-base font-black tracking-wide text-foreground uppercase">
                            {reportData.school?.name || "Edulytics Academy"}
                          </h1>
                          <p className="text-[10px] font-bold text-foreground/50 uppercase tracking-widest">
                            Academic Assessment Report &amp; Transcript
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] font-mono text-foreground/50 block">
                          Generated: {new Date().toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
                        </span>
                        <span className="text-[9px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-[4px] inline-block mt-1">
                          Official Record
                        </span>
                      </div>
                    </div>

                    {/* Metadata Context Bar */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 border-t border-border-main/40 text-xs text-foreground/70">
                      <div>
                        <span className="text-[10px] uppercase text-foreground/40 block font-bold">Class</span>
                        <strong className="text-foreground">{reportData.class_info?.name || "P.7 General"}</strong>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase text-foreground/40 block font-bold">Scope</span>
                        <strong className="text-foreground capitalize">{scope.replace("_", " ")}</strong>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase text-foreground/40 block font-bold">Subject</span>
                        <strong className="text-foreground">{reportData.exam?.subject || "All Subjects"}</strong>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase text-foreground/40 block font-bold">Exam Date</span>
                        <span className="font-mono text-foreground">{reportData.exam?.date_formatted || "Term 2"}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. KPI / Summary Strip */}
                {sections.kpiStrip && (
                  <div>
                    {scope === "student_exam" && reportData.performance && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-surface-soft/40 border border-border-main/70 rounded-[6px]">
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Total Score
                          </span>
                          <span className={cn("text-2xl font-black block", getScoreColor(reportData.performance.score))}>
                            {reportData.performance.score !== null ? `${reportData.performance.score}%` : "—"}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Letter Grade
                          </span>
                          <span className="text-2xl font-black text-foreground block">
                            Grade {reportData.performance.grade}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Class Rank
                          </span>
                          <span className="text-2xl font-black text-foreground block">
                            #{reportData.performance.rank} <span className="text-xs font-normal text-foreground/50">of {reportData.performance.class_total}</span>
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Class Average
                          </span>
                          <span className="text-2xl font-black text-foreground/70 block">
                            {reportData.performance.class_average}%
                          </span>
                        </div>
                      </div>
                    )}

                    {scope === "class_exam" && reportData.metrics && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-surface-soft/40 border border-border-main/70 rounded-[6px]">
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Class Average
                          </span>
                          <span className="text-2xl font-black text-emerald-700 dark:text-emerald-400 block">
                            {reportData.metrics.class_average}%
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Highest Score
                          </span>
                          <span className="text-2xl font-black text-foreground block">
                            {reportData.metrics.highest_score}%
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Pass Rate
                          </span>
                          <span className="text-2xl font-black text-brand-700 dark:text-brand-400 block">
                            {reportData.metrics.pass_rate}%
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Candidates
                          </span>
                          <span className="text-2xl font-black text-foreground/70 block">
                            {reportData.metrics.total_students}
                          </span>
                        </div>
                      </div>
                    )}

                    {scope === "student_history" && reportData.metrics && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-surface-soft/40 border border-border-main/70 rounded-[6px]">
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Cumulative Avg
                          </span>
                          <span className="text-2xl font-black text-brand-700 dark:text-brand-400 block">
                            {reportData.metrics.cumulative_average}%
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Exams Recorded
                          </span>
                          <span className="text-2xl font-black text-foreground block">
                            {reportData.metrics.total_exams}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Best Performance
                          </span>
                          <span className="text-2xl font-black text-emerald-700 dark:text-emerald-400 block">
                            {reportData.metrics.highest_score}%
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/50 block">
                            Progression Delta
                          </span>
                          <span className={cn(
                            "text-2xl font-black block",
                            reportData.metrics.trend_delta >= 0 ? "text-emerald-700" : "text-red-600"
                          )}>
                            {reportData.metrics.trend_delta >= 0 ? `+${reportData.metrics.trend_delta}%` : `${reportData.metrics.trend_delta}%`}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 3. Visual Charts Section */}
                {sections.visualCharts && (
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-foreground/70 border-b border-border-main/50 pb-1.5 flex items-center justify-between">
                      <span>Analytical Visualization</span>
                      <span className="text-[10px] text-foreground/40 font-mono">Comparative Metrics</span>
                    </h4>

                    {/* Student Exam: Score vs Class Benchmark */}
                    {scope === "student_exam" && reportData.performance && (
                      <div className="space-y-3 p-4 bg-surface-soft/30 border border-border-main/60 rounded-[6px]">
                        <div className="space-y-1.5">
                          <div className="flex justify-between text-xs">
                            <span className="font-medium text-foreground">Student Score: {reportData.student?.name}</span>
                            <span className="font-black text-foreground">{reportData.performance.score}%</span>
                          </div>
                          <div className="h-3 w-full bg-surface-soft rounded-full overflow-hidden border border-border-main/50">
                            <div
                              className="h-full bg-brand-600 rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(100, Math.max(0, reportData.performance.score || 0))}%` }}
                            />
                          </div>
                        </div>

                        <div className="space-y-1.5">
                          <div className="flex justify-between text-xs text-foreground/70">
                            <span>Class Average Benchmark</span>
                            <span className="font-semibold text-foreground/70">{reportData.performance.class_average}%</span>
                          </div>
                          <div className="h-2 w-full bg-surface-soft rounded-full overflow-hidden border border-border-main/40">
                            <div
                              className="h-full bg-emerald-600 rounded-full opacity-80"
                              style={{ width: `${Math.min(100, Math.max(0, reportData.performance.class_average || 0))}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Class Exam: Score Distribution Histogram */}
                    {scope === "class_exam" && reportData.distribution_buckets && (
                      <div className="p-4 bg-surface-soft/30 border border-border-main/60 rounded-[6px] space-y-3">
                        <span className="text-[11px] font-semibold text-foreground/60 block">
                          Score Range Distribution (Frequency of Marks)
                        </span>
                        <div className="flex items-end gap-2 h-28 pt-2">
                          {Object.entries(reportData.distribution_buckets as Record<string, number>).map(([range, count]) => {
                            const maxCount = Math.max(...Object.values(reportData.distribution_buckets as Record<string, number>), 1);
                            const heightPct = Math.round((count / maxCount) * 100);
                            return (
                              <div key={range} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                                <span className="text-[10px] font-bold text-foreground/70">{count}</span>
                                <div
                                  className="w-full bg-brand-600/80 hover:bg-brand-600 rounded-t-[3px] transition-all"
                                  style={{ height: `${Math.max(8, heightPct)}%` }}
                                  title={`${range}% range: ${count} student(s)`}
                                />
                                <span className="text-[9px] font-mono text-foreground/50">{range}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Student History: Historical Trend Visualizer */}
                    {scope === "student_history" && reportData.timeline && (
                      <div className="p-4 bg-surface-soft/30 border border-border-main/60 rounded-[6px] space-y-3">
                        <span className="text-[11px] font-semibold text-foreground/60 block">
                          Longitudinal Exam Score Progression
                        </span>
                        <div className="flex items-end gap-2 h-28 pt-2">
                          {reportData.timeline.map((item: any, idx: number) => {
                            const scoreVal = item.score !== null ? item.score : 0;
                            return (
                              <div key={item.result_id || idx} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                                <span className="text-[10px] font-bold text-foreground/70">{item.score !== null ? `${item.score}%` : "—"}</span>
                                <div
                                  className="w-full bg-emerald-600/80 hover:bg-emerald-600 rounded-t-[3px] transition-all"
                                  style={{ height: `${Math.max(8, scoreVal)}%` }}
                                  title={`${item.exam_name}: ${item.score}%`}
                                />
                                <span className="text-[9px] font-mono text-foreground/50 truncate max-w-[50px]">{item.subject.slice(0, 4)}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 4. Question-Level Breakdown (for Student Exam scope) */}
                {sections.questionBreakdown && scope === "student_exam" && reportData.questions?.length > 0 && (
                  <div className="space-y-2.5">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-foreground/70 border-b border-border-main/50 pb-1.5">
                      Question-Level Assessment Breakdown
                    </h4>
                    <div className="border border-border-main/60 rounded-[6px] overflow-hidden">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-surface-soft text-[10px] font-bold uppercase tracking-wider text-foreground/50 border-b border-border-main">
                          <tr>
                            <th className="px-3 py-2">Item</th>
                            <th className="px-3 py-2 text-right">Awarded</th>
                            <th className="px-3 py-2 text-right">Max</th>
                            <th className="px-3 py-2">Evaluation Remarks</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border-main/40">
                          {reportData.questions.map((q: any, idx: number) => (
                            <tr key={idx} className="hover:bg-surface-soft/40">
                              <td className="px-3 py-2 font-bold text-foreground">
                                {q.question_number}
                              </td>
                              <td className="px-3 py-2 text-right">
                                <span className={getScoreColor(Math.round((q.score_awarded / (q.max_score || 1)) * 100))}>
                                  {q.score_awarded}
                                </span>
                              </td>
                              <td className="px-3 py-2 text-right text-foreground/50 font-mono">
                                {q.max_score}
                              </td>
                              <td className="px-3 py-2 text-foreground/70 text-[11px]">
                                {q.feedback || "Correct response with clear methodology."}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 5. Class Roster Breakdown (for Class Exam scope) */}
                {sections.questionBreakdown && scope === "class_exam" && reportData.roster?.length > 0 && (
                  <div className="space-y-2.5">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-foreground/70 border-b border-border-main/50 pb-1.5 flex justify-between">
                      <span>Candidate Performance Roster</span>
                      <span className="text-[10px] text-foreground/40 font-mono">{reportData.roster.length} Candidates</span>
                    </h4>
                    <div className="border border-border-main/60 rounded-[6px] overflow-hidden max-h-72 overflow-y-auto custom-scrollbar">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-surface-soft text-[10px] font-bold uppercase tracking-wider text-foreground/50 border-b border-border-main sticky top-0">
                          <tr>
                            <th className="px-3 py-2">Rank</th>
                            <th className="px-3 py-2">Student Name</th>
                            <th className="px-3 py-2">Index No</th>
                            <th className="px-3 py-2 text-right">Total Score</th>
                            <th className="px-3 py-2 text-center">Grade</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border-main/40">
                          {reportData.roster.map((r: any) => (
                            <tr key={r.result_id} className="hover:bg-surface-soft/40">
                              <td className="px-3 py-2 font-mono text-foreground/60">
                                #{r.rank}
                              </td>
                              <td className="px-3 py-2 font-semibold text-foreground">
                                {r.student_name}
                              </td>
                              <td className="px-3 py-2 font-mono text-[11px] text-foreground/50">
                                {r.index_number}
                              </td>
                              <td className="px-3 py-2 text-right">
                                <span className={getScoreColor(r.score)}>
                                  {r.score !== null ? `${r.score}%` : "—"}
                                </span>
                              </td>
                              <td className="px-3 py-2 text-center font-bold text-foreground">
                                {r.grade}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 6. Multi-Subject Grade Sheet Matrix (for Class All Subjects scope) */}
                {sections.gradeMatrix && scope === "class_all_subjects" && reportData.matrix?.length > 0 && (
                  <div className="space-y-2.5">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-foreground/70 border-b border-border-main/50 pb-1.5 flex justify-between">
                      <span>Multi-Subject Term Grade Sheet Matrix</span>
                      <span className="text-[10px] text-foreground/40 font-mono">{reportData.subjects?.length} Subjects</span>
                    </h4>
                    <div className="border border-border-main/60 rounded-[6px] overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-surface-soft text-[10px] font-bold uppercase tracking-wider text-foreground/50 border-b border-border-main">
                          <tr>
                            <th className="px-3 py-2">Rank</th>
                            <th className="px-3 py-2">Student</th>
                            {reportData.subjects?.map((subj: string) => (
                              <th key={subj} className="px-2 py-2 text-right truncate max-w-[80px]">
                                {subj}
                              </th>
                            ))}
                            <th className="px-3 py-2 text-right">Average</th>
                            <th className="px-2 py-2 text-center">Grade</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border-main/40">
                          {reportData.matrix.map((row: any) => (
                            <tr key={row.student_id} className="hover:bg-surface-soft/40">
                              <td className="px-3 py-2 font-mono text-foreground/60">
                                #{row.rank}
                              </td>
                              <td className="px-3 py-2 font-semibold text-foreground truncate max-w-[120px]">
                                {row.student_name}
                              </td>
                              {reportData.subjects?.map((subj: string) => {
                                const sc = row.subject_scores?.[subj];
                                return (
                                  <td key={subj} className="px-2 py-2 text-right">
                                    <span className={getScoreColor(sc)}>
                                      {sc !== null && sc !== undefined ? `${sc}%` : "—"}
                                    </span>
                                  </td>
                                );
                              })}
                              <td className="px-3 py-2 text-right font-black text-foreground">
                                {row.average_score !== null ? `${row.average_score}%` : "—"}
                              </td>
                              <td className="px-2 py-2 text-center font-bold text-foreground">
                                {row.grade}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 7. Qualitative AI Insights & Pedagogical Remarks */}
                {sections.aiRemarks && (reportData.ai_remarks || reportData.batch_insights) && (
                  <div className="p-4 bg-surface-soft/40 border border-border-main/70 rounded-[6px] space-y-2">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-3.5 h-3.5 text-foreground/70" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
                        Qualitative Evaluation Remarks
                      </h4>
                    </div>
                    <p className="text-xs text-foreground/80 leading-relaxed italic border-l-2 border-border-main pl-3 py-0.5">
                      "{reportData.ai_remarks || reportData.batch_insights}"
                    </p>
                  </div>
                )}

                {/* 8. Signature & Verification Section */}
                {sections.signatures && (
                  <div className="pt-8 border-t border-border-main/60 grid grid-cols-2 gap-8 text-xs text-foreground/60">
                    <div className="space-y-6">
                      <div className="h-6 border-b border-border-main/60 w-44" />
                      <div>
                        <span className="font-bold text-foreground block">Subject Teacher / Evaluator</span>
                        <span className="text-[10px] text-foreground/50">Edulytics Automated Evaluation</span>
                      </div>
                    </div>
                    <div className="space-y-6 text-right">
                      <div className="h-6 border-b border-border-main/60 w-44 ml-auto" />
                      <div>
                        <span className="font-bold text-foreground block">Head of Department / Academic Dean</span>
                        <span className="text-[10px] text-foreground/50">Official Institutional Signature</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ─────────────────────────────────────────────────────────── */}
        {/* PANE 3: Right Report Controls, Toggles & Presets            */}
        {/* ─────────────────────────────────────────────────────────── */}
        <div className="col-span-12 lg:col-span-3 bg-surface border border-border-main rounded-[10px] shadow-none flex flex-col h-full overflow-hidden print-hide">
          {/* Action Header */}
          <div className="p-3 border-b border-border-main/60 shrink-0 bg-surface">
            <div className="p-1 bg-surface-soft rounded-[8px] flex items-center gap-1.5">
              <button
                type="button"
                onClick={handlePrint}
                className="flex-1 py-1.5 px-2 bg-surface hover:bg-surface-soft border border-border-main/80 text-foreground text-xs font-semibold rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-none"
                title="Print or Save as PDF"
              >
                <Printer className="w-3.5 h-3.5 text-foreground/70 shrink-0" />
                <span className="truncate">Print / PDF</span>
              </button>

              <button
                type="button"
                onClick={handleOpenInResults}
                className="flex-1 py-1.5 px-2 bg-surface hover:bg-surface-soft border border-border-main/80 text-foreground text-xs font-semibold rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-none"
                title="Edit or review scores in Results Gradebook"
              >
                <ExternalLink className="w-3.5 h-3.5 text-foreground/70 shrink-0" />
                <span className="truncate">In Results</span>
              </button>
            </div>
          </div>

          {/* Scrollable Accordions Panel */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
            {/* Accordion 1: SECTIONS TOGGLE */}
            <div>
              <button
                type="button"
                onClick={() => setIsSectionsOpen(prev => !prev)}
                className="w-full flex items-center justify-between text-left py-1 group cursor-pointer"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-foreground/70 group-hover:text-foreground transition-colors">
                    Report Sections
                  </span>
                  <span className="text-foreground/40 font-bold">·</span>
                  <span className="text-[11px] font-bold text-foreground/60 group-hover:text-foreground transition-colors">
                    {activeSectionsCount}
                  </span>
                </div>
                <ChevronDown
                  className={cn(
                    "w-3.5 h-3.5 text-foreground/40 group-hover:text-foreground transition-transform duration-200",
                    isSectionsOpen && "rotate-180"
                  )}
                />
              </button>

              {isSectionsOpen && (
                <div className="pt-2.5 space-y-2 animate-in fade-in duration-200 text-xs">
                  {[
                    { key: "header", label: "School Header & Emblems" },
                    { key: "kpiStrip", label: "KPI Performance Summary" },
                    { key: "visualCharts", label: "Analytical Visual Charts" },
                    { key: "questionBreakdown", label: "Question & Candidate Breakdown" },
                    { key: "gradeMatrix", label: "Multi-Subject Grade Sheet" },
                    { key: "aiRemarks", label: "Qualitative Pedagogical Remarks" },
                    { key: "signatures", label: "Institutional Signature Block" },
                  ].map(({ key, label }) => (
                    <label
                      key={key}
                      className="flex items-center gap-2.5 p-2 rounded-[5px] bg-surface-soft/40 hover:bg-surface-soft border border-border-main/50 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={sections[key as keyof ReportSectionToggles]}
                        onChange={(e) => setSections(prev => ({ ...prev, [key]: e.target.checked }))}
                        className="rounded text-brand-600 focus:ring-0 cursor-pointer"
                      />
                      <span className="text-foreground/80 font-medium">{label}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Accordion 2: TEMPLATE PRESETS */}
            <div className="border-t border-border-main/60 pt-3">
              <button
                type="button"
                onClick={() => setIsTemplateOpen(prev => !prev)}
                className="w-full flex items-center justify-between text-left py-1 group cursor-pointer"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-foreground/70 group-hover:text-foreground transition-colors">
                    Report Templates
                  </span>
                  <span className="text-foreground/40 font-bold">·</span>
                  <span className="text-[11px] font-bold text-foreground/60 group-hover:text-foreground transition-colors">
                    3
                  </span>
                </div>
                <ChevronDown
                  className={cn(
                    "w-3.5 h-3.5 text-foreground/40 group-hover:text-foreground transition-transform duration-200",
                    isTemplateOpen && "rotate-180"
                  )}
                />
              </button>

              {isTemplateOpen && (
                <div className="pt-2.5 space-y-1.5 animate-in fade-in duration-200">
                  {[
                    { id: "standard", name: "Standard Academic Report", desc: "Balanced KPIs, charts and item breakdown" },
                    { id: "report_card", name: "Student Term Report Card", desc: "Parent-ready summary with signature lines" },
                    { id: "detailed_analysis", name: "Pedagogical Deep Dive", desc: "Detailed question diagnostics and remarks" },
                  ].map((tpl) => (
                    <button
                      key={tpl.id}
                      type="button"
                      onClick={() => setTemplate(tpl.id as ReportTemplate)}
                      className={cn(
                        "w-full p-2.5 text-left rounded-[6px] border transition-all cursor-pointer",
                        template === tpl.id
                          ? "bg-surface-soft border-border-main text-foreground"
                          : "bg-surface-soft/40 hover:bg-surface-soft border-border-main/50 text-foreground/70"
                      )}
                    >
                      <span className="text-xs font-bold block">{tpl.name}</span>
                      <span className="text-[10px] text-foreground/50 block mt-0.5">{tpl.desc}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Accordion 3: EXAM HISTORY QUICK-LINKS */}
            <div className="border-t border-border-main/60 pt-3">
              <button
                type="button"
                onClick={() => setIsHistoryOpen(prev => !prev)}
                className="w-full flex items-center justify-between text-left py-1 group cursor-pointer"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-foreground/70 group-hover:text-foreground transition-colors">
                    Exam Runs
                  </span>
                  <span className="text-foreground/40 font-bold">·</span>
                  <span className="text-[11px] font-bold text-foreground/60 group-hover:text-foreground transition-colors">
                    {metadata.batches.length}
                  </span>
                </div>
                <ChevronDown
                  className={cn(
                    "w-3.5 h-3.5 text-foreground/40 group-hover:text-foreground transition-transform duration-200",
                    isHistoryOpen && "rotate-180"
                  )}
                />
              </button>

              {isHistoryOpen && (
                <div className="pt-2 space-y-1.5 animate-in fade-in duration-200">
                  {metadata.batches.slice(0, 5).map((b) => (
                    <button
                      key={b.id}
                      type="button"
                      onClick={() => {
                        setSelectedBatchId(b.id);
                        if (b.academic_group_id) setSelectedGroupId(b.academic_group_id);
                      }}
                      className="w-full group px-3 py-2 text-left rounded-[6px] bg-surface-soft/40 hover:bg-surface-soft border border-border-main/60 hover:border-border-main text-foreground transition-all flex items-center justify-between cursor-pointer"
                    >
                      <div className="min-w-0 pr-2">
                        <span className="text-xs font-semibold block truncate">
                          {b.subject} - {b.exam_type}
                        </span>
                        <span className="text-[10px] text-foreground/50 font-mono block">
                          {b.date_formatted}
                        </span>
                      </div>
                      <ArrowUpRight className="w-3.5 h-3.5 text-foreground/40 group-hover:text-foreground transition-all shrink-0" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
