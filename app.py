from flask import Flask, render_template, request, jsonify
from pathlib import Path
import pandas as pd
import numpy as np
import json, joblib
from config import *
from utils.preprocessing import load_and_prepare, format_inr

app = Flask(__name__)
DF = load_and_prepare(CSV_PATH)
METRICS = json.loads(Path("models/metrics.json").read_text())
INFO = json.loads(Path("models/feature_info.json").read_text())
MODELS = {
    "Linear Regression": joblib.load("models/linear_regression_pipeline.pkl"),
    "Random Forest": joblib.load("models/random_forest_pipeline.pkl")
}

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/metadata")
def metadata():
    return jsonify({
        "rows": len(DF),
        "regions": INFO["regions"],
        "types": INFO["types"],
        "statuses": INFO["statuses"],
        "ages": INFO["ages"],
        "bhk": INFO["bhk_values"],
        "stats": {
            "total": int(len(DF)),
            "regions": int(DF["region"].nunique()),
            "localities": int(DF["locality"].nunique()),
            "types": int(DF["type"].nunique()),
            "avg_price_lakh": float(DF["price_in_lakh"].mean()),
            "median_price_lakh": float(DF["price_in_lakh"].median()),
            "avg_area": float(DF["area"].mean()),
            "avg_ppsf": float(DF["price_per_sqft"].mean())
        }
    })

@app.get("/api/metrics")
def metrics():
    return jsonify({"metrics": METRICS, "model_used": INFO["default_model"]})

@app.post("/api/predict")
def predict():
    try:
        data = request.get_json(force=True)
        row = {
            "bhk": float(data["bhk"]),
            "type": str(data["type"]),
            "area": float(data["area"]),
            "region": str(data["region"]),
            "status": str(data["status"]),
            "age": str(data["age"])
        }
        if row["bhk"] <= 0 or row["area"] <= 0:
            raise ValueError("BHK and area must be positive.")
        # Model selection is automatic. User never chooses a model.
        model_name = INFO["default_model"]
        value = max(0.0, float(MODELS[model_name].predict(pd.DataFrame([row], columns=FEATURES))[0]))
        return jsonify({
            "predicted_price_lakh": value,
            "formatted_price": format_inr(value),
            "price_per_sqft": value * 100000 / row["area"],
            "model_used": model_name,
            "inputs": row
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/properties")
def properties():
    page = max(1, int(request.args.get("page", 1)))
    limit = min(18, max(1, int(request.args.get("limit", 12))))
    q = request.args.get("q", "").strip().lower()
    region = request.args.get("region", "")
    typ = request.args.get("type", "")
    status = request.args.get("status", "")
    age = request.args.get("age", "")
    bhk = request.args.get("bhk", "")
    sort = request.args.get("sort", "price_asc")
    d = DF
    if q:
        mask = d["region"].astype(str).str.lower().str.contains(q, na=False) | d["locality"].astype(str).str.lower().str.contains(q, na=False)
        d = d[mask]
    for col, val in [("region", region), ("type", typ), ("status", status), ("age", age)]:
        if val: d = d[d[col].astype(str) == val]
    if bhk:
        d = d[d["bhk"] == float(bhk)]
    sort_map = {"price_asc":"price_in_lakh","price_desc":"price_in_lakh","area_asc":"area","area_desc":"area","ppsf_asc":"price_per_sqft","ppsf_desc":"price_per_sqft"}
    d = d.sort_values(sort_map.get(sort, "price_in_lakh"), ascending=sort not in ["price_desc","area_desc","ppsf_desc"])
    total = len(d)
    start = (page - 1) * limit
    items = []
    for idx, r in d.iloc[start:start+limit].iterrows():
        items.append({
            "id": int(idx), "bhk": int(r.bhk), "type": r.type, "area": float(r.area),
            "locality": r.locality, "region": r.region, "status": r.status, "age": r.age,
            "price": format_inr(r.price_in_lakh), "price_lakh": float(r.price_in_lakh),
            "ppsf": float(r.price_per_sqft)
        })
    return jsonify({"items": items, "total": total, "page": page, "pages": max(1, int(np.ceil(total/limit)))})

@app.get("/api/similar")
def similar():
    try:
        bhk=float(request.args["bhk"]); area=float(request.args["area"])
        region=request.args["region"]; typ=request.args["type"]; status=request.args["status"]; age=request.args["age"]
        d=DF.copy()
        d["_score"]=(d["bhk"]-bhk).abs()*5+(d["area"]-area).abs()/max(area,1)*10+(d["region"].astype(str)!=region)*12+(d["type"].astype(str)!=typ)*6+(d["status"].astype(str)!=status)*2+(d["age"].astype(str)!=age)*2
        d=d.sort_values("_score").head(6)
        return jsonify({"items":[{"id":int(i),"bhk":int(r.bhk),"type":r.type,"area":float(r.area),"locality":r.locality,"region":r.region,"status":r.status,"age":r.age,"price":format_inr(r.price_in_lakh),"ppsf":float(r.price_per_sqft)} for i,r in d.iterrows()]})
    except Exception as e:
        return jsonify({"error":str(e)}),400

@app.get("/api/analytics")
def analytics():
    g=DF.groupby("region").agg(avg_price=("price_in_lakh","mean"),avg_ppsf=("price_per_sqft","mean"),count=("price_in_lakh","size")).sort_values("count",ascending=False).head(15)
    return jsonify({
        "regions":[{"name":str(i),"avg_price":float(r.avg_price),"avg_ppsf":float(r.avg_ppsf),"count":int(r["count"])} for i,r in g.iterrows()],
        "types":{str(k):int(v) for k,v in DF["type"].value_counts().items()},
        "bhk":{str(k):int(v) for k,v in DF["bhk"].value_counts().sort_index().items()},
        "status":{str(k):int(v) for k,v in DF["status"].value_counts().items()},
        "age":{str(k):int(v) for k,v in DF["age"].value_counts().items()}
    })

@app.post("/api/compare")
def compare():
    ids=request.get_json(force=True).get("ids",[])[:3]
    out=[]
    for idx in ids:
        try:
            r=DF.loc[int(idx)]
            out.append({"id":int(idx),"bhk":int(r.bhk),"type":r.type,"area":float(r.area),"locality":r.locality,"region":r.region,"status":r.status,"age":r.age,"price":format_inr(r.price_in_lakh),"ppsf":float(r.price_per_sqft)})
        except: pass
    return jsonify({"items":out})

if __name__ == "__main__":
    app.run(debug=True)
