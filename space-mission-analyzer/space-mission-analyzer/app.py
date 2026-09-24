import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
import requests

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///missions.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    agency = db.Column(db.String(80), nullable=False)
    country = db.Column(db.String(80), nullable=False)
    mission_type = db.Column(db.String(80), nullable=False)
    launch_date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(40), nullable=False)
    success = db.Column(db.Boolean, nullable=False)
    cost_million = db.Column(db.Float, nullable=False)
    duration_days = db.Column(db.Float, nullable=False)
    crew = db.Column(db.Integer, nullable=False)
    target = db.Column(db.String(100), nullable=False)


SEED_DATA = [
    ["Apollo 11","NASA","USA","Crewed","1969-07-16","Success",True,355,8,3,"Moon"],
    ["Apollo 13","NASA","USA","Crewed","1970-04-11","Partial",False,375,6,3,"Moon"],
    ["Voyager 1","NASA","USA","Probe","1977-09-05","Success",True,250,18250,0,"Interstellar"],
    ["Mars Pathfinder","NASA","USA","Rover","1996-12-04","Success",True,280,83,0,"Mars"],
    ["Mars Climate Orbiter","NASA","USA","Orbiter","1998-12-11","Failure",False,327,286,0,"Mars"],
    ["Mars Reconnaissance Orbiter","NASA","USA","Orbiter","2005-08-12","Success",True,720,7000,0,"Mars"],
    ["Curiosity","NASA","USA","Rover","2011-11-26","Success",True,2500,5400,0,"Mars"],
    ["Perseverance","NASA","USA","Rover","2020-07-30","Success",True,2700,2200,0,"Mars"],
    ["James Webb Space Telescope","NASA/ESA/CSA","International","Telescope","2021-12-25","Success",True,10000,5000,0,"Deep Space"],
    ["Rosetta","ESA","Europe","Probe","2004-03-02","Success",True,1400,4500,0,"Comet"],
    ["Philae","ESA","Europe","Lander","2014-11-12","Partial",False,210,2,0,"Comet"],
    ["Sputnik 1","Soviet Union","USSR","Satellite","1957-10-04","Success",True,0.3,92,0,"Earth Orbit"],
    ["Vostok 1","Soviet Union","USSR","Crewed","1961-04-12","Success",True,30,1,1,"Earth Orbit"],
    ["Hubble Space Telescope","NASA/ESA","International","Telescope","1990-04-24","Success",True,4700,13000,0,"Earth Orbit"],
    ["Cassini-Huygens","NASA/ESA/ASI","International","Orbiter","1997-10-15","Success",True,3260,7300,0,"Saturn"],
    ["Chandrayaan-2","ISRO","India","Orbiter","2019-07-22","Partial",False,140,1500,0,"Moon"],
    ["Chandrayaan-3","ISRO","India","Lander","2023-07-14","Success",True,75,100,0,"Moon"],
    ["Hayabusa2","JAXA","Japan","Probe","2014-12-03","Success",True,280,2500,0,"Asteroid"],
    ["Chang'e 4","CNSA","China","Lander","2018-12-07","Success",True,180,2100,0,"Moon"],
    ["Artemis I","NASA","USA","Uncrewed","2022-11-16","Success",True,4100,25,0,"Moon"],
]


def seed_database():
    if Mission.query.count() == 0:
        for row in SEED_DATA:
            db.session.add(Mission(
                name=row[0], agency=row[1], country=row[2],
                mission_type=row[3], launch_date=row[4],
                status=row[5], success=row[6], cost_million=row[7],
                duration_days=row[8], crew=row[9], target=row[10]
            ))
        db.session.commit()


def missions_to_df():
    missions = Mission.query.all()
    return pd.DataFrame([{
        "name": m.name, "agency": m.agency, "country": m.country,
        "mission_type": m.mission_type, "launch_date": m.launch_date,
        "status": m.status, "success": int(m.success),
        "cost_million": m.cost_million, "duration_days": m.duration_days,
        "crew": m.crew, "target": m.target
    } for m in missions])


