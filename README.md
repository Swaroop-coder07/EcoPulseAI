# 🌱 EcoPulseAI

**Smart Campus Sustainability Platform**

EcoPulseAI is a sustainability analytics platform designed to help campuses monitor resource consumption, analyze usage trends, identify unusual consumption patterns, and discover opportunities to reduce environmental impact.

## ✨ Features

- 📊 **Analytics Dashboard** — View campus resource usage and sustainability metrics.
- 📅 **Monthly Analytics** — Compare monthly consumption, track trends, and analyze changes over time.
- ⚡ **Resource Monitoring** — Monitor energy and other campus resource usage.
- 🚨 **Anomaly Detection** — Identify unusual consumption patterns.
- 🌍 **Environmental Impact** — Estimate CO₂ emissions and potential savings.
- 💡 **Smart Recommendations** — Suggest actions to improve campus sustainability.

## 🛠️ Tech Stack

**Frontend**
- React
- Vite
- Tailwind CSS

**Backend**
- Python
- FastAPI
- SQLite

## 📁 Project Structure

```text
EcoPulseAI/
├── ecopulse-ai/
│   ├── backend/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── requirements.txt
│   └── frontend/
└── README.md
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Swaroop-coder07/EcoPulseAI.git
cd EcoPulseAI
```

### 2. Run the backend

```bash
cd ecopulse-ai/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend API documentation: `http://127.0.0.1:8000/docs`

### 3. Run the frontend

Open a new terminal:

```bash
cd ecopulse-ai/frontend
npm install
npm run dev
```

Open the local URL shown in your terminal, usually `http://localhost:5173`.

## 🎯 Project Goal

To support data-driven sustainability decisions by helping campuses understand resource usage, detect unusual patterns, and identify opportunities for reducing consumption and emissions.

## 👨‍💻 Author

**Swaroop-coder07**

GitHub: https://github.com/Swaroop-coder07

---

*EcoPulseAI — Building smarter and more sustainable campuses.*
