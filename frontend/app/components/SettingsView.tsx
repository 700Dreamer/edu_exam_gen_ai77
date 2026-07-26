"use client";

import { useState } from "react";
import { Settings, Type, Palette, Check, RotateCcw } from "lucide-react";
import { cn } from "../lib/utils";

export default function SettingsView({
  theme,
  setTheme,
  fontSize,
  setFontSize
}: {
  theme: string;
  setTheme: (t: 'burgundy' | 'midnight' | 'emerald' | 'royal') => void;
  fontSize: 'small' | 'medium' | 'large';
  setFontSize: (s: 'small' | 'medium' | 'large') => void;
}) {
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
            Select your preferred font scaling. Changes take effect instantly across all Edulytics OS views and persist in your browser settings.
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
    </div>
  );
}
