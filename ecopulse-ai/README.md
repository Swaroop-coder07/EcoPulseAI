# EcoPulse AI - Smart Campus Sustainability Platform

**Problem:** colleges do not track wastage of electricity, water and other resources.
EcoPulse AI records building-wise usage, detects abnormal consumption against a baseline,
suggests actions, and tracks the estimated environmental impact of those actions.

**Stack:** React + Tailwind CSS (frontend) · FastAPI (backend) · SQLite · Pandas.
Anomaly detection is rule-based for the MVP; scikit-learn can be added later.

## Run it

### 1. Backend (Python 3.10+)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
On first start the app creates `ecopulse.db`, loads `data/sample_readings.csv`
and runs anomaly detection, so no internet or sensors are needed for the demo.
Interactive API docs: http://localhost:8000/docs

Useful commands (inside `backend/`):
```bash
python seed.py --reset    # wipe the DB and reseed from the CSV
python seed.py --regen    # regenerate the CSV so it ends "yesterday", then reseed
```

### 2. Frontend (Node 18+)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. In dev, Vite proxies `/api` to `localhost:8000`.
(Hosting the backend elsewhere? Set `VITE_API_URL=http://host:8000`.)

## Folder structure
```
ecopulse-ai/
  frontend/   React app (pages: Dashboard, Buildings, Analytics, Actions)
  backend/
    main.py, database.py, models.py, schemas.py, seed.py, sample_data.py, config.py
    routers/    resources.py (dashboard, buildings, readings), analytics.py (the rest)
    services/   anomaly.py, impact.py, recommendations.py
  data/sample_readings.csv   simulated usage (6 buildings x 3 resources x 30 days)
```

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/dashboard | Dashboard summary |
| GET | /api/readings | Consumption readings (filters: building_id, resource_type, days) |
| POST | /api/readings | Add a reading (runs instant anomaly check) |
| GET | /api/buildings | List of buildings |
| GET | /api/analytics | Trends, baseline series, building comparison |
| GET | /api/alerts | Detected anomalies |
| GET | /api/recommendations | Suggested actions |
| POST | /api/actions/{id}/complete | Complete an action, award eco-points |
| GET | /api/impact | Potential vs estimated vs measured impact |
| GET | /api/leaderboard | Building efficiency ranking |

## Core logic (what to show the judges)
All tunables live in `backend/config.py` and can be overridden with environment variables.

1. **Baseline** = median of the building's previous 14 daily readings for that resource
   (median ignores earlier spikes). At least 7 days of history are required.
2. **Anomaly detection:** `Excess % = (Actual - Baseline) / Baseline x 100`.
   Alert if Excess % > 25 (`ALERT_THRESHOLD_PCT`). Example: baseline 100 kWh, actual 135 kWh -> 35% -> alert.
   Severity: low (<30%), medium (30-40%), high (40-60%), critical (60%+).
3. **Potential saving** = `max(0, Actual - Target)`, target = baseline. An estimated opportunity, not a verified saving.
4. **CO2e reduction** = `Energy saved x Emission factor`.
   Defaults: electricity 0.82 kg CO2e/kWh (approximate Indian grid average - verify against the latest CEA data
   before presenting), water 0.000344 kg/litre, waste 0.5 kg/kg (the water and waste factors are illustrative).
   Cost uses illustrative tariffs (INR 8/kWh, 0.05/litre, 2/kg). **Document your own sources and units in the demo.**
5. **Completing an action:** status -> completed, estimated savings recorded, eco-points =
   10 + 2 x kg CO2e avoided, impact summary refreshed.
6. **Estimated vs measured:** the impact page keeps three separate numbers - *potential* (open alerts),
   *estimated* (completed actions, from the alert excess) and *measured* (new readings recorded after completion
   that fall below the old baseline). Add a lower reading on the Buildings page after completing an action to see
   measured savings appear.
7. **Efficiency ranking:** `100 - average excess %` over the last 7 days across all resources (higher is better).

## Demo script
1. Dashboard: weekly totals, emissions, potential savings.
2. Buildings -> Science Block -> Electricity: the red dot is the anomaly; add a reading to see instant detection.
3. AI Insights: severity, hypothesis, recommended action, estimated saving.
4. Actions: mark one completed (eco-points awarded), then show estimated vs measured and the ranking.

## Team split
| Member | Responsibility | Where to look |
|---|---|---|
| 1 | React UI, dashboard, charts | `frontend/src/pages`, `components/Charts.jsx` |
| 2 | FastAPI, endpoints, integration | `backend/main.py`, `routers/`, `frontend/src/services/api.js` |
| 3 | Anomaly detection, analytics | `services/anomaly.py`, `routers/analytics.py` |
| 4 | Database, sample data, impact formulas | `models.py`, `sample_data.py`, `seed.py`, `services/impact.py` |
| 5 | Action tracker, testing, Git, demo | `pages/Actions.jsx`, `/docs` testing, this README |

Agree on the API contract above (also visible at `/docs`) and work in one shared Git repository.

## Limitations
- Data is simulated; thresholds and emission factors must be tuned with real campus data.
- Rule-based detection only (no ML yet); hypotheses are template-based suggestions, not diagnoses.
- No authentication - fine for a demo, not for production.
