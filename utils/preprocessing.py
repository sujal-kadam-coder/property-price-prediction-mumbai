import pandas as pd
import numpy as np

def load_and_prepare(path):
    df = pd.read_csv(path).copy()
    for c in ["price", "area", "bhk"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["price_unit"] = df["price_unit"].astype(str).str.strip().str.upper()
    df["price_in_lakh"] = np.where(df["price_unit"].eq("CR"), df["price"] * 100, df["price"])
    df = df.dropna(subset=["price_in_lakh","bhk","area","type","region","status","age"])
    df = df[df["area"] > 0].copy()
    df["price_per_sqft"] = df["price_in_lakh"] * 100000 / df["area"]
    return df

def format_inr(lakh):
    lakh = float(lakh)
    if lakh >= 100:
        return f"₹{lakh/100:.2f} Cr"
    return f"₹{lakh:.2f} L"
