from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
import json
from typing import List

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load JSON once at startup
json_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
if not os.path.exists(json_path):
    # On Vercel, api folder is root for function, so try parent folder
    json_path = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")

with open(json_path, "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

@app.post("/latency")
async def get_latency_metrics(payload: dict):
    regions: List[str] = payload.get("regions", [])
    threshold: float = payload.get("threshold_ms", 180)

    # Filter by regions if provided
    filtered = df[df["region"].isin(regions)] if regions else df

    response = {}
    for region in filtered["region"].unique():
        region_df = filtered[filtered["region"] == region]
        avg_latency = region_df["latency_ms"].mean()
        p95_latency = np.percentile(region_df["latency_ms"], 95)
        avg_uptime = region_df["uptime"].mean()
        breaches = (region_df["latency_ms"] > threshold).sum()

        response[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": int(breaches)
        }

    return response