def train_model():
    df = missions_to_df()
    if len(df) < 5:
        return None
    X = df[["agency","country","mission_type","cost_million","duration_days","crew","target"]]
    y = df["success"]
    if y.nunique() < 2:
        return None

    categorical = ["agency","country","mission_type","target"]
    numeric = ["cost_million","duration_days","crew"]

    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ("num", StandardScaler(), numeric)
    ])

    model = Pipeline([
        ("prep", preprocessor),
        ("rf", RandomForestClassifier(
            n_estimators=250, random_state=42, class_weight="balanced"
        ))
    ])
    model.fit(X, y)
    return model


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/missions")
def api_missions():
    search = request.args.get("search", "").strip().lower()
    agency = request.args.get("agency", "")
    target = request.args.get("target", "")
    status = request.args.get("status", "")

    query = Mission.query
    if agency:
        query = query.filter_by(agency=agency)
    if target:
        query = query.filter_by(target=target)
    if status:
        query = query.filter_by(status=status)

    missions = query.order_by(Mission.launch_date.desc()).all()

    if search:
        missions = [
            m for m in missions
            if search in m.name.lower()
            or search in m.agency.lower()
            or search in m.country.lower()
            or search in m.target.lower()
        ]

    return jsonify([{
        "id": m.id, "name": m.name, "agency": m.agency,
        "country": m.country, "mission_type": m.mission_type,
        "launch_date": m.launch_date, "status": m.status,
        "success": m.success, "cost_million": m.cost_million,
        "duration_days": m.duration_days, "crew": m.crew,
        "target": m.target
    } for m in missions])


@app.route("/api/stats")
def api_stats():
    df = missions_to_df()
    success_count = int(df["success"].sum())
    total = len(df)

    by_target = df.groupby("target").agg(
        missions=("name","count"),
        success_rate=("success","mean")
    ).reset_index()
    by_target["success_rate"] = (by_target["success_rate"] * 100).round(1)

    by_agency = df.groupby("agency").agg(
        missions=("name","count"),
        success_rate=("success","mean"),
        avg_cost=("cost_million","mean")
    ).reset_index()
    by_agency["success_rate"] = (by_agency["success_rate"] * 100).round(1)
    by_agency["avg_cost"] = by_agency["avg_cost"].round(1)

    years = pd.to_datetime(df["launch_date"]).dt.year
    timeline = df.assign(year=years).groupby("year").agg(
        missions=("name","count"),
        successes=("success","sum")
    ).reset_index()

    return jsonify({
        "total": total,
        "successful": success_count,
        "failed_or_partial": total - success_count,
        "success_rate": round(success_count / total * 100, 1) if total else 0,
        "total_cost": round(float(df["cost_million"].sum()), 1),
        "avg_cost": round(float(df["cost_million"].mean()), 1),
        "by_target": by_target.to_dict("records"),
        "by_agency": by_agency.to_dict("records"),
        "timeline": timeline.to_dict("records")
    })


@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json()
    model = train_model()
    if model is None:
        return jsonify({"error": "Model için yeterli veri yok."}), 400

    row = pd.DataFrame([{
        "agency": data.get("agency", "NASA"),
        "country": data.get("country", "USA"),
        "mission_type": data.get("mission_type", "Rover"),
        "cost_million": float(data.get("cost_million", 500)),
        "duration_days": float(data.get("duration_days", 365)),
        "crew": int(data.get("crew", 0)),
        "target": data.get("target", "Mars")
    }])

    probability = float(model.predict_proba(row)[0][1])
    prediction = bool(model.predict(row)[0])

    return jsonify({
        "success_probability": round(probability * 100, 1),
        "prediction": "Likely Success" if prediction else "Higher Risk"
    })


@app.route("/api/nasa/apod")
def nasa_apod():
    key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    try:
        r = requests.get(
            "https://api.nasa.gov/planetary/apod",
            params={"api_key": key},
            timeout=10
        )
        r.raise_for_status()
        return jsonify(r.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


@app.post("/api/missions")
def add_mission():
    data = request.get_json()
    required = ["name", "agency", "country", "mission_type", "launch_date",
                "status", "cost_million", "duration_days", "crew", "target"]
    missing = [x for x in required if x not in data]
    if missing:
        return jsonify({"error": f"Eksik alanlar: {', '.join(missing)}"}), 400

    mission = Mission(
        name=data["name"], agency=data["agency"], country=data["country"],
        mission_type=data["mission_type"], launch_date=data["launch_date"],
        status=data["status"], success=data["status"] == "Success",
        cost_million=float(data["cost_million"]),
        duration_days=float(data["duration_days"]),
        crew=int(data["crew"]), target=data["target"]
    )
    db.session.add(mission)
    db.session.commit()
    return jsonify({"message": "Mission added", "id": mission.id}), 201


with app.app_context():
    db.create_all()
    seed_database()


if __name__ == "__main__":
    app.run(debug=True)
