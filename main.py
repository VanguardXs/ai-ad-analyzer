"""
FastAPI backend for the AI Ad Creative Performance Analyzer.

Exposes a small REST API over the shared analysis core (ad_core) and serves a
static HTML/JS frontend. This separates the backend (data + LLM pipeline) from
the UI, which is closer to how a production automation service is built.

Endpoints:
    GET  /                          -> the web app
    POST /api/analyze               -> run the pipeline on an uploaded CSV or JSON file
    GET  /api/download/{id}/{kind}  -> download the Excel ("excel") or report ("report")

Run with:
    pip install -r requirements.txt
    uvicorn main:app --reload
"""

import html
import io
import os
import tempfile
import uuid

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import ad_core as ac

app = FastAPI(title="Ad Creative Performance Analyzer")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Generated reports, keyed by id, so the frontend can download them afterwards.
REPORTS: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as f:
        page = f.read()
    # Single source of truth for the default audience text lives in ad_core.
    return page.replace("{{TARGET_AUDIENCE}}", html.escape(ac.TARGET_AUDIENCE))


@app.post("/api/analyze")
async def analyze(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    metric: str = Form("ROAS"),
    top_n: int = Form(3),
    min_spend: float = Form(1000.0),
    audience: str = Form(""),
):
    """Run metrics -> winner detection -> creative analysis -> synthesis."""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required.")

    # Fall back to the default persona if the user cleared the field.
    audience = audience.strip() or ac.TARGET_AUDIENCE

    filename = file.filename or ""
    is_json = filename.lower().endswith(".json")
    try:
        raw = await file.read()
        if is_json:
            df = pd.read_json(io.BytesIO(raw))
        else:
            df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:  # noqa: BLE001
        kind = "JSON" if is_json else "CSV"
        raise HTTPException(status_code=400, detail=f"Could not read {kind} file: {e}")

    missing = [c for c in ac.REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400,
                            detail=f"Missing required columns: {', '.join(missing)}")

    client = ac.get_client(api_key)

    # Deterministic metrics + winner selection.
    metrics_df = ac.compute_metrics(df)
    winners = ac.pick_winners(metrics_df, metric=metric, top_n=int(top_n),
                              min_spend=float(min_spend))
    winner_names = list(winners["ad_name"])

    # LLM creative analysis per winner.
    analyses = {}
    for _, row in winners.iterrows():
        name = row["ad_name"]
        try:
            analyses[name] = ac.analyze_ad(str(row.get("transcript", "")), client,
                                           audience=audience)
        except Exception as e:  # noqa: BLE001
            analyses[name] = {"hook": "", "error": str(e)}

    # LLM strategic synthesis.
    payload = []
    for name in winner_names:
        row = metrics_df[metrics_df["ad_name"] == name].iloc[0]
        payload.append({
            "ad_name": name,
            "metrics": {"ROAS": float(row["ROAS"]), "CTR": float(row["CTR"]),
                        "CPA": float(row["CPA"]), "CVR": float(row["CVR"]),
                        "spend": float(row["spend"])},
            "creative_breakdown": analyses.get(name, {}),
        })
    try:
        insights = ac.synthesize_insights(payload, client, audience=audience)
    except Exception:  # noqa: BLE001
        insights = {}

    # Persist exports for download.
    report_id = uuid.uuid4().hex
    tmp = tempfile.mkdtemp(prefix="adreport_")
    xlsx_path = os.path.join(tmp, "ad_analysis.xlsx")
    md_path = os.path.join(tmp, "ad_analysis_report.md")
    with open(xlsx_path, "wb") as f:
        f.write(ac.build_excel_bytes(metrics_df, winner_names, analyses, insights))
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(ac.build_markdown_report(metrics_df, winner_names, analyses, insights, metric))
    REPORTS[report_id] = {"excel": xlsx_path, "report": md_path}

    # JSON response for the frontend.
    show_cols = ["ad_name", "spend", "impressions", "clicks", "conversions",
                 "revenue", "CTR", "CVR", "CPA", "ROAS", "AOV"]
    performance = []
    for _, row in metrics_df.iterrows():
        record = {c: (float(row[c]) if c != "ad_name" else row[c]) for c in show_cols}
        record["winner"] = row["ad_name"] in winner_names
        performance.append(record)

    return JSONResponse({
        "status": f"Analyzed {len(winner_names)} winning ads (by {metric}) "
                  f"out of {len(metrics_df)} total.",
        "metric": metric,
        "performance": performance,
        "analyses": analyses,
        "insights": insights,
        "report_id": report_id,
    })


@app.get("/api/download/{report_id}/{kind}")
def download(report_id: str, kind: str):
    entry = REPORTS.get(report_id)
    if not entry or kind not in entry:
        raise HTTPException(status_code=404, detail="Report not found.")
    filename = "ad_analysis.xlsx" if kind == "excel" else "ad_analysis_report.md"
    return FileResponse(entry[kind], filename=filename)
