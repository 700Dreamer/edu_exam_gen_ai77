"use client";

import { useEffect, useState } from "react";
import { Activity, ArrowUpRight, CheckCheck, ChevronDown, RefreshCw } from "lucide-react";
import { cn, formatTimeAgo } from "../lib/utils";

export type RunStatusFilter = "all" | "queued" | "processing" | "completed";
export type RunSortOrder = "newest" | "oldest" | "subject";
export type RunLiveMode = "off" | "auto" | "30s";

const COLLAPSE_KEY = "edulytics-run-panel-collapsed";
const MAX_ACTIVE_ROWS = 3;

type SegmentOption<T extends string> = { value: T; label: string; count?: number };

function Segmented<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
}: {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  ariaLabel: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className="flex gap-0.5 p-1 bg-surface-soft/80 backdrop-blur-md rounded-[6px] border border-border-main/50"
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt.value)}
            className={cn(
              "flex-1 min-w-0 px-1.5 py-1.5 text-[11px] rounded-[5px] transition-all cursor-pointer flex items-center justify-center gap-1 whitespace-nowrap",
              active
                ? "bg-surface text-foreground font-semibold shadow-xs border border-border-main/60"
                : "text-foreground/55 hover:text-foreground/90 font-medium border border-transparent"
            )}
          >
            <span>{opt.label}</span>
            {typeof opt.count === "number" && (
              <span className={cn("text-[10px] tabular-nums", active ? "text-foreground/75" : "text-foreground/40")}>
                {opt.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

function StatusDot({ tone, pulse }: { tone: "active" | "queued" | "idle"; pulse?: boolean }) {
  const color = tone === "active" ? "bg-amber-500" : tone === "queued" ? "bg-sky-500" : "bg-foreground/30";
  return (
    <span className="relative flex w-2 h-2 shrink-0">
      {pulse && <span className={cn("absolute inline-flex h-full w-full rounded-full opacity-60 animate-ping", color)} />}
      <span className={cn("relative inline-flex w-2 h-2 rounded-full", color)} />
    </span>
  );
}

export default function GradingRunsControlPanel({
  batches,
  openedBatchIds,
  statusFilter,
  onStatusFilterChange,
  sortOrder,
  onSortOrderChange,
  liveMode,
  onLiveModeChange,
  lastSyncedAt,
  isRefreshing,
  onRefresh,
  onMarkAllReviewed,
  onOpenRun,
}: {
  batches: any[];
  openedBatchIds: Set<string>;
  statusFilter: RunStatusFilter;
  onStatusFilterChange: (value: RunStatusFilter) => void;
  sortOrder: RunSortOrder;
  onSortOrderChange: (value: RunSortOrder) => void;
  liveMode: RunLiveMode;
  onLiveModeChange: (value: RunLiveMode) => void;
  lastSyncedAt: Date | null;
  isRefreshing: boolean;
  onRefresh: () => void;
  onMarkAllReviewed: () => void;
  onOpenRun: (batch: any) => void;
}) {
  // null until resolved on the client, avoids a hydration flash
  const [collapsed, setCollapsed] = useState<boolean | null>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(COLLAPSE_KEY);
      if (saved !== null) {
        setCollapsed(saved === "1");
        return;
      }
    } catch {}
    // Start minimized on narrower screens so the panel never covers the table
    setCollapsed(!window.matchMedia("(min-width: 1536px)").matches);
  }, []);

  const toggleCollapsed = (next: boolean) => {
    setCollapsed(next);
    try {
      localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
    } catch {}
  };

  if (collapsed === null) return null;

  const queuedCount = batches.filter((b) => b.status === "Queued").length;
  const processingCount = batches.filter((b) => b.status === "Processing").length;
  const completedCount = batches.filter((b) => b.status === "Completed").length;
  const unreviewedCount = batches.filter((b) => b.status === "Completed" && !openedBatchIds.has(b.id)).length;

  const activeRuns = batches
    .filter((b) => b.status === "Processing" || b.status === "Queued")
    .sort((a, b) => {
      // Processing first, then newest
      if (a.status !== b.status) return a.status === "Processing" ? -1 : 1;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

  const syncDescription =
    liveMode === "off"
      ? "Live sync is off. Use refresh to update."
      : liveMode === "30s"
        ? "Refreshing every 30 seconds."
        : activeRuns.length > 0
          ? "Refreshing every 10 seconds while runs are active."
          : "Idle. Resumes when a run is queued.";

  if (collapsed) {
    return (
      <button
        type="button"
        onClick={() => toggleCollapsed(false)}
        className="fixed bottom-6 left-6 z-40 flex items-center gap-2.5 pl-3 pr-3.5 py-2 rounded-[8px] bg-surface/85 backdrop-blur-xl text-foreground border border-border-main/80 shadow-[0_12px_32px_-8px_rgba(0,0,0,0.15),0_0_0_1px_rgba(255,255,255,0.4)_inset] hover:bg-surface/95 transition-all cursor-pointer font-outfit animate-in fade-in slide-in-from-bottom-2 duration-300"
        title="Open run control"
        aria-label="Open run control panel"
      >
        <StatusDot tone={processingCount > 0 ? "active" : queuedCount > 0 ? "queued" : "idle"} pulse={activeRuns.length > 0} />
        <span className="text-[10px] font-bold tracking-[0.18em] uppercase text-foreground/75">Run Control</span>
        {activeRuns.length > 0 && (
          <span className="text-[10px] tabular-nums font-semibold text-brand-600 bg-brand-500/10 px-1.5 py-0.5 rounded-[4px]">{activeRuns.length} active</span>
        )}
      </button>
    );
  }

  return (
    <aside
      aria-label="Grading runs control panel"
      className="fixed bottom-6 left-6 z-40 w-[292px] rounded-[10px] bg-surface/85 backdrop-blur-2xl text-foreground border border-border-main/80 shadow-[0_20px_45px_-12px_rgba(0,0,0,0.18),0_0_0_1px_rgba(255,255,255,0.4)_inset] font-outfit animate-in fade-in slide-in-from-bottom-2 duration-300 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-3.5 pb-2.5 border-b border-border-main/60 bg-surface-soft/40 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-foreground/50" />
          <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-foreground/60">Run Control</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-1.5 rounded-[5px] text-foreground/50 hover:text-foreground hover:bg-surface-soft border border-transparent hover:border-border-main/50 transition-all cursor-pointer disabled:opacity-50"
            title="Sync now"
            aria-label="Sync now"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin")} />
          </button>
          <button
            type="button"
            onClick={() => toggleCollapsed(true)}
            className="p-1.5 rounded-[5px] text-foreground/50 hover:text-foreground hover:bg-surface-soft border border-transparent hover:border-border-main/50 transition-all cursor-pointer"
            title="Minimize"
            aria-label="Minimize run control panel"
          >
            <ChevronDown className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="px-4 py-3.5 space-y-3.5">
        {/* Status filter */}
        <section>
          <p className="text-[11px] font-semibold tracking-wide uppercase text-foreground/55 mb-1.5">Status</p>
          <Segmented<RunStatusFilter>
            ariaLabel="Filter runs by status"
            value={statusFilter}
            onChange={onStatusFilterChange}
            options={[
              { value: "all", label: "All", count: batches.length },
              { value: "queued", label: "Queued", count: queuedCount },
              { value: "processing", label: "Running", count: processingCount },
              { value: "completed", label: "Done", count: completedCount },
            ]}
          />
        </section>

        {/* Sort order */}
        <section>
          <p className="text-[11px] font-semibold tracking-wide uppercase text-foreground/55 mb-1.5">Sort</p>
          <Segmented<RunSortOrder>
            ariaLabel="Sort runs"
            value={sortOrder}
            onChange={onSortOrderChange}
            options={[
              { value: "newest", label: "Newest" },
              { value: "oldest", label: "Oldest" },
              { value: "subject", label: "Subject" },
            ]}
          />
        </section>

        {/* Live sync */}
        <section>
          <p className="text-[11px] font-semibold tracking-wide uppercase text-foreground/55 mb-1.5">Live sync</p>
          <Segmented<RunLiveMode>
            ariaLabel="Live sync mode"
            value={liveMode}
            onChange={onLiveModeChange}
            options={[
              { value: "off", label: "Off" },
              { value: "auto", label: "Auto" },
              { value: "30s", label: "30s" },
            ]}
          />
          <p className="text-[10px] text-foreground/45 mt-1.5 leading-relaxed">{syncDescription}</p>
        </section>

        {/* Active pipeline */}
        <section>
          <div className="flex items-center justify-between mb-1.5">
            <p className="text-[11px] font-semibold tracking-wide uppercase text-foreground/55">Active pipeline</p>
            <span className="text-[10px] tabular-nums font-mono text-foreground/45">{activeRuns.length} in flight</span>
          </div>
          {activeRuns.length === 0 ? (
            <div className="px-3 py-2.5 bg-surface-soft/60 backdrop-blur-xs rounded-[6px] border border-border-main/40 text-[11px] text-foreground/50">
              No runs queued or processing.
            </div>
          ) : (
            <ul className="bg-surface-soft/60 backdrop-blur-xs rounded-[6px] border border-border-main/50 divide-y divide-border-main/40 overflow-hidden">
              {activeRuns.slice(0, MAX_ACTIVE_ROWS).map((run) => {
                const isProcessing = run.status === "Processing";
                return (
                  <li key={run.id}>
                    <button
                      type="button"
                      onClick={() => onOpenRun(run)}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-surface-soft/90 transition-colors cursor-pointer group"
                      title="Open run"
                    >
                      <StatusDot tone={isProcessing ? "active" : "queued"} pulse={isProcessing} />
                      <span className="flex-1 min-w-0">
                        <span className="block text-[11px] font-semibold text-foreground truncate">
                          {run.subject} &middot; {run.level} {run.stream}
                        </span>
                        <span className="block text-[10px] text-foreground/50 truncate font-mono">
                          {isProcessing ? "Grading" : "Queued"} &middot; started {formatTimeAgo(run.created_at)}
                        </span>
                      </span>
                      <ArrowUpRight className="w-3 h-3 text-foreground/30 group-hover:text-foreground transition-colors shrink-0" />
                    </button>
                  </li>
                );
              })}
              {activeRuns.length > MAX_ACTIVE_ROWS && (
                <li className="px-3 py-1.5 text-[10px] text-foreground/50 bg-surface-soft/30">
                  +{activeRuns.length - MAX_ACTIVE_ROWS} more in the table
                </li>
              )}
            </ul>
          )}
        </section>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border-main/60 bg-surface-soft/30 backdrop-blur-sm flex items-center justify-between gap-2">
        <span className="text-[10px] font-mono text-foreground/45 truncate">
          Synced {lastSyncedAt ? formatTimeAgo(lastSyncedAt) : "never"}
        </span>
        <button
          type="button"
          onClick={onMarkAllReviewed}
          disabled={unreviewedCount === 0}
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] font-medium rounded-[5px] bg-surface hover:bg-surface-soft border border-border-main/60 text-foreground/80 hover:text-foreground transition-all cursor-pointer disabled:opacity-40 disabled:cursor-default disabled:hover:bg-surface shadow-2xs shrink-0"
          title="Clear the new-result markers on all completed runs"
        >
          <CheckCheck className="w-3.5 h-3.5 text-brand-600" />
          {unreviewedCount > 0 ? `Mark ${unreviewedCount} reviewed` : "All reviewed"}
        </button>
      </div>
    </aside>
  );
}
