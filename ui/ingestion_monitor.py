import os
import io
import re
import json
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_JSON = os.path.join(BASE_DIR, "extracted_syllabus_data.json")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

# ─── SVG Icon Library ───────────────────────────────────────────────────────
def _svg(path_d, size=14, stroke="#800020", fill="none", sw=2):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round">{path_d}</svg>')

ICON_DB      = _svg('<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>', stroke="white")
ICON_DOC     = _svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>')
ICON_OK      = _svg('<polyline points="20 6 9 17 4 12"/>', stroke="#16a34a", sw=2.5)
ICON_SKIP    = _svg('<circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/>', stroke="#f59e0b", sw=2)
ICON_WARN    = _svg('<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>', stroke="#ef4444", sw=2)
ICON_ARROW   = _svg('<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>', stroke="#800020")
ICON_REFRESH = _svg('<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>', stroke="#2563eb")


# ─── Lazy Imports ────────────────────────────────────────────────────────────
def _get_chromadb():
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        return chromadb, embedding_functions
    except ImportError:
        return None, None

def _get_pdf_reader():
    try:
        from PyPDF2 import PdfReader
        return PdfReader
    except ImportError:
        return None

def _get_docx():
    try:
        import docx
        return docx
    except ImportError:
        return None


# ─── Text Extraction ─────────────────────────────────────────────────────────
def extract_text_from_pdf(file_bytes):
    PdfReader = _get_pdf_reader()
    if not PdfReader:
        return ""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        return f"[PDF Error: {e}]"

def extract_text_from_docx(file_bytes):
    docx = _get_docx()
    if not docx:
        return ""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"[DOCX Error: {e}]"


# ─── Metadata Inference ───────────────────────────────────────────────────────
def infer_metadata(filename):
    fl = filename.lower()
    meta = {"level": "Unknown", "subject": "Unknown", "term": "Unknown", "doc_type": "Other"}
    lm = re.search(r'\b[ps]\s*\.?\s*([1-7])\b', fl)
    if lm:
        meta["level"] = ("P" if "p" in lm.group(0) else "S") + lm.group(1)
    for kw, val in [("primary one","P1"),("primary two","P2"),("primary three","P3"),
                    ("primary four","P4"),("primary five","P5"),("primary six","P6"),("primary seven","P7")]:
        if kw in fl: meta["level"] = val
    if re.search(r'\b(maths?|mathematics|mtc)\b', fl): meta["subject"] = "Mathematics"
    elif re.search(r'\b(eng|english)\b', fl): meta["subject"] = "English"
    elif re.search(r'\b(sci|science)\b', fl): meta["subject"] = "Science"
    elif re.search(r'\b(sst|social.?studies)\b', fl): meta["subject"] = "Social Studies"
    elif re.search(r'\b(physics|phy)\b', fl): meta["subject"] = "Physics"
    elif re.search(r'\b(chemistry|chem)\b', fl): meta["subject"] = "Chemistry"
    elif re.search(r'\b(biology|bio)\b', fl): meta["subject"] = "Biology"
    tm = re.search(r'term\s*([1-3]|i{1,3}|one|two|three)', fl)
    if tm:
        tv = tm.group(1)
        meta["term"] = "Term 1" if tv in ['1','i','one'] else "Term 2" if tv in ['2','ii','two'] else "Term 3"
    if "scheme" in fl: meta["doc_type"] = "Scheme"
    elif any(k in fl for k in ["exam","mock","ple","eot","bot"]): meta["doc_type"] = "Exam"
    elif any(k in fl for k in ["note","breakdown"]): meta["doc_type"] = "Notes"
    return meta


# ─── Chunking ─────────────────────────────────────────────────────────────────
def chunk_text(text, chunk_size=1500, overlap=200):
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            for sep in ['\n\n', '\n', ' ']:
                bp = text.rfind(sep, start, end)
                if bp > start:
                    end = bp
                    break
        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else len(text)
    return [c for c in chunks if c]


