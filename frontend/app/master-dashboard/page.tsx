"use client";

import { useState, useEffect } from "react";
import { Users, Link as LinkIcon, Trash2, Activity, Copy, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { cn, authFetch } from "../lib/utils";
import { useRouter } from "next/navigation";

export default function MasterDashboard() {
  const [activeTab, setActiveTab] = useState<"invite" | "manage" | "logs">("invite");
  const [email, setEmail] = useState("");
  const [generatedLink, setGeneratedLink] = useState("");
  const [copied, setCopied] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const [users, setUsers] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const router = useRouter();

  const [isAuthorized, setIsAuthorized] = useState(false);

  // Authentication & Event Listener
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("edulytics_token");
      if (!token) {
        router.push("/login");
        return;
      }
      try {
        const res = await authFetch("/api/v1/auth/me");
        if (res.ok) {
          const data = await res.json();
          if (data.role === "master") {
            setIsAuthorized(true);
          } else {
            // Logged in, but not master. Kick to regular dashboard.
            router.push("/");
          }
        } else {
          router.push("/login");
        }
      } catch (e) {
        router.push("/login");
      }
    };
    
    // Check on mount
    checkAuth();

    // Listen for global logout events (triggered by 401s in authFetch)
    const handleLogout = () => router.push("/login");
    window.addEventListener("edulytics_logout", handleLogout);
    
    return () => {
      window.removeEventListener("edulytics_logout", handleLogout);
    };
  }, [router]);

  const fetchUsers = async () => {
    try {
      const res = await authFetch("/api/v1/master/users");
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await authFetch("/api/v1/master/audit-logs");
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (activeTab === "manage") fetchUsers();
    if (activeTab === "logs") fetchLogs();
  }, [activeTab]);

  const handleGenerateInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setIsLoading(true);
    try {
      const res = await authFetch("/api/v1/master/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      if (res.ok) {
        const data = await res.json();
        const link = `${window.location.origin}/setup-account?token=${data.token}`;
        setGeneratedLink(link);
      } else {
        alert("Failed to generate invite.");
      }
    } catch (e) {
      alert("Network error.");
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm("Are you sure you want to delete this user?")) return;
    try {
      const res = await authFetch(`/api/v1/master/users/${userId}`, { method: "DELETE" });
      if (res.ok) {
        fetchUsers();
      } else {
        alert("Failed to delete user.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-surface-soft flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
      </div>
    );
  }



  return (
    <div className="flex min-h-screen bg-surface-soft text-foreground font-outfit">
      
      {/* Sidebar */}
      <div className="w-64 bg-surface border-r border-border-main flex flex-col shadow-none">
        <div className="p-6 border-b border-border-main">
          <h1 className="text-lg font-black tracking-tight flex items-center gap-2">
            <div className="w-6 h-6 bg-brand-600 text-white flex items-center justify-center rounded-none text-xs font-bold">M</div>
            Master Console
          </h1>
        </div>
        
        <div className="flex-1 p-4 space-y-2">
          <button 
            onClick={() => setActiveTab("invite")}
            className={cn("w-full flex items-center gap-3 px-4 py-3 text-sm font-bold transition-all rounded-none", activeTab === "invite" ? "bg-brand-500/10 text-brand-600 border-l-4 border-brand-600" : "text-foreground/60 hover:bg-surface-soft hover:text-foreground border-l-4 border-transparent")}
          >
            <LinkIcon className="w-4 h-4" /> Invite Staff
          </button>
          
          <button 
            onClick={() => setActiveTab("manage")}
            className={cn("w-full flex items-center gap-3 px-4 py-3 text-sm font-bold transition-all rounded-none", activeTab === "manage" ? "bg-brand-500/10 text-brand-600 border-l-4 border-brand-600" : "text-foreground/60 hover:bg-surface-soft hover:text-foreground border-l-4 border-transparent")}
          >
            <Users className="w-4 h-4" /> Manage Staff
          </button>
          
          <button 
            onClick={() => setActiveTab("logs")}
            className={cn("w-full flex items-center gap-3 px-4 py-3 text-sm font-bold transition-all rounded-none", activeTab === "logs" ? "bg-brand-500/10 text-brand-600 border-l-4 border-brand-600" : "text-foreground/60 hover:bg-surface-soft hover:text-foreground border-l-4 border-transparent")}
          >
            <Activity className="w-4 h-4" /> System Logs
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-10 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          
          {activeTab === "invite" && (
            <div className="animate-in fade-in duration-300">
              <h2 className="text-2xl font-black mb-2">Invite New Staff</h2>
              <p className="text-foreground/60 mb-8 text-sm">Generate a secure, single-use registration link valid for 1 hour.</p>
              
              <div className="bg-surface border border-border-main p-6 shadow-none">
                <form onSubmit={handleGenerateInvite} className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="text-xs font-bold uppercase tracking-widest text-foreground/60 mb-2 block">Staff Email Address</label>
                    <input 
                      type="email" 
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="teacher@school.edu"
                      className="w-full bg-surface-soft border border-border-main p-3 text-sm outline-none focus:ring-1 focus:ring-brand-500 rounded-none"
                    />
                  </div>
                  <button 
                    type="submit" 
                    disabled={isLoading}
                    className="px-6 py-3 bg-brand-600 text-white font-bold text-sm uppercase tracking-wider hover:bg-brand-700 transition-colors flex items-center gap-2 rounded-none"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LinkIcon className="w-4 h-4" />}
                    Generate Link
                  </button>
                </form>

                {generatedLink && (
                  <div className="mt-8 p-4 border border-emerald-500/30 bg-emerald-500/5 flex flex-col gap-3">
                    <div className="flex items-center gap-2 text-emerald-600 font-bold text-sm">
                      <CheckCircle2 className="w-4 h-4" /> Link Generated Successfully
                    </div>
                    <div className="flex gap-2">
                      <input 
                        type="text" 
                        readOnly 
                        value={generatedLink} 
                        className="flex-1 bg-surface border border-border-main p-2.5 text-sm text-foreground/80 font-mono outline-none rounded-none"
                      />
                      <button 
                        onClick={copyToClipboard}
                        className="px-4 py-2.5 bg-foreground text-surface font-bold text-sm hover:bg-foreground/80 transition-colors flex items-center gap-2 rounded-none"
                      >
                        {copied ? "Copied!" : <><Copy className="w-4 h-4" /> Copy</>}
                      </button>
                    </div>
                    <p className="text-xs text-foreground/50">This link will expire in exactly 1 hour. It can only be used once.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "manage" && (
            <div className="animate-in fade-in duration-300">
              <h2 className="text-2xl font-black mb-2">Staff Directory</h2>
              <p className="text-foreground/60 mb-8 text-sm">Manage all registered staff accounts.</p>
              
              <div className="bg-surface border border-border-main overflow-hidden shadow-none">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-surface-soft/50 border-b border-border-main text-foreground/60 uppercase tracking-wider text-xs font-bold">
                      <th className="p-4">Email</th>
                      <th className="p-4">Status</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-main/50">
                    {users.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="p-8 text-center text-foreground/50 text-sm">No staff accounts found.</td>
                      </tr>
                    ) : users.map(u => (
                      <tr key={u.id} className="hover:bg-surface-soft/30 transition-colors">
                        <td className="p-4 font-medium">{u.email}</td>
                        <td className="p-4">
                          <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-600 text-xs font-bold rounded-full">Active</span>
                        </td>
                        <td className="p-4 text-right">
                          <button 
                            onClick={() => handleDeleteUser(u.id)}
                            className="p-2 text-red-500/70 hover:text-red-600 hover:bg-red-50 transition-colors rounded-none"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "logs" && (
            <div className="animate-in fade-in duration-300">
              <h2 className="text-2xl font-black mb-2">System Audit Logs</h2>
              <p className="text-foreground/60 mb-8 text-sm">Recent security and administrative events.</p>
              
              <div className="bg-surface border border-border-main overflow-hidden shadow-none">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-surface-soft/50 border-b border-border-main text-foreground/60 uppercase tracking-wider text-xs font-bold">
                      <th className="p-4">Timestamp</th>
                      <th className="p-4">Action</th>
                      <th className="p-4">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-main/50">
                    {logs.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="p-8 text-center text-foreground/50 text-sm">No logs found.</td>
                      </tr>
                    ) : logs.map(l => (
                      <tr key={l.id} className="hover:bg-surface-soft/30 transition-colors">
                        <td className="p-4 text-xs font-mono text-foreground/60">{new Date(l.timestamp).toLocaleString()}</td>
                        <td className="p-4">
                          <span className="px-2 py-1 bg-foreground/5 font-mono text-xs font-bold rounded-sm border border-border-main uppercase">{l.action}</span>
                        </td>
                        <td className="p-4 text-xs font-mono break-all text-foreground/80">
                          {JSON.stringify(l.details)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
