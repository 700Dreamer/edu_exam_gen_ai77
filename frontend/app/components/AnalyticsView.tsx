"use client";

import { useState, useEffect } from "react";
import {
  BarChart3, Loader2, AlertCircle, Users, TrendingUp, Award, BookOpen, School, Trophy
} from "lucide-react";
import { authFetch } from "../lib/utils";

export default function AnalyticsView({ theme }: { theme: string }) {
  const [overview, setOverview] = useState<any>(null);
  const [tenants, setTenants] = useState<any[]>([]);
  const [selectedTenant, setSelectedTenant] = useState("");
  const [subjectPerf, setSubjectPerf] = useState<Record<string, any>>({});
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      authFetch("/api/v1/analytics/overview").then(r => r.json()),
      authFetch("/api/v1/tenant/list").then(r => r.json()),
      authFetch("/api/v1/analytics/school-leaderboard").then(r => r.json())
    ]).then(([ov, ten, lb]) => {
      setOverview(ov);
      const tenList = Array.isArray(ten) ? ten : [];
      setTenants(tenList);
      if (tenList.length > 0) setSelectedTenant(tenList[0].id);
      setLeaderboard(Array.isArray(lb) ? lb : []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedTenant) return;
    authFetch(`/api/v1/analytics/subject-performance/${selectedTenant}`)
      .then(r => r.json()).then(data => setSubjectPerf(data || {})).catch(() => {});
  }, [selectedTenant]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    );
  }

  const statCards = [
    { label: "Schools", value: overview?.total_schools ?? 0, icon: School, color: "text-brand-600", bg: "bg-brand-500/10" },
    { label: "Students", value: overview?.total_students ?? 0, icon: Users, color: "text-purple-600", bg: "bg-purple-500/10" },
    { label: "Grading Runs", value: overview?.total_batches ?? 0, icon: BookOpen, color: "text-sky-600", bg: "bg-sky-500/10" },
    { label: "Exams Graded", value: overview?.total_graded ?? 0, icon: Award, color: "text-emerald-600", bg: "bg-emerald-500/10" },
    { label: "Platform Avg Score", value: `${overview?.average_score ?? 0}%`, icon: TrendingUp, color: "text-amber-600", bg: "bg-amber-500/10" },
    { label: "Needs Review", value: overview?.needs_review_count ?? 0, icon: AlertCircle, color: "text-red-500", bg: "bg-red-500/10" },
  ];

  return (
    <div className="flex-1 bg-surface-soft/30 text-foreground p-8 overflow-y-auto font-outfit">
      <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

        <div className="flex items-center gap-3 border-b border-border-main pb-4">
          <BarChart3 className="w-6 h-6 text-brand-600" />
          <div>
            <h2 className="text-xl font-bold tracking-tight">Analytics Dashboard</h2>
            <p className="text-xs text-foreground/60 mt-0.5">Platform-wide grading insights and performance metrics</p>
          </div>
        </div>

        {/* KPI Stat Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {statCards.map(({ label, value, icon: Icon, color, bg }) => (
            <div key={label} className="bg-surface border border-border-main p-5 flex items-center gap-4 shadow-none">
              <div className={`${bg} p-3 rounded-none`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <div>
                <p className="text-2xl font-black text-foreground leading-none">{value}</p>
                <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/50 mt-1">{label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* School Ranking Leaderboard */}
        <div className="bg-surface border border-border-main shadow-none overflow-hidden font-outfit">
          <div className="px-6 py-4 border-b border-border-main bg-surface-soft/50 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-amber-500" />
              <div>
                <h3 className="text-sm font-extrabold text-foreground uppercase tracking-wider">Institutional Academic Standings</h3>
                <p className="text-[10px] text-foreground/50 font-medium mt-0.5">Comparative school rankings based on mean scores, pass rates, and script volume</p>
              </div>
            </div>
            <span className="text-[10px] font-mono text-foreground/50 uppercase font-extrabold bg-surface border border-border-main px-2 py-1">
              {leaderboard.length} Institutions Evaluated
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse font-outfit">
              <thead>
                <tr className="border-b border-border-main/50 bg-surface-soft/30 text-foreground/50 font-bold uppercase tracking-wider">
                  <th className="px-6 py-3.5 w-16">Rank</th>
                  <th className="px-6 py-3.5">Institution / School Name</th>
                  <th className="px-6 py-3.5">School Code</th>
                  <th className="px-6 py-3.5">Evaluated Scripts</th>
                  <th className="px-6 py-3.5">Pass Rate (&ge;50%)</th>
                  <th className="px-6 py-3.5">Peak Score</th>
                  <th className="px-6 py-3.5 text-right">Institutional Mean</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-main/50">
                {leaderboard.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-xs text-foreground/40 italic">
                      No institutional data recorded yet. Complete an assessment batch in the Grading Hub to compute standings.
                    </td>
                  </tr>
                ) : (
                  leaderboard.map((item) => (
                    <tr key={item.tenant_id} className="hover:bg-surface-soft/20 transition-colors group">
                      <td className="px-6 py-4 font-black">
                        {item.rank === 1 ? (
                          <span className="bg-amber-500/20 text-amber-600 border border-amber-500/40 px-2 py-0.5 rounded-none text-[10px] font-black inline-flex items-center gap-1">
                            <Trophy className="w-3 h-3 text-amber-500" /> Rank 1
                          </span>
                        ) : item.rank === 2 ? (
                          <span className="bg-slate-300/30 text-slate-700 border border-slate-400/40 px-2 py-0.5 rounded-none text-[10px] font-black inline-flex items-center gap-1">
                            <Award className="w-3 h-3 text-slate-500" /> Rank 2
                          </span>
                        ) : item.rank === 3 ? (
                          <span className="bg-amber-700/20 text-amber-800 border border-amber-700/40 px-2 py-0.5 rounded-none text-[10px] font-black inline-flex items-center gap-1">
                            <Award className="w-3 h-3 text-amber-700" /> Rank 3
                          </span>
                        ) : (
                          <span className="text-foreground/50 font-mono">Rank #{item.rank}</span>
                        )}
                      </td>
                      <td className="px-6 py-4 font-bold text-foreground">{item.school_name}</td>
                      <td className="px-6 py-4 font-mono text-foreground/60">{item.school_code || "—"}</td>
                      <td className="px-6 py-4 font-semibold text-foreground/80">{item.total_graded} scripts</td>
                      <td className="px-6 py-4 font-bold text-emerald-600">{item.pass_rate}%</td>
                      <td className="px-6 py-4 font-bold text-purple-600">{item.highest_score} pts</td>
                      <td className="px-6 py-4 text-right">
                        <span className="text-sm font-black text-brand-600 bg-brand-500/10 px-2.5 py-1 border border-brand-500/20">
                          {item.average_score}%
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Subject Performance Bar Chart */}
        <div className="bg-surface border border-border-main shadow-none">
          <div className="px-6 py-4 border-b border-border-main bg-surface-soft/50 flex justify-between items-center">
            <h3 className="text-sm font-bold text-foreground">Subject Performance by School</h3>
            <select
              value={selectedTenant}
              onChange={e => setSelectedTenant(e.target.value)}
              className="text-xs border border-border-main rounded-none p-2 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer"
            >
              {tenants.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div className="p-6">
            {Object.keys(subjectPerf).length === 0 ? (
              <p className="text-xs text-foreground/40 italic text-center py-8">No graded results yet for this school. Complete a grading batch to see subject averages.</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(subjectPerf).sort(([,a]: any, [,b]: any) => b.average - a.average).map(([subject, data]: [string, any]) => (
                  <div key={subject} className="flex items-center gap-4">
                    <span className="w-28 text-xs font-bold text-foreground/70 truncate shrink-0">{subject}</span>
                    <div className="flex-1 bg-surface-soft border border-border-main h-6 relative overflow-hidden">
                      <div
                        className="h-full bg-brand-500 transition-all duration-700"
                        style={{ width: `${(data.average / 100) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-black text-brand-700 w-12 text-right">{data.average}%</span>
                    <span className="text-[10px] text-foreground/40 w-14 text-right">{data.count} students</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Batch Completion Rate */}
        {overview && (
          <div className="bg-surface border border-border-main p-6 shadow-none">
            <h3 className="text-xs font-bold uppercase tracking-widest text-foreground/60 mb-4">Batch Completion Rate</h3>
            <div className="flex items-center gap-4">
              <div className="flex-1 bg-surface-soft border border-border-main h-4 relative overflow-hidden">
                <div
                  className="h-full bg-emerald-500 transition-all duration-700"
                  style={{ width: overview.total_batches > 0 ? `${(overview.completed_batches / overview.total_batches) * 100}%` : '0%' }}
                />
              </div>
              <span className="text-xs font-black text-emerald-600">
                {overview.completed_batches}/{overview.total_batches} Completed
              </span>
            </div>
            <p className="text-[10px] text-foreground/40 mt-2">{overview.needs_review_count} results still need manual identity resolution</p>
          </div>
        )}

      </div>
    </div>
  );
}