# ─── DB Stats ─────────────────────────────────────────────────────────────────
def get_db_stats():
    chromadb, embedding_functions = _get_chromadb()
    if not chromadb:
        return None
    try:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        client = chromadb.PersistentClient(path=DB_DIR)
        ef = embedding_functions.OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-3-small")
        col = client.get_or_create_collection(name="exam_syllabus_collection", embedding_function=ef)
        data = col.get(include=["metadatas"])
        filenames = set(m["filename"] for m in data["metadatas"] if m and "filename" in m)
        return {"total_chunks": len(data["ids"]), "total_files": len(filenames), "filenames": sorted(filenames)}
    except Exception:
        return {"total_chunks": 0, "total_files": 0, "filenames": []}


# ─── Stat Card ────────────────────────────────────────────────────────────────
def _stat_card(label, value, accent, icon_svg):
    st.markdown(f"""
    <div style="background:white;border-radius:10px;padding:14px 16px;
                border-top:3px solid {accent};box-shadow:0 1px 6px rgba(0,0,0,0.06);
                display:flex;align-items:center;gap:12px;">
        <div style="background:{accent}18;border-radius:8px;padding:8px;flex-shrink:0;">
            {icon_svg}
        </div>
        <div>
            <div style="font-size:8px;font-weight:900;color:#94a3b8;letter-spacing:2px;text-transform:uppercase;">{label}</div>
            <div style="font-size:22px;font-weight:900;color:{accent};line-height:1.1;margin-top:2px;">{value}</div>
        </div>
    </div>""", unsafe_allow_html=True)


# ─── Log Row ──────────────────────────────────────────────────────────────────
def _log_row(icon, fname, detail, bg="#f8fafc"):
    return f"""
    <div style="display:flex;align-items:flex-start;gap:10px;padding:7px 10px;
                border-radius:7px;background:{bg};margin-bottom:4px;">
        <div style="margin-top:1px;flex-shrink:0;">{icon}</div>
        <div>
            <div style="font-size:11px;font-weight:700;color:#1e293b;
                        overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:380px;"
                 title="{fname}">{fname}</div>
            <div style="font-size:9px;color:#64748b;margin-top:1px;">{detail}</div>
        </div>
    </div>"""


