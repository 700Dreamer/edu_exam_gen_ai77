"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import {
  Download, Loader2, FileCheck, AlertCircle, CheckCircle2, Trash2, Edit3, RefreshCw, ChevronLeft, ChevronRight,
  Upload, BookOpen, FileText, Layers, Eye, HelpCircle, Check, X, FileDown, Clock, Search,
  BarChart2, ChevronDown, ChevronUp, User, ArrowUpRight, Users, TrendingUp, Sparkles
} from "lucide-react";
import { cn, authFetch, formatTimeAgo } from "../lib/utils";
import GradingRunsControlPanel, {
  type RunStatusFilter, type RunSortOrder, type RunLiveMode
} from "./GradingRunsControlPanel";

export default function GradebookView({
  theme,
  onBatchActive
}: {
  theme?: string;
  onBatchActive?: (batch: any) => void;
}) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [batches, setBatches] = useState<any[]>([]);
  const [batchSearch, setBatchSearch] = useState("");
  const [isRefreshingBatches, setIsRefreshingBatches] = useState(false);
  const [runStatusFilter, setRunStatusFilter] = useState<RunStatusFilter>("all");
  const [runSortOrder, setRunSortOrder] = useState<RunSortOrder>("newest");
  const [runLiveMode, setRunLiveMode] = useState<RunLiveMode>("auto");
  const [batchesSyncedAt, setBatchesSyncedAt] = useState<Date | null>(null);
  const [, setRelativeTimeTick] = useState(0);
  const [selectedBatch, setSelectedBatch] = useState<any | null>(null);
  const [batchLoadingError, setBatchLoadingError] = useState<string | null>(null);
  const [isDirectHydrating, setIsDirectHydrating] = useState<boolean>(false);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [distribution, setDistribution] = useState<any | null>(null);

  const [selectedResult, setSelectedResult] = useState<any | null>(null);
  const [activeDetailTab, setActiveDetailTab] = useState<"inspector" | "report" | "paper">("inspector");
  const [selectedItemKey, setSelectedItemKey] = useState<string>("all");
  const [masterPageIndex, setMasterPageIndex] = useState<number>(0);
  const [showMasterUploadModal, setShowMasterUploadModal] = useState<boolean>(false);
  const [masterUploadFiles, setMasterUploadFiles] = useState<FileList | null>(null);
  const [isUploadingMaster, setIsUploadingMaster] = useState<boolean>(false);

  // Studio Results Workspace States
  const [navTab, setNavTab] = useState<"students" | "questions">("students");
  const [studentSearchQuery, setStudentSearchQuery] = useState("");
  const [showPaperModal, setShowPaperModal] = useState(false);
  const [paperModalPageIndex, setPaperModalPageIndex] = useState(0);
  const [isDistributionOpen, setIsDistributionOpen] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [isInsightsAccordionOpen, setIsInsightsAccordionOpen] = useState(false);

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [classStudents, setClassStudents] = useState<any[]>([]);
  const [resolutionStudentId, setResolutionStudentId] = useState("");
  const [isResolving, setIsResolving] = useState(false);
  const [overrideScore, setOverrideScore] = useState("");
  const [isOverriding, setIsOverriding] = useState(false);
  const [isReGrading, setIsReGrading] = useState(false);
  const [isRegradingPaper, setIsRegradingPaper] = useState(false);
  const [openedBatchIds, setOpenedBatchIds] = useState<Set<string>>(new Set());

  // PDF Export state
  const [pdfJobId, setPdfJobId] = useState<string | null>(null);
  const [pdfJobStatus, setPdfJobStatus] = useState<string>("");
  const [pdfToastMessage, setPdfToastMessage] = useState<string>("");
  const [isExportingStudentPdf, setIsExportingStudentPdf] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("edulytics-opened-batches");
      if (saved) {
        setOpenedBatchIds(new Set(JSON.parse(saved)));
      }
    } catch (e) { }
    try {
      const savedLive = localStorage.getItem("edulytics-run-live-mode");
      if (savedLive === "off" || savedLive === "auto" || savedLive === "30s") {
        setRunLiveMode(savedLive);
      }
    } catch (e) { }
    fetchBatches();
  }, []);

  const markBatchAsOpened = (batchId: string) => {
    setOpenedBatchIds(prev => {
      const next = new Set(prev);
      next.add(batchId);
      try {
        localStorage.setItem("edulytics-opened-batches", JSON.stringify(Array.from(next)));
      } catch (e) { }
      return next;
    });
  };

  const markBatchAsUnopened = (batchId: string) => {
    setOpenedBatchIds(prev => {
      const next = new Set(prev);
      next.delete(batchId);
      try {
        localStorage.setItem("edulytics-opened-batches", JSON.stringify(Array.from(next)));
      } catch (e) { }
      return next;
    });
  };

  const markAllBatchesAsOpened = () => {
    setOpenedBatchIds(prev => {
      const next = new Set(prev);
      batches.forEach(b => { if (b.status === "Completed") next.add(b.id); });
      try {
        localStorage.setItem("edulytics-opened-batches", JSON.stringify(Array.from(next)));
      } catch (e) { }
      return next;
    });
  };

  const handleRunLiveModeChange = (mode: RunLiveMode) => {
    setRunLiveMode(mode);
    try { localStorage.setItem("edulytics-run-live-mode", mode); } catch (e) { }
  };

  const handleRegradeSingleResult = async () => {
    if (!selectedResult) return;
    setIsRegradingPaper(true);
    try {
      const res = await authFetch(`/api/v1/assessment/result/${selectedResult.id}/regrade`, {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        const newResults: any[] = await refreshResults() as any[];
        const updated = newResults.find((x: any) => x.id === selectedResult.id);
        setSelectedResult(updated || data);
        alert(`Paper regraded successfully! Final Score: ${data.score}/${data.max_possible_score} pts.`);
      } else {
        alert("Failed to regrade paper.");
      }
    } catch (err) {
      console.error(err);
      alert("Error regrading paper.");
    } finally {
      setIsRegradingPaper(false);
    }
  };

  const handleReGradeBatch = async () => {
    if (!selectedBatch) return;
    setIsReGrading(true);
    markBatchAsUnopened(selectedBatch.id);
    try {
      const res = await authFetch(`/api/v1/assessment/batch/${selectedBatch.id}/process`, {
        method: "POST"
      });
      if (res.ok) {
        alert("Re-grading batch initiated successfully! Processing concurrently in background.");
        setSelectedBatch(null);
        setSelectedResult(null);
        fetchBatches();
      } else {
        alert("Failed to initiate re-grading.");
      }
    } catch (err) {
      console.error(err);
      alert("Error initiating re-grading.");
    } finally {
      setIsReGrading(false);
    }
  };

  const parseResultQuestions = (html: string) => {
    if (typeof window === "undefined" || !html) return [];
    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const rows = Array.from(doc.querySelectorAll("table tbody tr"));

      return rows.map((tr) => {
        const tds = Array.from(tr.querySelectorAll("td"));
        if (tds.length < 5) return null;

        const qNumRaw = tds[0]?.textContent?.trim() || "";
        const qNum = qNumRaw.replace(/^Q/i, "").trim();
        const qText = tds[1]?.textContent?.trim() || "";
        const studentAns = tds[2]?.textContent?.trim() || "";
        const statusText = tds[3]?.textContent?.trim() || "";
        const scoreStr = tds[4]?.textContent?.trim() || "0/0";
        const explanation = tds[5]?.innerHTML?.trim() || tds[5]?.textContent?.trim() || "";
        const remarks = tds[6]?.textContent?.trim() || "";

        let scoreAwarded = 0;
        let maxScore = 5;
        const scoreMatch = scoreStr.match(/(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)/);
        if (scoreMatch) {
          scoreAwarded = parseFloat(scoreMatch[1]);
          maxScore = parseFloat(scoreMatch[2]);
        }

        return {
          qNum,
          qText,
          studentAns,
          status: statusText.toUpperCase(),
          scoreStr,
          scoreAwarded,
          maxScore,
          explanation,
          remarks
        };
      }).filter(Boolean);
    } catch (e) {
      console.error("Error parsing result questions:", e);
      return [];
    }
  };

  const handleUploadMasterPaper = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatch || !masterUploadFiles || masterUploadFiles.length === 0) return;
    setIsUploadingMaster(true);
    try {
      const formData = new FormData();
      for (let i = 0; i < masterUploadFiles.length; i++) {
        formData.append("files", masterUploadFiles[i]);
      }
      const res = await authFetch(`/api/v1/assessment/batch/${selectedBatch.id}/upload-master-question`, {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedBatch((prev: any) => ({
          ...prev,
          mode: "answer_sheet",
          master_question_urls: data.master_urls,
          master_exam_structure: data.structure
        }));
        setBatches((prev: any[]) =>
          prev.map(b => b.id === selectedBatch.id ? {
            ...b,
            mode: "answer_sheet",
            master_question_urls: data.master_urls,
            master_exam_structure: data.structure
          } : b)
        );
        setShowMasterUploadModal(false);
        setMasterUploadFiles(null);
        alert("Master Question Paper uploaded successfully! Dual-Pane Question Inspector active.");
      } else {
        alert("Failed to upload Master Question Paper.");
      }
    } catch (err) {
      console.error("Master upload error:", err);
      alert("Error uploading Master Question Paper.");
    } finally {
      setIsUploadingMaster(false);
    }
  };

  const formatBatchInsightsHtml = (html: string) => {
    if (typeof window === "undefined" || !html) return html;
    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");

      let title = "";
      let generalInsightHTML = "";
      let strengthsHTML = "";
      let weaknessesHTML = "";
      let recommendationsHTML = "";

      const secGeneral = doc.getElementById("general-insight") || doc.querySelector('section[id*="insight"]');
      const secStrengths = doc.getElementById("key-strengths") || doc.querySelector('section[id*="strength"]');
      const secWeaknesses = doc.getElementById("key-weaknesses") || doc.querySelector('section[id*="weakness"]');
      const secRecs = doc.getElementById("actionable-recommendations") || doc.querySelector('section[id*="recommend"]');

      if (secGeneral || secStrengths || secWeaknesses || secRecs) {
        if (secGeneral) {
          const h = secGeneral.querySelector("h3, h4, h2");
          if (h) h.remove();
          generalInsightHTML = secGeneral.innerHTML;
        }
        if (secStrengths) {
          const h = secStrengths.querySelector("h3, h4, h2");
          if (h) h.remove();
          strengthsHTML = secStrengths.innerHTML;
        }
        if (secWeaknesses) {
          const h = secWeaknesses.querySelector("h3, h4, h2");
          if (h) h.remove();
          weaknessesHTML = secWeaknesses.innerHTML;
        }
        if (secRecs) {
          const h = secRecs.querySelector("h3, h4, h2");
          if (h) h.remove();
          recommendationsHTML = secRecs.innerHTML;
        }
      } else {
        const headings = Array.from(doc.querySelectorAll("h1, h2, h3, h4, p strong"));
        let currentSection = "";

        const children = Array.from(doc.body.children);
        children.forEach(el => {
          const text = el.textContent || "";
          const lowerText = text.toLowerCase();

          if (el.tagName.match(/^H[1-4]$/) || (el.tagName === "P" && el.querySelector("strong") && text.length < 100)) {
            if (lowerText.includes("performance") || lowerText.includes("insight")) {
              currentSection = "insight";
            } else if (lowerText.includes("strength")) {
              currentSection = "strengths";
            } else if (lowerText.includes("weakness") || lowerText.includes("improvement")) {
              currentSection = "weaknesses";
            } else if (lowerText.includes("recommendation") || lowerText.includes("actionable")) {
              currentSection = "recommendations";
            } else {
              title = text;
            }
          } else {
            if (currentSection === "insight") {
              generalInsightHTML += el.outerHTML;
            } else if (currentSection === "strengths") {
              strengthsHTML += el.outerHTML;
            } else if (currentSection === "weaknesses") {
              weaknessesHTML += el.outerHTML;
            } else if (currentSection === "recommendations") {
              recommendationsHTML += el.outerHTML;
            } else {
              if (el.tagName === "P") {
                generalInsightHTML += el.outerHTML;
              }
            }
          }
        });
      }

      if (!generalInsightHTML && !strengthsHTML && !weaknessesHTML && !recommendationsHTML) {
        return `<div class="prose prose-sm max-w-none text-foreground leading-relaxed">${html}</div>`;
      }

      const formatListItems = (listHtml: string, type: "strength" | "weakness") => {
        const d = parser.parseFromString(listHtml, "text/html");
        const lis = d.querySelectorAll("li");
        if (lis.length > 0) {
          let items = "";
          lis.forEach(li => {
            const text = li.innerHTML;
            items += `
              <li class="flex items-start gap-2.5 text-xs text-foreground/85 leading-relaxed py-1 text-left">
                <span class="mt-0.5 shrink-0 flex items-center justify-center w-4 h-4 rounded-full ${type === "strength" ? "bg-emerald-500/15 text-emerald-600" : "bg-amber-500/15 text-amber-600"} font-bold text-[10px]">
                  ${type === "strength" ? "+" : "!"}
                </span>
                <span>${text}</span>
              </li>
            `;
          });
          return `<ul class="space-y-1.5">${items}</ul>`;
        }
        return listHtml;
      };

      const formatRecs = (recsHtml: string) => {
        const d = parser.parseFromString(recsHtml, "text/html");
        const lis = d.querySelectorAll("li");
        if (lis.length > 0) {
          let cards = "";
          lis.forEach((li, idx) => {
            const htmlContent = li.innerHTML;
            let titleText = `Recommendation ${idx + 1}`;
            let descText = htmlContent;

            const strong = li.querySelector("strong");
            if (strong) {
              titleText = strong.textContent || titleText;
              strong.remove();
              descText = li.innerHTML.replace(/^[:\s\-]+/, "").trim();
            } else {
              const colonIndex = htmlContent.indexOf(":");
              if (colonIndex > 0 && colonIndex < 40) {
                titleText = htmlContent.slice(0, colonIndex).replace(/<\/?[^>]+(>|$)/g, "");
                descText = htmlContent.slice(colonIndex + 1).trim();
              }
            }

            cards += `
              <div class="p-4 bg-surface-soft border-l-4 border-brand-600 flex gap-3 shadow-none transition-all hover:bg-brand-50/10">
                <div class="shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-brand-500/15 text-brand-700 font-mono text-[10px] font-bold">
                  ${idx + 1}
                </div>
                <div class="space-y-1 text-left">
                  <h5 class="text-xs font-bold text-foreground">${titleText}</h5>
                  <p class="text-[11px] text-foreground/75 leading-relaxed">${descText}</p>
                </div>
              </div>
            `;
          });
          return `<div class="grid grid-cols-1 md:grid-cols-2 gap-4">${cards}</div>`;
        }
        return recsHtml;
      };

      return `
        <div class="space-y-6 font-outfit text-foreground">
          ${title ? `<div class="text-xs font-bold uppercase tracking-wider text-foreground/45 border-b border-border-main pb-2">${title}</div>` : ""}

          ${generalInsightHTML ? `
            <div class="bg-surface-soft/40 border border-border-main p-5 space-y-2">
              <h4 class="text-xs font-extrabold uppercase tracking-wider text-brand-700 flex items-center gap-1.5 text-left">
                <span class="w-1.5 h-3 bg-brand-600 rounded-none inline-block"></span>
                General Performance Insight
              </h4>
              <div class="text-xs text-foreground/80 leading-relaxed text-left">${generalInsightHTML}</div>
            </div>
          ` : ""}

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            ${strengthsHTML ? `
              <div class="bg-surface border border-border-main p-5 space-y-3">
                <h4 class="text-xs font-extrabold uppercase tracking-wider text-emerald-700 flex items-center gap-1.5 border-b border-border-main/50 pb-2.5 text-left">
                  <span class="w-1.5 h-3 bg-emerald-600 rounded-none inline-block"></span>
                  Key Strengths
                </h4>
                <div class="text-left">${formatListItems(strengthsHTML, "strength")}</div>
              </div>
            ` : ""}

            ${weaknessesHTML ? `
              <div class="bg-surface border border-border-main p-5 space-y-3">
                <h4 class="text-xs font-extrabold uppercase tracking-wider text-amber-700 flex items-center gap-1.5 border-b border-border-main/50 pb-2.5 text-left">
                  <span class="w-1.5 h-3 bg-amber-600 rounded-none inline-block"></span>
                  Key Weaknesses & Areas for Improvement
                </h4>
                <div class="text-left">${formatListItems(weaknessesHTML, "weakness")}</div>
              </div>
            ` : ""}
          </div>


        </div>
      `;

    } catch (e) {
      console.error("Error formatting batch insights:", e);
      return `<div class="prose prose-sm max-w-none text-foreground leading-relaxed">${html}</div>`;
    }
  };

  const formatRawReportHtml = (html: string) => {
    if (typeof window === "undefined" || !html) return html;
    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");

      // 1. Style tables
      const tables = doc.querySelectorAll("table");
      tables.forEach(table => {
        table.className = "w-full text-xs text-left border-collapse my-6 font-outfit shadow-sm overflow-hidden bg-surface border border-border-main";
        table.removeAttribute("border");
        table.removeAttribute("style");
      });

      // 2. Style table headers
      const ths = doc.querySelectorAll("th");
      ths.forEach(th => {
        th.className = "bg-surface-soft px-4 py-3 text-[9px] font-black uppercase tracking-widest text-foreground/50 border-b border-border-main";
        th.removeAttribute("style");
      });

      // 3. Style table cells
      const tds = doc.querySelectorAll("td");
      tds.forEach(td => {
        td.className = "px-4 py-3.5 border-b border-border-main text-foreground/85 leading-relaxed font-medium";
        td.removeAttribute("style");

        const text = td.textContent?.trim().toLowerCase();
        if (text === "correct") {
          td.innerHTML = `<span class="inline-flex items-center px-2 py-0.5 rounded-none text-[9px] font-extrabold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">Correct</span>`;
        } else if (text === "incorrect") {
          td.innerHTML = `<span class="inline-flex items-center px-2 py-0.5 rounded-none text-[9px] font-extrabold uppercase tracking-wider bg-rose-500/10 text-rose-600 border border-rose-500/20">Incorrect</span>`;
        } else if (text === "partial") {
          td.innerHTML = `<span class="inline-flex items-center px-2 py-0.5 rounded-none text-[9px] font-extrabold uppercase tracking-wider bg-amber-500/10 text-amber-600 border border-amber-500/20">Partial</span>`;
        }
      });

      // 4. Style Headings
      const h3s = doc.querySelectorAll("h3");
      h3s.forEach(h => {
        h.className = "text-xs font-black uppercase tracking-widest text-foreground/60 mt-8 mb-4 border-b border-border-main/50 pb-2 flex items-center gap-2";
      });

      const h2s = doc.querySelectorAll("h2");
      h2s.forEach(h => {
        h.className = "text-sm font-black uppercase tracking-widest text-foreground mt-8 mb-4 border-b border-border-main pb-2 flex items-center gap-2";
      });

      // 5. Wrap Executive Summary
      const execHeader = Array.from(doc.querySelectorAll("h3, h2, p, strong")).find(
        el => el.textContent?.includes("Executive Summary")
      );
      if (execHeader) {
        let studentName = "";
        let subject = "";
        let totalScore = "";

        const parent = execHeader.parentElement;
        if (parent) {
          const listItems = parent.querySelectorAll("p, li");
          listItems.forEach(item => {
            const txt = item.textContent || "";
            if (txt.includes("Student Name:")) studentName = txt.replace("Student Name:", "").trim();
            else if (txt.includes("Subject:")) subject = txt.replace("Subject:", "").trim();
            else if (txt.includes("Total Score:")) totalScore = txt.replace("Total Score:", "").trim();

            if (txt.includes("Student Name:") || txt.includes("Subject:") || txt.includes("Total Score:")) {
              item.remove();
            }
          });

          const gridDiv = doc.createElement("div");
          gridDiv.className = "grid grid-cols-1 sm:grid-cols-3 gap-4 my-6 font-outfit";

          if (studentName) {
            gridDiv.innerHTML += `
              <div class="p-4 space-y-1">
                <span class="text-[9px] font-bold uppercase tracking-wider text-foreground/40">Student Name</span>
                <p class="text-xs font-bold text-foreground truncate">${studentName}</p>
              </div>
            `;
          }
          if (subject) {
            gridDiv.innerHTML += `
              <div class=" p-4 space-y-1">
                <span class="text-[9px] font-bold uppercase tracking-wider text-foreground/40">Subject</span>
                <p class="text-xs font-bold text-foreground">${subject}</p>
              </div>
            `;
          }
          if (totalScore) {
            gridDiv.innerHTML += `
              <div class=" p-4 space-y-1">
                <span class="text-[9px] font-bold uppercase tracking-wider text-brand-600/80">Total Score</span>
                <p class="text-xs font-extrabold text-brand-600">${totalScore}</p>
              </div>
            `;
          }

          execHeader.after(gridDiv);
        }
      }

      // 6. Wrap Final Feedback
      const feedbackHeader = Array.from(doc.querySelectorAll("h3, h2")).find(
        el => el.textContent?.includes("Final Feedback") || el.textContent?.includes("Recommendations")
      );
      if (feedbackHeader) {
        const siblingParagraphs = [];
        let curr = feedbackHeader.nextElementSibling;
        while (curr && curr.tagName.toLowerCase() === "p") {
          siblingParagraphs.push(curr);
          curr = curr.nextElementSibling;
        }

        if (siblingParagraphs.length > 0) {
          const feedbackCard = doc.createElement("div");
          feedbackCard.className = "bg-brand-500/5 border-l-4 border-brand-600 p-5 space-y-3 font-outfit text-xs text-foreground/80 leading-relaxed my-4";

          siblingParagraphs.forEach(p => {
            const pCopy = doc.createElement("p");
            pCopy.textContent = p.textContent;
            feedbackCard.appendChild(pCopy);
            p.remove();
          });

          feedbackHeader.after(feedbackCard);
        }
      }

      return doc.body.innerHTML;
    } catch (e) {
      console.error("Error formatting report HTML:", e);
      return html;
    }
  };

  const updateUrlParams = useCallback((updates: Record<string, string | null>, replace: boolean = false) => {
    const params = new URLSearchParams(searchParams ? searchParams.toString() : "");
    if (!params.get("view") && !params.get("tab")) {
      params.set("view", "gradebook");
    }
    for (const [k, v] of Object.entries(updates)) {
      if (v === null || v === undefined) {
        params.delete(k);
      } else {
        params.set(k, v);
      }
    }
    const qs = params.toString();
    const newUrl = qs ? `${pathname}?${qs}` : pathname;
    if (replace) {
      router.replace(newUrl, { scroll: false });
    } else {
      router.push(newUrl, { scroll: false });
    }
  }, [searchParams, pathname, router]);

  useEffect(() => { fetchBatches(); }, []);

  const fetchBatches = async () => {
    try {
      const res = await authFetch("/api/v1/assessment/batches");
      if (res.ok) {
        const data = await res.json();
        setBatches(Array.isArray(data) ? data : []);
        setBatchesSyncedAt(new Date());
      }
    } catch (e) {
      console.error("Failed to fetch batches:", e);
    }
  };

  const handleRefreshBatches = async () => {
    setIsRefreshingBatches(true);
    try {
      await fetchBatches();
    } finally {
      setIsRefreshingBatches(false);
    }
  };

  const hasActiveRuns = batches.some(b => b.status === "Processing" || b.status === "Queued");

  // Live sync for the runs list. Auto polls only while runs are queued or processing.
  useEffect(() => {
    if (selectedBatch || runLiveMode === "off") return;
    const intervalMs = runLiveMode === "30s" ? 30000 : hasActiveRuns ? 10000 : null;
    if (!intervalMs) return;
    const id = setInterval(() => { fetchBatches(); }, intervalMs);
    return () => clearInterval(id);
  }, [runLiveMode, hasActiveRuns, selectedBatch]);

  // Keep relative "time ago" labels fresh on the runs list only
  useEffect(() => {
    if (selectedBatch) return;
    const id = setInterval(() => setRelativeTimeTick(t => t + 1), 30000);
    return () => clearInterval(id);
  }, [selectedBatch]);

  const loadBatchById = useCallback(async (batchId: string, targetStudentId?: string | null) => {
    setLoading(true);
    setIsDirectHydrating(true);
    setBatchLoadingError(null);
    try {
      const [bRes, rRes, dRes] = await Promise.all([
        authFetch(`/api/v1/assessment/batch/${batchId}`),
        authFetch(`/api/v1/assessment/batch/${batchId}/results`),
        authFetch(`/api/v1/analytics/score-distribution/${batchId}`)
      ]);

      if (!bRes.ok) {
        if (bRes.status === 404) {
          setBatchLoadingError("Grading run not found or was removed.");
        } else {
          setBatchLoadingError("Failed to load grading run details.");
        }
        setSelectedBatch(null);
        setLoading(false);
        setIsDirectHydrating(false);
        return;
      }

      const batchData = await bRes.json();
      setSelectedBatch(batchData);
      sessionStorage.setItem("edulytics_last_batch_id", batchId);
      markBatchAsOpened(batchId);

      if (onBatchActive) {
        onBatchActive(batchData);
      }

      let loadedResults: any[] = [];
      if (rRes.ok) {
        loadedResults = await rRes.json();
        setResults(loadedResults);
      }
      if (dRes.ok) {
        setDistribution(await dRes.json());
      }

      const desiredStudentId = targetStudentId || (searchParams ? searchParams.get("student") : null);
      if (desiredStudentId && loadedResults.length > 0) {
        const matched = loadedResults.find((r: any) => r.id === desiredStudentId);
        if (matched) {
          setSelectedResult(matched);
        } else {
          setSelectedResult(loadedResults[0]);
        }
      } else if (loadedResults.length > 0) {
        setSelectedResult(loadedResults[0]);
      }
    } catch (err) {
      console.error("Error loading batch by ID:", err);
      setBatchLoadingError("Network error while connecting to server.");
    } finally {
      setLoading(false);
      setIsDirectHydrating(false);
    }
  }, [onBatchActive, searchParams]);

  // Deep-linking & reload persistence effect
  const runId = searchParams ? (searchParams.get("run") || searchParams.get("batch")) : null;
  const studentParam = searchParams ? searchParams.get("student") : null;

  useEffect(() => {
    if (runId) {
      if (!selectedBatch || selectedBatch.id !== runId) {
        loadBatchById(runId, studentParam);
      } else if (studentParam && (!selectedResult || selectedResult.id !== studentParam)) {
        const found = results.find((r: any) => r.id === studentParam);
        if (found) setSelectedResult(found);
      } else if (!studentParam && selectedResult) {
        setSelectedResult(null);
      }
    } else {
      const cachedBatchId = typeof window !== "undefined" ? sessionStorage.getItem("edulytics_last_batch_id") : null;
      if (cachedBatchId) {
        updateUrlParams({ run: cachedBatchId }, true);
        loadBatchById(cachedBatchId);
      } else if (selectedBatch) {
        setSelectedBatch(null);
        setResults([]);
        setSelectedResult(null);
      }
    }
  }, [runId, studentParam]);

  const handleSelectBatch = async (batch: any) => {
    setSelectedBatch(batch);
    setSelectedResult(null);
    setIsSidebarCollapsed(false);
    setLoading(true);
    setBatchLoadingError(null);
    sessionStorage.setItem("edulytics_last_batch_id", batch.id);
    markBatchAsOpened(batch.id);
    updateUrlParams({ run: batch.id, student: null });

    if (onBatchActive) {
      onBatchActive(batch);
    }

    try {
      const [rRes, dRes] = await Promise.all([
        authFetch(`/api/v1/assessment/batch/${batch.id}/results`),
        authFetch(`/api/v1/analytics/score-distribution/${batch.id}`)
      ]);
      if (rRes.ok) {
        const rData = await rRes.json();
        const loadedResults = Array.isArray(rData) ? rData : [];
        setResults(loadedResults);
        if (loadedResults.length > 0 && !selectedResult) {
          setSelectedResult(loadedResults[0]);
        }
      }
      if (dRes.ok) setDistribution(await dRes.json());
    } catch (e) { }
    finally { setLoading(false); }
  };

  const handleBackToBatches = () => {
    sessionStorage.removeItem("edulytics_last_batch_id");
    setSelectedBatch(null);
    setResults([]);
    setSelectedResult(null);
    setIsSidebarCollapsed(false);
    setBatchLoadingError(null);
    updateUrlParams({ run: null, batch: null, student: null });
  };

  useEffect(() => {
    if (selectedBatch) {
      authFetch(`/api/v1/academic-group/${selectedBatch.academic_group_id}/students`)
        .then(res => res.json()).then(data => setClassStudents(data)).catch(() => { });
    } else { setClassStudents([]); }
  }, [selectedBatch]);

  const refreshResults = async () => {
    if (!selectedBatch) return;
    const [rRes, dRes] = await Promise.all([
      authFetch(`/api/v1/assessment/batch/${selectedBatch.id}/results`),
      authFetch(`/api/v1/analytics/score-distribution/${selectedBatch.id}`)
    ]);
    if (rRes.ok) { const d = await rRes.json(); setResults(d); return d; }
    if (dRes.ok) setDistribution(await dRes.json());
    return [];
  };

  const handleResolveIdentity = async () => {
    if (!selectedResult || !resolutionStudentId) return;
    setIsResolving(true);
    try {
      const res = await authFetch(`/api/v1/assessment/result/${selectedResult.id}/assign-student`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: resolutionStudentId })
      });
      if (res.ok) {
        const newResults: any[] = await refreshResults() as any[];
        const updated = newResults.find((x: any) => x.id === selectedResult.id);
        setSelectedResult(updated || null);
        setResolutionStudentId("");
      } else { alert("Failed to resolve identity."); }
    } catch (e) { alert("Network error."); }
    finally { setIsResolving(false); }
  };

  const handleReorderPages = async (fromIdx: number, toIdx: number) => {
    if (!selectedResult || !selectedResult.paper_images_urls) return;
    const sortedEntries = Object.entries(selectedResult.paper_images_urls).sort((a, b) =>
      a[0].localeCompare(b[0], undefined, { numeric: true, sensitivity: 'base' })
    );
    if (toIdx < 0 || toIdx >= sortedEntries.length) return;

    const urls = sortedEntries.map(([_, url]) => url as string);
    const [moved] = urls.splice(fromIdx, 1);
    urls.splice(toIdx, 0, moved);

    try {
      const res = await authFetch(`/api/v1/assessment/paper/${selectedResult.id}/reorder-pages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ page_urls: urls })
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedResult((prev: any) => ({ ...prev, paper_images_urls: data.paper_images_urls }));
        setResults((prev: any[]) => prev.map(r => r.id === selectedResult.id ? { ...r, paper_images_urls: data.paper_images_urls } : r));
      }
    } catch (e) {
      alert("Failed to update page sequence.");
    }
  };

  const handleOverrideScore = async () => {
    if (!selectedResult || !overrideScore) return;
    const score = parseInt(overrideScore);
    if (isNaN(score) || score < 0 || score > 100) { alert("Score must be 0–100"); return; }
    setIsOverriding(true);
    try {
      const res = await authFetch(`/api/v1/assessment/result/${selectedResult.id}/override-score`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ score })
      });
      if (res.ok) {
        const newResults: any[] = await refreshResults() as any[];
        const updated = newResults.find((x: any) => x.id === selectedResult.id);
        setSelectedResult(updated || null);
        setOverrideScore("");
      } else { alert("Failed to override score."); }
    } catch (e) { alert("Network error."); }
    finally { setIsOverriding(false); }
  };

  const handleDeleteBatch = async (batchId: string) => {
    if (!confirm("Delete this batch and all its results? This cannot be undone.")) return;
    try {
      const res = await authFetch(`/api/v1/assessment/batch/${batchId}`, { method: "DELETE" });
      if (res.ok) { setBatches(prev => prev.filter(b => b.id !== batchId)); }
      else { alert("Failed to delete batch."); }
    } catch { alert("Network error."); }
  };

  const handleExportCSV = (batchId: string, subject: string) => {
    window.open(`/api/v1/assessment/batch/${batchId}/export-csv`, "_blank");
  };

  // ── PDF Export Handlers ──

  const handleExportStudentPdf = async (resultId: string) => {
    setIsExportingStudentPdf(true);
    try {
      const res = await authFetch(`/api/v1/assessment/result/${resultId}/export-pdf`);
      if (!res.ok) {
        alert("Failed to generate student PDF.");
        return;
      }
      const blob = await res.blob();
      const disposition = res.headers.get("Content-Disposition") || "";
      const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
      const filename = filenameMatch ? filenameMatch[1] : "Edulytics_Student_Report.pdf";
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Student PDF export error:", err);
      alert("Error generating student PDF.");
    } finally {
      setIsExportingStudentPdf(false);
    }
  };

  const handleExportClassPdf = async (batchId: string) => {
    try {
      setPdfToastMessage("Initiating PDF report generation...");
      const res = await authFetch(`/api/v1/assessment/batch/${batchId}/export-pdf`, { method: "POST" });
      if (!res.ok) {
        setPdfToastMessage("");
        alert("Failed to start PDF generation.");
        return;
      }
      const data = await res.json();
      const jobId = data.job_id;
      setPdfJobId(jobId);
      setPdfJobStatus("generating");
      setPdfToastMessage("Generating class report and individual student PDFs...");

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await authFetch(`/api/v1/assessment/batch/${batchId}/report-status/${jobId}`);
          if (!statusRes.ok) {
            clearInterval(pollInterval);
            setPdfJobStatus("failed");
            setPdfToastMessage("PDF generation check failed.");
            setTimeout(() => setPdfToastMessage(""), 5000);
            return;
          }
          const statusData = await statusRes.json();

          if (statusData.status === "ready") {
            clearInterval(pollInterval);
            setPdfJobStatus("ready");
            setPdfToastMessage("PDF report ready! Downloading...");

            // Auto-download
            const dlRes = await authFetch(statusData.download_url);
            if (dlRes.ok) {
              const blob = await dlRes.blob();
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = statusData.filename || "Edulytics_Report.zip";
              document.body.appendChild(a);
              a.click();
              a.remove();
              URL.revokeObjectURL(url);
              setPdfToastMessage("PDF report downloaded successfully.");
            } else {
              setPdfToastMessage("Download failed. Try again.");
            }
            setTimeout(() => { setPdfToastMessage(""); setPdfJobId(null); setPdfJobStatus(""); }, 4000);

          } else if (statusData.status === "failed") {
            clearInterval(pollInterval);
            setPdfJobStatus("failed");
            setPdfToastMessage(`PDF generation failed: ${statusData.error || "Unknown error"}`);
            setTimeout(() => { setPdfToastMessage(""); setPdfJobId(null); setPdfJobStatus(""); }, 6000);
          }
        } catch (pollErr) {
          console.error("PDF poll error:", pollErr);
        }
      }, 2500);

    } catch (err) {
      console.error("Class PDF export error:", err);
      setPdfToastMessage("");
      alert("Error starting PDF generation.");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Completed": return "bg-emerald-500/10 text-emerald-500";
      case "Processing": return "bg-brand-500/10 text-brand-500 animate-pulse";
      default: return "bg-foreground/10 text-foreground/60";
    }
  };

  const [selectedBucket, setSelectedBucket] = useState<string | null>(null);

  const isScoreInBucket = (score: number | null, bucketLabel: string) => {
    if (score === null || score === undefined) return false;
    const [lowStr, highStr] = bucketLabel.split("-");
    const low = parseInt(lowStr, 10);
    const high = parseInt(highStr, 10);
    return score >= low && score <= high;
  };

  // Mini bar chart renderer with interactive click-filtering
  const ScoreChart = ({ dist }: { dist: any }) => {
    if (!dist) return null;
    const buckets = dist.buckets as Record<string, number>;
    const maxVal = Math.max(...Object.values(buckets), 1);
    const colors: Record<string, string> = {
      "0-49": "bg-red-500", "50-59": "bg-orange-400", "60-69": "bg-yellow-400",
      "70-79": "bg-lime-400", "80-89": "bg-emerald-400", "90-100": "bg-brand-500"
    };

    return (
      <div className="bg-surface border border-border-main p-5 space-y-4 font-outfit">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <h4 className="text-xs font-bold uppercase tracking-widest text-foreground/60">Score Distribution</h4>
            {selectedBucket && (
              <button
                onClick={() => setSelectedBucket(null)}
                className="text-[10px] font-black uppercase text-brand-600 bg-brand-500/10 hover:bg-brand-500/20 px-2 py-0.5 border border-brand-500/30 flex items-center gap-1 cursor-pointer transition-colors"
              >
                Filtered: {selectedBucket}% range (Click to Clear)
              </button>
            )}
          </div>
          <div className="flex gap-4 text-xs font-bold">
            <span>Avg: <strong className="text-brand-600">{dist.average}%</strong></span>
            <span>High: <strong className="text-emerald-600">{dist.highest}%</strong></span>
            <span>Low: <strong className="text-red-500">{dist.lowest}%</strong></span>
          </div>
        </div>

        <div className="flex items-end gap-2 h-24 pt-4">
          {Object.entries(buckets).map(([label, count]) => {
            const isSelected = selectedBucket === label;
            return (
              <div
                key={label}
                onClick={() => setSelectedBucket(prev => prev === label ? null : label)}
                className={cn(
                  "flex-1 flex flex-col items-center gap-1 cursor-pointer group transition-all duration-200 p-1 rounded-none",
                  isSelected ? "bg-brand-500/10 border border-brand-500/40" : "hover:bg-surface-soft"
                )}
                title={`Score range ${label}%: ${count} student(s) - Click to filter roster`}
              >
                <span className={cn("text-[9px] font-extrabold transition-transform group-hover:scale-110", isSelected ? "text-brand-600" : "text-foreground/50")}>
                  {count}
                </span>
                <div
                  className={cn(
                    `w-full ${colors[label] || "bg-brand-500"} transition-all duration-300 group-hover:brightness-110`,
                    isSelected ? "ring-2 ring-brand-500 ring-offset-1 ring-offset-surface scale-105" : "opacity-80 group-hover:opacity-100"
                  )}
                  style={{ height: `${Math.max((count / maxVal) * 64, count > 0 ? 8 : 2)}px` }}
                />
                <span className={cn("text-[9px] font-mono font-bold uppercase tracking-wider transition-colors", isSelected ? "text-brand-600 font-black" : "text-foreground/40")}>
                  {label}
                </span>
              </div>
            );
          })}
        </div>

        <div className="flex justify-between items-center text-[10px] text-foreground/50 pt-1">
          <span>Click any bar to filter student roster below by score range</span>
          <span>{dist.count} students total</span>
        </div>
      </div>
    );
  };

  // Batch Insights Card Component
  const BatchInsightsCard = ({ batchId }: { batchId: string }) => {
    const [insights, setInsights] = useState<string>("");
    const [loadingInsights, setLoadingInsights] = useState<boolean>(false);

    const fetchInsights = (force: boolean = false) => {
      if (!batchId) return;
      setLoadingInsights(true);
      if (force) setInsights("");
      const url = `/api/v1/analytics/batch-insights/${batchId}${force ? '?force_regenerate=true' : ''}`;
      authFetch(url)
        .then(async (res) => {
          const data = await res.json();
          if (!res.ok) {
            setInsights(data.insights || "<p class='text-xs text-red-500 italic'>Failed to load insights. Click Generate Insights to attempt again.</p>");
          } else {
            setInsights(data.insights || "");
          }
        })
        .catch(err => {
          console.error("Failed to fetch batch insights:", err);
          setInsights("<p class='text-xs text-red-500 italic'>Failed to load insights. Click Generate Insights to attempt again.</p>");
        })
        .finally(() => {
          setLoadingInsights(false);
        });
    };

    useEffect(() => {
      fetchInsights(false);
    }, [batchId]);

    const isError = insights.includes("text-red-500") || insights.includes("Failed");

    return (
      <div className="bg-surface border border-border-main p-6 space-y-4 font-outfit relative">
        <div className="flex justify-between items-center border-b border-border-main/50 pb-3">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 bg-foreground/40 rounded-full animate-pulse" />
            <h4 className="text-xs font-bold uppercase tracking-widest text-foreground/60">General AI Recommendation & Insights</h4>
          </div>
          <button
            type="button"
            onClick={() => fetchInsights(true)}
            disabled={loadingInsights}
            className="flex items-center gap-1.5 text-xs font-semibold text-foreground/70 hover:text-foreground disabled:opacity-50 cursor-pointer"
            title="Retry / Regenerate Insights"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", loadingInsights && "animate-spin")} />
            <span>{loadingInsights ? "Generating..." : "Regenerate"}</span>
          </button>
        </div>

        {loadingInsights ? (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-foreground/40" />
            <span className="text-xs text-foreground/50 italic">Generating general batch recommendations and learning insights...</span>
          </div>
        ) : insights ? (
          <div className="space-y-4">
            <div
              className="w-full text-foreground"
              dangerouslySetInnerHTML={{ __html: formatBatchInsightsHtml(insights) }}
            />
            {isError && (
              <button
                type="button"
                onClick={() => fetchInsights(true)}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs transition-all cursor-pointer inline-flex items-center gap-2"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Generating Insights</span>
              </button>
            )}
          </div>
        ) : (
          <div className="py-4 flex items-center justify-between">
            <p className="text-xs text-foreground/40 italic text-left">No insights generated for this batch.</p>
            <button
              type="button"
              onClick={() => fetchInsights(true)}
              className="px-3 py-1.5 border border-brand-500 text-brand-600 text-xs font-bold hover:bg-brand-50 cursor-pointer"
            >
              Generate Insights
            </button>
          </div>
        )}
      </div>
    );
  };

  const runStatusMap: Record<RunStatusFilter, string | null> = {
    all: null, queued: "Queued", processing: "Processing", completed: "Completed"
  };

  const filteredBatches = batches
    .filter(batch => {
      const wantedStatus = runStatusMap[runStatusFilter];
      if (wantedStatus && batch.status !== wantedStatus) return false;
      if (!batchSearch.trim()) return true;
      const q = batchSearch.toLowerCase();
      return (
        (batch.tenant_name && batch.tenant_name.toLowerCase().includes(q)) ||
        (batch.subject && batch.subject.toLowerCase().includes(q)) ||
        (batch.level && batch.level.toLowerCase().includes(q)) ||
        (batch.stream && batch.stream.toLowerCase().includes(q)) ||
        (batch.status && batch.status.toLowerCase().includes(q)) ||
        (batch.exam_type && batch.exam_type.toLowerCase().includes(q))
      );
    })
    .sort((a, b) => {
      if (runSortOrder === "subject") {
        return (a.subject || "").localeCompare(b.subject || "");
      }
      const diff = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      return runSortOrder === "oldest" ? diff : -diff;
    });

  const hasActiveRunFilters = batchSearch.trim() !== "" || runStatusFilter !== "all";
  const clearRunFilters = () => {
    setBatchSearch("");
    setRunStatusFilter("all");
  };

  const getLetterGrade = (score: number | null | undefined): string => {
    if (score === null || score === undefined) return "—";
    if (score >= 90) return "A+";
    if (score >= 80) return "A";
    if (score >= 75) return "B+";
    if (score >= 70) return "B";
    if (score >= 65) return "C+";
    if (score >= 60) return "C";
    if (score >= 50) return "D";
    return "F";
  };

  const getInitials = (name: string): string => {
    if (!name) return "ST";
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  const allBatchQuestions = useMemo(() => {
    if (!results || results.length === 0) return [];
    const qMap = new Map<string, { qNum: string; maxScore: number; scores: number[]; qText: string }>();
    results.forEach(r => {
      const qs = parseResultQuestions(r.raw_extracted_html || "");
      qs.forEach((q: any) => {
        if (!qMap.has(q.qNum)) {
          qMap.set(q.qNum, { qNum: q.qNum, maxScore: q.maxScore || 5, scores: [], qText: q.qText || "" });
        }
        const entry = qMap.get(q.qNum)!;
        entry.scores.push(typeof q.scoreAwarded === "number" ? q.scoreAwarded : 0);
        if (!entry.qText && q.qText) entry.qText = q.qText;
      });
    });
    return Array.from(qMap.values()).map(item => {
      const avgScore = item.scores.length > 0
        ? (item.scores.reduce((a, b) => a + b, 0) / item.scores.length)
        : 0;
      const avgPercent = item.maxScore > 0 ? Math.round((avgScore / item.maxScore) * 100) : 0;
      return {
        ...item,
        avgScore: Math.round(avgScore * 10) / 10,
        avgPercent,
        attemptCount: item.scores.length
      };
    }).sort((a, b) => {
      const numA = parseInt(a.qNum.replace(/\D/g, "") || "0");
      const numB = parseInt(b.qNum.replace(/\D/g, "") || "0");
      return numA - numB;
    });
  }, [results]);

  const validScores = useMemo(() => {
    return results
      .map(r => r.total_score)
      .filter((s): s is number => typeof s === "number" && !isNaN(s));
  }, [results]);

  const classAverage = useMemo(() => {
    return validScores.length > 0
      ? Math.round(validScores.reduce((a, b) => a + b, 0) / validScores.length)
      : null;
  }, [validScores]);

  const filteredStudents = useMemo(() => {
    return results.filter(r => {
      if (selectedBucket && !isScoreInBucket(r.total_score, selectedBucket)) {
        return false;
      }
      if (!studentSearchQuery.trim()) return true;
      const q = studentSearchQuery.toLowerCase();
      return (
        (r.student_name && r.student_name.toLowerCase().includes(q)) ||
        (r.index_number && r.index_number.toLowerCase().includes(q))
      );
    });
  }, [results, selectedBucket, studentSearchQuery]);

  return (
    <div className={cn(
      "flex-1 text-foreground font-outfit relative flex flex-col transition-colors duration-300",
      selectedBatch ? "p-3 sm:p-4 overflow-hidden h-[calc(100vh-62px)]" : "p-8 overflow-y-auto bg-surface-soft/30"
    )}>
      <div className={cn(
        "animate-in fade-in duration-300 flex-1 flex flex-col",
        selectedBatch ? "w-full max-w-[1720px] mx-auto overflow-hidden h-full gap-3" : "max-w-5xl mx-auto space-y-8"
      )}>

        {/* Header (Runs List Only) */}
        {!selectedBatch && (
          <div className="flex justify-between items-center border-b border-border-main pb-4">
            <div className="flex items-center gap-3">
              <div>
                <div className="flex items-center gap-1.5 text-xs text-foreground/50 font-medium">
                  <span>Grading Runs</span>
                </div>
                <h2 className="text-xl font-bold tracking-tight mt-0.5">Gradebook & Batch History</h2>
                <p className="text-xs text-foreground/60 mt-0.5">Review automatic grading stats and individual results</p>
              </div>
            </div>
          </div>
        )}

        {/* Not Found State */}
        {batchLoadingError && !selectedBatch && (
          <div className="bg-surface border border-border-main p-12 text-center max-w-lg mx-auto my-12 space-y-4">
            <div className="w-10 h-10 mx-auto rounded-none bg-foreground/5 border border-border-main flex items-center justify-center text-foreground/60 font-bold text-sm">
              !
            </div>
            <h3 className="text-sm font-bold text-foreground">Grading Run Not Found</h3>
            <p className="text-xs text-foreground/60 leading-relaxed">
              {batchLoadingError}
            </p>
            <button
              onClick={handleBackToBatches}
              className="px-4 py-2 bg-foreground text-surface text-xs font-bold hover:bg-foreground/90 transition-all cursor-pointer"
            >
              Return to Grading Runs
            </button>
          </div>
        )}

        {/* Direct Hydration Skeleton */}
        {Boolean(runId) && !selectedBatch && !batchLoadingError ? (
          <div className="space-y-6 animate-pulse py-4">
            <div className="h-28 bg-surface-soft/40 border border-border-main/50" />
            <div className="grid grid-cols-12 gap-6">
              <div className="col-span-12 lg:col-span-4 h-96 bg-surface-soft/40 border border-border-main/50" />
              <div className="col-span-12 lg:col-span-8 h-96 bg-surface-soft/40 border border-border-main/50" />
            </div>
          </div>
        ) : !selectedBatch ? (
          /* List of Batches */
          <div className="bg-surface border border-border-main rounded-[10px] shadow-none overflow-hidden flex flex-col">
            {/* Dashboard Toolbar Header */}
            <div className="px-5 py-3.5 border-b border-border-main bg-surface-soft/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-surface-soft rounded-[6px]">
                  <Layers className="w-4 h-4 text-foreground/60" />
                </div>
                <div>
                  <h3 className="text-[11px] font-semibold text-foreground/60 tracking-[0.18em] uppercase">
                    Grading Runs <span className="text-foreground/40">&middot; {batches.length} {batches.length === 1 ? "Run" : "Runs"}</span>
                  </h3>
                  <p className="text-[11px] text-foreground/45 mt-0.5">
                    Completed and active assessment evaluations
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-foreground/40 pointer-events-none" />
                  <input
                    type="text"
                    value={batchSearch}
                    onChange={(e) => setBatchSearch(e.target.value)}
                    placeholder="Filter runs..."
                    className="pl-8 pr-7 py-1.5 text-xs bg-surface-soft border border-transparent text-foreground placeholder:text-foreground/40 rounded-[6px] focus:outline-none focus:bg-surface focus:border-border-main w-44 sm:w-56 transition-all"
                  />
                  {batchSearch && (
                    <button
                      onClick={() => setBatchSearch("")}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-foreground/40 hover:text-foreground p-0.5 cursor-pointer"
                      title="Clear filter"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>

                <button
                  onClick={handleRefreshBatches}
                  disabled={isRefreshingBatches}
                  className="p-2 bg-surface-soft hover:bg-foreground/10 text-foreground/60 hover:text-foreground transition-all rounded-[6px] cursor-pointer disabled:opacity-50"
                  title="Refresh runs"
                  aria-label="Refresh runs"
                >
                  <RefreshCw className={cn("w-3.5 h-3.5", isRefreshingBatches && "animate-spin")} />
                </button>
              </div>
            </div>

            {batches.length === 0 ? (
              <div className="p-12 text-center text-xs text-foreground/40 italic">
                No assessment batches found. Execute an Orchestration from the Grading Pipeline page.
              </div>
            ) : filteredBatches.length === 0 ? (
              <div className="p-12 text-center text-xs text-foreground/60 space-y-2">
                <p>No grading runs match the current filters.</p>
                <button
                  onClick={clearRunFilters}
                  className="px-3 py-1 bg-surface border border-border-main text-xs font-semibold hover:bg-surface-soft text-brand-600 rounded-[5px] cursor-pointer"
                >
                  Clear filters
                </button>
              </div>
            ) : (
              /* Scrollable Table Viewport */
              <div className="overflow-x-auto overflow-y-auto max-h-[520px] relative scrollbar-thin">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="sticky top-0 z-10 bg-surface-soft/95 backdrop-blur-md border-b border-border-main shadow-xs">
                    <tr className="text-foreground/50 font-bold uppercase tracking-wider text-[10px]">
                      <th className="px-5 py-3">School / Tenant</th>
                      <th className="px-5 py-3">Class Stream</th>
                      <th className="px-5 py-3">Subject</th>
                      <th className="px-5 py-3">Evaluated</th>
                      <th className="px-5 py-3">Status</th>
                      <th className="px-5 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-main/50">
                    {filteredBatches.map(batch => (
                      <tr key={batch.id} className="hover:bg-surface-soft/30 transition-colors group">
                        <td className="px-5 py-3.5">
                          <span className="font-bold text-foreground block text-xs">{batch.tenant_name}</span>
                          {batch.exam_type && (
                            <span className="text-[10px] text-foreground/45 block font-mono mt-0.5">{batch.exam_type}</span>
                          )}
                        </td>
                        <td className="px-5 py-3.5">
                          <span className="px-2 py-0.5 text-[11px] font-semibold bg-surface-soft text-foreground/80 rounded-[4px] inline-block">
                            {batch.level} - {batch.stream}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <span className="font-semibold text-brand-700 text-xs">{batch.subject}</span>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-1.5 font-medium text-foreground text-xs">
                            <Clock className="w-3 h-3 text-foreground/40 shrink-0" />
                            <span>{formatTimeAgo(batch.created_at)}</span>
                          </div>
                          <span className="text-[10px] font-mono text-foreground/45 block mt-0.5">
                            {new Date(batch.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })} · {new Date(batch.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-2">
                            <span className={cn("px-2 py-0.5 rounded-[4px] text-[10px] font-black uppercase tracking-wider inline-block", getStatusColor(batch.status))}>
                              {batch.status}
                            </span>
                            {batch.status === "Completed" && !openedBatchIds.has(batch.id) && (
                              <span
                                className="px-2 py-0.5 rounded-[4px] text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 border border-emerald-500/30 flex items-center gap-1"
                                title={`Evaluated ${formatTimeAgo(batch.created_at)}`}
                              >
                                <Clock className="w-2.5 h-2.5 text-emerald-500" />
                                {formatTimeAgo(batch.created_at)}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleSelectBatch(batch)}
                              className="p-2 bg-surface-soft text-foreground/70 hover:text-foreground hover:bg-foreground/10 rounded-[5px] transition-all cursor-pointer shadow-none flex items-center justify-center group/btn"
                              title="View Results"
                              aria-label="View Results"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleExportCSV(batch.id, batch.subject)}
                              className="p-2 bg-surface-soft text-foreground/70 hover:text-emerald-600 hover:bg-emerald-500/10 rounded-[5px] transition-all cursor-pointer shadow-none flex items-center justify-center group/btn"
                              title="Export CSV"
                              aria-label="Export CSV"
                            >
                              <Download className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDeleteBatch(batch.id)}
                              className="p-2 bg-surface-soft text-foreground/50 hover:text-red-600 hover:bg-red-500/10 rounded-[5px] transition-all cursor-pointer shadow-none flex items-center justify-center group/btn"
                              title="Delete batch"
                              aria-label="Delete batch"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Bottom Summary Bar */}
            {batches.length > 0 && (
              <div className="px-5 py-2.5 bg-surface-soft/40 border-t border-border-main flex items-center justify-between text-[11px] text-foreground/50">
                <span>
                  Showing {filteredBatches.length} of {batches.length} grading {batches.length === 1 ? "run" : "runs"}
                </span>
                {hasActiveRunFilters && (
                  <button
                    onClick={clearRunFilters}
                    className="text-brand-600 hover:underline cursor-pointer font-medium"
                  >
                    Clear filters
                  </button>
                )}
              </div>
            )}
          </div>
        ) : (
          /* Studio Results Workspace */
          <div className="flex-1 flex flex-col gap-3 min-h-0 overflow-hidden">
            {/* Collapsible Score Distribution Drawer */}
            {isDistributionOpen && distribution && (
              <div className="bg-surface border border-border-main rounded-[10px] p-4 shadow-sm animate-in slide-in-from-top-2 duration-200 shrink-0">
                <div className="flex justify-between items-center pb-3 border-b border-border-main/50 mb-3">
                  <div className="flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-foreground/70" />
                    <h4 className="text-xs font-black uppercase tracking-wider text-foreground">
                      Class Score Distribution
                    </h4>
                  </div>
                  <button
                    onClick={() => setIsDistributionOpen(false)}
                    className="text-foreground/40 hover:text-foreground p-1 cursor-pointer"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <ScoreChart dist={distribution} />
              </div>
            )}

            {/* 3-Pane Studio Workspace */}
            <div className="grid grid-cols-12 gap-3 flex-1 min-h-0 overflow-hidden">
              {/* PANE 1: Left Roster & Question Navigator */}
              <div className="col-span-12 lg:col-span-3 bg-surface border border-border-main rounded-[10px] shadow-none flex flex-col h-full overflow-hidden">
                {/* Left Panel Back Navigation & Title */}
                <div className="p-3 border-b border-border-main/60 flex items-center justify-between gap-2 shrink-0">
                  <div className="flex items-center gap-2 min-w-0">
                    <button
                      onClick={handleBackToBatches}
                      className="p-1.5 text-foreground/60 hover:text-foreground hover:bg-surface-soft rounded-[6px] border border-border-main/60 transition-all cursor-pointer shrink-0"
                      title="Back to Grading Runs"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                    </button>
                    <div className="min-w-0">
                      <h3 className="text-xs font-bold text-foreground truncate leading-tight">
                        {selectedBatch.subject}
                      </h3>
                      <p className="text-[10px] text-foreground/45 truncate">
                        {selectedBatch.tenant_name} · {selectedBatch.level} {selectedBatch.stream}
                      </p>
                    </div>
                  </div>
                  <span className="text-[9px] font-bold uppercase tracking-wider bg-brand-500/10 text-brand-700 border border-brand-500/20 px-2 py-0.5 rounded-[4px] shrink-0">
                    {selectedBatch.mode === "answer_sheet" ? "Answer Sheet" : "Hybrid"}
                  </span>
                </div>

                {/* Segmented Tab Bar (Templates | Layers design) */}
                <div className="p-3 pb-2.5 border-b border-border-main/60 shrink-0">
                  <div className="p-1 bg-surface-soft rounded-[8px] flex items-center gap-1">
                    <button
                      onClick={() => setNavTab("students")}
                      className={cn(
                        "flex-1 py-1.5 text-xs rounded-[6px] transition-all text-center cursor-pointer",
                        navTab === "students"
                          ? "bg-white dark:bg-neutral-900 text-foreground font-semibold shadow-xs border border-border-main/50"
                          : "text-foreground/60 hover:text-foreground font-medium bg-transparent"
                      )}
                    >
                      Students
                    </button>
                    <button
                      onClick={() => setNavTab("questions")}
                      className={cn(
                        "flex-1 py-1.5 text-xs rounded-[6px] transition-all text-center cursor-pointer",
                        navTab === "questions"
                          ? "bg-white dark:bg-neutral-900 text-foreground font-semibold shadow-xs border border-border-main/50"
                          : "text-foreground/60 hover:text-foreground font-medium bg-transparent"
                      )}
                    >
                      Questions
                    </button>
                  </div>
                </div>

                {navTab === "students" ? (
                  <>
                    {/* Search & Filter Bar */}
                    <div className="p-2.5 border-b border-border-main bg-surface shrink-0 space-y-2">
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-foreground/40 pointer-events-none" />
                        <input
                          type="text"
                          value={studentSearchQuery}
                          onChange={(e) => setStudentSearchQuery(e.target.value)}
                          placeholder="Search student or index..."
                          className="w-full pl-8 pr-7 py-1.5 text-xs bg-surface-soft/60 border border-border-main rounded-[6px] text-foreground placeholder:text-foreground/40 outline-none focus:ring-1 focus:ring-brand-500 transition-all"
                        />
                        {studentSearchQuery && (
                          <button
                            onClick={() => setStudentSearchQuery("")}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-foreground/40 hover:text-foreground p-0.5 cursor-pointer"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        )}
                      </div>

                      {selectedBucket && (
                        <div className="flex items-center justify-between text-[10px] bg-brand-500/10 text-brand-700 border border-brand-500/20 px-2 py-1 rounded-[4px]">
                          <span>Bucket: {selectedBucket}</span>
                          <button
                            onClick={() => setSelectedBucket(null)}
                            className="text-brand-700/60 hover:text-brand-700 cursor-pointer font-bold"
                          >
                            Clear
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Student List */}
                    {loading ? (
                      <div className="flex-1 flex items-center justify-center p-8">
                        <Loader2 className="w-5 h-5 animate-spin text-foreground/40" />
                      </div>
                    ) : filteredStudents.length === 0 ? (
                      <div className="flex-1 p-8 text-center text-xs text-foreground/40 italic flex flex-col items-center justify-center">
                        <p>No students match your filter.</p>
                        {(studentSearchQuery || selectedBucket) && (
                          <button
                            onClick={() => {
                              setStudentSearchQuery("");
                              setSelectedBucket(null);
                            }}
                            className="mt-2 text-brand-600 font-bold hover:underline cursor-pointer"
                          >
                            Reset filters
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="flex-1 overflow-y-auto custom-scrollbar divide-y divide-border-main/50">
                        {filteredStudents.map((r) => {
                          const isSelected = selectedResult?.id === r.id;
                          const score = typeof r.total_score === "number" ? Math.round(r.total_score) : null;
                          const initials = getInitials(r.student_name);
                          return (
                            <div
                              key={r.id}
                              onClick={() => {
                                setSelectedResult(r);
                                setResolutionStudentId("");
                                setSelectedItemKey("all");
                                setMasterPageIndex(0);
                                const resMode = r.mode || selectedBatch?.mode || "hybrid";
                                if (resMode === "answer_sheet") {
                                  setActiveDetailTab("inspector");
                                } else {
                                  setActiveDetailTab("report");
                                }
                                updateUrlParams({ student: r.id }, true);
                              }}
                              className={cn(
                                "p-3 cursor-pointer transition-all flex items-center justify-between gap-2.5",
                                isSelected
                                  ? "bg-brand-500/10 border-l-4 border-brand-600 pl-2"
                                  : "hover:bg-surface-soft/60"
                              )}
                            >
                              <div className="flex items-center gap-2.5 min-w-0">
                                <div className={cn(
                                  "w-7 h-7 rounded-[6px] border flex items-center justify-center text-[10px] font-black shrink-0",
                                  isSelected
                                    ? "bg-brand-600 text-white border-brand-600"
                                    : "bg-surface-soft border-border-main text-foreground/70"
                                )}>
                                  {initials}
                                </div>
                                <div className="min-w-0">
                                  <h4 className="text-xs font-bold text-foreground truncate">
                                    {r.student_name}
                                  </h4>
                                  <p className="text-[10px] text-foreground/45 font-mono truncate">
                                    {r.index_number ? `Idx: ${r.index_number}` : "No Index Linked"}
                                  </p>
                                </div>
                              </div>
                              <div className="shrink-0 text-right">
                                {r.needs_manual_review ? (
                                  <span className="text-[10px] font-extrabold uppercase text-amber-600 tracking-wider">
                                    Review
                                  </span>
                                ) : score !== null ? (
                                  <span className={cn(
                                    "text-xs font-bold font-mono",
                                    score >= 70
                                      ? "text-emerald-600"
                                      : score >= 50
                                        ? "text-brand-600"
                                        : "text-rose-600"
                                  )}>
                                    {score}%
                                  </span>
                                ) : (
                                  <span className="text-xs text-foreground/40 font-mono">—</span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </>
                ) : (
                  /* Question Breakdown Navigator */
                  <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-2">
                    {allBatchQuestions.length === 0 ? (
                      <div className="p-8 text-center text-xs text-foreground/40 italic">
                        No question breakdown data extracted from results yet.
                      </div>
                    ) : (
                      allBatchQuestions.map((q) => {
                        const isSelected = selectedItemKey === q.qNum;
                        return (
                          <div
                            key={q.qNum}
                            onClick={() => setSelectedItemKey(q.qNum)}
                            className={cn(
                              "p-2.5 border rounded-[6px] transition-all cursor-pointer space-y-1.5",
                              isSelected
                                ? "bg-brand-500/10 border-brand-600 shadow-xs"
                                : "bg-surface border-border-main hover:bg-surface-soft/60"
                            )}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-black text-foreground">
                                Question {q.qNum}
                              </span>
                              <span className={cn(
                                "text-xs font-bold font-mono",
                                q.avgPercent >= 70
                                  ? "text-emerald-600"
                                  : q.avgPercent >= 50
                                    ? "text-brand-600"
                                    : "text-rose-600"
                              )}>
                                {q.avgPercent}% Avg
                              </span>
                            </div>
                            {q.qText && (
                              <p className="text-[10px] text-foreground/60 line-clamp-2 leading-relaxed">
                                {q.qText}
                              </p>
                            )}
                            <div className="flex items-center justify-between text-[10px] text-foreground/45 pt-1 border-t border-border-main/40">
                              <span>Max: {q.maxScore} marks</span>
                              <span>{q.attemptCount} responses</span>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>

              {/* PANE 2: Center Hero Canvas */}
              <div className="col-span-12 lg:col-span-6 bg-transparent border border-border-main rounded-[10px] shadow-sm flex flex-col h-full overflow-hidden relative">
                {!selectedResult ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-center opacity-50 p-12 space-y-3">
                    <FileCheck className="w-12 h-12 text-foreground/40" />
                    <h4 className="text-sm font-bold text-foreground">Select a Student</h4>
                    <p className="text-xs text-foreground/60 max-w-sm">
                      Select any student from the left roster to view their graded exam paper, rubric breakdown, and AI diagnostic feedback.
                    </p>
                  </div>
                ) : (() => {
                  const attemptedList: string[] = selectedResult.attempted_items?.items || [];
                  const rawParsedQs = selectedResult.raw_extracted_html ? parseResultQuestions(selectedResult.raw_extracted_html) : [];
                  const parsedQs = attemptedList.length > 0
                    ? rawParsedQs.filter((q: any) => attemptedList.includes(q.qNum))
                    : rawParsedQs;
                  const activeItem = parsedQs.find((q: any) => q.qNum === selectedItemKey) || (selectedItemKey !== "all" && parsedQs.length > 0 ? parsedQs[0] : null);
                  const paperImages = selectedResult.paper_images_urls || {};
                  const paperCount = Object.keys(paperImages).length;
                  const scoreVal = typeof selectedResult.total_score === "number" ? Math.round(selectedResult.total_score) : null;

                  return (
                    <div className="flex-1 flex flex-col h-full overflow-hidden relative">
                      {/* Hero Header */}
                      <div className="px-5 py-3 border-b border-border-main bg-surface/80 backdrop-blur-md flex items-center justify-between gap-3 shrink-0">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="text-sm font-bold text-foreground truncate">
                              {selectedResult.student_name}
                            </h3>
                            {scoreVal !== null && !selectedResult.needs_manual_review && (
                              <span className={cn(
                                "text-xs font-bold font-mono",
                                scoreVal >= 70
                                  ? "text-emerald-600"
                                  : scoreVal >= 50
                                    ? "text-brand-600"
                                    : "text-rose-600"
                              )}>
                                {scoreVal}% · Grade {getLetterGrade(scoreVal)}
                              </span>
                            )}
                          </div>
                          <p className="text-[10px] text-foreground/50 font-mono mt-0.5 truncate">
                            {selectedResult.index_number ? `Index: ${selectedResult.index_number} · ` : ""}
                            ID: {selectedResult.id}
                          </p>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            onClick={handleRegradeSingleResult}
                            disabled={isRegradingPaper}
                            className="px-2.5 py-1.5 bg-brand-500/10 hover:bg-brand-500/20 text-brand-600 border border-brand-500/30 text-xs font-bold rounded-[6px] transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                            title="Re-run AI evaluation for this student script"
                          >
                            {isRegradingPaper ? <Loader2 className="w-3.5 h-3.5 animate-spin text-foreground/70" /> : <RefreshCw className="w-3.5 h-3.5 text-foreground/70" />}
                            <span>{isRegradingPaper ? "Evaluating..." : "Re-evaluate"}</span>
                          </button>
                        </div>
                      </div>

                      {/* Question Item Navigator Track */}
                      {parsedQs.length > 0 && !selectedResult.needs_manual_review && (
                        <div className="px-4 py-2 bg-surface/80 backdrop-blur-md border-b border-border-main flex items-center gap-1.5 overflow-x-auto custom-scrollbar shrink-0">
                          <button
                            onClick={() => setSelectedItemKey("all")}
                            className={cn(
                              "px-2.5 py-1 text-[11px] font-bold rounded-[4px] border transition-all cursor-pointer shrink-0",
                              selectedItemKey === "all"
                                ? "bg-brand-600 text-white border-brand-600 shadow-xs"
                                : "bg-surface-soft text-foreground/70 border-border-main hover:bg-surface-soft/80"
                            )}
                          >
                            All Report ({parsedQs.length})
                          </button>
                          {parsedQs.map((q: any) => {
                            const isSelected = selectedItemKey === q.qNum;
                            const isCorrect = q.status === "CORRECT";
                            const isPartial = q.status === "PARTIAL";
                            return (
                              <button
                                key={q.qNum}
                                onClick={() => setSelectedItemKey(q.qNum)}
                                className={cn(
                                  "px-2.5 py-1 text-[11px] font-bold rounded-[4px] border transition-all cursor-pointer shrink-0 flex items-center gap-1.5",
                                  isSelected
                                    ? "bg-brand-600 text-white border-brand-600 shadow-xs"
                                    : "bg-surface text-foreground/80 border-border-main hover:bg-surface-soft"
                                )}
                              >
                                <span>Q{q.qNum}</span>
                                <span className={cn(
                                  "px-1 py-0.2 text-[9px] font-extrabold rounded-[3px]",
                                  isSelected
                                    ? "bg-white/20 text-white"
                                    : isCorrect
                                      ? "bg-emerald-500/15 text-emerald-700"
                                      : isPartial
                                        ? "bg-amber-500/15 text-amber-700"
                                        : "bg-rose-500/15 text-rose-700"
                                )}>
                                  {q.scoreAwarded}/{q.maxScore}
                                </span>
                              </button>
                            );
                          })}
                        </div>
                      )}

                      {/* Main Scrollable Canvas Content */}
                      <div className="bg-transparent flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 pb-24">
                        {/* MANUAL REVIEW NEEDED CENTER */}
                        {selectedResult.needs_manual_review ? (
                          <div className="bg-amber-500/5 border border-amber-500/30 rounded-[10px] p-6 space-y-4 text-left">
                            <div className="flex items-center gap-2 text-foreground/80">
                              <AlertCircle className="w-5 h-5 shrink-0 text-foreground/70" />
                              <h4 className="font-bold text-sm text-foreground">Identity Resolution Center</h4>
                            </div>
                            <p className="text-xs text-foreground/75 leading-relaxed">
                              The AI engine could not match this script with a registered student record.
                              {selectedResult.ai_remarks && (
                                <span className="block mt-1 font-mono text-amber-800 bg-amber-500/10 px-2 py-1 rounded-[4px] border border-amber-500/20">
                                  {selectedResult.ai_remarks}
                                </span>
                              )}
                            </p>

                            <div className="h-44 bg-transparent border border-border-main rounded-[6px] overflow-hidden flex items-center justify-center p-2">
                              {selectedResult.paper_images_urls?.page1 ? (
                                <img
                                  src={selectedResult.paper_images_urls.page1}
                                  alt="Student Scan Crop"
                                  className="max-h-full max-w-full object-contain"
                                  onError={(e: any) => {
                                    e.target.src = "https://via.placeholder.com/600x200?text=Scan+Header+Offline";
                                  }}
                                />
                              ) : (
                                <span className="text-xs text-foreground/40 italic">No image file found</span>
                              )}
                            </div>

                            <div className="space-y-1.5">
                              <label className="text-xs font-bold text-foreground/70 block">
                                Link to Registered Student
                              </label>
                              <select
                                value={resolutionStudentId}
                                onChange={(e) => setResolutionStudentId(e.target.value)}
                                className="w-full p-2.5 bg-surface border border-border-main rounded-[6px] text-xs text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer"
                              >
                                <option value="">Select Student from Roster...</option>
                                {classStudents.map((st: any) => (
                                  <option key={st.id} value={st.id}>
                                    {st.full_name} {st.index_number ? `(Index: ${st.index_number})` : ""}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <button
                              onClick={handleResolveIdentity}
                              disabled={!resolutionStudentId || isResolving}
                              className="w-full py-2.5 bg-foreground text-surface text-xs font-bold rounded-[6px] hover:bg-foreground/90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs"
                            >
                              {isResolving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                              <span>Confirm Match & Link Grade</span>
                            </button>
                          </div>
                        ) : (
                          <>
                            {/* Selected Single Question Detail Card */}
                            {activeItem && selectedItemKey !== "all" && (
                              <div className=" border border-brand-500/25 rounded-[8px] p-4 space-y-3 shadow-xs">
                                <div className="flex items-center justify-between border-b border-border-main/60 pb-2">
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs font-black uppercase tracking-wider text-foreground">
                                      Item {activeItem.qNum} Evaluation
                                    </span>
                                    <span className={cn(
                                      "px-2 py-0.5 text-[9px] font-black uppercase tracking-wider rounded-[4px] border",
                                      activeItem.status === "CORRECT"
                                        ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/20"
                                        : activeItem.status === "PARTIAL"
                                          ? "bg-amber-500/10 text-amber-700 border-amber-500/20"
                                          : "bg-rose-500/10 text-rose-700 border-rose-500/20"
                                    )}>
                                      {activeItem.status}
                                    </span>
                                  </div>
                                  <span className="text-xs font-black text-brand-700 bg-brand-500/10 px-2.5 py-0.5 rounded-[4px] border border-brand-500/20">
                                    {activeItem.scoreAwarded} / {activeItem.maxScore} Marks
                                  </span>
                                </div>

                                {activeItem.qText && (
                                  <div className="space-y-1">
                                    <span className="text-[10px] font-black uppercase tracking-wider text-foreground/50 block">Question Prompt:</span>
                                    <p className="text-xs font-medium text-foreground bg-surface p-2.5 border border-border-main/60 rounded-[4px] leading-relaxed">
                                      {activeItem.qText}
                                    </p>
                                  </div>
                                )}

                                <div className="space-y-1">
                                  <span className="text-[10px] font-black uppercase tracking-wider text-foreground/50 block">Student Response:</span>
                                  <p className="text-xs font-semibold text-foreground bg-surface p-2.5 border border-border-main/60 rounded-[4px] leading-relaxed">
                                    {activeItem.studentAns || "—"}
                                  </p>
                                </div>

                                {activeItem.explanation && (
                                  <div className="space-y-1">
                                    <span className="text-[10px] font-black uppercase tracking-wider text-foreground/50 block">Marking Justification:</span>
                                    <div
                                      className="text-foreground/80 bg-surface p-2.5 border border-border-main/60 rounded-[4px] leading-relaxed text-xs"
                                      dangerouslySetInnerHTML={{ __html: activeItem.explanation }}
                                    />
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Full AI Feedback Report (HERO) */}
                            <div className="bg-surface rounded-[8px] border border-border-main/70 p-6 shadow-xs text-left">
                              <div className="flex items-center gap-2 pb-3 mb-4 border-b border-border-main/60">
                                <Sparkles className="w-4 h-4 text-foreground/70" />
                                <h4 className="text-xs font-black uppercase tracking-wider text-foreground">
                                  AI Diagnostic & Feedback Report
                                </h4>
                              </div>

                              {selectedResult.raw_extracted_html ? (
                                <div
                                  className="prose prose-sm prose-slate max-w-none text-foreground"
                                  dangerouslySetInnerHTML={{ __html: formatRawReportHtml(selectedResult.raw_extracted_html) }}
                                />
                              ) : (
                                <div className="text-center py-12 text-xs text-foreground/50 italic space-y-2">
                                  <p>{selectedResult.ai_remarks || "No grading report details generated yet."}</p>
                                  <p className="text-[11px] text-foreground/40 font-mono">Click Re-evaluate above if you wish to run evaluation again.</p>
                                </div>
                              )}
                            </div>
                          </>
                        )}
                      </div>

                      {/* Floating Bottom Pill: View Scanned Paper */}
                      {paperCount > 0 && (
                        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 pointer-events-auto">
                          <button
                            onClick={() => {
                              setShowPaperModal(true);
                              setPaperModalPageIndex(0);
                            }}
                            className="px-4 py-2 bg-surface/90 hover:bg-surface border border-border-main rounded-[6px] shadow-lg backdrop-blur-md text-xs font-bold text-foreground flex items-center gap-2 cursor-pointer transition-all hover:scale-105 active:scale-95"
                          >
                            <Layers className="w-4 h-4 text-foreground/70" />
                            <span>View Scanned Paper ({paperCount} {paperCount === 1 ? "Page" : "Pages"})</span>
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>

              {/* PANE 3: Right Inspector */}
              <div className="col-span-12 lg:col-span-3 bg-surface border border-border-main rounded-[10px] shadow-none flex flex-col h-full overflow-hidden">
                {/* Pinned Top Header: The 3 Batch Actions */}
                <div className="p-3 border-b border-border-main/60 shrink-0 bg-surface">
                  <div className="p-1 bg-surface-soft rounded-[8px] flex items-center gap-1.5">
                    {/* Action 1: Re-Grade */}
                    <button
                      onClick={handleReGradeBatch}
                      disabled={isReGrading}
                      className="flex-1 py-1.5 px-2 bg-surface hover:bg-surface-soft border border-border-main/80 text-foreground text-xs font-semibold rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                      title="Re-Grade Batch"
                    >
                      {isReGrading ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-foreground/70 shrink-0" />
                      ) : (
                        <RefreshCw className="w-3.5 h-3.5 text-foreground/70 shrink-0" />
                      )}
                      <span className="truncate">Re-Grade</span>
                    </button>

                    {/* Action 2: Export Menu */}
                    <div className="relative flex-1">
                      <button
                        onClick={() => setExportMenuOpen(prev => !prev)}
                        className="w-full py-1.5 px-2 bg-surface hover:bg-surface-soft border border-border-main/80 text-foreground text-xs font-semibold rounded-[6px] transition-all flex items-center justify-center gap-1 cursor-pointer"
                        title="Export Options"
                      >
                        <Download className="w-3.5 h-3.5 text-foreground/70 shrink-0" />
                        <span className="truncate">Export</span>
                        <ChevronDown className="w-3 h-3 text-foreground/40 shrink-0" />
                      </button>

                      {exportMenuOpen && (
                        <>
                          <div
                            className="fixed inset-0 z-30"
                            onClick={() => setExportMenuOpen(false)}
                          />
                          <div className="absolute right-0 mt-1.5 w-52 bg-surface border border-border-main rounded-[6px] shadow-xl py-1 z-40 animate-in fade-in zoom-in-95 duration-150">
                            <button
                              onClick={() => {
                                setExportMenuOpen(false);
                                handleExportCSV(selectedBatch.id, selectedBatch.subject);
                              }}
                              className="w-full text-left px-3.5 py-2 text-xs font-medium text-foreground hover:bg-surface-soft flex items-center gap-2 cursor-pointer"
                            >
                              <Download className="w-3.5 h-3.5 text-foreground/70" />
                              <span>Export CSV Spreadsheet</span>
                            </button>
                            <button
                              onClick={() => {
                                setExportMenuOpen(false);
                                handleExportClassPdf(selectedBatch.id);
                              }}
                              disabled={pdfJobStatus === "generating"}
                              className="w-full text-left px-3.5 py-2 text-xs font-medium text-foreground hover:bg-surface-soft flex items-center gap-2 cursor-pointer disabled:opacity-50"
                            >
                              {pdfJobStatus === "generating" ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin text-foreground/70" />
                              ) : (
                                <FileDown className="w-3.5 h-3.5 text-foreground/70" />
                              )}
                              <span>Export Class PDF Report</span>
                            </button>
                            {selectedResult && selectedResult.total_score !== null && !selectedResult.needs_manual_review && (
                              <button
                                onClick={() => {
                                  setExportMenuOpen(false);
                                  handleExportStudentPdf(selectedResult.id);
                                }}
                                disabled={isExportingStudentPdf}
                                className="w-full text-left px-3.5 py-2 text-xs font-medium text-foreground hover:bg-surface-soft flex items-center gap-2 cursor-pointer disabled:opacity-50 border-t border-border-main/50"
                              >
                                {isExportingStudentPdf ? (
                                  <Loader2 className="w-3.5 h-3.5 animate-spin text-foreground/70" />
                                ) : (
                                  <FileText className="w-3.5 h-3.5 text-foreground/70" />
                                )}
                                <span>Export Student PDF</span>
                              </button>
                            )}
                          </div>
                        </>
                      )}
                    </div>

                    {/* Action 3: Score Distribution */}
                    <button
                      onClick={() => setIsDistributionOpen(prev => !prev)}
                      className={cn(
                        "flex-1 py-1.5 px-2 text-xs font-semibold rounded-[6px] border transition-all flex items-center justify-center gap-1.5 cursor-pointer",
                        isDistributionOpen
                          ? "bg-brand-600 text-white border-brand-600 shadow-xs"
                          : "bg-surface hover:bg-surface-soft border-border-main/80 text-foreground"
                      )}
                      title="Toggle Score Distribution Drawer"
                    >
                      <BarChart2 className={cn("w-3.5 h-3.5 shrink-0", isDistributionOpen ? "text-white" : "text-foreground/70")} />
                      <span className="truncate">Distribution</span>
                    </button>
                  </div>
                </div>

                {/* Scrollable Inspector Body */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
                  {!selectedResult ? (
                    <div className="space-y-4">
                      <div className="border border-border-main rounded-[8px] p-4 bg-surface-soft/40 space-y-2">
                        <h4 className="text-xs font-black uppercase tracking-wider text-foreground">
                          Batch Summary
                        </h4>
                        <div className="space-y-1.5 text-xs text-foreground/70">
                          <div className="flex justify-between">
                            <span>Subject</span>
                            <strong className="text-foreground">{selectedBatch.subject}</strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Class</span>
                            <strong className="text-foreground">{selectedBatch.level} {selectedBatch.stream}</strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Exam Type</span>
                            <strong className="text-foreground">{selectedBatch.exam_type}</strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Submissions</span>
                            <strong className="text-foreground">{results.length}</strong>
                          </div>
                          {classAverage !== null && (
                            <div className="flex justify-between pt-1 border-t border-border-main/50">
                              <span>Class Average</span>
                              <strong className="text-emerald-700">{classAverage}%</strong>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Class Insights */}
                      <div className="border border-border-main rounded-[8px] bg-surface overflow-hidden">
                        <div className="p-3 bg-surface-soft/60 border-b border-border-main flex items-center gap-2">
                          <Sparkles className="w-3.5 h-3.5 text-foreground/70" />
                          <h4 className="text-xs font-bold text-foreground">Class AI Insights</h4>
                        </div>
                        <div className="p-3">
                          <BatchInsightsCard batchId={selectedBatch.id} />
                        </div>
                      </div>
                    </div>
                  ) : (() => {
                    const scoreVal = typeof selectedResult.total_score === "number" ? Math.round(selectedResult.total_score) : null;
                    const letterGrade = scoreVal !== null ? getLetterGrade(scoreVal) : "—";
                    const paperImages = selectedResult.paper_images_urls || {};
                    const paperCount = Object.keys(paperImages).length;

                    return (
                      <div className="space-y-4">
                        {/* Performance Snapshot Card */}
                        <div className="border border-border-main rounded-[8px] p-4 bg-surface-soft/40 space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-black uppercase tracking-wider text-foreground/50">
                              Performance
                            </span>
                            <span className={cn(
                              "px-2 py-0.5 text-[9px] font-bold uppercase rounded-[4px] border",
                              selectedResult.needs_manual_review
                                ? "bg-amber-500/10 text-amber-700 border-amber-500/20"
                                : "bg-emerald-500/10 text-emerald-700 border-emerald-500/20"
                            )}>
                              {selectedResult.needs_manual_review ? "Review Required" : "Evaluated"}
                            </span>
                          </div>

                          <div className="flex items-baseline justify-between pt-1">
                            <div>
                              <span className="text-3xl font-black text-foreground">
                                {scoreVal !== null ? `${scoreVal}%` : "—"}
                              </span>
                            </div>
                            <div className="text-right">
                              <span className="px-3 py-1 bg-brand-500/10 border border-brand-500/20 text-brand-700 text-sm font-black rounded-[4px]">
                                Grade {letterGrade}
                              </span>
                            </div>
                          </div>

                          <div className="space-y-1.5 text-[11px] text-foreground/60 pt-2 border-t border-border-main/50">
                            <div className="flex justify-between">
                              <span>Student:</span>
                              <strong className="text-foreground truncate max-w-[140px]">{selectedResult.student_name}</strong>
                            </div>
                            <div className="flex justify-between">
                              <span>Index:</span>
                              <span className="font-mono text-foreground">{selectedResult.index_number || "Unlinked"}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Exam Mode:</span>
                              <span className="text-foreground">{selectedResult.mode || selectedBatch.mode || "Hybrid"}</span>
                            </div>
                          </div>
                        </div>

                        {/* Override Score Form */}
                        <div className="border border-border-main rounded-[8px] p-3.5 bg-surface space-y-2">
                          <label className="text-[10px] font-black uppercase tracking-wider text-foreground/50 block">
                            <Edit3 className="w-3 h-3 inline mr-1 text-foreground/60" />
                            Override Final Score
                          </label>
                          <div className="flex gap-2">
                            <input
                              type="number"
                              min="0"
                              max="100"
                              placeholder="0–100"
                              value={overrideScore}
                              onChange={e => setOverrideScore(e.target.value)}
                              className="w-20 text-xs border border-border-main rounded-[6px] p-2 bg-surface-soft text-foreground focus:ring-1 focus:ring-brand-500 outline-none"
                            />
                            <button
                              onClick={handleOverrideScore}
                              disabled={!overrideScore || isOverriding}
                              className="flex-1 py-2 bg-brand-600 text-white text-xs font-bold rounded-[6px] hover:bg-brand-700 disabled:opacity-50 transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
                            >
                              {isOverriding && <Loader2 className="w-3 h-3 animate-spin" />}
                              <span>Set Score</span>
                            </button>
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="space-y-2">
                          {scoreVal !== null && !selectedResult.needs_manual_review && (
                            <button
                              onClick={() => handleExportStudentPdf(selectedResult.id)}
                              disabled={isExportingStudentPdf}
                              className="w-full py-2 bg-surface hover:bg-surface-soft border border-border-main text-foreground text-xs font-bold rounded-[6px] transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 shadow-xs"
                            >
                              {isExportingStudentPdf ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin text-foreground/70" />
                              ) : (
                                <FileDown className="w-3.5 h-3.5 text-foreground/70" />
                              )}
                              <span>{isExportingStudentPdf ? "Generating PDF..." : "Export Student PDF"}</span>
                            </button>
                          )}

                          {paperCount > 0 && (
                            <button
                              onClick={() => {
                                setShowPaperModal(true);
                                setPaperModalPageIndex(0);
                              }}
                              className="w-full py-2 bg-surface-soft hover:bg-surface-soft/80 border border-border-main text-foreground/80 hover:text-foreground text-xs font-bold rounded-[6px] transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs"
                            >
                              <Layers className="w-3.5 h-3.5 text-foreground/70" />
                              <span>Inspect Paper Pages ({paperCount})</span>
                            </button>
                          )}
                        </div>

                        {/* Master Question Paper (Answer Sheet Mode) */}
                        {selectedBatch.mode === "answer_sheet" && (
                          <div className="border border-border-main rounded-[8px] p-3.5 bg-surface space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-black uppercase tracking-wider text-foreground/50">
                                Master Question Paper
                              </span>
                              {selectedBatch.master_question_urls ? (
                                <span className="text-[9px] font-bold uppercase text-emerald-700 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded-[4px]">
                                  Attached
                                </span>
                              ) : (
                                <span className="text-[9px] font-bold uppercase text-amber-700 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded-[4px]">
                                  Not Attached
                                </span>
                              )}
                            </div>
                            <button
                              onClick={() => setShowMasterUploadModal(true)}
                              className="w-full py-1.5 bg-surface-soft hover:bg-surface-soft/80 border border-border-main text-foreground/80 hover:text-foreground text-xs font-bold rounded-[6px] transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                            >
                              <Upload className="w-3.5 h-3.5 text-foreground/70" />
                              <span>{selectedBatch.master_question_urls ? "Change Master Paper" : "Upload Master Paper"}</span>
                            </button>
                          </div>
                        )}

                        {/* Class Batch AI Insights Accordion */}
                        <div className="border border-border-main rounded-[8px] bg-surface overflow-hidden">
                          <button
                            onClick={() => setIsInsightsAccordionOpen(prev => !prev)}
                            className="w-full p-3.5 flex items-center justify-between text-left hover:bg-surface-soft/60 transition-colors cursor-pointer"
                          >
                            <div className="flex items-center gap-2">
                              <Sparkles className="w-4 h-4 text-foreground/70" />
                              <span className="text-xs font-bold text-foreground">Class AI Insights</span>
                            </div>
                            <ChevronDown className={cn("w-3.5 h-3.5 text-foreground/40 transition-transform duration-200", isInsightsAccordionOpen && "rotate-180")} />
                          </button>
                          {isInsightsAccordionOpen && (
                            <div className="p-3 border-t border-border-main bg-surface-soft/30 animate-in fade-in duration-200">
                              <BatchInsightsCard batchId={selectedBatch.id} />
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Scanned Paper Lightbox Modal */}
        {showPaperModal && selectedResult && (() => {
          const paper_images = selectedResult.paper_images_urls || {};
          const sortedEntries = Object.entries(paper_images).sort((a, b) => {
            const numA = parseInt(a[0].replace(/\D/g, "") || "0");
            const numB = parseInt(b[0].replace(/\D/g, "") || "0");
            if (numA !== numB) return numA - numB;
            return a[0].localeCompare(b[0], undefined, { numeric: true, sensitivity: "base" });
          });
          const safePageIndex = Math.min(paperModalPageIndex, Math.max(0, sortedEntries.length - 1));
          const currentPageUrl = sortedEntries[safePageIndex]?.[1] as string | undefined;

          return (
            <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 font-outfit animate-in fade-in duration-200">
              <div className="bg-surface border border-border-main rounded-[10px] max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden text-left">
                {/* Modal Header */}
                <div className="px-5 py-3.5 border-b border-border-main bg-surface-soft/60 flex items-center justify-between shrink-0">
                  <div className="flex items-center gap-3">
                    <Layers className="w-4 h-4 text-foreground/70" />
                    <div>
                      <h3 className="text-xs font-black uppercase tracking-wider text-foreground">
                        Scanned Paper — {selectedResult.student_name}
                      </h3>
                      <p className="text-[10px] text-foreground/50 font-mono">
                        Page {safePageIndex + 1} of {sortedEntries.length} {sortedEntries[safePageIndex]?.[0] ? `(${sortedEntries[safePageIndex][0]})` : ""}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {sortedEntries.length > 1 && (
                      <div className="flex items-center gap-1.5 mr-2">
                        <button
                          onClick={() => handleReorderPages(safePageIndex, safePageIndex - 1)}
                          disabled={safePageIndex === 0}
                          className="px-2 py-1 text-[10px] font-bold bg-surface border border-border-main rounded-[4px] hover:bg-surface-soft disabled:opacity-30 cursor-pointer"
                          title="Move page earlier in sequence"
                        >
                          Move Up
                        </button>
                        <button
                          onClick={() => handleReorderPages(safePageIndex, safePageIndex + 1)}
                          disabled={safePageIndex === sortedEntries.length - 1}
                          className="px-2 py-1 text-[10px] font-bold bg-surface border border-border-main rounded-[4px] hover:bg-surface-soft disabled:opacity-30 cursor-pointer"
                          title="Move page later in sequence"
                        >
                          Move Down
                        </button>
                      </div>
                    )}
                    <button
                      onClick={() => setShowPaperModal(false)}
                      className="text-foreground/40 hover:text-foreground p-1.5 rounded-[6px] hover:bg-surface-soft cursor-pointer transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Modal Canvas Body */}
                <div className="flex-1 overflow-y-auto p-4 flex flex-col items-center justify-center bg-surface-soft/30 relative min-h-[300px]">
                  {sortedEntries.length === 0 ? (
                    <div className="text-xs text-foreground/40 italic py-16">
                      No scanned pages found for this student.
                    </div>
                  ) : (
                    <div className="relative max-w-full flex items-center justify-center">
                      {safePageIndex > 0 && (
                        <button
                          onClick={() => setPaperModalPageIndex(prev => Math.max(0, prev - 1))}
                          className="absolute left-2 top-1/2 -translate-y-1/2 p-2 bg-surface/90 hover:bg-surface border border-border-main rounded-[6px] shadow-md text-foreground cursor-pointer z-10"
                          title="Previous page"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                      )}

                      <img
                        src={currentPageUrl}
                        alt={`Scanned paper page ${safePageIndex + 1}`}
                        className="max-h-[68vh] w-auto object-contain border border-border-main rounded-[4px] shadow-lg bg-white"
                        onError={(e: any) => {
                          e.target.src = `https://via.placeholder.com/600x800?text=Page+${safePageIndex + 1}+Offline`;
                        }}
                      />

                      {safePageIndex < sortedEntries.length - 1 && (
                        <button
                          onClick={() => setPaperModalPageIndex(prev => Math.min(sortedEntries.length - 1, prev + 1))}
                          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-surface/90 hover:bg-surface border border-border-main rounded-[6px] shadow-md text-foreground cursor-pointer z-10"
                          title="Next page"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* Modal Footer / Thumbnail Strip */}
                {sortedEntries.length > 1 && (
                  <div className="px-4 py-2.5 border-t border-border-main bg-surface flex items-center justify-center gap-2 shrink-0 overflow-x-auto">
                    {sortedEntries.map(([key, url], idx) => (
                      <button
                        key={key}
                        onClick={() => setPaperModalPageIndex(idx)}
                        className={cn(
                          "px-2.5 py-1 text-xs font-bold rounded-[4px] border transition-all cursor-pointer flex items-center gap-1",
                          idx === safePageIndex
                            ? "bg-brand-600 text-white border-brand-600 shadow-xs"
                            : "bg-surface-soft border-border-main text-foreground/70 hover:bg-surface-soft/80"
                        )}
                      >
                        Page {idx + 1}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })()}

        {/* Master Question Paper Upload Modal */}
        {showMasterUploadModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4 font-outfit animate-in fade-in duration-200">
            <div className="bg-surface border border-border-main max-w-lg w-full p-6 space-y-5 shadow-2xl relative text-left">
              <div className="flex justify-between items-center border-b border-border-main pb-3">
                <div className="flex items-center gap-2">
                  <Upload className="w-5 h-5 text-foreground/70" />
                  <h3 className="text-sm font-extrabold uppercase tracking-wider text-foreground">
                    Upload Master Question Paper
                  </h3>
                </div>
                <button
                  onClick={() => { setShowMasterUploadModal(false); setMasterUploadFiles(null); }}
                  className="text-foreground/40 hover:text-foreground p-1 cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleUploadMasterPaper} className="space-y-4">
                <p className="text-xs text-foreground/75 leading-relaxed">
                  Select the Master Question Paper image file(s) or PDF for <strong>{selectedBatch?.subject} ({selectedBatch?.level} {selectedBatch?.stream})</strong>.
                  The AI engine will index all question items and display them side-by-side with student answer scripts.
                </p>

                <div className="border-2 border-dashed border-border-main p-6 text-center space-y-2 hover:border-brand-500 transition-colors bg-surface-soft/40">
                  <BookOpen className="w-8 h-8 mx-auto text-foreground/40" />
                  <input
                    type="file"
                    multiple
                    accept="image/*,.pdf"
                    onChange={(e) => setMasterUploadFiles(e.target.files)}
                    className="w-full text-xs text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-none file:border-0 file:text-xs file:font-extrabold file:bg-brand-600 file:text-white hover:file:bg-brand-700 cursor-pointer"
                  />
                  <p className="text-[10px] text-foreground/40 font-mono">Supports PNG, JPG, WEBP or PDF files</p>
                </div>

                <div className="flex gap-3 justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => { setShowMasterUploadModal(false); setMasterUploadFiles(null); }}
                    className="px-4 py-2 border border-border-main text-xs font-bold text-foreground/70 hover:bg-surface-soft cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!masterUploadFiles || masterUploadFiles.length === 0 || isUploadingMaster}
                    className="px-5 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-black uppercase tracking-wider disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer shadow-none"
                  >
                    {isUploadingMaster && <Loader2 className="w-4 h-4 animate-spin" />}
                    {isUploadingMaster ? "Indexing Master Paper..." : "Attach & Index Master Paper"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* Floating Run Control panel, runs list only */}
      {!selectedBatch && !runId && (
        <GradingRunsControlPanel
          batches={batches}
          openedBatchIds={openedBatchIds}
          statusFilter={runStatusFilter}
          onStatusFilterChange={setRunStatusFilter}
          sortOrder={runSortOrder}
          onSortOrderChange={setRunSortOrder}
          liveMode={runLiveMode}
          onLiveModeChange={handleRunLiveModeChange}
          lastSyncedAt={batchesSyncedAt}
          isRefreshing={isRefreshingBatches}
          onRefresh={handleRefreshBatches}
          onMarkAllReviewed={markAllBatchesAsOpened}
          onOpenRun={handleSelectBatch}
        />
      )}

      {/* PDF Generation Toast */}
      {pdfToastMessage && (
        <div className="fixed bottom-6 right-6 z-50 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="bg-surface border border-border-main shadow-lg px-5 py-3 flex items-center gap-3 font-outfit max-w-md">
            {pdfJobStatus === "generating" && (
              <Loader2 className="w-4 h-4 animate-spin text-foreground/70 shrink-0" />
            )}
            {pdfJobStatus === "ready" && (
              <CheckCircle2 className="w-4 h-4 text-foreground/80 shrink-0" />
            )}
            {pdfJobStatus === "failed" && (
              <AlertCircle className="w-4 h-4 text-foreground/80 shrink-0" />
            )}
            <span className="text-xs font-bold text-foreground">{pdfToastMessage}</span>
            <button
              onClick={() => { setPdfToastMessage(""); setPdfJobId(null); setPdfJobStatus(""); }}
              className="text-foreground/40 hover:text-foreground ml-2 cursor-pointer shrink-0"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


