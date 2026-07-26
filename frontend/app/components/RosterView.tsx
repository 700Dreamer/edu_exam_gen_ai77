"use client";

import { useState, useEffect } from "react";
import { Users, Loader2, Trash2, Download } from "lucide-react";
import { authFetch } from "../lib/utils";

export default function RosterView({ theme }: { theme: string }) {
  const [tenants, setTenants] = useState<any[]>([]);
  const [groups, setGroups] = useState<any[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [selectedTenant, setSelectedTenant] = useState("");
  const [selectedGroup, setSelectedGroup] = useState("");
  const [newStudentName, setNewStudentName] = useState("");
  const [newStudentIndex, setNewStudentIndex] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const [newGroupLevel, setNewGroupLevel] = useState("S.1");
  const [newGroupStream, setNewGroupStream] = useState("");
  const [isAddingGroup, setIsAddingGroup] = useState(false);
  const [showAddGroupModal, setShowAddGroupModal] = useState(false);

  const handleAddGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTenant || !newGroupStream.trim()) return;
    setIsAddingGroup(true);
    try {
      const res = await authFetch(`/api/v1/tenant/${selectedTenant}/groups`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          level: newGroupLevel,
          stream: newGroupStream.trim()
        })
      });
      if (res.ok) {
        const newG = await res.json();
        setGroups(prev => [...prev, newG]);
        setSelectedGroup(newG.id);
        setNewGroupStream("");
        setShowAddGroupModal(false);
      } else {
        alert("Failed to add class stream.");
      }
    } catch(e) {
      alert("Network error.");
    } finally {
      setIsAddingGroup(false);
    }
  };

  useEffect(() => {
    authFetch("/api/v1/tenant/list")
      .then(res => res.json())
      .then(data => {
        const list = Array.isArray(data) ? data : [];
        setTenants(list);
        if (list.length > 0) setSelectedTenant(list[0].id);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedTenant) {
      authFetch(`/api/v1/tenant/${selectedTenant}/groups`)
        .then(res => res.json())
        .then(data => {
          const list = Array.isArray(data) ? data : [];
          setGroups(list);
          if (list.length > 0) {
            setSelectedGroup(list[0].id);
          } else {
            setSelectedGroup("");
            setStudents([]);
          }
        })
        .catch(() => {});
    }
  }, [selectedTenant]);

  useEffect(() => {
    if (selectedGroup) {
      authFetch(`/api/v1/academic-group/${selectedGroup}/students`)
        .then(res => res.json())
        .then(data => setStudents(data))
        .catch(() => {});
    } else {
      setStudents([]);
    }
  }, [selectedGroup]);

  const handleAddStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGroup || !newStudentName.trim()) return;
    setIsAdding(true);
    try {
      const res = await authFetch(`/api/v1/academic-group/${selectedGroup}/students`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: newStudentName.trim(),
          index_number: newStudentIndex.trim() || null
        })
      });
      if (res.ok) {
        const student = await res.json();
        setStudents(prev => [...prev, student].sort((a, b) => a.full_name.localeCompare(b.full_name)));
        setNewStudentName("");
        setNewStudentIndex("");
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(errData.detail || "Failed to add student. Ensure index number is unique.");
      }
    } catch (e) {
      alert("Network error.");
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="flex-1 bg-surface-soft/30 text-foreground p-8 overflow-y-auto font-outfit">
      <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="flex items-center gap-3 border-b border-border-main pb-4">
          <Users className="w-6 h-6 text-brand-600" />
          <div>
            <h2 className="text-xl font-bold tracking-tight">Roster Manager</h2>
            <p className="text-xs text-foreground/60 mt-0.5">Manage students, classes, and index mappings</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Tenant Selector */}
          <div className="bg-surface border border-border-main rounded-none p-5 shadow-none space-y-4">
            <label className="text-xs font-bold uppercase tracking-widest text-foreground/50 block">Select School</label>
            <select
              value={selectedTenant}
              onChange={(e) => setSelectedTenant(e.target.value)}
              className="w-full text-sm border border-border-main rounded-none p-3 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer"
            >
              {tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>

          {/* Academic Group Selector */}
          <div className="bg-surface border border-border-main rounded-none p-5 shadow-none space-y-4">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold uppercase tracking-widest text-foreground/50 block">Class Stream</label>
              <button
                type="button"
                onClick={() => setShowAddGroupModal(prev => !prev)}
                className="text-[10px] font-bold text-brand-600 hover:text-brand-700 uppercase tracking-wider cursor-pointer"
              >
                {showAddGroupModal ? "Cancel" : "+ Add Class"}
              </button>
            </div>

            {showAddGroupModal ? (
              <form onSubmit={handleAddGroup} className="space-y-3 pt-1 border-t border-border-main">
                <div>
                  <label className="text-[10px] uppercase font-bold text-foreground/50 block mb-1">Academic Level</label>
                  <select
                    value={newGroupLevel}
                    onChange={(e) => setNewGroupLevel(e.target.value)}
                    className="w-full text-xs border border-border-main p-2 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer"
                  >
                    {["P.1", "P.2", "P.3", "P.4", "P.5", "P.6", "P.7", "S.1", "S.2", "S.3", "S.4", "S.5", "S.6"].map(l => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] uppercase font-bold text-foreground/50 block mb-1">Stream Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Blue, North, Science"
                    value={newGroupStream}
                    onChange={(e) => setNewGroupStream(e.target.value)}
                    className="w-full text-xs border border-border-main p-2 bg-surface text-foreground outline-none"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isAddingGroup}
                  className="w-full py-2 bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  {isAddingGroup ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Save Class Stream"}
                </button>
              </form>
            ) : groups.length === 0 ? (
              <p className="text-xs text-foreground/40 italic py-2">No groups created yet. Click '+ Add Class' above.</p>
            ) : (
              <select
                value={selectedGroup}
                onChange={(e) => setSelectedGroup(e.target.value)}
                className="w-full text-sm border border-border-main rounded-none p-3 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer"
              >
                {groups.map(g => <option key={g.id} value={g.id}>{g.level} - {g.stream}</option>)}
              </select>
            )}
          </div>

          {/* Quick Add Student */}
          <div className="bg-surface border border-border-main rounded-none p-5 shadow-none">
            <label className="text-xs font-bold uppercase tracking-widest text-foreground/50 block mb-4">Add Student</label>
            <form onSubmit={handleAddStudent} className="space-y-4">
              <input
                type="text"
                required
                placeholder="Full Name"
                value={newStudentName}
                onChange={(e) => setNewStudentName(e.target.value)}
                className="w-full text-xs border border-border-main rounded-none p-3 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none"
              />
              <div className="space-y-1">
                <input
                  type="text"
                  placeholder="System Index (Auto-Generated e.g. STU-2026-0001)"
                  value={newStudentIndex}
                  onChange={(e) => setNewStudentIndex(e.target.value)}
                  className="w-full text-xs border border-border-main rounded-none p-3 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none"
                />
                <p className="text-[10px] text-brand-600 font-bold uppercase tracking-wider">System-generated e.g. STU-2026-0001 auto-assigned if empty.</p>
              </div>
              <button
                type="submit"
                disabled={isAdding || !selectedGroup}
                className="w-full py-2.5 bg-brand-600 text-white text-xs font-bold rounded-none hover:bg-brand-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-none"
              >
                {isAdding && <Loader2 className="w-3 h-3 animate-spin" />}
                Add Student
              </button>
            </form>
          </div>
        </div>

        {/* Student Table */}
        <div className="bg-surface border border-border-main rounded-none shadow-none overflow-hidden">
          <div className="px-6 py-4 border-b border-border-main bg-surface-soft/50 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-bold text-foreground">Enrolled Students</h3>
              <span className="text-xs font-black bg-brand-500/10 text-brand-600 px-3 py-1 rounded-none">{students.length} Total</span>
            </div>
            {selectedGroup && students.length > 0 && (
              <button
                onClick={handleExportRosterCSV}
                className="px-3.5 py-1.5 bg-emerald-600 text-white text-xs font-bold rounded-none hover:bg-emerald-700 transition-all cursor-pointer flex items-center gap-1.5 shadow-none"
                title="Export class roster to CSV file"
              >
                <Download className="w-3.5 h-3.5" /> Export Roster CSV
              </button>
            )}
          </div>
          {students.length === 0 ? (
            <div className="p-8 text-center text-xs text-foreground/40 italic">No students registered in this class.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-border-main/50 bg-surface-soft/30 text-foreground/50 font-bold uppercase tracking-wider">
                    <th className="px-6 py-3">No.</th>
                    <th className="px-6 py-3">Full Name</th>
                    <th className="px-6 py-3">Index Number</th>
                    <th className="px-6 py-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-main/50">
                  {students.map((student, idx) => (
                    <tr key={student.id} className="hover:bg-surface-soft/20 transition-colors group">
                      <td className="px-6 py-4 font-mono text-foreground/40">{idx + 1}</td>
                      <td className="px-6 py-4 font-bold text-foreground">{student.full_name}</td>
                      <td className="px-6 py-4 font-mono text-foreground/60">{student.index_number || "—"}</td>
                      <td className="px-6 py-4">
                        <button
                          onClick={async () => {
                            if (!confirm(`Remove ${student.full_name} from roster?`)) return;
                            try {
                              const res = await authFetch(`/api/v1/students/${student.id}`, { method: "DELETE" });
                              if (res.ok) setStudents(prev => prev.filter(s => s.id !== student.id));
                              else alert("Failed to delete student.");
                            } catch { alert("Network error."); }
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 text-red-500 hover:bg-red-50 rounded-none cursor-pointer"
                          title="Remove student"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
