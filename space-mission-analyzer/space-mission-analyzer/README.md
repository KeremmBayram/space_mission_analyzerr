# Space Mission Analyzer 🚀

Full-stack space mission analytics project built with Flask, SQLite, Pandas, Scikit-learn and Plotly.

## Features
- Historical mission database
- Mission search and filters
- KPI dashboard
- Success-rate analysis by target
- Agency performance analysis
- AI/ML mission success probability estimator
- NASA Astronomy Picture of the Day integration
- REST API endpoints
- Add-mission API

## Run on Windows

```powershell
cd space-mission-analyzer
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Then open:

http://127.0.0.1:5000

## Run on macOS/Linux

```bash
cd space-mission-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## API
- GET `/api/missions`
- GET `/api/stats`
- POST `/api/predict`
- GET `/api/nasa/apod`
- POST `/api/missions`

The included dataset is a demo dataset. For a serious ML project, replace it with a larger historical dataset and evaluate the model with cross-validation, precision, recall, F1 and ROC-AUC.
