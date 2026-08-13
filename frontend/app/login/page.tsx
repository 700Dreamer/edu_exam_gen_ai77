"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { API_BASE } from "../lib/utils";
import Vortex from "../../components/originkit/ui/tornado";
import { motion, AnimatePresence } from "framer-motion";

const formVariants = {
  enter: (direction: "forward" | "back") => ({
    x: direction === "forward" ? 40 : -40,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: "forward" | "back") => ({
    x: direction === "forward" ? -40 : 40,
    opacity: 0,
  }),
};

export default function LoginPage() {
  const [step, setStep] = useState(0); // 0 = email, 1 = password
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [animDir, setAnimDir] = useState<"forward" | "back">("forward");

  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("edulytics_token");
    if (token) {
      router.push("/");
    } else {
      setIsCheckingAuth(false);
    }
  }, [router]);

  useEffect(() => {
    if (step === 0 && !isCheckingAuth) emailRef.current?.focus();
    if (step === 1 && !isCheckingAuth) passwordRef.current?.focus();
  }, [step, isCheckingAuth]);

  const isValidEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const goToStep = (target: number) => {
    if (target === 1) {
      if (!isValidEmail(email)) {
        setError("Please enter a valid email address.");
        return;
      }
    }
    setError(null);
    setAnimDir(target > step ? "forward" : "back");
    setStep(target);
  };

  const handleEmailNext = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    goToStep(1);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await fetch(`${API_BASE}/api/v1/auth/jwt/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("edulytics_token", data.access_token);
        router.push("/");
      } else {
        const errData = await res.json();
        setError(errData.detail || "Invalid credentials.");
      }
    } catch {
      setError("Network error. Could not connect to server.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isCheckingAuth) return null;

  return (
    <div className="min-h-screen bg-black flex flex-col items-start justify-center p-4 pl-16 font-outfit relative select-none">
      {/* Vortex background */}
      <div className="absolute inset-0 z-0 opacity-80 pointer-events-none">
        <Vortex background="black" />
      </div>

      {/* Card */}
      <div className="w-full max-w-sm relative z-10 flex flex-col items-center gap-6 ml-[8%]">

        {/* Brand mark */}
        <div className="text-white/30 text-[10px] tracking-[0.4em] uppercase font-bold mb-2">
          Edulytics &mdash; Restricted Access
        </div>

        {/* Form card */}
        <div className="w-full bg-[#660033] shadow-2xl overflow-hidden relative">
          {/* Top accent line */}
          <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-white/30 to-transparent" />

          <div className="p-8">
            {/* Error banner */}
            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mb-5 flex items-center gap-2 text-red-300 text-xs font-bold bg-red-500/10 border border-red-500/20 px-3 py-2"
                >
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Step label */}
            <p className="text-white/40 text-[10px] uppercase tracking-[0.3em] font-bold mb-3">
              {step === 0 ? "Identify yourself" : "Verify access"}
            </p>

            <AnimatePresence mode="wait" custom={animDir}>
              {/* Step 0 — Email */}
              {step === 0 && (
                <motion.form
                  key="email-step"
                  custom={animDir}
                  variants={formVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  onSubmit={handleEmailNext}
                >
                  <div className="flex items-stretch gap-0">
                    <input
                      ref={emailRef}
                      type="email"
                      required
                      autoComplete="email"
                      placeholder="your@email.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="flex-1 bg-transparent border-b-2 border-white/20 focus:border-white/60 text-white placeholder-white/25 text-base font-medium py-2 pr-4 outline-none transition-all duration-300 min-w-0"
                    />
                    <button
                      type="submit"
                      disabled={!email.trim()}
                      className="shrink-0 flex items-center gap-1.5 px-4 py-2 bg-white/10 hover:bg-white/20 disabled:opacity-30 text-white text-xs font-bold uppercase tracking-widest border-b-2 border-white/20 transition-all duration-200 cursor-pointer"
                    >
                      Password <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </motion.form>
              )}

              {/* Step 1 — Password */}
              {step === 1 && (
                <motion.form
                  key="password-step"
                  custom={animDir}
                  variants={formVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  onSubmit={handleLogin}
                >
                  <div className="flex items-stretch gap-0">
                    <input
                      ref={passwordRef}
                      type="password"
                      required
                      autoComplete="current-password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="flex-1 bg-transparent border-b-2 border-white/20 focus:border-white/60 text-white placeholder-white/25 text-base font-medium py-2 pr-4 outline-none transition-all duration-300 min-w-0"
                    />
                    <button
                      type="submit"
                      disabled={isLoading || !password.trim()}
                      className="shrink-0 flex items-center gap-1.5 px-4 py-2 bg-white/10 hover:bg-white/20 disabled:opacity-30 text-white text-xs font-bold uppercase tracking-widest border-b-2 border-white/20 transition-all duration-200 cursor-pointer"
                    >
                      {isLoading ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <>Proceed <ArrowRight className="w-3.5 h-3.5" /></>
                      )}
                    </button>
                  </div>
                </motion.form>
              )}
            </AnimatePresence>
          </div>

          {/* Bottom accent line */}
          <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        </div>

        {/* Dot stepper — outside the card */}
        <div className="w-full flex items-center justify-start gap-3 mt-2">
          {[0, 1].map((i) => (
            <button
              key={i}
              onClick={() => goToStep(i)}
              disabled={i === 1 && !email.trim()}
              aria-label={i === 0 ? "Email step" : "Password step"}
              className="group p-1 cursor-pointer disabled:cursor-not-allowed relative h-5 w-5 flex items-center justify-center"
            >
              <span className={`block rounded-full transition-all duration-300 ${step === i ? "w-5 h-[5px] bg-white" : "w-[5px] h-[5px] bg-white/25 group-hover:bg-white/50 group-disabled:group-hover:bg-white/25"}`} />
            </button>
          ))}
        </div>

      </div>
    </div>
  );
}
