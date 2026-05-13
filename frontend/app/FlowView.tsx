"use client";

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  Handle,
  Position,
  applyEdgeChanges,
  applyNodeChanges,
  NodeProps,
  Edge,
  Node,
  OnConnect,
  OnNodesChange,
  OnEdgesChange,
  ReactFlowProvider,
  useReactFlow
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  Database,
  GitBranch,
  Sparkles,
  Brain,
  Layers,
  Activity,
  Play,
  ChevronRight,
  Filter,
  AlertCircle,
  Settings,
  X
} from 'lucide-react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ── CUSTOM NODES ──

const SourceNode = ({ data, id }: NodeProps) => (
  <div className="bg-surface border-2 border-brand-800/50 rounded-2xl p-4 shadow-xl min-w-[220px] transition-all duration-300 card-premium">
    <div className="flex items-center gap-2 mb-3 border-b border-border-main pb-2">
      <Database className="w-4 h-4 text-brand-800" />
      <span className="text-[10px] font-black uppercase tracking-widest text-foreground">Curriculum Source</span>
    </div>
    <div className="space-y-3">
      <div className="space-y-1">
        <label className="text-[7px] font-black opacity-50 uppercase tracking-widest">Subject Baseline</label>
        <select
          value={data.subject}
          onChange={(e) => data.onChange?.(id, { subject: e.target.value })}
          className="w-full bg-surface-soft border border-border-main rounded-md px-2 py-1.5 text-[10px] font-bold outline-none focus:border-brand-800 transition-all text-foreground"
        >
          {['Mathematics', 'Physics', 'English', 'Biology', 'Chemistry', 'Geography', 'History', 'CRS', 'ICT'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>
      <div className="space-y-1">
        <label className="text-[7px] font-black opacity-50 uppercase tracking-widest">Target Level</label>
        <select
          value={data.level}
          onChange={(e) => data.onChange?.(id, { level: e.target.value })}
          className="w-full bg-surface-soft border border-border-main rounded-md px-2 py-1.5 text-[10px] font-bold outline-none focus:border-brand-800 transition-all text-foreground"
        >
          {['Primary 1', 'Primary 2', 'Primary 3', 'Primary 4', 'Primary 5', 'Primary 6', 'Primary 7', 'Senior 1', 'Senior 2', 'Senior 3', 'Senior 4', 'Senior 5', 'Senior 6'].map(l => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 bg-brand-800 border-2 border-surface" />
  </div>
);

const TopicNode = ({ data, id }: NodeProps) => (
  <div className="bg-surface border-2 border-emerald-500/50 rounded-2xl p-4 shadow-xl min-w-[200px] transition-all duration-300 card-premium">
    <Handle type="target" position={Position.Left} className="w-2 h-2 bg-emerald-500" />
    <div className="flex items-center gap-2 mb-3 border-b border-border-main pb-2">
      <Filter className="w-4 h-4 text-emerald-500" />
      <span className="text-[10px] font-black uppercase tracking-widest text-foreground">Topic Selection</span>
    </div>
    <div className="space-y-2">
      <div className="max-h-[80px] overflow-y-auto space-y-1 pr-1 custom-scroll">
        {data.topics?.map((t: string) => (
          <div key={t} className="flex items-center justify-between px-2 py-1 bg-emerald-500/10 text-[9px] font-bold rounded border border-emerald-500/20 italic text-foreground/80">
            <span className="truncate max-w-[120px]">{t}</span>
            <button
              onClick={() => data.onChange?.(id, { topics: data.topics.filter((x: string) => x !== t) })}
              className="text-emerald-500 hover:text-rose-500 transition-colors"
            >
              <X className="w-2 h-2" />
            </button>
          </div>
        )) || <div className="text-[9px] opacity-40 italic">No topics...</div>}
      </div>
      <input
        type="text"
        placeholder="Add Topic..."
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            const val = (e.target as HTMLInputElement).value;
            if (val.trim()) {
              data.onChange?.(id, { topics: [...(data.topics || []), val.trim()] });
              (e.target as HTMLInputElement).value = '';
            }
          }
        }}
        className="w-full bg-surface-soft border border-border-main rounded-md px-2 py-1 text-[9px] font-bold outline-none focus:border-emerald-500 text-foreground"
      />
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 bg-emerald-500 border-2 border-surface" />
  </div>
);

const LogicNode = ({ data, id }: NodeProps) => (
  <div className="bg-surface border-2 border-amber-500/50 rounded-2xl p-4 shadow-xl min-w-[180px] transition-all duration-300 card-premium">
    <Handle type="target" position={Position.Left} className="w-2 h-2 bg-amber-500" />
    <div className="flex items-center gap-2 mb-3 border-b border-border-main pb-2">
      <Brain className="w-4 h-4 text-amber-500" />
      <span className="text-[10px] font-black uppercase tracking-widest text-foreground">Neural Tuning</span>
    </div>
    <div className="space-y-3">
      <div className="space-y-1">
        <label className="text-[7px] font-black opacity-50 uppercase tracking-widest">Cognitive Depth</label>
        <select
          value={data.bloom}
          onChange={(e) => data.onChange?.(id, { bloom: e.target.value })}
          className="w-full bg-surface-soft border border-border-main rounded-md px-2 py-1.5 text-[10px] font-bold outline-none focus:border-amber-500 transition-all text-foreground"
        >
          {['Recall', 'Comprehension', 'Application', 'Analysis', 'Synthesis', 'Evaluation'].map(b => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <label className="text-[7px] font-black opacity-50 uppercase tracking-widest">Neural Weight</label>
          <span className="text-[10px] font-black text-amber-600 dark:text-amber-400">{data.weight || 50}%</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          value={data.weight || 50}
          onChange={(e) => data.onChange?.(id, { weight: e.target.value })}
          className="w-full accent-amber-500 h-1 bg-surface-soft rounded-lg appearance-none cursor-pointer hover:accent-amber-400 transition-all"
        />
      </div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 bg-amber-500 border-2 border-surface" />
  </div>
);

const OutputNode = ({ data }: NodeProps) => (
  <div className="bg-brand-900 border-2 border-brand-500/50 rounded-2xl p-4 shadow-2xl min-w-[180px] text-white transition-all duration-300 neon-glow">
    <Handle type="target" position={Position.Left} className="w-2 h-2 bg-brand-500" />
    <div className="flex items-center gap-2 mb-3 border-b border-white/10 pb-2">
      <Sparkles className="w-4 h-4 text-brand-500" />
      <span className="text-[10px] font-black uppercase tracking-widest">Compiler</span>
    </div>
    <button
      onClick={() => data.onExecute()}
      disabled={data.isExecuting}
      className={cn(
        "w-full py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg active:scale-95",
        data.isExecuting && "opacity-50 cursor-not-allowed"
      )}
    >
      {data.isExecuting ? 'Synthesizing...' : 'Execute Flow'}
    </button>
  </div>
);

// ── MAIN VIEW ──

const nodeTypes = {
  source: SourceNode,
  topic: TopicNode,
  logic: LogicNode,
  output: OutputNode,
};

const initialNodes: Node[] = [
  { id: '1', type: 'source', position: { x: 50, y: 150 }, data: { subject: 'Mathematics', level: 'Primary 7' } },
  { id: '2', type: 'topic', position: { x: 350, y: 150 }, data: { topics: ['Algebra', 'Fractions', 'Sets'] } },
  { id: '3', type: 'logic', position: { x: 650, y: 150 }, data: { bloom: 'Application', weight: '70' } },
  { id: '4', type: 'output', position: { x: 900, y: 150 }, data: { onExecute: () => { }, isExecuting: false } },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e2-3', source: '2', target: '3', animated: true },
  { id: 'e3-4', source: '3', target: '4', animated: true },
];

function FlowViewInner({ theme, onBridge }: { theme: string, onBridge?: (t: string) => void }) {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);
  const [isExecuting, setIsExecuting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [output, setOutput] = useState<string[]>([]);

  const { getNodes, getEdges } = useReactFlow();

  // Fetch master syllabus for auto-sync
  const [masterSyllabus, setMasterSyllabus] = useState<any>(null);
  useEffect(() => {
    fetch("/api/syllabus/config")
      .then(res => res.json())
      .then(data => setMasterSyllabus(data.syllabus))
      .catch(e => console.error("Syllabus fetch failed", e));
  }, []);

  const updateNodeData = useCallback((nodeId: string, newData: any) => {
    setNodes(nds => {
      let nextNodes = nds.map(node => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, ...newData } };
        }
        return node;
      });

      // ── AUTO-SYNC TOPICS ──
      // If the Source node was updated, automatically push topics to the Topic node
      const sourceNode = nextNodes.find(n => n.type === 'source');
      const topicNode = nextNodes.find(n => n.type === 'topic');

      if (sourceNode && topicNode && nodeId === sourceNode.id && masterSyllabus) {
        const { subject, level } = sourceNode.data;
        const auto = masterSyllabus[subject]?.[level] || [];

        nextNodes = nextNodes.map(n => {
          if (n.id === topicNode.id) {
            return { ...n, data: { ...n.data, topics: auto } };
          }
          return n;
        });
      }
      return nextNodes;
    });
  }, [masterSyllabus]);

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect: OnConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)),
    []
  );

  const handleExecute = useCallback(async () => {
    const currentNodes = getNodes();
    const currentEdges = getEdges();

    setIsExecuting(true);
    setProgress(0);
    setOutput(["[INIT] Neural Flow Pipeline Started..."]);

    try {
      const response = await fetch("/api/flow/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nodes: currentNodes, edges: currentEdges })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let totalProcessed = 0;
      const topicsCount = currentNodes.find(n => n.type === 'topic')?.data.topics?.length || 1;

      while (true) {
        const { done, value } = await reader?.read() || { done: true, value: null };
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const q = JSON.parse(line.slice(6));
            totalProcessed++;
            setProgress(Math.round((totalProcessed / topicsCount) * 100));

            const formatted = `### [Neural Flow Generation]\n\n**Topic**: ${q.topic || 'N/A'}\n**Question**: ${q.question}\n\n*Options*:\n${q.options.map((o: string, idx: number) => `${String.fromCharCode(65 + idx)}. ${o}`).join("\n")}\n\n**Key**: ${q.answer}\n**Pedagogy**: ${q.explanation}\n\n---\n`;

            setOutput(prev => [...prev, `[SUCCESS] Processed: ${q.topic || 'Question'}`]);
            if (onBridge) onBridge(formatted);
          }
        }
      }
    } catch (e) {
      setOutput(prev => [...prev, `[ERROR] Pipeline Interrupted: ${e}`]);
    } finally {
      setIsExecuting(false);
      setProgress(100);
      setOutput(prev => [...prev, "[COMPLETE] All nodes processed. Content available in Studio."]);
    }
  }, [getNodes, getEdges, onBridge]);

  // Automatic topic sync when syllabus first loads
  useEffect(() => {
    if (!masterSyllabus) return;
    const sourceNode = nodes.find(n => n.type === 'source');
    if (sourceNode) updateNodeData(sourceNode.id, {});
  }, [masterSyllabus]); // Run once when syllabus is available

  // Inject execution handler and change handlers into nodes
  useEffect(() => {
    setNodes(nds => nds.map(node => {
      return {
        ...node,
        data: {
          ...node.data,
          onChange: updateNodeData,
          onExecute: handleExecute,
          isExecuting
        }
      };
    }));
  }, [isExecuting, updateNodeData, handleExecute]);

  // ── PERSISTENCE ──
  const saveTemplate = useCallback(() => {
    const flow = { nodes, edges };
    localStorage.setItem('eduquest_flow_template', JSON.stringify(flow));
    alert("Flow Template Saved to Institutional Registry.");
  }, [nodes, edges]);

  const loadTemplate = useCallback(() => {
    const saved = localStorage.getItem('eduquest_flow_template');
    if (saved) {
      const { nodes: n, edges: e } = JSON.parse(saved);
      setNodes(n);
      setEdges(e);
    }
  }, []);

  return (
    <div className="flex-1 h-full flex flex-col bg-surface-soft/30">
      {/* Header bar */}
      <HeaderBar
        isExecuting={isExecuting}
        progress={progress}
        onSave={saveTemplate}
        onLoad={loadTemplate}
        onExecute={handleExecute}
      />

      <div className="flex-1 flex relative">
        {/* Node Sidebar */}
        <div className="w-16 border-r border-border-main bg-surface flex flex-col items-center py-6 gap-6 shadow-sm">
          <NodeIcon type="source" icon={<Database className="w-4 h-4" />} color="text-brand-800" label="Source" />
          <NodeIcon type="topic" icon={<Filter className="w-4 h-4" />} color="text-emerald-500" label="Topic" />
          <NodeIcon type="logic" icon={<Brain className="w-4 h-4" />} color="text-amber-500" label="Logic" />
          <NodeIcon type="output" icon={<Sparkles className="w-4 h-4" />} color="text-brand-500" label="Neural" />
        </div>

        {/* Canvas Area */}
        <div className="flex-1 relative flex">
          <div className="flex-1 relative">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              fitView
              className="bg-dot-pattern"
            >
              <Background color="var(--border-color)" gap={20} />
              <Controls className="bg-surface border border-border-main shadow-lg rounded-xl overflow-hidden" />
            </ReactFlow>

            {/* Floating Sidebar Tips */}
            <div className="absolute top-8 left-8 p-4 bg-surface/80 backdrop-blur-md border border-border-main rounded-2xl shadow-xl max-w-[200px] pointer-events-none">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-3 h-3 text-brand-800" />
                <span className="text-[9px] font-black uppercase tracking-widest">Pro Tip</span>
              </div>
              <p className="text-[10px] text-foreground font-bold leading-relaxed">
                Wire a <span className="text-emerald-500">Source</span> to a <span className="text-amber-500">Logic</span> node to inject depth.
              </p>
            </div>
          </div>

          {/* Right Output Terminal */}
          <div className="w-64 border-l border-border-main bg-brand-900/10 p-4 flex flex-col gap-3 font-mono">
            <div className="flex items-center justify-between border-b border-border-main pb-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.4)]"></div>
                <span className="text-[9px] font-black text-foreground opacity-50 uppercase tracking-widest">Neural Terminal</span>
              </div>
              <button onClick={() => setOutput([])} className="text-[8px] text-foreground opacity-30 hover:opacity-100 uppercase transition-opacity">Clear</button>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 custom-scroll">
              {output.map((line, i) => (
                <div key={i} className={cn(
                  "text-[10px] leading-tight break-words",
                  line.startsWith("[ERROR]") ? "text-rose-400" :
                    line.startsWith("[SUCCESS]") ? "text-emerald-400" :
                      line.startsWith("[INIT]") ? "text-amber-400" : "text-foreground opacity-80"
                )}>
                  <span className="opacity-40 mr-2">{'>'}</span>
                  {line}
                </div>
              ))}
              {isExecuting && (
                <div className="text-[10px] text-emerald-400 animate-pulse italic">
                  <span className="opacity-40 mr-2">{'>'}</span>
                  Synthesis in progress...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FlowView(props: any) {
  return (
    <ReactFlowProvider>
      <FlowViewInner {...props} />
    </ReactFlowProvider>
  );
}

function NodeIcon({ icon, color, label }: any) {
  return (
    <div className="group relative flex flex-col items-center cursor-grab active:cursor-grabbing">
      <div className={cn("p-3 rounded-xl bg-surface-soft border border-border-main transition-all hover:scale-110 hover:shadow-md", color)}>
        {icon}
      </div>
      <span className="text-[7px] font-black uppercase tracking-tighter mt-1 text-foreground opacity-40 group-hover:opacity-60">{label}</span>
    </div>
  )
}

function HeaderBar({ isExecuting, progress, onSave, onLoad, onExecute }: any) {
  return (
    <div className="h-16 border-b border-border-main flex items-center justify-between px-8 bg-surface/50 backdrop-blur-md transition-all">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 bg-brand-800 rounded-xl flex items-center justify-center shadow-lg transition-colors">
          <GitBranch className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-sm font-black text-foreground uppercase tracking-widest leading-none">Neural Flow Studio</h2>
          <p className="text-[9px] font-bold text-foreground opacity-40 uppercase mt-1">Generative Pedagogical Pipeline</p>
        </div>
      </div>

      {isExecuting && (
        <div className="flex items-center gap-3 animate-in fade-in zoom-in-95">
          <div className="w-32 h-1.5 bg-surface-soft border border-border-main rounded-full overflow-hidden shadow-inner">
            <div className="h-full bg-brand-800 transition-all duration-300 shadow-[0_0_8px_rgba(128,0,32,0.4)]" style={{ width: `${progress}%` }}></div>
          </div>
          <span className="text-[10px] font-black text-brand-800">{progress}%</span>
        </div>
      )}

      <div className="flex items-center gap-2">
        <button onClick={onLoad} className="px-4 py-2 bg-surface border border-border-main rounded-xl text-[10px] font-black uppercase tracking-widest hover:border-brand-800 transition-all">
          Load Template
        </button>
        <button onClick={onSave} className="px-4 py-2 bg-surface border border-border-main rounded-xl text-[10px] font-black uppercase tracking-widest hover:border-brand-800 transition-all">
          Save
        </button>
        <button
          onClick={onExecute}
          disabled={isExecuting}
          className="px-6 py-2 bg-brand-800 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-brand-900 transition-all shadow-md active:scale-95 flex items-center gap-2"
        >
          {isExecuting ? <Activity className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
          {isExecuting ? 'Synthesizing...' : 'Execute Flow'}
        </button>
      </div>
    </div>
  );
}