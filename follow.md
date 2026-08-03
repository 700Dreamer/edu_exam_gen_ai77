# EduQuest AI Assessor — Project Progress & Context Guide (`follow.md`)

> **Note for AI Assistant in New Chat**: Read this file at the start of any new conversation to instantly understand the codebase architecture, design constraints, completed user requests, and current state.

---

## 1. Core Architecture & Stack

- **Application Name**: EduQuest AI Assessor
- **Frontend Directory**: `/Users/riky/Orlins/eduqest assessor/app/backend/src/front/ed_front`
- **Frontend Framework**: Next.js (App Router), React, TypeScript, TailwindCSS / Custom CSS tokens.
- **Backend Directory**: `/Users/riky/Orlins/eduqest assessor/app/backend/src`
- **Backend Framework**: FastAPI, Python, SQLAlchemy / PostgreSQL, Alembic.
- **Multi-Tenant Context**: `tenant_id` and `school_name` are persisted in `localStorage`. Backend proxy endpoints in `app/api/endpoints/results.py` process batch results per school.

---

## 2. Design System & Aesthetics Rules

1. **STRICT NO-EMOJI RULE** (`AGENTS.md` constraint):
   - **NEVER** use emojis anywhere in the codebase, UI, terminal logs, backend messages, or agent responses.
   - Use clean **Lucide icons**, status badges, or standard text formatting instead.
2. **Color Palette & Tokens**:
   - Signature Maroon/Burgundy (`#660033`, `bg-primary-600`), Deep Magenta (`#aa2e64`), Rich Berry (`#8b1a4a`), Muted Rose (`#b33c70`), Dark Wine (`#701a40`).
   - Clean dark-carbon text (`text-carbon`), soft fog borders (`border-fog`), and canvas backgrounds (`bg-canvas`).
3. **UI Patterns**:
   - Alternating Zebra Striping on table rows (`bg-pure-white` vs `bg-canvas/50`).
   - Minimalist 2px accent dots (`w-2 h-2 rounded-full`) per student, using deterministic system-tone maroon/berry hues.

---

## 3. Completed Key Pages & Components

### A. Dashboard Home (`/dashboard/page.tsx`)
- **School Benchmarking Widget**: Replaced "Grading Load" widget with a privacy-preserving School Benchmarking widget featuring a semi-circular SVG arc gauge, anonymized ranks, tier badges (Platinum/Gold/Silver/Bronze), and score deltas.
- **Student Energy Widget**: Replaced "Performance by Subject" with an 18-pill segmented progress bar (High Performers $\ge 70\%$, Balanced $50–69\%$, Needs Support $<50\%$), wired live to backend student test scores.

### B. Class Exam Results (`/dashboard/classes/[classId]/exams/[examId]/results/page.tsx`)
- Restored original rich multi-chart UI with 7 Recharts charts (Radar, Topic Heatmap, Performance Trend, Score Distribution, etc.), AI insights cards, and at-risk student table wired to live `/api/v1/results/batch/{batchId}/results`.

### C. Student Roster (`/dashboard/students/page.tsx`)
- **Class Pill Filter Tabs**: "All Classes" pill and individual class pills showing live student counts.
- **List & Grid Toggle**: Clean view switcher.
- **Inline Minimal Pagination**: Placed on the search bar row (`1–15 of 45` indicator with `<` `>` chevron controls), 15 items per page limit with auto-reset on filter change.
- **Zebra Striping & System-Tone Accent Dots**: Alternating row backgrounds and minimal maroon/berry accent dots.

### D. Academic Assessment Results (`/dashboard/results/page.tsx`)
- **4 View Modes**:
  1. `Session Broadsheet (All Subjects)`: Multi-subject broadsheet matrix displaying student marks across all subjects taken in that exam session, Total Score, Mean %, Grade, and Class Rank (`#1`, `#2`...).
  2. `Single Exam Results`: Batch inspector with expandable AI grading HTML proof reports.
  3. `Class Performance Summary`: Class-wide average score, pass rate %, and top performer metrics.
  4. `Student Report Card`: Official printable student report card layout.
- **Built-in A4 Print & PDF Engine (`@media print`)**:
  - Clicking **"Print / Export PDF"** triggers auto A4 landscape/portrait layout.
  - Hides screen-only controls and renders official school header, term session details, and Headmaster/Class Teacher signature blocks.

---

## 4. Primary Codebase Locations

| Module | File Path |
| :--- | :--- |
| **Main Dashboard** | `app/backend/src/front/ed_front/app/dashboard/page.tsx` |
| **Student Roster** | `app/backend/src/front/ed_front/app/dashboard/students/page.tsx` |
| **Results & Broadsheet** | `app/backend/src/front/ed_front/app/dashboard/results/page.tsx` |
| **Exam Class Results** | `app/backend/src/front/ed_front/app/dashboard/classes/[classId]/exams/[examId]/results/page.tsx` |
| **Backend Results API** | `app/backend/src/app/api/endpoints/results.py` |
| **Global Design System** | `app/backend/src/front/ed_front/app/globals.css` |
| **Repository Rules** | `AGENTS.md` |

---

## 5. Verification Commands

To verify frontend builds:
```bash
cd "/Users/riky/Orlins/eduqest assessor/app/backend/src/front/ed_front" && pnpm build
```

To run frontend dev server:
```bash
cd "/Users/riky/Orlins/eduqest assessor/app/backend/src/front/ed_front" && pnpm dev
```
