"use client";

import { useState, useEffect } from "react";
import {
  Download, Loader2, FileCheck, AlertCircle, CheckCircle2, Trash2, Edit3, RefreshCw, ChevronLeft, ChevronRight
} from "lucide-react";
import { cn, authFetch } from "../lib/utils";

export default function GradebookView({ theme }: { theme: string }) {
  const [batches, setBatches] = useState<any[]>([]);
  const [selectedBatch, setSelectedBatch] = useState<any | null>(null);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [distribution, setDistribution] = useState<any | null>(null);

  const [selectedResult, setSelectedResult] = useState<any | null>(null);
  const [activeDetailTab, setActiveDetailTab] = useState<"report" | "paper">("report");
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [classStudents, setClassStudents] = useState<any[]>([]);
  const [resolutionStudentId, setResolutionStudentId] = useState("");
  const [isResolving, setIsResolving] = useState(false);
  const [overrideScore, setOverrideScore] = useState("");
  const [isOverriding, setIsOverriding] = useState(false);
  const [isReGrading, setIsReGrading] = useState(false);

  const handleReGradeBatch = async () => {
    if (!selectedBatch) return;
    setIsReGrading(true);
    try {
      const res = await authFetch(`/api/v1/assessment/batch/${selectedBatch.id}/process`, {
        method: "POST"
      });
      if (res.ok) {
        alert("Re-grading batch initiated successfully! All pages are being re-graded in the background. The page will auto-refresh. Please check back in a few moments.");
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
                  ${type === "strength" ? "✓" : "⚠"}
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
              <div class="bg-surface border border-border-main p-4 space-y-1">
                <span class="text-[9px] font-bold uppercase tracking-wider text-foreground/40">Student Name</span>
                <p class="text-xs font-bold text-foreground truncate">${studentName}</p>
              </div>
            `;
          }
          if (subject) {
            gridDiv.innerHTML += `
              <div class="bg-surface border border-border-main p-4 space-y-1">
                <span class="text-[9px] font-bold uppercase tracking-wider text-foreground/40">Subject</span>
                <p class="text-xs font-bold text-foreground">${subject}</p>
              </div>
            `;
          }
          if (totalScore) {
            gridDiv.innerHTML += `
              <div class="bg-brand-500/5 border border-brand-500/20 p-4 space-y-1">
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

  useEffect(() => { fetchBatches(); }, []);

  const fetchBatches = () => {
    authFetch("/api/v1/assessment/batches")
      .then(res => res.json())
      .then(data => setBatches(Array.isArray(data) ? data : []))
      .catch(() => { });
  };

  const handleSelectBatch = async (batch: any) => {
    setSelectedBatch(batch);
    setSelectedResult(null);
    setIsSidebarCollapsed(false);
    setLoading(true);
    try {
      const [rRes, dRes] = await Promise.all([
        authFetch(`/api/v1/assessment/batch/${batch.id}/results`),
        authFetch(`/api/v1/analytics/score-distribution/${batch.id}`)
      ]);
      if (rRes.ok) setResults(await rRes.json());
      if (dRes.ok) setDistribution(await dRes.json());
    } catch (e) { }
    finally { setLoading(false); }
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Completed": return "bg-emerald-500/10 text-emerald-500";
      case "Processing": return "bg-brand-500/10 text-brand-500 animate-pulse";
      default: return "bg-foreground/10 text-foreground/60";
    }
  };

  // Mini bar chart renderer
  const ScoreChart = ({ dist }: { dist: any }) => {
    if (!dist) return null;
    const buckets = dist.buckets as Record<string, number>;
    const maxVal = Math.max(...Object.values(buckets), 1);
    const colors: Record<string, string> = {
      "0-49": "bg-red-500", "50-59": "bg-orange-400", "60-69": "bg-yellow-400",
      "70-79": "bg-lime-400", "80-89": "bg-emerald-400", "90-100": "bg-brand-500"
    };
    return (
      <div className="bg-surface border border-border-main p-5 space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-xs font-bold uppercase tracking-widest text-foreground/60">Score Distribution</h4>
          <div className="flex gap-4 text-xs">
            <span>Avg: <strong className="text-brand-600">{dist.average}%</strong></span>
            <span>High: <strong className="text-emerald-600">{dist.highest}%</strong></span>
            <span>Low: <strong className="text-red-500">{dist.lowest}%</strong></span>
          </div>
        </div>
        <div className="flex items-end gap-2 h-20">
          {Object.entries(buckets).map(([label, count]) => (
            <div key={label} className="flex-1 flex flex-col items-center gap-1">
              <span className="text-[9px] font-bold text-foreground/50">{count}</span>
              <div
                className={`w-full ${colors[label] || "bg-brand-500"} transition-all duration-500`}
                style={{ height: `${Math.max((count / maxVal) * 64, count > 0 ? 6 : 0)}px` }}
              />
              <span className="text-[8px] font-mono text-foreground/40 rotate-0">{label}</span>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-foreground/40">{dist.count} students graded</p>
      </div>
    );
  };

  // Batch Insights Card Component
  const BatchInsightsCard = ({ batchId }: { batchId: string }) => {
    const [insights, setInsights] = useState<string>("");
    const [loadingInsights, setLoadingInsights] = useState<boolean>(false);

    useEffect(() => {
      if (!batchId) return;
      setLoadingInsights(true);
      setInsights("");
      authFetch(`/api/v1/analytics/batch-insights/${batchId}`)
        .then(res => res.json())
        .then(data => {
          setInsights(data.insights || "");
        })
        .catch(err => {
          console.error("Failed to fetch batch insights:", err);
          setInsights("<p class='text-xs text-red-500 italic'>Failed to load insights.</p>");
        })
        .finally(() => {
          setLoadingInsights(false);
        });
    }, [batchId]);

    return (
      <div className="bg-surface border border-border-main p-6 space-y-4 font-outfit relative">
        <div className="flex justify-between items-center border-b border-border-main/50 pb-3">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 bg-brand-600 rounded-full animate-pulse" />
            <h4 className="text-xs font-bold uppercase tracking-widest text-foreground/60">General AI Recommendation & Insights</h4>
          </div>
        </div>

        {loadingInsights ? (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
            <span className="text-xs text-foreground/50 italic">Generating general batch recommendations and learning insights...</span>
          </div>
        ) : insights ? (
          <div
            className="w-full text-foreground"
            dangerouslySetInnerHTML={{ __html: formatBatchInsightsHtml(insights) }}
          />
        ) : (
          <p className="text-xs text-foreground/40 italic text-left">No insights generated for this batch.</p>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 bg-surface-soft/30 text-foreground p-8 overflow-y-auto font-outfit relative">
      <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

        {/* Header or back navigation */}
        <div className="flex justify-between items-center border-b border-border-main pb-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-6 h-6 text-brand-600" />
            <div>
              <h2 className="text-xl font-bold tracking-tight">Gradebook & Batch History</h2>
              <p className="text-xs text-foreground/60 mt-0.5">Review automatic grading stats and individual results</p>
            </div>
          </div>
          {selectedBatch && (
            <button
              onClick={() => { setSelectedBatch(null); setResults([]); setSelectedResult(null); setIsSidebarCollapsed(false); }}
              className="px-4 py-2 text-xs font-bold bg-surface border border-border-main rounded-none hover:bg-surface-soft transition-colors cursor-pointer"
            >
              Back to Batches
            </button>
          )}
        </div>

        {!selectedBatch ? (
          /* List of Batches */
          <div className="bg-surface border border-border-main rounded-none shadow-none overflow-hidden">
            <div className="px-6 py-4 border-b border-border-main bg-surface-soft/50">
              <h3 className="text-sm font-bold text-foreground">Grading Runs</h3>
            </div>
            {batches.length === 0 ? (
              <div className="p-12 text-center text-xs text-foreground/40 italic">No assessment batches found. Execute an Orchestration from the Grading Pipeline page.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-border-main/50 bg-surface-soft/30 text-foreground/50 font-bold uppercase tracking-wider">
                      <th className="px-6 py-3.5">School / Tenant</th>
                      <th className="px-6 py-3.5">Class Stream</th>
                      <th className="px-6 py-3.5">Subject</th>
                      <th className="px-6 py-3.5">Date</th>
                      <th className="px-6 py-3.5">Status</th>
                      <th className="px-6 py-3.5" colSpan={3}>Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-main/50">
                    {batches.map(batch => (
                      <tr key={batch.id} className="hover:bg-surface-soft/20 transition-colors group">
                        <td className="px-6 py-4 font-bold text-foreground">{batch.tenant_name}</td>
                        <td className="px-6 py-4 text-foreground/80">{batch.level} - {batch.stream}</td>
                        <td className="px-6 py-4 font-semibold text-brand-700">{batch.subject}</td>
                        <td className="px-6 py-4 font-mono text-foreground/60">{new Date(batch.created_at).toLocaleString()}</td>
                        <td className="px-6 py-4">
                          <span className={cn("px-2.5 py-1 rounded-none text-[10px] font-black uppercase tracking-wider", getStatusColor(batch.status))}>
                            {batch.status}
                          </span>
                        </td>
                        <td className="px-3 py-4">
                          <button
                            onClick={() => handleSelectBatch(batch)}
                            className="px-3 py-1.5 bg-foreground text-surface text-[10px] font-bold rounded-none hover:bg-foreground/90 transition-all cursor-pointer shadow-none"
                          >
                            View Results
                          </button>
                        </td>
                        <td className="px-2 py-4">
                          <button
                            onClick={() => handleExportCSV(batch.id, batch.subject)}
                            className="px-3 py-1.5 bg-emerald-600 text-white text-[10px] font-bold rounded-none hover:bg-emerald-700 transition-all cursor-pointer shadow-none flex items-center gap-1"
                            title="Export CSV"
                          >
                            <Download className="w-3 h-3" /> CSV
                          </button>
                        </td>
                        <td className="px-2 py-4">
                          <button
                            onClick={() => handleDeleteBatch(batch.id)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 text-red-500 hover:bg-red-50 rounded-none cursor-pointer"
                            title="Delete batch"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          /* Detailed Batch Results */
          <div className="space-y-6">
            {/* Score Distribution Chart */}
            {distribution && <ScoreChart dist={distribution} />}

            {/* General AI Recommendations & Insights */}
            {selectedBatch && <BatchInsightsCard batchId={selectedBatch.id} />}
            <div className="flex gap-2 justify-end">
              <button
                onClick={handleReGradeBatch}
                disabled={isReGrading}
                className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white text-xs font-bold rounded-none hover:bg-brand-700 disabled:opacity-50 transition-all cursor-pointer shadow-none"
              >
                {isReGrading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" /> Re-grading...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-3.5 h-3.5" /> Re-Grade Batch
                  </>
                )}
              </button>
              <button
                onClick={() => handleExportCSV(selectedBatch.id, selectedBatch.subject)}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-xs font-bold rounded-none hover:bg-emerald-700 transition-all cursor-pointer shadow-none"
              >
                <Download className="w-3.5 h-3.5" /> Export CSV
              </button>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Student Results Table */}
              <div className={cn(
                "lg:col-span-1 bg-surface border border-border-main rounded-none shadow-none overflow-hidden self-start transition-all duration-300",
                isSidebarCollapsed ? "hidden" : "block"
              )}>
                <div className="px-6 py-4 border-b border-border-main bg-surface-soft/50">
                  <h3 className="text-sm font-bold text-foreground">{selectedBatch.tenant_name} — {selectedBatch.level} {selectedBatch.stream}</h3>
                  <p className="text-[10px] text-foreground/50 mt-1 font-semibold">{selectedBatch.subject} | {selectedBatch.exam_type}</p>
                </div>

                {loading ? (
                  <div className="p-12 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-brand-500" /></div>
                ) : results.length === 0 ? (
                  <div className="p-8 text-center text-xs text-foreground/40 italic">No uploads processed in this batch.</div>
                ) : (
                  <div className="divide-y divide-border-main/50 max-h-[500px] overflow-y-auto custom-scrollbar">
                    {results.map(r => (
                      <div
                        key={r.id}
                        onClick={() => { setSelectedResult(r); setResolutionStudentId(""); setActiveDetailTab("report"); }}
                        className={cn(
                          "p-4 cursor-pointer hover:bg-surface-soft/30 transition-all flex justify-between items-center",
                          selectedResult?.id === r.id ? "bg-brand-50/40 border-l-4 border-brand-600 pl-3" : ""
                        )}
                      >
                        <div>
                          <h4 className="text-xs font-bold text-foreground">{r.student_name}</h4>
                          <p className="text-[10px] text-foreground/40 font-mono mt-0.5">{r.index_number ? `Index: ${r.index_number}` : "No Index Linked"}</p>
                        </div>
                        <div className="text-right">
                          {r.needs_manual_review ? (
                            <span className="text-[9px] font-black uppercase text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-none">Unresolved</span>
                          ) : (
                            <span className="text-xs font-black text-brand-700 bg-brand-500/10 px-2 py-0.5 rounded-none">{r.total_score !== null ? `${r.total_score}%` : "—"}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Individual Result Details Panel */}
              <div className={cn(
                "bg-surface border border-border-main rounded-none shadow-none overflow-hidden min-h-[400px] flex flex-col transition-all duration-300",
                isSidebarCollapsed ? "lg:col-span-3" : "lg:col-span-2"
              )}>
                {!selectedResult ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-center opacity-40 p-12">
                    <FileCheck className="w-16 h-16 mb-4 text-foreground/40" />
                    <h4 className="text-sm font-bold text-foreground">Select Student</h4>
                    <p className="text-xs text-foreground/60 mt-1">Select a student from the list on the left to display their graded exam paper and AI feedback.</p>
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col h-[600px] overflow-hidden">
                    {/* Top Panel Bar */}
                    <div className="px-6 py-4 border-b border-border-main bg-surface-soft/50 flex justify-between items-center shrink-0">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => setIsSidebarCollapsed(prev => !prev)}
                          className="p-1.5 text-foreground/50 hover:text-foreground hover:bg-surface-soft/80 border border-border-main transition-all cursor-pointer rounded-none flex items-center justify-center shrink-0"
                          title={isSidebarCollapsed ? "Expand Roster" : "Collapse Roster"}
                        >
                          {isSidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
                        </button>
                        <div>
                          <h4 className="text-sm font-bold text-foreground">{selectedResult.student_name}</h4>
                          <p className="text-[10px] text-foreground/40 font-mono mt-0.5">Result ID: {selectedResult.id}</p>
                        </div>
                      </div>
                      {selectedResult.total_score !== null && !selectedResult.needs_manual_review && (
                        <div className="text-2xl font-black text-brand-600 bg-brand-500/10 px-4 py-1.5 rounded-none border border-brand-500/20 shadow-none">
                          {selectedResult.total_score}%
                        </div>
                      )}
                    </div>

                    {/* Toggle Tabs (only if not in manual review) */}
                    {!selectedResult.needs_manual_review && (
                      <div className="flex border-b border-border-main bg-surface-soft/20 px-6 shrink-0 font-outfit">
                        <button
                          onClick={() => setActiveDetailTab("report")}
                          className={cn(
                            "px-4 py-3 text-[10px] font-black uppercase tracking-widest border-b-2 transition-all cursor-pointer mr-4",
                            activeDetailTab === "report"
                              ? "border-brand-600 text-brand-600 font-extrabold"
                              : "border-transparent text-foreground/50 hover:text-foreground"
                          )}
                        >
                          Exam Report
                        </button>
                        <button
                          onClick={() => setActiveDetailTab("paper")}
                          className={cn(
                            "px-4 py-3 text-[10px] font-black uppercase tracking-widest border-b-2 transition-all cursor-pointer",
                            activeDetailTab === "paper"
                              ? "border-brand-600 text-brand-600 font-extrabold"
                              : "border-transparent text-foreground/50 hover:text-foreground"
                          )}
                        >
                          Scanned Paper
                        </button>
                      </div>
                    )}

                    {/* Identity Resolution Form vs Regular Output */}
                    {selectedResult.needs_manual_review ? (
                      <div className="flex-1 p-6 flex flex-col justify-center items-center bg-amber-500/5 overflow-y-auto custom-scrollbar">
                        <div className="w-full max-w-md bg-surface border border-amber-500/30 rounded-none p-6 shadow-none space-y-4 font-outfit text-left">
                          <div className="flex items-center gap-2 text-amber-600 mb-2">
                            <AlertCircle className="w-5 h-5" />
                            <h4 className="font-bold text-sm">Identity Resolution Center</h4>
                          </div>
                          <p className="text-xs text-foreground/75 leading-relaxed">
                            The AI could not map this scan to a registered student. Remarks: <span className="font-mono bg-slate-50 px-1 py-0.5 border border-border-main rounded-none text-red-600">{selectedResult.ai_remarks}</span>
                          </p>

                          <div className="h-40 bg-surface-soft border border-border-main rounded-none overflow-hidden relative flex items-center justify-center">
                            {selectedResult.paper_images_urls?.page1 ? (
                              <img
                                src={selectedResult.paper_images_urls.page1}
                                alt="Scan Crop"
                                className="max-h-full object-contain"
                                onError={(e: any) => { e.target.src = "https://via.placeholder.com/600x200?text=Handwritten+Name+Header"; }}
                              />
                            ) : (
                              <span className="text-xs text-foreground/40 italic">No image file found</span>
                            )}
                          </div>

                          <div>
                            <label className="text-xs font-bold text-foreground/60 mb-2 block">Link to Student Record</label>
                            <select
                              value={resolutionStudentId}
                              onChange={(e) => setResolutionStudentId(e.target.value)}
                              className="w-full p-3 bg-surface border border-border-main rounded-none text-xs text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer"
                            >
                              <option value="">Select Student...</option>
                              {classStudents.map((st: any) => (
                                <option key={st.id} value={st.id}>{st.full_name} {st.index_number ? `(Index: ${st.index_number})` : ""}</option>
                              ))}
                            </select>
                          </div>

                          <button
                            onClick={handleResolveIdentity}
                            disabled={!resolutionStudentId || isResolving}
                            className="w-full py-2.5 bg-foreground text-surface text-xs font-bold rounded-none hover:bg-foreground/90 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-none"
                          >
                            {isResolving && <Loader2 className="w-3 h-3 animate-spin" />}
                            Confirm Match & Link Grade
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* Display Graded scan & AI report based on active detail tab */
                      <div className="flex-1 flex flex-col overflow-hidden">
                        {activeDetailTab === "paper" ? (
                          /* Graded scan Image (Full Width) */
                          <div className="flex-1 bg-surface-soft overflow-y-auto p-6 flex flex-col gap-6 items-center custom-scrollbar">
                            {(() => {
                              const paper_images = selectedResult.paper_images_urls || {};
                              const sortedEntries = Object.entries(paper_images).sort((a, b) =>
                                a[0].localeCompare(b[0], undefined, { numeric: true, sensitivity: 'base' })
                              );
                              if (sortedEntries.length === 0) {
                                return <div className="text-xs text-foreground/40 italic py-12">No image file found for this scan.</div>;
                              }
                              return sortedEntries.map(([key, url], idx) => (
                                <div key={key} className="w-full max-w-2xl space-y-1.5 flex flex-col items-center">
                                  <p className="text-[10px] text-foreground/50 font-bold uppercase tracking-wider self-start pl-2">
                                    Page {idx + 1} of {sortedEntries.length}
                                  </p>
                                  <img
                                    src={url as string}
                                    alt={`Graded scan page ${idx + 1}`}
                                    className="w-full rounded-none border border-border-main shadow-lg object-contain bg-white animate-in fade-in zoom-in-95 duration-300"
                                    onError={(e: any) => { e.target.src = `https://via.placeholder.com/600x800?text=Page+${idx + 1}+Offline`; }}
                                  />
                                </div>
                              ));
                            })()}
                          </div>
                        ) : (
                          /* AI Feedback Report (HTML Rendering) - Full Width with Premium Styling */
                          <div className="flex-1 overflow-y-auto bg-surface custom-scrollbar text-left flex flex-col animate-in fade-in duration-300">
                            <div className="flex-1 p-6">
                              {selectedResult.raw_extracted_html ? (
                                <div
                                  className="prose prose-sm prose-slate max-w-none text-foreground"
                                  dangerouslySetInnerHTML={{ __html: formatRawReportHtml(selectedResult.raw_extracted_html) }}
                                />
                              ) : (
                                <div className="text-center py-12 text-xs text-foreground/40 italic">
                                  {selectedResult.ai_remarks || "No grading report details generated yet."}
                                </div>
                              )}
                            </div>
                            {/* Score Override Form */}
                            <div className="border-t border-border-main p-4 bg-surface-soft/50 shrink-0">
                              <label className="text-[10px] font-bold uppercase tracking-widest text-foreground/50 block mb-2">
                                <Edit3 className="w-3 h-3 inline mr-1" />Override Score
                              </label>
                              <div className="flex gap-2">
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  placeholder="0–100"
                                  value={overrideScore}
                                  onChange={e => setOverrideScore(e.target.value)}
                                  className="w-20 text-xs border border-border-main rounded-none p-2 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none"
                                />
                                <button
                                  onClick={handleOverrideScore}
                                  disabled={!overrideScore || isOverriding}
                                  className="flex-1 py-2 bg-brand-600 text-white text-xs font-bold rounded-none hover:bg-brand-700 disabled:opacity-50 transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-none"
                                >
                                  {isOverriding && <Loader2 className="w-3 h-3 animate-spin" />}
                                  Set Score
                                </button>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


