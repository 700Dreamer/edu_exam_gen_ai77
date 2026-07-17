"use client";

import { useState, useEffect } from "react";
import {
  Database, Plus, Users, Layers, CheckCircle2, BarChart3
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import RosterView from "./components/RosterView";
import GradebookView from "./components/GradebookView";
import AssessmentView from "./components/AssessmentView";
import AnalyticsView from "./components/AnalyticsView";
import SchoolOnboardingView from "./components/SchoolOnboardingView";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

type Page = "onboarding" | "roster" | "assessment" | "gradebook" | "analytics";

const Header = ({ theme, setTheme, currentPage, setCurrentPage }: any) => {
  return (
    <header className="bg-surface border-b border-border-main text-foreground px-8 py-2 shadow-none flex justify-between items-center sticky top-0 z-50 transition-colors duration-500 font-outfit">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3 group px-4 py-2 hover:bg-foreground/5 rounded-none transition-all cursor-default">
          <div className="bg-brand-500/10 border border-brand-500/20 p-2 rounded-none backdrop-blur-md relative overflow-hidden">
             <Database className="w-6 h-6 text-brand-500 relative z-10" />
             <div className="absolute inset-0 bg-brand-500/20 animate-pulse"></div>
          </div>
          <div>
             <h1 className="text-xl font-black tracking-widest leading-none">EDULYTICS</h1>
             <p className="text-[9px] tracking-[0.3em] font-bold mt-1 uppercase text-brand-500 opacity-80">Tenant Setup &amp; Assessment</p>
          </div>
        </div>
        <div className="flex gap-2 border-l border-border-main pl-6 items-center">
          {([
            { key: "onboarding", label: "Tenant Setup", Icon: Plus },
            { key: "roster", label: "Roster Manager", Icon: Users },
            { key: "assessment", label: "Grading Pipeline", Icon: Layers },
            { key: "gradebook", label: "Gradebook", Icon: CheckCircle2 },
            { key: "analytics", label: "Analytics", Icon: BarChart3 },
          ] as const).map(({ key, label, Icon }) => (
            <button
              key={key}
              onClick={() => setCurrentPage(key)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-none font-bold text-xs transition-all cursor-pointer",
                currentPage === key ? "bg-brand-800 text-white shadow-none" : "bg-transparent text-foreground opacity-50 hover:text-brand-800 hover:opacity-100"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-4">
        {/* Theme Toggle */}
        <div className="flex gap-1.5 items-center">
          <span className="text-[10px] font-bold uppercase tracking-wider text-foreground/40 mr-1">Theme</span>
          {(['burgundy', 'midnight', 'emerald', 'royal'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTheme(t)}
              title={t}
              className={cn(
                "w-5 h-5 rounded-none border-2 transition-all cursor-pointer",
                theme === t ? "scale-125 border-foreground" : "border-transparent opacity-60 hover:opacity-100 hover:scale-110",
                t === 'burgundy' ? 'bg-[#8B1A3A]' : t === 'midnight' ? 'bg-[#1A237E]' : t === 'emerald' ? 'bg-[#1B5E20]' : 'bg-[#4A148C]'
              )}
            />
          ))}
        </div>
      </div>
    </header>
  );
};

export default function Home() {
  const [currentPage, setCurrentPage] = useState<Page>("onboarding");
  const [theme, setTheme] = useState<'burgundy' | 'midnight' | 'emerald' | 'royal'>('burgundy');

  useEffect(() => {
    const saved = localStorage.getItem('edulytics-theme') as any;
    if (saved && ['burgundy', 'midnight', 'emerald', 'royal'].includes(saved)) {
      setTheme(saved);
    }
  }, []);

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('edulytics-theme', theme);
  }, [theme]);

  return (
    <div className="h-screen overflow-hidden flex flex-col transition-colors duration-500">
      <Header
        theme={theme}
        setTheme={setTheme}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
      />

      <main className="flex-1 overflow-hidden flex flex-col relative">
        {currentPage === "onboarding" ? (
          <SchoolOnboardingView theme={theme} setActiveTab={setCurrentPage} />
        ) : currentPage === "roster" ? (
          <RosterView theme={theme} />
        ) : currentPage === "assessment" ? (
          <AssessmentView theme={theme} />
        ) : currentPage === "analytics" ? (
          <AnalyticsView theme={theme} />
        ) : (
          <GradebookView theme={theme} />
        )}
      </main>
    </div>
  );
}
