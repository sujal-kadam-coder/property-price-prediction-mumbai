import json
from pathlib import Path
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from config import *
from utils.preprocessing import load_and_prepare

df = load_and_prepare(CSV_PATH)
X, y = df[FEATURES], df[TARGET]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

pre = ColumnTransformer([
    ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), NUMERICAL_FEATURES),
    ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                      ("onehot", OneHotEncoder(handle_unknown="ignore"))]), CATEGORICAL_FEATURES)
])

models = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(n_estimators=180, random_state=42, n_jobs=-1, min_samples_leaf=2)
}
Path("models").mkdir(exist_ok=True)
metrics = {}
for name, estimator in models.items():
    pipe = Pipeline([("preprocess", pre), ("model", estimator)])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    metrics[name] = {
        "MAE_lakh": float(mean_absolute_error(y_test, pred)),
        "MSE_lakh2": float(mean_squared_error(y_test, pred)),
        "RMSE_lakh": float(mean_squared_error(y_test, pred) ** 0.5),
        "R2": float(r2_score(y_test, pred))
    }
    joblib.dump(pipe, Path("models") / ("linear_regression_pipeline.pkl" if name.startswith("Linear") else "random_forest_pipeline.pkl"))

default_model = min(metrics, key=lambda k: metrics[k]["RMSE_lakh"])
info = {
    "rows_used": int(len(df)),
    "features": FEATURES,
    "target": TARGET,
    "default_model": default_model,
    "regions": sorted(df["region"].astype(str).unique().tolist()),
    "types": sorted(df["type"].astype(str).unique().tolist()),
    "statuses": sorted(df["status"].astype(str).unique().tolist()),
    "ages": sorted(df["age"].astype(str).unique().tolist()),
    "bhk_values": sorted(int(x) for x in df["bhk"].dropna().unique())
}
Path("models/metrics.json").write_text(json.dumps(metrics, indent=2))
Path("models/feature_info.json").write_text(json.dumps(info, indent=2))
print(json.dumps(metrics, indent=2))
print("AUTOMATIC MODEL:", default_model)
