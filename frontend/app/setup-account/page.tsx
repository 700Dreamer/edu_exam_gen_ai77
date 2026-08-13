"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { CheckCircle2, Lock, ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { cn, authFetch } from "../lib/utils";

function SetupForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const router = useRouter();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isVerifying, setIsVerifying] = useState(true);
  const [invalidReason, setInvalidReason] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const checkToken = async () => {
      if (!token) {
        setInvalidReason("Invalid or missing invitation token.");
        setIsVerifying(false);
        return;
      }
      try {
        const res = await authFetch(`/api/v1/auth/verify-invite/${token}`);
        if (!res.ok) {
          const data = await res.json();
          setInvalidReason(data.detail || "This invitation link is invalid or has expired.");
        }
      } catch (e) {
        setInvalidReason("Failed to verify invitation link.");
      } finally {
        setIsVerifying(false);
      }
    };
    checkToken();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!token) {
      setError("Invalid or missing invitation token.");
      return;
    }
    
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setIsLoading(true);
    
    try {
      const res = await authFetch("/api/v1/auth/register-via-invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password })
      });
      
      if (res.ok) {
        setSuccess(true);
        setTimeout(() => {
          router.push("/login");
        }, 2000);
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to setup account.");
      }
    } catch (e) {
      setError("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isVerifying) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600 mb-3" />
        <p className="text-sm font-medium text-foreground/70">Verifying invitation link...</p>
      </div>
    );
  }

  if (invalidReason) {
    return (
      <div className="p-6 border border-red-500/30 bg-red-500/5 flex flex-col items-center justify-center text-center">
        <AlertCircle className="w-10 h-10 text-red-500 mb-3" />
        <h2 className="text-lg font-black text-red-600 mb-1">Invitation Link Expired</h2>
        <p className="text-sm text-foreground/70 mt-1 mb-4 leading-relaxed">{invalidReason}</p>
        <p className="text-xs text-foreground/50">Please contact your system administrator to generate a new invitation link.</p>
      </div>
    );
  }

  if (success) {
    return (
      <div className="p-8 border border-emerald-500/30 bg-emerald-500/5 flex flex-col items-center justify-center text-center animate-in zoom-in-95 duration-500">
        <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mb-4">
          <CheckCircle2 className="w-8 h-8 text-emerald-600" />
        </div>
        <h2 className="text-2xl font-black text-emerald-700 mb-2">Account Created!</h2>
        <p className="text-sm text-foreground/70">Your staff account is ready. Redirecting to login...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 border border-red-500/30 bg-red-500/10 text-red-600 text-sm font-bold flex items-center gap-2">
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      )}

      <div>
        <label className="text-xs font-bold uppercase tracking-widest text-foreground/60 mb-2 block">Create a Secure Password</label>
        <div className="relative">
          <Lock className="w-5 h-5 text-foreground/40 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input 
            type="password" 
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-surface-soft border border-border-main p-4 pl-12 text-sm outline-none focus:ring-1 focus:ring-brand-500 rounded-none transition-all"
            placeholder="Min. 8 characters"
          />
        </div>
      </div>
      
      <div>
        <label className="text-xs font-bold uppercase tracking-widest text-foreground/60 mb-2 block">Confirm Password</label>
        <div className="relative">
          <Lock className="w-5 h-5 text-foreground/40 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input 
            type="password" 
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full bg-surface-soft border border-border-main p-4 pl-12 text-sm outline-none focus:ring-1 focus:ring-brand-500 rounded-none transition-all"
            placeholder="Retype password"
          />
        </div>
      </div>

      <button 
        type="submit" 
        disabled={isLoading}
        className="w-full py-4 bg-brand-600 text-white font-bold text-sm uppercase tracking-wider hover:bg-brand-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2 rounded-none"
      >
        {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Complete Setup"} 
        {!isLoading && <ArrowRight className="w-4 h-4" />}
      </button>
    </form>
  );
}

export default function SetupAccountPage() {
  return (
    <div className="min-h-screen bg-surface-soft flex items-center justify-center p-4 font-outfit">
      <div className="w-full max-w-md bg-surface border border-border-main p-8 shadow-2xl relative overflow-hidden">
        
        {/* Aesthetic accents */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand-500 to-brand-300"></div>
        <div className="absolute -top-16 -right-16 w-32 h-32 bg-brand-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="mb-8 relative z-10">
          <h1 className="text-2xl font-black tracking-tight mb-2">Welcome Aboard</h1>
          <p className="text-sm text-foreground/60">Set a password to complete your staff account setup. This link is single-use.</p>
        </div>

        <div className="relative z-10">
          <Suspense fallback={<div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-brand-600" /></div>}>
            <SetupForm />
          </Suspense>
        </div>
        
      </div>
    </div>
  );
}
