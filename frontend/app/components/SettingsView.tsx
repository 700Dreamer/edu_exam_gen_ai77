"use client";

import { useState, useEffect } from "react";
import {
  Settings, Type, Palette, Check, RotateCcw, LogOut, ShieldAlert,
  Trash2, AlertTriangle, X, Loader2, CheckCircle2
} from "lucide-react";
import { cn, authFetch } from "../lib/utils";

interface SettingsViewProps {
  theme: string;
  setTheme: (t: 'burgundy' | 'midnight' | 'emerald' | 'royal') => void;
  fontSize: 'small' | 'medium' | 'large';
  setFontSize: (s: 'small' | 'medium' | 'large') => void;
  tenants?: { id: string; name: string }[];
  activeTenantId?: string;
  setActiveTenantId?: (id: string) => void;
  onTenantsUpdated?: () => void | Promise<void>;
}

export default function SettingsView({
  theme,
  setTheme,
  fontSize,
  setFontSize,
  tenants = [],
  activeTenantId,
  setActiveTenantId,
  onTenantsUpdated
}: SettingsViewProps) {
  const [userRole, setUserRole] = useState<string | null>(null);

  // School deletion states
  const [selectedSchoolId, setSelectedSchoolId] = useState<string>(activeTenantId || "");
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [confirmInput, setConfirmInput] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deletionError, setDeletionError] = useState<string | null>(null);
  const [deletionSuccess, setDeletionSuccess] = useState<{
    schoolName: string;
    classes: number;
    students: number;
    batches: number;
    results: number;
    s3Files: number;
  } | null>(null);

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const res = await authFetch("/api/v1/auth/me");
        if (res.ok) {
          const data = await res.json();
          setUserRole(data.role);
        }
      } catch (e) {
        console.error("Failed to fetch user role");
      }
    };
    fetchMe();
  }, []);

  // Synchronize selectedSchoolId if tenants or activeTenantId changes
  useEffect(() => {
    if (activeTenantId && tenants.some(t => t.id === activeTenantId)) {
      setSelectedSchoolId(activeTenantId);
    } else if (tenants.length > 0 && !tenants.some(t => t.id === selectedSchoolId)) {
      setSelectedSchoolId(tenants[0].id);
    }
  }, [activeTenantId, tenants]);

  const selectedSchool = tenants.find(t => t.id === selectedSchoolId) || null;

  const handleDeleteSchool = async () => {
    if (!selectedSchoolId || !selectedSchool) return;
    setIsDeleting(true);
    setDeletionError(null);

    try {
      const res = await authFetch(`/api/v1/tenant/${selectedSchoolId}`, {
        method: "DELETE"
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to delete school.");
      }

      const result = await res.json();
      setDeletionSuccess({
        schoolName: result.school_name || selectedSchool.name,
        classes: result.summary?.classes_deleted || 0,
        students: result.summary?.students_deleted || 0,
        batches: result.summary?.batches_deleted || 0,
        results: result.summary?.results_deleted || 0,
        s3Files: result.summary?.s3_objects_purged || 0
      });

      setIsDeleteModalOpen(false);
      setConfirmInput("");

      if (onTenantsUpdated) {
        await onTenantsUpdated();
      }
    } catch (err: any) {
      setDeletionError(err.message || "An unexpected error occurred during deletion.");
    } finally {
      setIsDeleting(false);
    }
  };

  const fontOptions = [
    {
      key: "small",
      label: "Small (Current Size / 1x)",
      scaleText: "100% Base Scale",
      description: "Standard ultra-dense UI font scaling for maximum screen space utilization."
    },
    {
      key: "medium",
      label: "Medium (Legible / 2x)",
      scaleText: "125% Medium Scale",
      description: "Comfortable enhanced typography scale for easier reading during long grading sessions."
    },
    {
      key: "large",
      label: "Large (High Visibility / 4x)",
      scaleText: "150% High-Contrast Scale",
      description: "Maximum accessibility typography scale for projector presentations and large displays."
    }
  ] as const;

  const themes = [
    { key: "burgundy", name: "Burgundy Classic", bg: "#8B1A3A" },
    { key: "midnight", name: "Midnight Cyber", bg: "#1A237E" },
    { key: "emerald", name: "Emerald Academic", bg: "#1B5E20" },
    { key: "royal", name: "Royal Purple", bg: "#4A148C" }
  ] as const;

  return (
    <div className="flex-1 p-8 overflow-y-auto font-outfit custom-scrollbar bg-background text-foreground">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="border-b border-border-main pb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-brand-500/10 border border-brand-500/30 text-brand-600">
              <Settings className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-black uppercase tracking-wider text-foreground">Studio Settings &amp; Preferences</h1>
              <p className="text-xs text-foreground/60 mt-0.5 font-medium">Configure global typography accessibility scaling, themes, and display settings.</p>
            </div>
          </div>
        </div>

        {/* Font Size & Typography Scaling Card */}
        <div className="bg-surface border border-border-main p-6 space-y-6">
          <div className="flex items-center gap-2 border-b border-border-main/60 pb-3">
            <Type className="w-5 h-5 text-brand-500" />
            <h2 className="text-sm font-extrabold uppercase tracking-wider text-foreground">Typography &amp; Font Size Scaling</h2>
          </div>

          <p className="text-xs text-foreground/70 leading-relaxed font-medium">
            Select your preferred font scaling. Changes take effect instantly across all Edulytics views and persist in your browser settings.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {fontOptions.map(opt => {
              const isSelected = fontSize === opt.key;
              return (
                <div
                  key={opt.key}
                  onClick={() => setFontSize(opt.key as any)}
                  className={cn(
                    "border p-5 cursor-pointer transition-all flex flex-col justify-between group relative",
                    isSelected
                      ? "border-brand-600 bg-brand-500/10 shadow-sm"
                      : "border-border-main hover:border-brand-500/50 bg-surface-soft/40"
                  )}
                >
                  {isSelected && (
                    <div className="absolute top-3 right-3 bg-brand-600 text-white p-1">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                  )}

                  <div className="space-y-2">
                    <span className="text-[10px] font-black uppercase tracking-widest text-brand-600 bg-brand-500/15 px-2 py-0.5 border border-brand-500/20 inline-block">
                      {opt.scaleText}
                    </span>
                    <h3 className="text-sm font-bold text-foreground group-hover:text-brand-600 transition-colors">
                      {opt.label}
                    </h3>
                    <p className="text-xs text-foreground/60 font-medium leading-relaxed">
                      {opt.description}
                    </p>
                  </div>

                  {/* Live Text Sample */}
                  <div className="mt-4 pt-3 border-t border-border-main/40">
                    <span className="text-[10px] font-bold text-foreground/40 uppercase block mb-1">Preview Sample</span>
                    <p className={cn(
                      "font-semibold text-foreground border border-dashed border-border-main p-2 bg-surface",
                      opt.key === 'small' ? "text-xs" : opt.key === 'medium' ? "text-sm font-bold" : "text-base font-extrabold"
                    )}>
                      Student Exam Grade: 88% PASS
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Theme & Color Palette Card */}
        <div className="bg-surface border border-border-main p-6 space-y-6">
          <div className="flex items-center gap-2 border-b border-border-main/60 pb-3">
            <Palette className="w-5 h-5 text-brand-500" />
            <h2 className="text-sm font-extrabold uppercase tracking-wider text-foreground">Appearance Theme Palette</h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {themes.map(t => {
              const isSelected = theme === t.key;
              return (
                <div
                  key={t.key}
                  onClick={() => setTheme(t.key as any)}
                  className={cn(
                    "border p-4 cursor-pointer transition-all flex items-center gap-3 group",
                    isSelected
                      ? "border-brand-600 bg-brand-500/10"
                      : "border-border-main hover:border-brand-500/40 bg-surface-soft/20"
                  )}
                >
                  <div 
                    className="w-6 h-6 border border-foreground/20 shrink-0" 
                    style={{ backgroundColor: t.bg }} 
                  />
                  <div>
                    <h4 className="text-xs font-bold text-foreground">{t.name}</h4>
                    {isSelected && <span className="text-[9px] font-black uppercase text-brand-600">Active</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Account & Access Card */}
        <div className="bg-surface border border-border-main p-6 space-y-6">
          <div className="flex items-center gap-2 border-b border-border-main/60 pb-3">
            <LogOut className="w-5 h-5 text-brand-500" />
            <h2 className="text-sm font-extrabold uppercase tracking-wider text-foreground">Account &amp; Access</h2>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={() => {
                if (typeof window !== "undefined") {
                  window.dispatchEvent(new Event("edulytics_logout"));
                }
              }}
              className="flex items-center gap-2 px-6 py-2.5 bg-red-600/10 text-red-600 border border-red-600/20 text-xs font-bold uppercase tracking-wider hover:bg-red-600 hover:text-white transition-all cursor-pointer"
            >
              <LogOut className="w-4 h-4" /> Sign Out
            </button>

            {userRole === "master" && (
              <a
                href="/master-dashboard"
                className="flex items-center gap-2 px-6 py-2.5 bg-brand-600/10 text-brand-600 border border-brand-600/20 text-xs font-bold uppercase tracking-wider hover:bg-brand-600 hover:text-white transition-all"
              >
                <ShieldAlert className="w-4 h-4" /> Master Console
              </a>
            )}
          </div>
        </div>

        {/* Danger Zone: School Deletion Card */}
        <div className="bg-surface border border-red-500/30 p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-border-main/60 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-red-500/10 text-red-500 border border-red-500/20">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-extrabold uppercase tracking-wider text-red-500">
                  Danger Zone - Institution Deletion
                </h2>
                <p className="text-[11px] text-foreground/50 font-normal">
                  Permanently erase a school and all associated data, classes, rosters, exams, and cloud files.
                </p>
              </div>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-widest text-red-500 bg-red-500/10 border border-red-500/20 px-2 py-0.5">
              Irreversible
            </span>
          </div>

          {deletionSuccess && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 space-y-1 text-xs">
              <div className="flex items-center gap-2 font-bold text-emerald-300">
                <CheckCircle2 className="w-4 h-4" />
                <span>School Deleted Successfully</span>
              </div>
              <p className="text-[11px] text-emerald-400/90 leading-relaxed font-mono">
                "{deletionSuccess.schoolName}" was completely wiped: {deletionSuccess.classes} classes, {deletionSuccess.students} students, {deletionSuccess.batches} exam batches, {deletionSuccess.results} student results, and {deletionSuccess.s3Files} cloud storage files purged.
              </p>
            </div>
          )}

          {tenants.length === 0 ? (
            <p className="text-xs text-foreground/60 italic">
              No registered schools found in the system.
            </p>
          ) : (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold uppercase tracking-wide text-foreground/80 block">
                  Select School To Remove:
                </label>
                <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
                  <select
                    value={selectedSchoolId}
                    onChange={(e) => {
                      setSelectedSchoolId(e.target.value);
                      setDeletionSuccess(null);
                    }}
                    className="flex-1 bg-background border border-border-main px-3 py-2 text-xs font-medium text-foreground focus:outline-none focus:border-red-500"
                  >
                    {tenants.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} ({t.id.slice(0, 8)}...)
                      </option>
                    ))}
                  </select>

                  <button
                    type="button"
                    onClick={() => {
                      setConfirmInput("");
                      setDeletionError(null);
                      setIsDeleteModalOpen(true);
                    }}
                    disabled={!selectedSchool}
                    className="flex items-center justify-center gap-2 px-5 py-2 bg-red-600/10 text-red-500 border border-red-500/30 text-xs font-bold uppercase tracking-wider hover:bg-red-600 hover:text-white transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete School &amp; Data
                  </button>
                </div>
              </div>

              <div className="p-3 bg-foreground/[0.02] border border-border-main/60 space-y-2 text-xs text-foreground/70">
                <span className="text-[10px] uppercase font-bold tracking-wider text-foreground/40 block">
                  Deletion Scope Includes:
                </span>
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[11px] text-foreground/60 list-disc list-inside">
                  <li>School registry entry &amp; settings</li>
                  <li>All classes, streams, and academic groups</li>
                  <li>Student roster records &amp; profiles</li>
                  <li>Assessment batches &amp; master blueprints</li>
                  <li>Student marks, scores, and AI evaluations</li>
                  <li>All S3 cloud storage files and exam scans</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Reset Preferences Button */}
        <div className="flex justify-end pt-4">
          <button
            onClick={() => {
              setFontSize('small');
              setTheme('burgundy');
            }}
            className="flex items-center gap-2 px-4 py-2 border border-border-main text-xs font-bold uppercase tracking-wider text-foreground/70 hover:text-foreground hover:bg-surface-soft transition-all cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset Default Settings
          </button>
        </div>
      </div>

      {/* Confirmation Modal */}
      {isDeleteModalOpen && selectedSchool && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-surface border border-red-500/40 shadow-2xl max-w-md w-full p-6 space-y-5 animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-500/10 border border-red-500/30 text-red-500">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-extrabold uppercase tracking-wider text-red-500">
                    Confirm School Deletion
                  </h3>
                  <p className="text-[11px] text-foreground/60">
                    This action cannot be undone.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => !isDeleting && setIsDeleteModalOpen(false)}
                disabled={isDeleting}
                className="text-foreground/40 hover:text-foreground cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Warning Message */}
            <div className="p-3 bg-red-500/10 border border-red-500/20 text-xs text-red-300 space-y-1.5 leading-relaxed">
              <p className="font-bold">You are about to permanently wipe:</p>
              <div className="font-mono text-sm font-black text-white bg-red-950/40 p-2 border border-red-500/30">
                {selectedSchool.name}
              </div>
              <p className="text-[11px] text-red-300/80">
                All classes, students, exam results, worker tasks, and cloud storage images will be permanently erased.
              </p>
            </div>

            {/* Error display */}
            {deletionError && (
              <div className="p-2.5 bg-red-500/20 border border-red-500/40 text-red-200 text-xs">
                {deletionError}
              </div>
            )}

            {/* Confirmation Input Field */}
            <div className="space-y-2">
              <label className="text-xs text-foreground/80 block leading-tight font-medium">
                To confirm, type <span className="font-mono font-bold text-red-400">DELETE</span> or the school name below:
              </label>
              <input
                type="text"
                value={confirmInput}
                onChange={(e) => setConfirmInput(e.target.value)}
                placeholder='Type "DELETE" to confirm'
                disabled={isDeleting}
                className="w-full bg-background border border-border-main text-foreground px-3 py-2 text-xs font-mono focus:outline-none focus:border-red-500"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setIsDeleteModalOpen(false)}
                disabled={isDeleting}
                className="px-4 py-2 border border-border-main text-xs font-medium text-foreground/70 hover:text-foreground hover:bg-surface-soft transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteSchool}
                disabled={isDeleting || (confirmInput.trim() !== "DELETE" && confirmInput.trim().toLowerCase() !== selectedSchool.name.trim().toLowerCase())}
                className="flex items-center gap-2 px-5 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-bold uppercase tracking-wider transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Deleting &amp; Purging...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    Permanently Delete School
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