# ─── Main Page ────────────────────────────────────────────────────────────────
def render_ingestion_page():

    # ── Page CSS ──
    st.markdown("""<style>
        /* compact section label */
        .sec-label {
            font-size:8px;font-weight:900;color:#94a3b8;letter-spacing:2.5px;
            text-transform:uppercase;margin:14px 0 6px 0;
            display:flex;align-items:center;gap:8px;
        }
        .sec-label::after{content:'';flex:1;height:1px;background:#f1f5f9;}
        /* document list card */
        .doc-row {
            background:white;border-radius:7px;padding:8px 12px;
            margin-bottom:4px;border-left:3px solid #800020;
            box-shadow:0 1px 3px rgba(0,0,0,0.04);
        }
        .doc-row-name{font-size:11px;font-weight:700;color:#1e293b;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
        .doc-row-meta{font-size:9px;color:#94a3b8;margin-top:1px;}
        /* action buttons — primary override */
        .ingest-btn .stButton>button{
            border-radius:8px !important;font-weight:700 !important;
            font-size:12px !important;letter-spacing:0.5px !important;
        }
    </style>""", unsafe_allow_html=True)

    # ── Header Banner ──
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#800020 0%,#5a0015 100%);
                border-radius:12px;padding:18px 24px;margin-bottom:18px;
                display:flex;align-items:center;justify-content:space-between;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="background:rgba(255,255,255,0.12);border-radius:8px;padding:8px;">
                {ICON_DB}
            </div>
            <div>
                <div style="font-size:16px;font-weight:900;letter-spacing:2px;color:white;">
                    DATA INGESTION <span style="font-weight:300;opacity:0.6;">MONITOR</span>
                </div>
                <div style="font-size:8px;color:rgba(255,255,255,0.5);letter-spacing:2.5px;margin-top:2px;">
                    ADMIN &middot; VECTOR DATABASE MANAGEMENT
                </div>
            </div>
        </div>
        <div style="display:flex;gap:8px;">
            <div style="background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.15);
                        border-radius:20px;padding:3px 12px;font-size:8px;font-weight:700;
                        color:white;letter-spacing:1px;">RAG-SYNAPSE v4</div>
            <div style="background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.15);
                        border-radius:20px;padding:3px 12px;font-size:8px;font-weight:700;
                        color:white;letter-spacing:1px;">INCREMENTAL</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stat Row ──
    stats = get_db_stats()
    json_size = os.path.getsize(OUTPUT_JSON) // 1024 if os.path.exists(OUTPUT_JSON) else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _stat_card("Chunks in DB", f"{stats['total_chunks']:,}" if stats else "—", "#800020",
                   _svg('<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>', stroke="#800020"))
    with c2:
        _stat_card("Docs Embedded", f"{stats['total_files']:,}" if stats else "—", "#16a34a",
                   _svg('<path d="M14 2H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8z"/><polyline points="14 2 14 8 20 8"/><polyline points="9 13 12 16 15 13"/>', stroke="#16a34a"))
    with c3:
        _stat_card("Dataset Size", f"{json_size:,} KB", "#2563eb",
                   _svg('<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>', stroke="#2563eb"))
    with c4:
        json_count = 0
        if os.path.exists(OUTPUT_JSON):
            try:
                with open(OUTPUT_JSON) as f:
                    json_count = len(json.load(f))
            except Exception:
                pass
        _stat_card("Extracted Docs", f"{json_count:,}", "#7c3aed",
                   _svg('<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>', stroke="#7c3aed"))

    st.markdown("<div style='margin:12px 0 0 0;'></div>", unsafe_allow_html=True)

    # ── Two-Column Layout ──
    left, right = st.columns([1.5, 1], gap="medium")

    # ═══════════════════════════════════════════════════════════
    # LEFT: Actions
    # ═══════════════════════════════════════════════════════════
    with left:

        # ── Upload Zone ──
        st.markdown("<div class='sec-label'>Upload New Documents</div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Drop PDFs or Word documents here",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="visible",
            help="Supports PDF and DOCX. Files already in the dataset will be skipped automatically."
        )

        if uploaded_files:
            file_html = ""
            for uf in uploaded_files:
                ext = uf.name.rsplit(".", 1)[-1].upper()
                color = "#800020" if ext == "PDF" else "#2563eb"
                file_html += f"""
                <div style="display:flex;align-items:center;justify-content:space-between;
                            padding:6px 10px;border-radius:6px;background:#f8fafc;
                            border:1px solid #e2e8f0;margin-bottom:4px;">
                    <div style="font-size:11px;font-weight:600;color:#1e293b;
                                overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:260px;"
                         title="{uf.name}">{uf.name}</div>
                    <div style="font-size:8px;font-weight:900;color:{color};
                                background:{color}18;border-radius:4px;padding:2px 7px;flex-shrink:0;">{ext}</div>
                </div>"""
            st.markdown(file_html, unsafe_allow_html=True)

        # ── Step 1: Extract ──
        st.markdown("<div class='sec-label' style='margin-top:10px;'>Step 1 — Text Extraction</div>", unsafe_allow_html=True)

        col_s1, col_s1b = st.columns([3, 1])
        with col_s1:
            st.markdown("<div style='font-size:11px;color:#64748b;padding:2px 0;'>Parse new PDF/DOCX files and infer metadata (level, subject, term).</div>", unsafe_allow_html=True)
        with col_s1b:
            extract_btn = st.button("Extract", use_container_width=True, key="btn_extract")

        if extract_btn:
            if not uploaded_files:
                st.warning("Upload at least one file before extracting.")
            else:
                existing_dataset = []
                if os.path.exists(OUTPUT_JSON):
                    try:
                        with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
                            existing_dataset = json.load(f)
                    except Exception:
                        pass

                existing_filenames = {d.get("filename") for d in existing_dataset}
                new_docs = []
                log_html_parts = []

                prog = st.progress(0, text="Initialising...")
                log_area = st.empty()

                for idx, uf in enumerate(uploaded_files):
                    pct = int((idx / len(uploaded_files)) * 100)
                    prog.progress(pct, text=f"Reading {uf.name}  ({idx+1}/{len(uploaded_files)})")

                    if uf.name in existing_filenames:
                        log_html_parts.append(_log_row(ICON_SKIP, uf.name, "Already extracted — skipped"))
                        log_area.markdown("".join(log_html_parts), unsafe_allow_html=True)
                        continue

                    file_bytes = uf.read()
                    ext = uf.name.rsplit(".", 1)[-1].lower()
                    text = extract_text_from_pdf(file_bytes) if ext == "pdf" else extract_text_from_docx(file_bytes)

                    if len(text.strip()) > 50:
                        meta = infer_metadata(uf.name)
                        meta.update({"filename": uf.name, "content": text, "content_length": len(text)})
                        new_docs.append(meta)
                        log_html_parts.append(_log_row(ICON_OK, uf.name,
                            f"{len(text):,} chars &middot; {meta['level']} &middot; {meta['subject']} &middot; {meta['doc_type']}"))
                    else:
                        log_html_parts.append(_log_row(ICON_WARN, uf.name, "Too little text extracted — check scanned PDF"))

                    log_area.markdown("".join(log_html_parts), unsafe_allow_html=True)

                prog.progress(100, text="Extraction complete.")

                if new_docs:
                    final = existing_dataset + new_docs
                    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
                        json.dump(final, f, indent=4)
                    st.success(f"{len(new_docs)} new document(s) added. Dataset total: {len(final)}")
                    st.session_state["extraction_done"] = True
                else:
                    st.info("No new documents added — all files already in the dataset.")

        # ── Step 2: Embed ──
        st.markdown("<div class='sec-label' style='margin-top:10px;'>Step 2 — Embed & Train Vector DB</div>", unsafe_allow_html=True)

        col_s2, col_s2b = st.columns([3, 1])
        with col_s2:
            st.markdown("<div style='font-size:11px;color:#64748b;padding:2px 0;'>Send new documents to OpenAI for embedding. Only unembedded files are processed.</div>", unsafe_allow_html=True)
        with col_s2b:
            embed_btn = st.button("Embed", use_container_width=True, type="primary", key="btn_embed")

        if embed_btn:
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                st.error("OPENAI_API_KEY not found in .env file.")
            elif not os.path.exists(OUTPUT_JSON):
                st.error("No dataset found. Run Step 1 first.")
            else:
                chromadb_lib, embedding_functions = _get_chromadb()
                if not chromadb_lib:
                    st.error("ChromaDB not installed — run: pip install chromadb")
                else:
                    with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
                        dataset = json.load(f)

                    client = chromadb_lib.PersistentClient(path=DB_DIR)
                    ef = embedding_functions.OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-3-small")

                    existing_filenames, existing_chunk_count = set(), 0
                    col_ = client.get_or_create_collection(
                        name="exam_syllabus_collection", embedding_function=ef
                    )
                    try:
                        existing_data = col_.get(include=["metadatas"])
                        existing_filenames = {m["filename"] for m in existing_data["metadatas"] if m and "filename" in m}
                        existing_chunk_count = len(existing_data["ids"])
                        st.caption(f"Connected to DB — {len(existing_filenames)} docs already embedded.")
                    except Exception:
                        st.caption("Created a new ChromaDB collection.")

                    documents, metadatas, ids = [], [], []
                    chunk_id = existing_chunk_count
                    new_file_count = 0

                    for doc in dataset:
                        fn = str(doc.get("filename", "Unknown"))
                        if fn in existing_filenames or not doc.get("content"):
                            continue
                        new_file_count += 1
                        for chunk in chunk_text(doc["content"]):
                            documents.append(chunk)
                            metadatas.append({
                                "filename": fn,
                                "level":    str(doc.get("level",    "Unknown")),
                                "subject":  str(doc.get("subject",  "Unknown")),
                                "term":     str(doc.get("term",     "Unknown")),
                                "doc_type": str(doc.get("doc_type", "Unknown")),
                            })
                            ids.append(f"chunk_{chunk_id}")
                            chunk_id += 1

                    if not documents:
                        st.success("Vector DB is fully up-to-date. Nothing new to embed.")
                    else:
                        st.markdown(f"<div style='font-size:11px;color:#475569;margin:6px 0;'>Embedding <b>{len(documents)}</b> chunks from <b>{new_file_count}</b> document(s)…</div>", unsafe_allow_html=True)
                        embed_prog = st.progress(0, text="Connecting to OpenAI Embedding API…")
                        embed_log  = st.empty()
                        e_logs = []

                        batch_size   = 100
                        total_batches = (len(documents) + batch_size - 1) // batch_size

                        for b_idx, i in enumerate(range(0, len(documents), batch_size)):
                            end = min(i + batch_size, len(documents))
                            pct = int(((b_idx + 1) / total_batches) * 100)
                            embed_prog.progress(pct, text=f"Batch {b_idx+1}/{total_batches}  —  {end}/{len(documents)} chunks stored")
                            try:
                                col_.add(documents=documents[i:end], metadatas=metadatas[i:end], ids=ids[i:end])
                                e_logs.append(f"[OK] Batch {b_idx+1}/{total_batches} — chunks {i}–{end} stored.")
                            except Exception as e:
                                e_logs.append(f"[ERROR] Batch {b_idx+1} — {e}")
                            embed_log.code("\n".join(e_logs[-8:]), language=None)

                        embed_prog.progress(100, text="All chunks embedded successfully.")
                        st.success(f"{len(documents):,} chunks from {new_file_count} document(s) are now live in the Vector DB.")
                        st.balloons()

    # ═══════════════════════════════════════════════════════════
    # RIGHT: Document Registry
    # ═══════════════════════════════════════════════════════════
    with right:
        st.markdown("<div class='sec-label'>Vector DB Registry</div>", unsafe_allow_html=True)

        if not stats:
            st.warning("ChromaDB unavailable. Install with: pip install chromadb")
        elif not stats["filenames"]:
            st.markdown("""
            <div style="background:#f8fafc;border-radius:10px;padding:24px;text-align:center;
                        border:1px dashed #e2e8f0;color:#94a3b8;">
                <div style="font-size:11px;font-weight:700;">No documents embedded yet</div>
                <div style="font-size:10px;margin-top:4px;">Upload files and run Step 1 then Step 2</div>
            </div>""", unsafe_allow_html=True)
        else:
            # Subject filter
            all_subjects = sorted(set(infer_metadata(f)["subject"] for f in stats["filenames"]))
            filter_sub = st.selectbox("Filter by Subject", ["All"] + all_subjects,
                                      label_visibility="collapsed", key="reg_filter")

            rows_html = ""
            shown = 0
            for fname in stats["filenames"]:
                meta = infer_metadata(fname)
                if filter_sub != "All" and meta["subject"] != filter_sub:
                    continue
                shown += 1
                if shown > 40:
                    break
                dot_color = {"Exam":"#ef4444","Notes":"#16a34a","Scheme":"#f59e0b"}.get(meta["doc_type"], "#94a3b8")
                rows_html += f"""
                <div class="doc-row">
                    <div class="doc-row-name" title="{fname}">{fname}</div>
                    <div class="doc-row-meta">
                        <span style="display:inline-block;width:6px;height:6px;border-radius:50%;
                                     background:{dot_color};margin-right:4px;margin-bottom:-1px;"></span>
                        {meta['level']} &middot; {meta['subject']} &middot; {meta['doc_type']}
                    </div>
                </div>"""
            st.markdown(rows_html, unsafe_allow_html=True)
            if shown > 40:
                st.caption(f"Showing 40 of {len(stats['filenames'])} documents.")
            else:
                st.caption(f"{shown} document(s) shown.")
