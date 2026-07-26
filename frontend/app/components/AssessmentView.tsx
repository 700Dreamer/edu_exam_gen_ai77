"use client";

import { useState, useEffect, useRef } from "react";
import {
  FileText, Download, Loader2, Camera, Archive, Eye, X, FileCheck, Plus, ArrowRight, Layers, CheckCircle2, ScanLine, AlertTriangle, RefreshCw, RotateCw, Building2, ShieldCheck
} from "lucide-react";
import { cn, authFetch, API_BASE } from "../lib/utils";


export default function AssessmentView({
  theme,
  globalTenantId,
  globalGroupId,
  globalSubject,
  globalTerm,
  globalYear
}: {
  theme: string;
  globalTenantId?: string;
  globalGroupId?: string;
  globalSubject?: string;
  globalTerm?: string;
  globalYear?: number;
}) {
  const [tenants, setTenants] = useState<any[]>([]);
  const [selectedTenant, setSelectedTenant] = useState<string>(globalTenantId || "");
  const [groups, setGroups] = useState<any[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>(globalGroupId || "");

  const [subject, setSubject] = useState(globalSubject || "Physics");
  const [configLocked, setConfigLocked] = useState(true);
  const [dragActive, setDragActive] = useState(false);
  const [scannedPages, setScannedPages] = useState<{file: File, url: string}[]>([]);
  const [currentExamId, setCurrentExamId] = useState<string>("");
  const [currentExamPageCount, setCurrentExamPageCount] = useState<number>(0);
  const [expectedPageCount, setExpectedPageCount] = useState<number | "">("");
  const [showNextExamPrompt, setShowNextExamPrompt] = useState<boolean>(false);
  const [examLabel, setExamLabel] = useState<string>("");
  
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batchStatus, setBatchStatus] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isCompilingPdf, setIsCompilingPdf] = useState(false);

  const [batchMode, setBatchMode] = useState<"worksheet" | "answer_sheet" | "hybrid">("hybrid");
  const [masterQuestionFiles, setMasterQuestionFiles] = useState<File[]>([]);

  // Scanned Thumbnail Full Preview Modal States
  const [previewModalUrl, setPreviewModalUrl] = useState<string | null>(null);
  const [previewModalTitle, setPreviewModalTitle] = useState<string>("");
  
  const [apiConfig, setApiConfig] = useState<any>({ subjects: [] });

  // 3-Mode Upload States
  const [uploadMode, setUploadMode] = useState<"camera" | "scanner" | "zip">("scanner");
  
  // Camera Device States & Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");

  // Bulk Zip States
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [isUploadingZip, setIsUploadingZip] = useState(false);

  // Flatbed Scanner Hardware States
  const [scannerDevices, setScannerDevices] = useState<any[]>([]);
  const [selectedScanner, setSelectedScanner] = useState<string>("");
  const [scannerLoading, setScannerLoading] = useState(false);
  const [scannerError, setScannerError] = useState<string>("");
  const [scannerPlatform, setScannerPlatform] = useState<string>("");
  const [saneInstalled, setSaneInstalled] = useState<boolean | null>(null);
  const [scannerSource, setScannerSource] = useState<"local" | "remote">("remote");
  const [scanDpi, setScanDpi] = useState(150);
  const [scanMode, setScanMode] = useState("Color");
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [lastScanPreview, setLastScanPreview] = useState<string>("");

  useEffect(() => {
    authFetch("/api/v1/tenant/list")
      .then(res => res.json())
      .then(data => {
        setTenants(data);
        if (data.length > 0) setSelectedTenant(data[0].id);
      })
      .catch(() => {});

    authFetch(`${API_BASE}/api/syllabus/config?t=${Date.now()}`)
      .then(res => res.json())
      .then(data => setApiConfig(data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedTenant) {
      authFetch(`/api/v1/tenant/${selectedTenant}/groups`)
        .then(res => res.json())
        .then(data => {
          setGroups(data);
          if (data.length > 0) setSelectedGroup(data[0].id);
          else setSelectedGroup("");
        })
        .catch(() => {});
    }
  }, [selectedTenant]);

  const selectedGroupObj = groups.find((g: any) => g.id === selectedGroup);
  const selectedLevel = selectedGroupObj ? (selectedGroupObj.level || selectedGroupObj.name || "") : "";

  // Helper function to check if subject is appropriate for chosen level/class
  const isSubjectForLevel = (subjectName: string, levelStr: string) => {
    if (!levelStr) return true;
    const lvl = levelStr.toLowerCase().replace(/\s+/g, "");
    const sub = subjectName.toLowerCase().trim();

    const isPrimary = lvl.includes("primary") || /^p[1-7]/i.test(lvl);
    const isNursery = lvl.includes("baby") || lvl.includes("middle") || lvl.includes("top") || lvl.includes("nursery");
    const isSenior = lvl.includes("senior") || /^s[1-6]/i.test(lvl);

    if (isPrimary) {
      // Primary classes (P.1 - P.7): strictly exclude secondary subjects
      const secondaryOnly = [
        "biology", "chemistry", "physics", "commerce", "entrepreneurship", "sub-math", 
        "sub math", "general paper", "geography", "history", "accounting", "economics", 
        "agriculture", "computer studies", "literature"
      ];
      if (secondaryOnly.some(sec => sub === sec || sub.includes(sec))) return false;

      const primarySubjects = [
        "mathematics", "math", "integrated science", "science", "english", 
        "social studies with religious education", "social studies", "sst", 
        "religious education", "re", "reading", "luganda", "physical education", "art and craft"
      ];
      return primarySubjects.some(ps => sub.includes(ps) || ps.includes(sub));
    }

    if (isNursery) {
      const nurserySubjects = ["learning area", "reading", "mathematical concepts", "language development"];
      return nurserySubjects.some(ns => sub.includes(ns));
    }

    if (isSenior) {
      // Senior classes (S.1 - S.6): strictly exclude primary-only subjects
      if (sub.includes("integrated science") || sub.includes("learning area") || sub === "sst" || sub.includes("social studies")) return false;
      return true;
    }

    return true;
  };

  // Default fallback lists if API config returns empty
  const defaultPrimarySubjects = [
    "Mathematics", "English", "Integrated Science", 
    "Social Studies with Religious Education", "Luganda", "Art and Craft", "Physical Education"
  ];
  const defaultSecondarySubjects = [
    "Mathematics", "English Language", "Biology", "Chemistry", "Physics", 
    "Geography", "History", "Commerce", "Entrepreneurship Education", 
    "Agriculture", "Computer Studies", "Sub-Math", "General Paper", "Luganda", "Literature in English"
  ];
  const defaultNurserySubjects = [
    "Learning Area 1 (Language Development)", "Learning Area 2 (Mathematical Concepts)", 
    "Learning Area 3 (Expressive Arts)", "Learning Area 4 (Environment)", "Learning Area 5 (Health & Physical)"
  ];

  const getFallbackSubjects = (levelStr: string) => {
    if (!levelStr) return defaultSecondarySubjects;
    const lvl = levelStr.toLowerCase().replace(/\s+/g, "");
    if (lvl.includes("primary") || /^p[1-7]/i.test(lvl)) return defaultPrimarySubjects;
    if (lvl.includes("baby") || lvl.includes("middle") || lvl.includes("top") || lvl.includes("nursery")) return defaultNurserySubjects;
    return defaultSecondarySubjects;
  };

  const rawSubjects = apiConfig.subjects && apiConfig.subjects.length > 0 
    ? apiConfig.subjects 
    : getFallbackSubjects(selectedLevel);

  const subjects = rawSubjects.filter((s: string) => isSubjectForLevel(s, selectedLevel));

  // Auto-adjust selected subject when class/level changes if current subject is invalid for that class
  useEffect(() => {
    if (subjects.length > 0 && (!subject || !subjects.includes(subject))) {
      setSubject(subjects[0]);
    }
  }, [selectedGroup, selectedLevel, apiConfig, subjects]);

  // Detect scanners when scanner mode is selected
  const refreshScanners = async (force = false) => {
    setScannerLoading(true);
    setScannerError("");
    try {
      // First try the local scanner agent (http://127.0.0.1 is a "potentially trustworthy"
      // origin; Chrome/Edge allow fetching it even from https:// pages — no mixed-content block).
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 1500);
        const localRes = await fetch("http://127.0.0.1:8181/devices", { signal: controller.signal });
        clearTimeout(timer);
        if (localRes.ok) {
          const localData = await localRes.json();
          setScannerSource("local");
          setSaneInstalled(localData.sane_installed);
          setScannerDevices(localData.devices || []);
          if (localData.platform) setScannerPlatform(localData.platform);
          if (localData.devices?.length > 0 && !selectedScanner) {
            setSelectedScanner(localData.devices[0].device_id);
          }
          if (localData.message) setScannerError(localData.message);
          setScannerLoading(false);
          return; // Success — skip remote fallback
        }
      } catch (e) {
        // Local agent not running or blocked — fall through to remote
      }

      // Fallback to remote backend
      const res = await authFetch(`/api/v1/scanner/devices${force ? "?refresh=true" : ""}`);
      const data = await res.json();
      setScannerSource("remote");
      setSaneInstalled(data.sane_installed);
      setScannerDevices(data.devices || []);
      if (data.platform) setScannerPlatform(data.platform);
      if (data.devices?.length > 0 && !selectedScanner) {
        setSelectedScanner(data.devices[0].device_id);
      }
      if (data.message) setScannerError(data.message);
    } catch {
      setScannerError("Could not connect to scanner service.");
    } finally {
      setScannerLoading(false);
    }
  };

  useEffect(() => {
    if (globalTenantId) setSelectedTenant(globalTenantId);
    if (globalGroupId) setSelectedGroup(globalGroupId);
    if (globalSubject) setSubject(globalSubject);
    if (globalTenantId && globalGroupId) setConfigLocked(true);
  }, [globalTenantId, globalGroupId, globalSubject]);

  useEffect(() => {
    if (uploadMode === "scanner" && saneInstalled === null) {
      refreshScanners();
    }
  }, [uploadMode]);

  // Scan a page from the selected flatbed scanner
  const scanFromDevice = async () => {
    if (!selectedScanner) return;
    setIsScanning(true);
    setScanProgress(0);
    setLastScanPreview("");

    // Simulate scanning progress logarithmically up to 98%
    let progressVal = 0;
    const progressInterval = setInterval(() => {
      progressVal += (100 - progressVal) * 0.08;
      if (progressVal >= 98) progressVal = 98;
      setScanProgress(progressVal);
    }, 120);

    try {
      let res;
      if (scannerSource === "local") {
        res = await fetch("http://127.0.0.1:8181/scan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            device_id: selectedScanner,
            dpi: scanDpi,
            mode: scanMode,
          }),
        });
      } else {
        res = await authFetch("/api/v1/scanner/scan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            device_id: selectedScanner,
            dpi: scanDpi,
            mode: scanMode,
          }),
        });
      }

      clearInterval(progressInterval);
      setScanProgress(100);

      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || "Scan failed.");
        return;
      }
      const data = await res.json();
      if (data.device_id && data.device_id !== selectedScanner) {
        setSelectedScanner(data.device_id);
      }
      const imagesList = data.image_base64_list || (data.image_base64 ? [data.image_base64] : []);
      if (imagesList.length === 0) {
        alert("Scan completed but no images were returned.");
        return;
      }

      // Generate exam ID if this is the first page
      let eid = currentExamId;
      if (!eid) {
        eid = `exam_${Date.now()}`;
        setCurrentExamId(eid);
      }

      let currentStudentName = examLabel.trim();
      let currentStudentExamId = currentExamId || `exam_${Date.now()}`;
      if (!currentExamId) setCurrentExamId(currentStudentExamId);

      let startPageNum = currentExamPageCount;
      let lastPreview = "";
      
      const newPages: {file: File, url: string}[] = [];

      for (let index = 0; index < imagesList.length; index++) {
        const b64 = imagesList[index];
        if (!b64) continue;
        
        const binary = atob(b64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        const blob = new Blob([bytes], { type: data.format === "jpeg" ? "image/jpeg" : "image/png" });

        const isNewStudentExam = expectedPageCount && typeof expectedPageCount === "number"
          ? (index % expectedPageCount === 0)
          : (index === 0 && startPageNum === 0);

        if (isNewStudentExam) {
          if (index > 0) {
            currentStudentExamId = `exam_${Date.now()}_${index}`;
            currentStudentName = "";
          }
          const ocrResultName = await runOcrForStudentName(blob);
          if (ocrResultName && ocrResultName !== "Unknown") {
            currentStudentName = ocrResultName;
            if (index === 0) setExamLabel(ocrResultName);
          }
        }

        const pageWithinExam = expectedPageCount && typeof expectedPageCount === "number"
          ? (index % expectedPageCount) + 1
          : startPageNum + index + 1;

        const prefix = currentStudentName.trim()
          ? `${currentStudentName.trim().replace(/[^a-zA-Z0-9]/g, "_")}_${currentStudentExamId}`
          : currentStudentExamId;

        const ext = data.format === "jpeg" ? "jpg" : "png";
        const fileName = `${prefix}_page${pageWithinExam}.${ext}`;
        const file = new File([blob], fileName, { type: data.format === "jpeg" ? "image/jpeg" : "image/png" });
        const url = URL.createObjectURL(blob);

        newPages.push({ file, url });
        lastPreview = url;
      }

      if (newPages.length > 0) {
        setScannedPages(prev => [...prev, ...newPages]);
        setCurrentExamPageCount(startPageNum + newPages.length);
        setLastScanPreview(lastPreview);
      }
    } catch (e: any) {
      clearInterval(progressInterval);
      alert("Scanner error: " + (e.message || "Unknown error"));
    } finally {
      setIsScanning(false);
    }
  };

  const [liveLogs, setLiveLogs] = useState<Array<{ time: string; message: string; type?: 'info' | 'success' | 'warning' | 'error' }>>([]);
  const [livePapers, setLivePapers] = useState<Record<number, any>>({});

  useEffect(() => {
    let interval: any;
    let eventSource: EventSource | null = null;

    if (batchId && (batchStatus?.status === "Initiated" || batchStatus?.status === "Processing" || isProcessing)) {
      // ── 1. SSE Real-Time Stream Connection ──
      const sseUrl = API_BASE ? `${API_BASE}/api/v1/assessment/batch/${batchId}/stream` : `/api/v1/assessment/batch/${batchId}/stream`;
      eventSource = new EventSource(sseUrl);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const timeStr = new Date().toLocaleTimeString();

          if (data.type === "batch_started") {
            setLiveLogs((prev) => [...prev, { time: timeStr, message: `Batch initiated for ${data.total_papers} student papers.`, type: "info" }]);
          } else if (data.type === "paper_start") {
            setLivePapers((prev) => ({
              ...prev,
              [data.paper_idx]: {
                paper_idx: data.paper_idx,
                student_name: `Paper #${data.paper_idx}`,
                phase: data.phase,
                status: "extracting"
              }
            }));
            setLiveLogs((prev) => [...prev, { time: timeStr, message: `Paper #${data.paper_idx}: Started Phase 1 (Parallel Page Extraction)...`, type: "info" }]);
          } else if (data.type === "page_extraction_complete") {
            setLivePapers((prev) => ({
              ...prev,
              [data.paper_idx]: {
                ...prev[data.paper_idx],
                student_name: data.student_name,
                phase: data.phase,
                questions_found: data.total_questions_extracted,
                status: "grading"
              }
            }));
            setLiveLogs((prev) => [...prev, { time: timeStr, message: `Paper #${data.paper_idx} (${data.student_name}): Extracted ${data.total_questions_extracted} questions. Starting Phase 2 (Micro-Batch Grading)...`, type: "info" }]);
          } else if (data.type === "paper_completed") {
            setLivePapers((prev) => ({
              ...prev,
              [data.paper_idx]: {
                ...prev[data.paper_idx],
                student_name: data.student_name,
                phase: "Complete",
                score: data.score,
                max_score: data.max_score,
                questions_count: data.questions_count,
                status: "completed"
              }
            }));
            setLiveLogs((prev) => [...prev, { time: timeStr, message: `Paper #${data.paper_idx} (${data.student_name}): Graded successfully (${data.score}/${data.max_score} pts, ${data.questions_count} questions).`, type: "success" }]);
          } else if (data.type === "paper_error") {
            setLivePapers((prev) => ({
              ...prev,
              [data.paper_idx]: {
                ...prev[data.paper_idx],
                phase: "Error",
                status: "error"
              }
            }));
            setLiveLogs((prev) => [...prev, { time: timeStr, message: `Paper #${data.paper_idx}: Error during processing: ${data.error}`, type: "error" }]);
          } else if (data.type === "batch_complete") {
            setLiveLogs((prev) => [...prev, { time: timeStr, message: `Batch completed! All results persisted to Gradebook.`, type: "success" }]);
            setIsProcessing(false);
          }
        } catch (e) {}
      };

      // ── 2. Fallback Polling (Syncs state even if production reverse proxies buffer SSE) ──
      interval = setInterval(async () => {
        try {
          const res = await authFetch(`/api/v1/assessment/batch/${batchId}/status`);
          if (res.ok) {
            const data = await res.json();
            setBatchStatus(data);
            if (data.papers && Array.isArray(data.papers)) {
              setLivePapers((prev) => {
                const nextState = { ...prev };
                for (const p of data.papers) {
                  if (!nextState[p.paper_idx] || p.status === "completed") {
                    nextState[p.paper_idx] = {
                      paper_idx: p.paper_idx,
                      student_name: p.student_name,
                      phase: p.status === "completed" ? "Complete" : (p.status === "grading" ? "Grading" : "Processing"),
                      score: p.score,
                      max_score: p.max_score,
                      status: p.status
                    };
                  }
                }
                return nextState;
              });
            }
            if (data.status === "Completed") {
              setIsProcessing(false);
            }
          }
        } catch (e) {}
      }, 2000);
    }

    return () => {
      if (interval) clearInterval(interval);
      if (eventSource) eventSource.close();
    };
  }, [batchId, batchStatus, isProcessing]);

  // Clean up camera on change
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  useEffect(() => {
    if (uploadMode === "camera") {
      setCurrentExamId(Math.random().toString(36).substring(2, 10));
      setCurrentExamPageCount(0);
      setExamLabel("");
      startCamera();
    } else {
      stopCamera();
    }
  }, [uploadMode]);

  // Dynamic Camera device enumeration
  const enumerateCameraDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = devices.filter(d => d.kind === "videoinput");
      setVideoDevices(videoInputs);
      if (videoInputs.length > 0 && !selectedDeviceId) {
        setSelectedDeviceId(videoInputs[0].deviceId);
      }
    } catch (e) {
      console.error("Error listing webcams:", e);
    }
  };

  // Webcam Controls
  const startCamera = async (deviceId?: string) => {
    setCameraError("");
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      const activeDeviceId = deviceId || selectedDeviceId;
      const constraints = {
        video: activeDeviceId ? { deviceId: { exact: activeDeviceId } } : { facingMode: "environment" }
      };
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
      
      // Enumerate device labels once user grants video permission
      enumerateCameraDevices();
    } catch (e: any) {
      setCameraError("Camera access denied or unavailable.");
      setCameraActive(false);
    }
  };

  // Auto-refresh camera stream when active input source switches
  useEffect(() => {
    if (uploadMode === "camera" && selectedDeviceId) {
      startCamera(selectedDeviceId);
    }
  }, [selectedDeviceId, uploadMode]);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  const captureImage = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 1280;
    canvas.height = videoRef.current.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(async (blob) => {
        if (blob) {
          const pageNum = currentExamPageCount + 1;
          
          let eid = currentExamId;
          if (!eid) {
            eid = `exam_${Date.now()}`;
            setCurrentExamId(eid);
          }

          let detectedName = "";
          if (pageNum === 1 && !examLabel.trim()) {
            setIsScanning(true);
            detectedName = await runOcrForStudentName(blob);
            setIsScanning(false);
            if (detectedName) {
              setExamLabel(detectedName);
            }
          }

          const prefix = detectedName.trim() || examLabel.trim() || eid;
          const filename = `${prefix}_page_${pageNum}.jpg`;
          const file = new File([blob], filename, { type: "image/jpeg" });
          
          setScannedPages(prev => [...prev, {
            file: file,
            url: URL.createObjectURL(file)
          }]);
          
          setCurrentExamPageCount(pageNum);

          if (expectedPageCount && pageNum >= expectedPageCount) {
            setShowNextExamPrompt(true);
          }
        }
      }, "image/jpeg", 0.9);
    }
  };

  const finishCurrentExam = () => {
    setCurrentExamId(Math.random().toString(36).substring(2, 10));
    setCurrentExamPageCount(0);
    setExamLabel("");
  };

  const getCurrentExamPages = () => {
    if (uploadMode === "camera") {
      const cameraPrefix = examLabel.trim()
        ? `${examLabel.trim().replace(/[^a-zA-Z0-9]/g, "_")}_${currentExamId}`
        : `exam_${currentExamId}`;
      return scannedPages.filter(p => p.file.name.startsWith(cameraPrefix));
    } else {
      const scannerPrefix = examLabel.trim() || currentExamId;
      return scannedPages.filter(p => p.file.name.startsWith(scannerPrefix));
    }
  };

  const downloadGroupPdf = async (groupName: string, pages: { file: File, url: string }[]) => {
    if (pages.length === 0) return;
    setIsCompilingPdf(true);
    try {
      const formData = new FormData();
      // Sort pages by page index (by filename) to ensure correct order in compiled PDF
      const sortedPages = [...pages].sort((a, b) => a.file.name.localeCompare(b.file.name));
      sortedPages.forEach(p => {
        formData.append("files", p.file);
      });

      const res = await authFetch("/api/v1/scanner/compile-pdf", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Failed to compile PDF");
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${groupName.replace(/[^a-zA-Z0-9_-]/g, "_") || "scanned_exam"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      alert("Error compiling PDF: " + (e.message || "Unknown error"));
    } finally {
      setIsCompilingPdf(false);
    }
  };

  const rotatePage = async (globalIndex: number) => {
    const page = scannedPages[globalIndex];
    if (!page) return;

    try {
      const img = new window.Image();
      img.src = page.url;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
      });

      const canvas = document.createElement("canvas");
      canvas.width = img.height;
      canvas.height = img.width;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate((90 * Math.PI) / 180);
      ctx.drawImage(img, -img.width / 2, -img.height / 2);

      const blob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob((b) => resolve(b), "image/png");
      });

      if (!blob) return;

      const rotatedFile = new File([blob], page.file.name, { type: "image/png" });
      const rotatedUrl = URL.createObjectURL(blob);

      // Revoke old URL
      URL.revokeObjectURL(page.url);

      setScannedPages(prev => {
        const copy = [...prev];
        copy[globalIndex] = { file: rotatedFile, url: rotatedUrl };
        return copy;
      });

      if (lastScanPreview === page.url) {
        setLastScanPreview(rotatedUrl);
      }
    } catch (e) {
      console.error("Failed to rotate image:", e);
      alert("Failed to rotate image.");
    }
  };

  const runOcrForStudentName = async (blob: Blob): Promise<string> => {
    try {
      const formData = new FormData();
      formData.append("file", blob, "scanned_page.png");

      const res = await authFetch("/api/v1/scanner/ocr-name", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        if (data.name && data.name !== "Unknown") {
          return data.name;
        }
      }
    } catch (e) {
      console.error("AI OCR failed:", e);
    }
    return "";
  };

  const getGroupedPages = () => {
    const groups: { [key: string]: typeof scannedPages } = {};
    scannedPages.forEach(page => {
      const name = page.file.name;
      const match = name.match(/^(.*?)(?:[_-](?:page)?\d+)?\.[^.]+$/i);
      const key = match ? match[1] : name;
      if (!groups[key]) groups[key] = [];
      groups[key].push(page);
    });
    return Object.entries(groups);
  };

  const handleDrag = (e: any) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e: any) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
       const newPages = Array.from(e.dataTransfer.files).map((f: any) => ({
           file: f,
           url: URL.createObjectURL(f)
       }));
       setScannedPages(prev => [...prev, ...newPages]);
     }
  };

  const processBatch = async () => {
    if (scannedPages.length === 0 || !selectedGroup) return;
    setIsProcessing(true);
    
    try {
      const initRes = await authFetch("/api/v1/assessment/batch/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          academic_group_id: selectedGroup,
          subject: subject,
          exam_type: "Mid Term",
          mode: batchMode
        })
      });
      if (!initRes.ok) throw new Error("Failed to init batch");
      const { batch_id } = await initRes.json();
      setBatchId(batch_id);
      
      if (masterQuestionFiles.length > 0) {
        const masterData = new FormData();
        for (const mFile of masterQuestionFiles) {
          masterData.append("files", mFile);
        }
        await authFetch(`/api/v1/assessment/batch/${batch_id}/upload-master-question`, {
          method: "POST",
          body: masterData
        });
      }
      
      const formData = new FormData();
      for (const page of scannedPages) {
         formData.append("files", page.file);
      }
      
      await authFetch(`/api/v1/assessment/batch/${batch_id}/upload`, {
        method: "POST",
        body: formData,
      });
      
      await authFetch(`/api/v1/assessment/batch/${batch_id}/process`, {
        method: "POST"
      });
      
      setBatchStatus({ status: "Processing", processed: 0, total: scannedPages.length, needs_review: 0 });
      setScannedPages([]);
    } catch (e) {
      console.error(e);
      setIsProcessing(false);
      alert("Failed to process batch.");
    }
  };

  const handleZipSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setZipFile(e.target.files[0]);
    }
  };

  const processZipBatch = async () => {
    if (!zipFile || !selectedGroup) return;
    setIsUploadingZip(true);
    setIsProcessing(true);
    
    try {
      const initRes = await authFetch("/api/v1/assessment/batch/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          academic_group_id: selectedGroup,
          subject: subject,
          exam_type: "Mid Term"
        })
      });
      if (!initRes.ok) throw new Error("Failed to init batch");
      const { batch_id } = await initRes.json();
      setBatchId(batch_id);

      const formData = new FormData();
      formData.append("file", zipFile);

      const uploadRes = await authFetch(`/api/v1/assessment/batch/${batch_id}/upload-zip`, {
        method: "POST",
        body: formData
      });
      if (!uploadRes.ok) throw new Error("Failed to upload zip file");
      const uploadData = await uploadRes.json();
      
      await authFetch(`/api/v1/assessment/batch/${batch_id}/process`, {
        method: "POST"
      });
      
      setBatchStatus({ status: "Processing", processed: 0, total: uploadData.uploaded_count || 1, needs_review: 0 });
      setZipFile(null);
    } catch (e) {
      console.error(e);
      setIsProcessing(false);
      alert("Failed to process ZIP batch. Ensure the ZIP file is valid.");
    } finally {
      setIsUploadingZip(false);
    }
  };

  const isSidebarMode = isProcessing || batchStatus !== null;

  return (
    <div className={cn(
      "flex-1 bg-surface-soft text-foreground overflow-hidden relative flex transition-all duration-700 ease-in-out",
      isSidebarMode ? "flex-col lg:flex-row" : "flex-col items-center overflow-y-auto py-12 lg:py-20"
    )}>
      <div className={cn(
        "bg-surface z-20 flex flex-col transition-all duration-700 ease-[cubic-bezier(0.4,0,0.2,1)] shadow-none",
        isSidebarMode 
          ? "w-full lg:w-[340px] lg:min-w-[340px] border-r border-border-main h-full rounded-none" 
          : "w-full max-w-5xl border border-border-main rounded-none mb-8 flex-none"
      )}>
         <div className={cn("p-6 border-b border-border-main bg-surface-soft", isSidebarMode ? "" : "rounded-none")}>
             <h2 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                <Layers className="w-5 h-5 text-brand-600"/> Batch Assessment Engine
             </h2>
             <p className="text-xs text-foreground/60 mt-1 font-medium">Enterprise Semantic Grading Pipeline</p>
         </div>
         
         <div className={cn("p-6 flex-1", isSidebarMode ? "space-y-6 overflow-y-auto" : "")}>
             <div className={cn("transition-all duration-500 overflow-hidden", configLocked ? "max-h-0 opacity-0 mb-0" : "max-h-[1000px] opacity-100")}>
               <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                 
                 {/* ── COLUMN 1: Paper Specifics ── */}
                 <div className="space-y-4 border-b md:border-b-0 md:border-r border-border-main/50 pb-4 md:pb-0 md:pr-6">
                   <div className="flex items-center gap-2 border-b border-border-main pb-2">
                     <Building2 className="w-4 h-4 text-brand-600" />
                     <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">1. Paper Specifics</h3>
                   </div>
                   
                   <div>
                     <label className="text-xs font-medium text-foreground/60 mb-1.5 block">School / Tenant</label>
                     <select 
                       value={selectedTenant} 
                       onChange={(e) => setSelectedTenant(e.target.value)}
                       className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none transition-all cursor-pointer"
                     >
                       <option value="" disabled>Select School...</option>
                       {tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                     </select>
                   </div>
                   
                   <div>
                     <label className="text-xs font-medium text-foreground/60 mb-1.5 block">Academic Class & Stream</label>
                     <select 
                       value={selectedGroup} 
                       onChange={(e) => setSelectedGroup(e.target.value)}
                       className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none transition-all cursor-pointer"
                       disabled={groups.length === 0}
                     >
                       <option value="" disabled>Select Class Stream...</option>
                       {groups.map(g => <option key={g.id} value={g.id}>{g.level} - {g.stream}</option>)}
                     </select>
                   </div>

                   <div>
                     <label className="text-xs font-medium text-foreground/60 mb-1.5 block">Subject</label>
                     <select 
                       value={subject} 
                       onChange={(e) => setSubject(e.target.value)}
                       className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none transition-all cursor-pointer"
                     >
                       <option value="" disabled>Select Subject...</option>
                       {subjects.map((s: string) => <option key={s} value={s}>{s}</option>)}
                     </select>
                   </div>
                 </div>

                 {/* ── COLUMN 2: Exam Layout & Marking Format ── */}
                 <div className="space-y-4 border-b md:border-b-0 md:border-r border-border-main/50 pb-4 md:pb-0 md:pr-6">
                   <div className="flex items-center gap-2 border-b border-border-main pb-2">
                     <FileText className="w-4 h-4 text-brand-600" />
                     <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">2. Exam Layout</h3>
                   </div>

                   <div>
                     <label className="text-xs font-medium text-foreground/60 mb-2 block">Marking Format</label>
                     <div className="grid grid-cols-1 gap-2">
                       <button
                         type="button"
                         onClick={() => setBatchMode("hybrid")}
                         className={cn(
                           "p-2.5 border text-left rounded-none transition-all cursor-pointer",
                           batchMode === "hybrid"
                             ? "border-brand-600 bg-brand-500/10 text-foreground font-bold"
                             : "border-border-main text-foreground/60 hover:bg-surface-soft"
                         )}
                       >
                         <div className="text-xs font-bold text-brand-600">Hybrid Format</div>
                         <div className="text-[10px] text-foreground/50 mt-0.5">Section A Worksheet + Section B/C Answer Sheet</div>
                       </button>

                       <button
                         type="button"
                         onClick={() => setBatchMode("answer_sheet")}
                         className={cn(
                           "p-2.5 border text-left rounded-none transition-all cursor-pointer",
                           batchMode === "answer_sheet"
                             ? "border-brand-600 bg-brand-500/10 text-foreground font-bold"
                             : "border-border-main text-foreground/60 hover:bg-surface-soft"
                         )}
                       >
                         <div className="text-xs font-bold">Answer Sheet Only</div>
                         <div className="text-[10px] text-foreground/50 mt-0.5">1-Time Master Paper + Student Answer Sheets</div>
                       </button>

                       <button
                         type="button"
                         onClick={() => setBatchMode("worksheet")}
                         className={cn(
                           "p-2.5 border text-left rounded-none transition-all cursor-pointer",
                           batchMode === "worksheet"
                             ? "border-brand-600 bg-brand-500/10 text-foreground font-bold"
                             : "border-border-main text-foreground/60 hover:bg-surface-soft"
                         )}
                       >
                         <div className="text-xs font-bold">Worksheet Format</div>
                         <div className="text-[10px] text-foreground/50 mt-0.5">Questions & answers printed together</div>
                       </button>
                     </div>
                   </div>

                   {(batchMode === "answer_sheet" || batchMode === "hybrid") && (
                     <div className="p-3 bg-brand-500/5 border border-brand-500/20 rounded-none space-y-2">
                       <div className="flex justify-between items-center">
                         <label className="text-[11px] font-bold text-brand-600 uppercase tracking-wider block">
                           Master Paper {batchMode === "hybrid" ? "(Optional)" : "(1-Time)"}
                         </label>
                         {masterQuestionFiles.length > 0 && (
                           <span className="text-[10px] font-bold text-emerald-600">{masterQuestionFiles.length} page(s)</span>
                         )}
                       </div>
                       <input
                         type="file"
                         multiple
                         accept="image/*,.pdf"
                         onChange={(e) => {
                           if (e.target.files) {
                             setMasterQuestionFiles(Array.from(e.target.files));
                           }
                         }}
                         className="w-full text-xs text-foreground file:mr-2 file:py-1 file:px-2 file:border-0 file:text-[11px] file:font-bold file:bg-brand-600 file:text-white hover:file:bg-brand-700 cursor-pointer"
                       />
                     </div>
                   )}
                 </div>

                 {/* ── COLUMN 3: Lock & Proceed ── */}
                 <div className="space-y-4 flex flex-col justify-between">
                   <div className="space-y-3">
                     <div className="flex items-center gap-2 border-b border-border-main pb-2">
                       <ShieldCheck className="w-4 h-4 text-brand-600" />
                       <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">3. Lock & Proceed</h3>
                     </div>

                     <div className="p-3 bg-surface-soft border border-border-main space-y-2 text-xs">
                       <div className="flex justify-between text-foreground/60">
                         <span>Class:</span>
                         <span className="font-bold text-foreground">{groups.find(g => g.id === selectedGroup)?.level || "Not set"}</span>
                       </div>
                       <div className="flex justify-between text-foreground/60">
                         <span>Subject:</span>
                         <span className="font-bold text-foreground">{subject || "Not set"}</span>
                       </div>
                       <div className="flex justify-between text-foreground/60">
                         <span>Format:</span>
                         <span className="font-bold text-brand-600 uppercase text-[10px]">{batchMode}</span>
                       </div>
                     </div>
                   </div>

                   <button 
                     onClick={() => setConfigLocked(true)} 
                     disabled={!subject || !selectedGroup} 
                     className="w-full bg-brand-600 text-white text-xs font-bold py-3.5 rounded-none hover:bg-brand-700 disabled:opacity-50 transition-all shadow-none hover:shadow-none active:scale-[0.98] cursor-pointer uppercase tracking-wider flex items-center justify-center gap-2"
                   >
                     Lock Configuration & Proceed <ArrowRight className="w-4 h-4" />
                   </button>
                 </div>

               </div>
             </div>
             
             {configLocked && (
               <div className="bg-surface border border-border-main rounded-none p-5 animate-in fade-in slide-in-from-right-4 duration-300 shadow-none font-outfit">
                 <div className="flex justify-between items-center mb-4 border-b border-border-main/50 pb-3">
                   <span className="text-xs font-black uppercase tracking-wider text-emerald-600 flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4"/> Active Context</span>
                   <button onClick={()=>{setConfigLocked(false); setBatchStatus(null); setBatchId(null); setScannedPages([]); stopCamera();}} className="text-xs font-bold text-foreground/50 hover:text-foreground transition-colors cursor-pointer">Edit</button>
                 </div>
                 <div className="grid grid-cols-1 gap-4">
                   <div className="flex flex-col gap-1">
                     <span className="text-[10px] uppercase font-bold tracking-widest text-foreground/40">School / Tenant</span>
                     <span className="text-sm font-bold text-foreground">{tenants.find(t => t.id === selectedTenant)?.name || "—"}</span>
                   </div>
                   <div className="flex flex-col gap-1">
                     <span className="text-[10px] uppercase font-bold tracking-widest text-foreground/40">Class Stream</span>
                     <span className="text-sm font-bold text-foreground">
                       {(() => {
                         const g = groups.find(x => x.id === selectedGroup);
                         return g ? `${g.level} - ${g.stream}` : "—";
                       })()}
                     </span>
                   </div>
                   <div className="flex flex-col gap-1">
                     <span className="text-[10px] uppercase font-bold tracking-widest text-foreground/40">Subject</span>
                     <span className="text-sm font-bold text-foreground truncate">{subject}</span>
                   </div>
                 </div>
               </div>
             )}
         </div>
      </div>

      <div className={cn(
        "transition-all duration-700 ease-[cubic-bezier(0.4,0,0.2,1)] relative",
        isSidebarMode ? "flex-1 h-full overflow-y-auto p-6 lg:p-10" : "w-full max-w-3xl px-4 flex-none"
      )}>
        <div className="max-w-5xl mx-auto w-full h-full space-y-6">
          {configLocked && !batchStatus && !isProcessing && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
              
              {/* Mode Selectors */}
              <div className="flex gap-2 bg-surface border border-border-main p-1.5 rounded-none w-fit mx-auto shadow-none">
                <button
                  onClick={() => setUploadMode("scanner")}
                  className={cn(
                    "px-4 py-2 rounded-none text-xs font-bold flex items-center gap-2 transition-all cursor-pointer",
                    uploadMode === "scanner" ? "bg-foreground text-surface shadow-none" : "text-foreground/60 hover:text-foreground hover:bg-surface-soft"
                  )}
                >
                  <Download className="w-3.5 h-3.5" />
                  Scanner Upload
                </button>
                <button
                  onClick={() => {
                    setUploadMode("camera");
                    startCamera();
                  }}
                  className={cn(
                    "px-4 py-2 rounded-none text-xs font-bold flex items-center gap-2 transition-all cursor-pointer",
                    uploadMode === "camera" ? "bg-foreground text-surface shadow-none" : "text-foreground/60 hover:text-foreground hover:bg-surface-soft"
                  )}
                >
                  <Camera className="w-3.5 h-3.5" />
                  Camera Mode
                </button>
                <button
                  onClick={() => setUploadMode("zip")}
                  className={cn(
                    "px-4 py-2 rounded-none text-xs font-bold flex items-center gap-2 transition-all cursor-pointer",
                    uploadMode === "zip" ? "bg-foreground text-surface shadow-none" : "text-foreground/60 hover:text-foreground hover:bg-surface-soft"
                  )}
                >
                  <Archive className="w-3.5 h-3.5" />
                  Bulk Zip Mode
                </button>
              </div>

              {/* Scanner Hardware Mode */}
              {uploadMode === "scanner" && (
                <div className="bg-surface border border-border-main rounded-none shadow-none overflow-hidden">
                  {/* Scanner Header */}
                  <div className="px-6 py-4 border-b border-border-main bg-surface-soft flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <ScanLine className="w-4 h-4 text-brand-600" />
                      <h3 className="text-sm font-bold text-foreground">Flatbed Scanner</h3>
                    </div>
                    <button
                      onClick={() => refreshScanners(true)}
                      disabled={scannerLoading}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-foreground/60 hover:text-brand-600 hover:bg-brand-500/5 transition-all cursor-pointer rounded-none border border-border-main"
                    >
                      <RefreshCw className={cn("w-3 h-3", scannerLoading && "animate-spin")} />
                      {scannerLoading ? "Detecting..." : "Refresh Devices"}
                    </button>
                  </div>

                  <div className="p-6 space-y-5">
                    {/* SANE not installed warning */}
                    {saneInstalled === false && (
                      <div className="bg-amber-500/5 border border-amber-500/30 p-4 flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-bold text-amber-700">Scanner Drivers Not Detected</p>
                          <p className="text-[11px] text-foreground/60 mt-1 leading-relaxed">
                            {scannerPlatform === "windows" ? (
                              <>Windows scanner support requires pywin32. Install with:<br />
                              <code className="bg-surface-soft px-2 py-0.5 border border-border-main text-[10px] font-mono mt-1 inline-block">pip install pywin32</code>
                              <br /><span className="text-[10px] text-foreground/40 mt-1 inline-block">Make sure your scanner is connected and powered on. Windows usually auto-installs scanner drivers.</span>
                              </>
                            ) : scannerPlatform === "linux" ? (
                              <>SANE scanner drivers are required. Install with:<br />
                              <code className="bg-surface-soft px-2 py-0.5 border border-border-main text-[10px] font-mono mt-1 inline-block">sudo apt-get install sane-utils</code>
                              </>
                            ) : (
                              <>SANE scanner drivers are required. Install with:<br />
                              <code className="bg-surface-soft px-2 py-0.5 border border-border-main text-[10px] font-mono mt-1 inline-block">brew install sane-backends</code>
                              </>
                            )}
                          </p>
                          <p className="text-[10px] text-foreground/40 mt-2">You can still use the file upload fallback below.</p>
                        </div>
                      </div>
                    )}

                    {/* Fast scanning prompt */}
                    {scannerSource === "remote" && scannerPlatform === "windows" && scannerDevices.length > 0 && (
                      <div className="bg-brand-500/5 border border-brand-500/30 p-4 flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-brand-500 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-bold text-brand-700">Want Instant Scanning Speed?</p>
                          <p className="text-[11px] text-foreground/70 mt-1 leading-relaxed">
                            You are currently using the remote scanner fallback which can be slow. 
                            Download the <b>Edulytics Scanner Agent</b> for instant, zero-delay ADF batch scanning.
                          </p>
                          <a href="/ScannerAgent.exe" download className="mt-2 inline-block px-3 py-1 bg-brand-600 text-white text-[10px] font-bold uppercase tracking-wider rounded-none hover:bg-brand-700 transition-colors">
                            Download Scanner Agent
                          </a>
                        </div>
                      </div>
                    )}

                    {/* Scanner detected — show controls */}
                    {scannerDevices.length > 0 && (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Device Selector */}
                        <div className="space-y-1.5">
                          <label className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Scanner Device</label>
                          <select
                            value={selectedScanner}
                            onChange={(e) => setSelectedScanner(e.target.value)}
                            className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer"
                          >
                            {scannerDevices.map((d: any) => (
                              <option key={d.device_id} value={d.device_id}>
                                {d.display_name} ({d.device_type})
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* DPI Selector */}
                        <div className="space-y-1.5">
                          <label className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Resolution (DPI)</label>
                          <select
                            value={scanDpi}
                            onChange={(e) => setScanDpi(Number(e.target.value))}
                            className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer"
                          >
                            <option value={150}>150 DPI — Fast Preview</option>
                            <option value={300}>300 DPI — Standard</option>
                            <option value={600}>600 DPI — High Quality</option>
                          </select>
                        </div>

                        {/* Color Mode Selector */}
                        <div className="space-y-1.5">
                          <label className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Color Mode</label>
                          <select
                            value={scanMode}
                            onChange={(e) => setScanMode(e.target.value)}
                            className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer"
                          >
                            <option value="Color">Color</option>
                            <option value="Gray">Grayscale</option>
                            <option value="Lineart">Black & White</option>
                          </select>
                        </div>
                      </div>
                    )}

                    {/* Exam label + Page counter (for scanner too) */}
                    {scannerDevices.length > 0 && (
                      <div className="bg-surface-soft p-4 border border-border-main space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-bold text-brand-600">Active Exam Capture Group</span>
                          <span className="text-[10px] bg-brand-500/10 text-brand-600 px-2.5 py-1 font-black uppercase tracking-wider">
                            {expectedPageCount ? `${currentExamPageCount} of ${expectedPageCount} Pages` : `${currentExamPageCount} Pages`} Scanned
                          </span>
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Student Name / Prefix (Optional)</label>
                          <input
                            type="text"
                            placeholder="e.g. Bruce Wayne"
                            value={examLabel}
                            onChange={(e) => setExamLabel(e.target.value)}
                            className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none"
                          />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Pages per Exam (Optional)</label>
                          <input
                            type="number"
                            min={1}
                            placeholder="e.g. 3"
                            value={expectedPageCount}
                            onChange={(e) => setExpectedPageCount(e.target.value === "" ? "" : parseInt(e.target.value))}
                            className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none"
                          />
                        </div>
                      </div>
                    )}

                    {/* Scan Button + Preview */}
                    {scannerDevices.length > 0 && (
                      <div className="space-y-6">
                        <div className="flex gap-6 items-start">
                          <div className="flex flex-col gap-3">
                            <button
                              onClick={scanFromDevice}
                              disabled={isScanning || !selectedScanner || (expectedPageCount !== "" && currentExamPageCount >= expectedPageCount)}
                              className="px-6 py-3 bg-brand-600 text-white text-xs font-bold rounded-none hover:bg-brand-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-none"
                            >
                              {isScanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <ScanLine className="w-4 h-4" />}
                              {isScanning ? "Scanning..." : expectedPageCount ? (currentExamPageCount >= expectedPageCount ? "All Pages Scanned" : `Scan Page ${currentExamPageCount + 1} of ${expectedPageCount}`) : `Scan Page ${currentExamPageCount + 1}`}
                            </button>

                            {currentExamPageCount > 0 && (
                              <div className="flex flex-col gap-2">
                                <button
                                  onClick={finishCurrentExam}
                                  className="px-6 py-2.5 bg-emerald-600 text-white text-xs font-bold rounded-none hover:bg-emerald-700 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-none"
                                >
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  Finalize Exam ({currentExamPageCount} pages)
                                </button>
                                <button
                                  onClick={() => downloadGroupPdf(examLabel.trim() || currentExamId || "scanned_exam", getCurrentExamPages())}
                                  disabled={isCompilingPdf}
                                  className="px-6 py-2 bg-brand-500/10 text-brand-600 hover:text-brand-700 hover:bg-brand-500/15 border border-brand-500/20 text-xs font-bold rounded-none transition-all flex items-center justify-center gap-2 cursor-pointer shadow-none"
                                >
                                  {isCompilingPdf ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                                  Download Exam PDF
                                </button>
                              </div>
                            )}
                          </div>

                          {/* Real-time Scanning Progress Preview or Last scan preview */}
                          {isScanning ? (
                            <div className="border border-border-main bg-zinc-950 p-3 shadow-none relative w-48 h-64 overflow-hidden flex flex-col justify-between select-none">
                              <div className="absolute inset-0 bg-gradient-to-b from-zinc-900 via-zinc-950 to-black" />
                              
                              {/* Scanner Bed Glass Grid */}
                              <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,_transparent_1px),_linear-gradient(90deg,_rgba(255,255,255,0.03)_1px,_transparent_1px)] bg-[size:10px_10px]" />
                              
                              {/* Document Paper Container */}
                              <div className="absolute inset-x-4 top-4 bottom-4 bg-zinc-800 border border-zinc-700 shadow-xl overflow-hidden flex items-center justify-center">
                                {/* Mock Document Content (blurred/sketchy) */}
                                <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,_rgba(0,0,0,0.15)_50%)] bg-[size:100%_4px] flex flex-col p-4 justify-between select-none opacity-40">
                                  <div className="h-2 w-3/4 bg-white/20 rounded" />
                                  <div className="space-y-1.5">
                                    <div className="h-1 bg-white/10 rounded" />
                                    <div className="h-1 w-5/6 bg-white/10 rounded" />
                                    <div className="h-1 w-2/3 bg-white/10 rounded" />
                                  </div>
                                  <div className="h-8 w-full border border-white/10 rounded-sm flex items-center justify-center text-[6px] text-white/20">Signature</div>
                                </div>

                                {/* Scanned Reveal Layer */}
                                <div 
                                  className="absolute inset-0 bg-white transition-all duration-100 ease-out"
                                  style={{
                                    clipPath: `inset(0px 0px ${100 - scanProgress}% 0px)`
                                  }}
                                >
                                  {/* Clear/Sharp Scanned Mock Sheet */}
                                  <div className="absolute inset-0 bg-white flex flex-col p-4 justify-between select-none">
                                    <div className="h-2 w-3/4 bg-zinc-300 rounded" />
                                    <div className="space-y-1.5">
                                      <div className="h-1 bg-zinc-200 rounded" />
                                      <div className="h-1 w-5/6 bg-zinc-200 rounded" />
                                      <div className="h-1 w-2/3 bg-zinc-200 rounded" />
                                    </div>
                                    <div className="h-8 w-full border border-zinc-200 rounded-sm flex items-center justify-center text-[6px] text-zinc-300">Signature</div>
                                  </div>
                                </div>
                              </div>

                              {/* Laser Scan Line */}
                              <div 
                                className="absolute left-0 right-0 h-0.5 bg-green-400 shadow-[0_0_10px_#4ade80,_0_0_20px_#22c55e] transition-all duration-100 ease-out z-10 animate-pulse"
                                style={{
                                  top: `${scanProgress}%`
                                }}
                              />
                                   {/* Progress bar info overlay */}
                              <div className="absolute bottom-2 left-2 right-2 flex justify-between items-center bg-zinc-950 border border-zinc-800 px-2 py-1 text-[8px] font-mono text-green-400 z-20">
                                <span>SCANNING...</span>
                                <span>{Math.round(scanProgress)}%</span>
                              </div>
                            </div>
                          ) : lastScanPreview ? (
                            <div className="border border-border-main bg-surface-soft p-2 shadow-none">
                              <p className="text-[10px] text-foreground/40 font-bold uppercase tracking-wider mb-1">Last Scan</p>
                              <img
                                src={lastScanPreview}
                                alt="Last scanned page"
                                className="h-32 object-contain"
                              />
                            </div>
                          ) : null}
                        </div>

                        {/* Active Exam Progress Preview */}
                        {currentExamPageCount > 0 && (
                          <div className="bg-surface-soft border border-border-main p-4 space-y-2 text-left">
                            <p className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Active Exam Pages Progress ({currentExamPageCount} pages)</p>
                            <div className="flex gap-3 overflow-x-auto pb-2 custom-scrollbar">
                              {getCurrentExamPages().map((page, idx) => {
                                const globalIndex = scannedPages.findIndex(x => x.file === page.file);
                                return (
                                  <div key={idx} className="relative min-w-[80px] h-24 bg-surface rounded-none border border-border-main overflow-hidden group">
                                    <img src={page.url} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-all" alt={`Page ${idx + 1}`} />
                                    <div className="absolute bottom-1 left-1 text-white text-[8px] font-bold px-1.5 py-0.5 rounded-none bg-zinc-900 border border-zinc-800">
                                      Page {idx + 1}
                                    </div>
                                    <button
                                      onClick={() => rotatePage(globalIndex)}
                                      className="absolute top-1 right-7 bg-brand-600 text-white p-0.5 rounded-none hover:bg-brand-700 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                                      title="Rotate 90° Clockwise"
                                    >
                                      <RotateCw className="w-3 h-3" />
                                    </button>
                                    <button
                                      onClick={() => {
                                        setScannedPages(prev => prev.filter((_, i) => i !== globalIndex));
                                        setCurrentExamPageCount(prev => Math.max(0, prev - 1));
                                      }}
                                      className="absolute top-1 right-1 bg-red-500 text-white p-0.5 rounded-none hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                                    >
                                      <X className="w-3 h-3" />
                                    </button>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* No scanners — show status message */}
                    {saneInstalled !== null && scannerDevices.length === 0 && !scannerLoading && (
                      <div className="text-center py-4">
                        <p className="text-xs text-foreground/50 italic">
                          {saneInstalled
                            ? "No scanners detected. Connect a flatbed scanner and click Refresh Devices."
                            : "Install SANE drivers to enable hardware scanning."}
                        </p>
                      </div>
                    )}

                    {/* File Upload Fallback — always available */}
                    <div className="border-t border-border-main pt-5">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-foreground/40 mb-3">Or upload scanned files manually</p>
                      <div 
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        className={cn(
                          "border-2 border-dashed rounded-none p-10 flex flex-col items-center justify-center text-center transition-all duration-300 cursor-pointer bg-surface",
                          dragActive ? "border-brand-500 bg-brand-500/5" : "border-border-main hover:border-brand-400 hover:bg-surface-soft"
                        )}
                      >
                        <Download className={cn("w-6 h-6 mb-3 transition-colors", dragActive ? "text-brand-600" : "text-foreground/30")} />
                        <p className="text-xs font-bold text-foreground/60">Drop exam images here (JPG/PNG)</p>
                        <p className="text-[10px] text-foreground/40 mt-1">For pre-scanned documents from external software</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Camera Capture Mode */}
              {uploadMode === "camera" && (
                <div className="bg-surface border border-border-main rounded-none p-8 shadow-none text-center space-y-6 max-w-xl mx-auto">
                  <h3 className="text-sm font-bold text-foreground">Live Exam Camera</h3>

                  {/* Dynamic device selector */}
                  {videoDevices.length > 1 && (
                    <div className="flex flex-col gap-1.5 items-start max-w-xs mx-auto text-left">
                      <label className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Select Video Device</label>
                      <select
                        value={selectedDeviceId}
                        onChange={(e) => setSelectedDeviceId(e.target.value)}
                        className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none cursor-pointer shadow-none"
                      >
                        {videoDevices.map(d => (
                          <option key={d.deviceId} value={d.deviceId}>{d.label || `Camera ${d.deviceId.substring(0,5)}`}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Student/Exam Label Input & Counter */}
                  <div className="bg-surface-soft p-4 border border-border-main space-y-3 text-left">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-brand-600">Active Exam Capture Group</span>
                      <span className="text-[10px] bg-brand-500/10 text-brand-600 px-2.5 py-1 font-black uppercase tracking-wider">
                        {expectedPageCount ? `${currentExamPageCount} of ${expectedPageCount} Pages` : `${currentExamPageCount} Pages`} Snapped
                      </span>
                    </div>
                    
                    <div className="space-y-1.5">
                      <label className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Student Name / Prefix (Optional)</label>
                      <input
                        type="text"
                        placeholder="e.g. Bruce Wayne"
                        value={examLabel}
                        onChange={(e) => setExamLabel(e.target.value)}
                        className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Pages per Exam (Optional)</label>
                      <input
                        type="number"
                        min={1}
                        placeholder="e.g. 3"
                        value={expectedPageCount}
                        onChange={(e) => setExpectedPageCount(e.target.value === "" ? "" : parseInt(e.target.value))}
                        className="w-full text-xs border border-border-main rounded-none p-2.5 bg-surface text-foreground focus:ring-1 focus:ring-brand-500 outline-none"
                      />
                    </div>
                  </div>

                  {cameraActive ? (
                    <div className="relative aspect-[4/3] bg-black rounded-none overflow-hidden shadow-none border border-border-main">
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="aspect-[4/3] bg-surface-soft border border-dashed border-border-main rounded-none flex flex-col items-center justify-center text-xs text-foreground/40 italic p-6">
                      {cameraError || "Connecting to camera stream..."}
                      <button onClick={() => startCamera()} className="mt-4 px-4 py-2 bg-brand-600 text-white text-xs font-bold rounded-none hover:bg-brand-700 transition-all cursor-pointer">Retry Connection</button>
                    </div>
                  )}
                  
                  {cameraActive && (
                    <div className="space-y-4">
                      <div className="flex gap-4 justify-center">
                        <button
                          onClick={captureImage}
                          disabled={expectedPageCount !== "" && currentExamPageCount >= expectedPageCount}
                          className="px-5 py-3 bg-brand-600 text-white text-xs font-bold rounded-none hover:bg-brand-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-none"
                        >
                          <Camera className="w-4 h-4" />
                          {expectedPageCount ? (currentExamPageCount >= expectedPageCount ? "All Pages Snapped" : `Snap Page ${currentExamPageCount + 1} of ${expectedPageCount}`) : `Snap Page ${currentExamPageCount + 1}`}
                        </button>

                        {currentExamPageCount > 0 && (
                          <div className="flex gap-2">
                            <button
                              onClick={finishCurrentExam}
                              className="px-5 py-3 bg-emerald-600 text-white text-xs font-bold rounded-none hover:bg-emerald-700 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-none"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                              Save Exam ({currentExamPageCount} pages)
                            </button>
                            <button
                              onClick={() => downloadGroupPdf(examLabel.trim() ? `${examLabel.trim().replace(/[^a-zA-Z0-9]/g, "_")}_${currentExamId}` : `exam_${currentExamId}`, getCurrentExamPages())}
                              disabled={isCompilingPdf}
                              className="px-5 py-3 bg-brand-500/10 text-brand-600 hover:text-brand-700 hover:bg-brand-500/15 border border-brand-500/20 text-xs font-bold rounded-none transition-all flex items-center justify-center gap-2 cursor-pointer shadow-none"
                            >
                              {isCompilingPdf ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                              Download PDF
                            </button>
                          </div>
                        )}
                      </div>

                      {/* Active Exam Progress Preview */}
                      {currentExamPageCount > 0 && (
                        <div className="bg-surface-soft border border-border-main p-4 space-y-2 text-left">
                          <p className="text-[10px] uppercase font-bold tracking-wider text-foreground/50">Active Exam Pages Progress ({currentExamPageCount} pages)</p>
                          <div className="flex gap-3 overflow-x-auto pb-2 custom-scrollbar">
                            {getCurrentExamPages().map((page, idx) => {
                              const globalIndex = scannedPages.findIndex(x => x.file === page.file);
                              return (
                                <div key={idx} className="relative min-w-[80px] h-24 bg-surface rounded-none border border-border-main overflow-hidden group">
                                  <img src={page.url} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-all" alt={`Page ${idx + 1}`} />
                                  <div className="absolute bottom-1 left-1 text-white text-[8px] font-bold px-1.5 py-0.5 rounded-none bg-zinc-900 border border-zinc-800">
                                    Page {idx + 1}
                                  </div>
                                  <button
                                    onClick={() => rotatePage(globalIndex)}
                                    className="absolute top-1 right-7 bg-brand-600 text-white p-0.5 rounded-none hover:bg-brand-700 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                                    title="Rotate 90° Clockwise"
                                  >
                                    <RotateCw className="w-3 h-3" />
                                  </button>
                                  <button
                                    onClick={() => {
                                      setScannedPages(prev => prev.filter((_, i) => i !== globalIndex));
                                      setCurrentExamPageCount(prev => Math.max(0, prev - 1));
                                    }}
                                    className="absolute top-1 right-1 bg-red-500 text-white p-0.5 rounded-none hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                                  >
                                    <X className="w-3 h-3" />
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Bulk Zip Mode */}
              {uploadMode === "zip" && (
                <div className="bg-surface border border-border-main rounded-none p-8 shadow-none text-center space-y-6 max-w-xl mx-auto">
                  <div className="w-16 h-16 rounded-none bg-surface-soft flex items-center justify-center mx-auto shadow-none">
                    <Archive className="w-8 h-8 text-foreground/40" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">Upload Bulk Zip File</h3>
                  <p className="text-xs text-foreground/50 max-w-sm mx-auto font-medium leading-relaxed">
                    Upload a single `.zip` archive containing scanned JPEG/PNG exam pages. The backend will extract them automatically.
                  </p>
                  
                  <div className="max-w-md mx-auto">
                    <input
                      type="file"
                      accept=".zip"
                      onChange={handleZipSelect}
                      className="w-full text-xs text-foreground/70 file:mr-4 file:py-2.5 file:px-4 file:rounded-none file:border file:border-border-main file:text-xs file:font-bold file:bg-surface-soft file:text-foreground hover:file:bg-surface-soft/80 cursor-pointer"
                    />
                  </div>

                  {zipFile && (
                    <button
                      onClick={processZipBatch}
                      disabled={isUploadingZip}
                      className="w-full py-4 bg-brand-600 text-white text-sm font-black uppercase tracking-wider rounded-none hover:bg-brand-700 shadow-none hover:shadow-none transition-all flex items-center justify-center gap-3 cursor-pointer"
                    >
                      {isUploadingZip ? <Loader2 className="w-5 h-5 animate-spin" /> : <Layers className="w-5 h-5" />}
                      {isUploadingZip ? "Extracting & Uploading..." : "Process Zip Archive"}
                    </button>
                  )}
                </div>
              )}
              
              {/* Document Queue Display (Camera/Scanner list) */}
              {uploadMode !== "zip" && scannedPages.length > 0 && (
                <div className="bg-surface border border-border-main p-6 rounded-none shadow-none mt-8">
                  <div className="flex justify-between items-center mb-6 border-b border-border-main/50 pb-3">
                     <h3 className="text-sm font-bold text-foreground flex items-center gap-2"><FileText className="w-4 h-4 text-brand-500"/> Document Queue</h3>
                     <span className="text-xs font-black bg-brand-500/10 text-brand-600 px-3 py-1 rounded-none">
                       {getGroupedPages().length} Exam(s) | {scannedPages.length} Pages Pending
                     </span>
                  </div>
                  
                  <div className="space-y-6">
                    {getGroupedPages().map(([groupName, pages]) => (
                      <div key={groupName} className="bg-surface-soft border border-border-main p-4 space-y-3 text-left">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-bold text-foreground">{groupName.replace(/_/g, " ")}</span>
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => downloadGroupPdf(groupName, pages)}
                              className="text-[10px] font-bold uppercase tracking-wider text-brand-600 hover:text-brand-700 bg-brand-500/5 hover:bg-brand-500/10 px-2.5 py-1 border border-brand-500/20 transition-all flex items-center gap-1 cursor-pointer"
                            >
                              <Download className="w-3 h-3" /> Download PDF
                            </button>
                            <span className="text-[10px] text-foreground/50 font-bold uppercase tracking-wider">
                              {pages.length} {pages.length === 1 ? "page" : "pages"}
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex gap-4 overflow-x-auto pb-2 custom-scrollbar">
                           {pages.map((page, idx) => {
                             const globalIndex = scannedPages.findIndex(x => x.file === page.file);
                             return (
                               <div 
                                 key={idx} 
                                 className="relative min-w-[110px] h-36 bg-surface rounded-none border border-border-main overflow-hidden group cursor-pointer"
                                 onClick={() => {
                                   setPreviewModalUrl(page.url);
                                   setPreviewModalTitle(`${groupName.replace(/_/g, " ")} - Page ${idx + 1}`);
                                 }}
                               >
                                 <img 
                                   src={page.url} 
                                   className="w-full h-full object-cover opacity-85 group-hover:opacity-100 transition-all group-hover:scale-105" 
                                   alt={`Page ${idx + 1}`} 
                                 />
                                 <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-2">
                                   <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                                     <button 
                                       onClick={() => rotatePage(globalIndex)} 
                                       className="bg-brand-600 text-white p-1 rounded-none hover:bg-brand-700 transition-all shadow-none hover:scale-110 cursor-pointer"
                                       title="Rotate 90° Clockwise"
                                     >
                                       <RotateCw className="w-3 h-3"/>
                                     </button>
                                     <button 
                                       onClick={() => setScannedPages(prev => prev.filter((_, i) => i !== globalIndex))} 
                                       className="bg-red-500 text-white p-1 rounded-none hover:bg-red-600 transition-all shadow-none hover:scale-110 cursor-pointer"
                                       title="Delete Page"
                                     >
                                       <X className="w-3 h-3"/>
                                     </button>
                                   </div>

                                   <div className="flex items-center justify-between text-white text-[10px] font-extrabold tracking-wider uppercase">
                                     <span>Page {idx + 1}</span>
                                     <span className="bg-brand-500/80 px-1.5 py-0.5 rounded-none text-[9px] flex items-center gap-1">
                                       <Eye className="w-3 h-3" /> Preview
                                     </span>
                                   </div>
                                 </div>
                               </div>
                             );
                           })}
                        </div>
                      </div>
                    ))}
                  </div>

                  <button 
                    onClick={processBatch}
                    className="w-full mt-6 py-4 bg-brand-600 text-white text-sm font-black uppercase tracking-wider rounded-none hover:bg-brand-700 shadow-none hover:shadow-none transition-all flex items-center justify-center gap-3 group cursor-pointer"
                  >
                    <Layers className="w-5 h-5 group-hover:scale-110 transition-transform" /> Orchestrate Batch Grading
                  </button>
                </div>
              )}
            </div>
          )}

          {(isProcessing || batchStatus) && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700 font-outfit">
               <div className="bg-surface border border-border-main rounded-none p-8 shadow-none">
                 <div className="flex justify-between items-start mb-6">
                   <div>
                     <h3 className="text-xl font-black text-foreground mb-1 flex items-center gap-2">
                       Batch Progress Engine
                       {batchStatus?.status === "Processing" && (
                         <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-extrabold uppercase bg-brand-500/10 text-brand-600 border border-brand-500/30 animate-pulse">
                           Live SSE Stream Active
                         </span>
                       )}
                     </h3>
                     <p className="text-sm text-foreground/60">Batch ID: <span className="font-mono text-xs">{batchId}</span></p>
                   </div>
                   <div className={cn(
                     "px-4 py-1.5 rounded-none text-xs font-black uppercase tracking-wider flex items-center gap-2",
                     batchStatus?.status === "Completed" ? "bg-emerald-500/10 text-emerald-500" : "bg-brand-500/10 text-brand-500 animate-pulse"
                   )}>
                     {batchStatus?.status === "Completed" ? <CheckCircle2 className="w-4 h-4" /> : <Loader2 className="w-4 h-4 animate-spin" />}
                     {batchStatus?.status || "Processing"}
                   </div>
                 </div>

                 <div className="w-full h-3 bg-surface-soft rounded-none overflow-hidden mb-6 shadow-none">
                   <div 
                     className="h-full bg-brand-500 transition-all duration-700 ease-out" 
                     style={{ width: `${batchStatus?.total ? (batchStatus.processed / batchStatus.total) * 100 : 0}%` }}
                   >
                     <div className="w-full h-full bg-white/20 animate-[shimmer_2s_infinite]"></div>
                   </div>
                 </div>
                 
                 <div className="grid grid-cols-3 gap-6 text-center mb-8">
                   <div className="p-4 rounded-none bg-surface-soft border border-border-main">
                     <div className="text-3xl font-black text-foreground mb-1">{batchStatus?.processed || 0} / {batchStatus?.total || 0}</div>
                     <div className="text-[10px] font-bold uppercase tracking-widest text-foreground/50">Graded</div>
                   </div>
                   <div className={cn("p-4 rounded-none border transition-colors", batchStatus?.needs_review > 0 ? "bg-amber-500/10 border-amber-500/30" : "bg-surface-soft border-border-main")}>
                     <div className={cn("text-3xl font-black mb-1", batchStatus?.needs_review > 0 ? "text-amber-500" : "text-foreground")}>{batchStatus?.needs_review || 0}</div>
                     <div className="text-[10px] font-bold uppercase tracking-widest text-foreground/50">Manual Review</div>
                   </div>
                   <div className="p-4 rounded-none bg-surface-soft border border-border-main">
                     <div className="text-3xl font-black text-foreground mb-1">{batchStatus?.status === "Completed" ? "100%" : "—"}</div>
                     <div className="text-[10px] font-bold uppercase tracking-widest text-foreground/50">Confidence</div>
                   </div>
                 </div>

                 {/* ── LIVE PER-PAPER PROGRESS CARDS ── */}
                 {Object.keys(livePapers).length > 0 && (
                   <div className="mt-8 pt-6 border-t border-border-main">
                     <h4 className="text-xs font-black uppercase tracking-wider text-foreground/70 mb-4 flex items-center gap-2">
                       <Layers className="w-4 h-4 text-brand-500" /> Live Paper Micro-Phases
                     </h4>
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-60 overflow-y-auto pr-1">
                       {Object.values(livePapers).map((paper: any) => (
                         <div key={paper.paper_idx} className="p-3 border border-border-main bg-surface-soft flex items-center justify-between font-outfit">
                           <div>
                             <div className="font-bold text-sm text-foreground flex items-center gap-2">
                               {paper.student_name}
                               {paper.status === "completed" && <span className="text-[10px] bg-emerald-500/10 text-emerald-600 px-1.5 py-0.5 font-black border border-emerald-500/20">DONE</span>}
                               {paper.status === "grading" && <span className="text-[10px] bg-brand-500/10 text-brand-600 px-1.5 py-0.5 font-black border border-brand-500/20 animate-pulse">GRADING</span>}
                               {paper.status === "extracting" && <span className="text-[10px] bg-sky-500/10 text-sky-600 px-1.5 py-0.5 font-black border border-sky-500/20 animate-pulse">OCR</span>}
                             </div>
                             <div className="text-xs text-foreground/60 mt-0.5 flex items-center gap-2">
                               <span>{paper.phase}</span>
                               {paper.questions_found && <span>• {paper.questions_found} Qs Extracted</span>}
                             </div>
                           </div>
                           {paper.score !== undefined && (
                             <div className="text-right">
                               <div className="text-sm font-black text-brand-600">{paper.score} / {paper.max_score}</div>
                               <div className="text-[10px] font-bold text-foreground/50">{paper.questions_count} Qs Graded</div>
                             </div>
                           )}
                         </div>
                       ))}
                     </div>
                   </div>
                 )}

                 {/* ── LIVE STREAM TERMINAL LOG ── */}
                 {liveLogs.length > 0 && (
                   <div className="mt-6 pt-6 border-t border-border-main font-mono text-xs">
                     <div className="flex justify-between items-center mb-2">
                       <span className="text-[10px] font-bold uppercase tracking-widest text-foreground/50 flex items-center gap-1.5">
                         <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping inline-block" /> Live Server Log Feed
                       </span>
                       <span className="text-[10px] text-foreground/40">{liveLogs.length} events</span>
                     </div>
                     <div className="bg-zinc-950 text-emerald-400 p-4 rounded-none h-40 overflow-y-auto space-y-1.5 shadow-inner">
                       {liveLogs.map((log, idx) => (
                         <div key={idx} className="flex gap-2">
                           <span className="text-zinc-600 select-none">[{log.time}]</span>
                           <span className={cn(
                             log.type === "success" && "text-emerald-400 font-bold",
                             log.type === "error" && "text-rose-400 font-bold",
                             log.type === "warning" && "text-amber-300",
                             log.type === "info" && "text-zinc-300"
                           )}>{log.message}</span>
                         </div>
                       ))}
                     </div>
                   </div>
                 )}
               </div>
            </div>
          )}

          {!configLocked && (
            <div className="flex flex-col items-center justify-center text-center opacity-40 pointer-events-none mt-12 pb-12">
               <FileCheck className="w-20 h-20 mb-5 text-foreground/40" />
               <h3 className="text-xl font-bold text-foreground">Awaiting Context</h3>
               <p className="text-sm text-foreground/60 mt-2 max-w-sm">Configure and lock the academic context on the left to initiate the batch grading engine.</p>
            </div>
          )}
        </div>
      </div>

      {/* Multi-Page Completion Prompt Modal */}
      {showNextExamPrompt && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-surface border border-border-main p-6 max-w-sm w-full space-y-5 animate-in fade-in zoom-in-95 duration-200 text-center font-outfit shadow-2xl">
            <div className="w-12 h-12 rounded-none bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6 text-brand-600" />
            </div>
            <div className="space-y-2">
              <h3 className="text-sm font-black uppercase tracking-wider text-foreground">Exam Complete</h3>
              <p className="text-xs text-foreground/60 leading-relaxed font-medium">
                All <span className="font-bold text-foreground">{expectedPageCount}</span> pages for <span className="font-bold text-foreground">{examLabel.trim() || `Student Exam #${currentExamId.substring(0, 6)}`}</span> have been scanned.
              </p>
              <p className="text-[11px] text-foreground/40 font-medium">
                Would you like to finalize this exam and start scanning the next student's paper?
              </p>
            </div>
            <div className="space-y-2 pt-2">
              <button
                onClick={() => {
                  finishCurrentExam();
                  setShowNextExamPrompt(false);
                }}
                className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold uppercase tracking-wider rounded-none transition-all cursor-pointer border-none outline-none"
              >
                Yes, Start Next Exam
              </button>
              <button
                onClick={() => setShowNextExamPrompt(false)}
                className="w-full py-2.5 bg-transparent border border-border-main text-foreground opacity-60 hover:opacity-100 text-xs font-bold uppercase tracking-wider rounded-none transition-all cursor-pointer"
              >
                No, Review Pages
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── SCANNED PAGE FULL-SCREEN PREVIEW MODAL ── */}
      {previewModalUrl && (
        <div 
          className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-6 animate-in fade-in duration-300 font-outfit"
          onClick={() => setPreviewModalUrl(null)}
        >
          <div 
            className="bg-surface border border-border-main max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border-main bg-surface-soft">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-brand-500" />
                <h3 className="font-extrabold text-sm text-foreground uppercase tracking-wider">{previewModalTitle}</h3>
              </div>
              <button 
                onClick={() => setPreviewModalUrl(null)}
                className="p-1.5 hover:bg-foreground/10 text-foreground transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Image Display */}
            <div className="flex-1 bg-zinc-950 p-6 flex items-center justify-center overflow-auto">
              <img 
                src={previewModalUrl} 
                alt="Scanned Exam Page Preview" 
                className="max-h-[75vh] w-auto object-contain border border-zinc-800 shadow-xl"
              />
            </div>

            {/* Modal Footer Controls */}
            <div className="flex items-center justify-between px-6 py-3 border-t border-border-main bg-surface-soft text-xs text-foreground/70 font-bold">
              <span>Click outside or press X to return to Document Queue</span>
              <a 
                href={previewModalUrl} 
                download="scanned_exam_page.jpg" 
                target="_blank" 
                rel="noreferrer"
                className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-1.5 rounded-none uppercase text-[11px] font-black tracking-wider flex items-center gap-2 cursor-pointer transition-colors"
              >
                <Download className="w-3.5 h-3.5" /> Download High-Res Image
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

