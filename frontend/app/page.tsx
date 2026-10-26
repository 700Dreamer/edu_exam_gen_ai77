"use client";

import { useState, useEffect, Suspense, useCallback } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import {
  Database, Plus, Users, Layers, CheckCircle2, BarChart3, School, BookOpen, Calendar
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import RosterView from "./components/RosterView";
import GradebookView from "./components/GradebookView";
import AssessmentView from "./components/AssessmentView";
import AnalyticsView from "./components/AnalyticsView";
import ReportLabView from "./components/ReportLabView";
import SchoolOnboardingView from "./components/SchoolOnboardingView";
import SettingsView from "./components/SettingsView";
import { Settings, FileText, Sparkles, Clock, ArrowRight } from "lucide-react";
import { authFetch } from "./lib/utils";
import DotField from "@/components/DotField";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

type Page = "onboarding" | "roster" | "assessment" | "gradebook" | "reports" | "analytics" | "settings";

const Header = ({
  theme,
  setTheme,
  currentPage,
  setCurrentPage,
  tenants,
  activeTenantId,
  setActiveTenantId,
  groups,
  activeGroupId,
  setActiveGroupId,
  subjects,
  activeSubject,
  setActiveSubject,
  activeTerm,
  setActiveTerm,
  activeYear,
  setActiveYear
}: any) => {
  return (
    <header className="bg-surface border-b border-border-main text-foreground px-6 py-2.5 shadow-none flex flex-col md:flex-row justify-between items-center gap-3 sticky top-0 z-50 transition-colors duration-500 font-outfit">
      {/* Brand & Task Navigation */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-3 group px-3 py-1.5 hover:bg-foreground/5 rounded-none transition-all cursor-default">
          <div className="bg-brand-500/10 border border-brand-500/20 p-2 rounded-none backdrop-blur-md relative overflow-hidden">
            <Database className="w-5 h-5 text-brand-500 relative z-10" />
            <div className="absolute inset-0 bg-brand-500/20 animate-pulse"></div>
          </div>
          <div>
            <h1 className="text-lg font-black tracking-widest leading-none">EDULYTICS V2.4</h1>
            <p className="text-[8px] tracking-[0.25em] font-bold mt-1 uppercase text-brand-500 opacity-90">AI Grading &amp; Analytics</p>
          </div>
        </div>

        {/* Task Hubs */}
        <div className="flex gap-1.5 border-l border-border-main pl-4 items-center">
          {([
            { key: "onboarding", label: "Onboarding", Icon: Plus },
            { key: "assessment", label: "Grading", Icon: Layers },
            { key: "gradebook", label: "Results", Icon: CheckCircle2 },
            { key: "reports", label: "Report Lab", Icon: FileText, tag: "BETA" },
            { key: "analytics", label: "Insights", Icon: BarChart3 },
            { key: "roster", label: "Class Rosters", Icon: Users },
            { key: "settings", label: "Settings", Icon: Settings },
          ] as const).map(({ key, label, Icon, ...item }) => {
            const hasTag = "tag" in item && Boolean(item.tag);
            const tagText = hasTag ? (item as any).tag : null;

            return (
              <button
                key={key}
                onClick={() => setCurrentPage(key)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-[5px] font-medium text-xs transition-all cursor-pointer border relative",
                  currentPage === key
                    ? "bg-brand-800 text-white border-brand-700 shadow-none"
                    : "bg-transparent text-foreground/70 border-transparent hover:text-foreground hover:bg-surface-soft"
                )}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{label}</span>
                {tagText && (
                  <span
                    className={cn(
                      "text-[9px] font-semibold tracking-wider px-1.5 py-0.5 rounded-[3px] border leading-none transition-colors",
                      currentPage === key
                        ? "bg-white/15 text-white/90 border-white/20"
                        : "bg-foreground/[0.05] text-foreground/50 border-border-main"
                    )}
                  >
                    {tagText}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};

function HomeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const getInitialPage = (): Page => {
    if (!searchParams) return "assessment";
    if (searchParams.get("run") || searchParams.get("batch")) {
      return "gradebook";
    }
    const view = searchParams.get("view") || searchParams.get("tab");
    if (view === "results" || view === "gradebook") return "gradebook";
    if (view === "reports" || view === "report_lab") return "reports";
    if (view === "grading" || view === "assessment") return "assessment";
    if (view === "insights" || view === "analytics") return "analytics";
    if (view && ["onboarding", "roster", "settings"].includes(view)) {
      return view as Page;
    }
    return "assessment";
  };

  const [currentPage, setCurrentPage] = useState<Page>(getInitialPage);
  const [theme, setTheme] = useState<'burgundy' | 'midnight' | 'emerald' | 'royal'>('burgundy');
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('small');

  // Sync state if user clicks Browser Back/Forward
  useEffect(() => {
    if (!searchParams) return;
    const runParam = searchParams.get("run") || searchParams.get("batch");
    if (runParam && currentPage !== "gradebook") {
      setCurrentPage("gradebook");
      return;
    }
    const viewParam = searchParams.get("view") || searchParams.get("tab");
    let targetPage: Page | null = null;
    if (viewParam === "results" || viewParam === "gradebook") targetPage = "gradebook";
    else if (viewParam === "reports" || viewParam === "report_lab") targetPage = "reports";
    else if (viewParam === "grading" || viewParam === "assessment") targetPage = "assessment";
    else if (viewParam === "insights" || viewParam === "analytics") targetPage = "analytics";
    else if (viewParam && ["onboarding", "roster", "settings"].includes(viewParam)) targetPage = viewParam as Page;

    if (targetPage && targetPage !== currentPage) {
      setCurrentPage(targetPage);
    }
  }, [searchParams]);

  const handlePageChange = useCallback((newPage: Page) => {
    setCurrentPage(newPage);
    const params = new URLSearchParams(searchParams ? searchParams.toString() : "");
    params.set("view", newPage);
    if (newPage !== "gradebook") {
      params.delete("run");
      params.delete("batch");
      params.delete("student");
    }
    const qs = params.toString();
    const newUrl = qs ? `${pathname}?${qs}` : pathname;
    router.push(newUrl, { scroll: false });
  }, [searchParams, pathname, router]);

  // Global persistent academic context states
  const [tenants, setTenants] = useState<any[]>([]);
  const [activeTenantId, setActiveTenantId] = useState<string>("");
  const [groups, setGroups] = useState<any[]>([]);
  const [activeGroupId, setActiveGroupId] = useState<string>("");
  const [subjects, setSubjects] = useState<string[]>(["Physics", "Mathematics", "Biology", "Chemistry", "English"]);
  const [activeSubject, setActiveSubject] = useState<string>("Physics");
  const [activeTerm, setActiveTerm] = useState<string>("Term 1");
  const [activeYear, setActiveYear] = useState<number>(2026);

  useEffect(() => {
    const savedTheme = localStorage.getItem('edulytics-theme') as any;
    if (savedTheme && ['burgundy', 'midnight', 'emerald', 'royal'].includes(savedTheme)) {
      setTheme(savedTheme);
    }
    const savedFontSize = localStorage.getItem('edulytics-font-size') as any;
    if (savedFontSize && ['small', 'medium', 'large'].includes(savedFontSize)) {
      setFontSize(savedFontSize);
    }

    // Fetch initial tenants and groups
    const loadGlobalContext = async () => {
      const token = localStorage.getItem("edulytics_token");
      if (!token) {
        window.location.href = "/login";
        return;
      }
      try {
        const res = await authFetch("/api/v1/tenant/list");
        if (res.ok) {
          const data = await res.json();
          setTenants(data);
          if (data.length > 0) {
            const firstT = data[0].id;
            setActiveTenantId(firstT);

            // Load groups for first tenant
            const gRes = await authFetch(`/api/v1/tenant/${firstT}/groups`);
            if (gRes.ok) {
              const gData = await gRes.json();
              setGroups(gData);
              if (gData.length > 0) {
                setActiveGroupId(gData[0].id);
              }
            }
          }
        }
      } catch (e) { }
    };

    loadGlobalContext();

    const handleLogout = () => {
      window.location.href = "/login";
    };
    window.addEventListener("edulytics_logout", handleLogout);

    return () => {
      window.removeEventListener("edulytics_logout", handleLogout);
    };
  }, []);

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('edulytics-theme', theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute('data-font-size', fontSize);
    document.body.setAttribute('data-font-size', fontSize);
    localStorage.setItem('edulytics-font-size', fontSize);
  }, [fontSize]);

  // When active tenant changes, reload its groups
  useEffect(() => {
    if (!activeTenantId) return;
    const fetchGroups = async () => {
      try {
        const gRes = await authFetch(`/api/v1/tenant/${activeTenantId}/groups`);
        if (gRes.ok) {
          const gData = await gRes.json();
          setGroups(gData);
          if (gData.length > 0) {
            setActiveGroupId(gData[0].id);
          }
        }
      } catch (e) { }
    };
    fetchGroups();
  }, [activeTenantId]);

  return (
    <div className="h-screen overflow-hidden flex flex-col transition-colors duration-500 relative">
      {/* Base Background: DotField */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
        <DotField
          gradientFrom="#94a3b8"
          gradientTo="#94a3b8"
          dotRadius={1.2}
          dotSpacing={18}
          cursorRadius={240}
          bulgeStrength={0.6}
          glowRadius={70}
          pattern="grid"
          glowColor="#ffffff"
          gradientAngle={164}
          twist={-110}
          glowIntensity={0.8}
          baseOpacity={0.45}
          waveAmplitude={0}
          speed={1}
          sparkle={false}
          interactive={false}
          holdToZoom
          intro
          lightMode
        />
      </div>

      <Header
        theme={theme}
        setTheme={setTheme}
        currentPage={currentPage}
        setCurrentPage={handlePageChange}
        tenants={tenants}
        activeTenantId={activeTenantId}
        setActiveTenantId={setActiveTenantId}
        groups={groups}
        activeGroupId={activeGroupId}
        setActiveGroupId={setActiveGroupId}
        subjects={subjects}
        activeSubject={activeSubject}
        setActiveSubject={setActiveSubject}
        activeTerm={activeTerm}
        setActiveTerm={setActiveTerm}
        activeYear={activeYear}
        setActiveYear={setActiveYear}
      />

      <main className="flex-1 overflow-hidden flex flex-col relative z-10">
        {currentPage === "onboarding" ? (
          <SchoolOnboardingView theme={theme} setActiveTab={handlePageChange} />
        ) : currentPage === "roster" ? (
          <RosterView theme={theme} />
        ) : currentPage === "assessment" ? (
          <AssessmentView
            theme={theme}
            globalTenantId={activeTenantId}
            globalGroupId={activeGroupId}
            globalSubject={activeSubject}
            globalTerm={activeTerm}
            globalYear={activeYear}
          />
        ) : currentPage === "reports" ? (
          <div className="flex-1 overflow-hidden relative flex flex-col">
            {/* Subtle underlying preview with deep blur */}
            <div className="flex-1 overflow-hidden pointer-events-none filter blur-md select-none opacity-20">
              <ReportLabView theme={theme} />
            </div>

            {/* Apple-style Ultra-minimal Monochromatic Overlay */}
            <div className="absolute inset-0 z-30 bg-surface/80 backdrop-blur-xl flex items-center justify-center p-6 animate-in fade-in duration-300 font-outfit">
              <div className="max-w-xs w-full text-center space-y-6">
                {/* Monochromatic icon badge */}
                <div className="w-11 h-11 rounded-full bg-foreground/[0.04] border border-border-main flex items-center justify-center mx-auto text-foreground/70">
                  <FileText className="w-5 h-5 stroke-[1.5]" />
                </div>

                {/* Typography */}
                <div className="space-y-1.5">
                  <div className="text-[10px] font-semibold tracking-[0.2em] uppercase text-foreground/40">
                    Report Lab
                  </div>
                  <h2 className="text-xl font-medium tracking-tight text-foreground">
                    Coming Soon
                  </h2>
                  <p className="text-xs text-foreground/50 leading-relaxed font-normal pt-1">
                    Automated report cards, transcripts, and cross-subject analytics are on the way.
                  </p>
                </div>

                {/* Monochromatic Back Action */}
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => handlePageChange("gradebook")}
                    className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-foreground/80 hover:text-foreground bg-foreground/[0.04] hover:bg-foreground/[0.08] border border-border-main rounded-full transition-all cursor-pointer active:scale-95"
                  >
                    Return to Results
                    <ArrowRight className="w-3 h-3 text-foreground/40" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : currentPage === "analytics" ? (
          <AnalyticsView theme={theme} />
        ) : currentPage === "settings" ? (
          <SettingsView
            theme={theme}
            setTheme={setTheme}
            fontSize={fontSize}
            setFontSize={setFontSize}
          />
        ) : (
          <GradebookView
            theme={theme}
            onBatchActive={(batch: any) => {
              if (batch.tenant_id) setActiveTenantId(batch.tenant_id);
              if (batch.academic_group_id) setActiveGroupId(batch.academic_group_id);
              if (batch.subject) setActiveSubject(batch.subject);
            }}
          />
        )}
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="h-screen w-screen flex items-center justify-center bg-surface font-outfit text-foreground/40 text-xs">
        Loading Edulytics...
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}
