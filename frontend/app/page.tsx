"use client";

import { useState, useEffect } from "react";
import {
  Database, Plus, Users, Layers, CheckCircle2, BarChart3, School, BookOpen, Calendar
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import RosterView from "./components/RosterView";
import GradebookView from "./components/GradebookView";
import AssessmentView from "./components/AssessmentView";
import AnalyticsView from "./components/AnalyticsView";
import SchoolOnboardingView from "./components/SchoolOnboardingView";
import SettingsView from "./components/SettingsView";
import { Settings } from "lucide-react";
import { authFetch } from "./lib/utils";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

type Page = "onboarding" | "roster" | "assessment" | "gradebook" | "analytics" | "settings";

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
            { key: "analytics", label: "Insights", Icon: BarChart3 },
            { key: "roster", label: "Class Rosters", Icon: Users },
            { key: "settings", label: "Settings", Icon: Settings },
          ] as const).map(({ key, label, Icon }) => (
            <button
              key={key}
              onClick={() => setCurrentPage(key)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-none font-extrabold text-xs transition-all cursor-pointer border",
                currentPage === key 
                  ? "bg-brand-800 text-white border-brand-700 shadow-none" 
                  : "bg-transparent text-foreground/70 border-transparent hover:text-foreground hover:bg-surface-soft"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};

export default function Home() {
  const [currentPage, setCurrentPage] = useState<Page>("assessment");
  const [theme, setTheme] = useState<'burgundy' | 'midnight' | 'emerald' | 'royal'>('burgundy');
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('small');

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
      } catch (e) {}
    };

    loadGlobalContext();
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
      } catch (e) {}
    };
    fetchGroups();
  }, [activeTenantId]);

  return (
    <div className="h-screen overflow-hidden flex flex-col transition-colors duration-500">
      <Header
        theme={theme}
        setTheme={setTheme}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
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

      <main className="flex-1 overflow-hidden flex flex-col relative">
        {currentPage === "onboarding" ? (
          <SchoolOnboardingView theme={theme} setActiveTab={setCurrentPage} />
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
          <GradebookView theme={theme} />
        )}
      </main>
    </div>
  );
}
