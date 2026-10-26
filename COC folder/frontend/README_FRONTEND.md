# AgriCost AI Frontend — React + Vite + TypeScript Client

**IT4010 Research Project — Web Client for Agricultural Cultivation Cost Prediction (SO1)**

---

## 1. Overview & Architecture

This client is a modern, responsive web dashboard built for agricultural extension officers, researchers, and farmers in Sri Lanka. It connects directly to the FastAPI REST backend exposing the tuned **Gradient Boosting Regressor** (`gb_tuned_v1`) trained on over a decade of Department of Agriculture (DOA) Cost of Cultivation (COC) survey records.

### Technology Stack
- **Framework**: Vite + React 18/19 + TypeScript
- **Styling**: Tailwind CSS + PostCSS + Inter Typography
- **Routing**: React Router v6
- **Server State & Caching**: TanStack Query (`@tanstack/react-query`)
- **Form State & Schema Validation**: React Hook Form + Zod (`@hookform/resolvers`)
- **Data Visualization**: Recharts (Horizontal TreeSHAP attributions)
- **Icons**: Lucide React
- **HTTP Client**: Axios with dynamic base URL and 422 error normalization
- **Batch CSV Parsing**: PapaParse

---

## 2. Prerequisites & Setup

### Prerequisites
- **Node.js**: v18.0.0 or later (v22+ supported)
- **npm**: v9.0.0 or later
- **FastAPI Backend**: Running at `http://localhost:8000`

### Installation
From the `frontend/` directory:
```bash
npm install
```

### Environment Configuration
The application reads from `.env.local` (or `.env`):
```env
VITE_API_BASE_URL=http://localhost:8000
```
*Note: If the backend runs on a different port or host, you can also change the API endpoint directly at runtime in the **Settings** page (`/settings`), which persists in browser `localStorage`.*

---

## 3. Running Locally

### Development Server
```bash
npm run dev
```
The application will launch at **`http://localhost:5173`**.

### Production Build
```bash
npm run build
```
Outputs optimized static assets to the `dist/` directory.

### Preview Production Build
```bash
npm run preview
```

---

## 4. Backend Connection & CORS

The FastAPI backend (`prediction_api.py`) is pre-configured with CORS middleware allowing:
- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:3000`

To start the backend server before testing the frontend:
```powershell
# From the parent directory:
python -m uvicorn prediction_api:app --host 0.0.0.0 --port 8000 --lifespan on
```

---

## 5. Component Ownership & Research Objective Mapping

| Route | Page Component | Research Objective & Owner | Description |
|---|---|---|---|
| `/` | `DashboardPage.tsx` | System Overview | Model status, active uptime, DOA survey scope, and recent 20 cached predictions. |
| `/predict` | `PredictPage.tsx` | **SO1 (Core Engine)** | Forward-looking prediction form (no year entry), auto-populated prior costs, 80% multiplicative intervals, and TreeSHAP horizontal bar chart. |
| `/model-comparison` | `ModelComparisonPage.tsx` | **SO1 (Evaluation)** | Comprehensive benchmark of 8 ML models (4 shallow vs. 4 deep) under LOSO CV with interactive Recharts bar chart, sortable metrics table, and architectural analysis. |
| `/batch` | `BatchPage.tsx` | **SO1 (Bulk Estimator)** | CSV dropzone (no year column needed), sample template generator, sequential progress bar, and exportable results table. |

---

### Predict Cost: Forward-Looking Planning Flow

The user experience is tailored specifically for agricultural extension officers projecting upcoming cultivation cycles:
- **No Year Input**: Officers never input a historical calendar year. The system automatically anchors predictions to **2025** (the latest Department of Agriculture survey baseline) and labels the forward planning horizon (e.g., *"Predicting for: Maha 2026/27 — Using 2025 reference data"*).
- **Auto-Populated Prior Costs**: Selecting a **District + Crop + Water Regime** queries `GET /defaults.latest_available_costs` and automatically inputs the latest surveyed cultivation cost. Officers can freely override this if they have more recent field figures.
- **Auto-Populated Currency Assumption**: Defaults to the latest Central Bank rate (**300.73 LKR/USD**), with an inline note that officers can override with current spot rates.
- **Dynamic Reference & Stale Baseline Warning**:
  - The prediction result highlights the baseline via a `Reference: 2025` pill.
  - If the reference year is at the training ceiling, the response displays an amber warning callout:
    > *"Prediction uses 2025 data as reference. Will improve when newer data is available."*
  - If the currency rate deviates by $>30\%$ from the historical mean (217.03 LKR/USD), an amber currency shock banner informs the officer that intervals have been widened by $1.5\times$.
| `/simulation` | `SimulationPage.tsx` | **SO2 (K.U.R.C.T Rathnayake)** | Interactive what-if policy and input shock simulation (fertilizer subsidies, currency swings). |
| `/expenses` | `ExpenseTrackerPage.tsx` | **SO3 (D.G.K.A Thasindu)** | Daily farm expenditure ledger (labor man-days, agrochemical invoices, budget variance). |
| `/chat` | `ChatPage.tsx` | LLM Advisory Shell | Natural language cost intelligence powered by narrative LLMs backed by SO1 models. |
| `/settings` | `SettingsPage.tsx` | Client Configuration | Endpoint override, live `/health` connection probe, and cache clearing. |

---

## 6. Integration Guide for SO2 & SO3 Teammates

To plug in your respective research modules:
1. **Create your view component** in `src/pages/` (e.g., `SimulationPage.tsx` for SO2, `ExpenseTrackerPage.tsx` for SO3).
2. **Mount sub-components** in `src/components/` (e.g., `src/components/simulation/` or `src/components/expenses/`).
3. **Verify the route** in `src/App.tsx`:
   ```tsx
   <Route path="/simulation" element={<SimulationPage />} />
   <Route path="/expenses" element={<ExpenseTrackerPage />} />
   ```
4. **Update the navigation item** in `src/components/layout/Sidebar.tsx` if additional sub-routes are needed.

---

## 7. Folder Structure

```
frontend/
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
├── .env.example
├── .env.local
├── README_FRONTEND.md
└── src/
    ├── App.tsx
    ├── index.css
    ├── main.tsx
    ├── api/
    │   ├── client.ts         # Axios instance, 422 error normalization
    │   ├── health.ts         # /health and /metadata endpoints
    │   └── prediction.ts     # /predict single and batch endpoints
    ├── components/
    │   ├── layout/
    │   │   ├── AppShell.tsx  # Main layout wrapper
    │   │   ├── Sidebar.tsx   # Fixed left nav drawer with mobile support
    │   │   └── TopBar.tsx    # Header with status dot and model pill
    │   └── predict/
    │       ├── PredictionForm.tsx    # Zod-validated input form
    │       ├── PredictionResult.tsx  # Cost, interval, confidence display
    │       └── SHAPBarChart.tsx      # Recharts TreeSHAP attribution
    ├── hooks/
    │   ├── useHealth.ts      # 30s polling query hook
    │   ├── useMetadata.ts    # 1hr cached query hook
    │   └── usePrediction.ts  # TanStack mutation hook
    ├── lib/
    │   ├── format.ts         # LKR currency, percentage, and label formatters
    │   └── storage.ts        # LocalStorage persistence for 20 recent runs
    └── types/
        └── api.ts            # TypeScript interfaces matching FastAPI schema
```
