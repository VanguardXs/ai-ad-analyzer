# 📈 AI Ad Creative Performance Analyzer (FastAPI)

An AI automation tool for e-commerce / DTC brands that answers the question every performance team asks: **why are our winning ads winning — and what should we make next?**

This version is built as a **FastAPI backend + HTML/JS frontend**, separating the data/LLM pipeline (a clean REST API) from the UI — closer to how a production automation service is structured.

Upload your ad performance data with creative transcripts — as CSV or JSON — and the tool identifies your top performers by the metrics that matter, breaks down the creative strategy behind each winner, finds the patterns across them, and generates new ad concepts, hooks and scripts to test.

> It doesn't just summarize ads. It explains **what is working, why it is working, and how to use it** — then turns that into a testable creative plan.

---

## ✨ Features

- **REST API** — a documented `/api/analyze` endpoint you can call from any client, plus a built-in web UI.
- **Deterministic performance metrics** — CTR, CVR, CPA, ROAS and AOV computed in Python, never guessed by the LLM.
- **Winner detection** — rank ads by ROAS, CPA, CTR, CVR or revenue, with a minimum-spend filter.
- **Creative breakdown** — hook, hook type, angle, format, psychological triggers, and the pain points / desires each winner targets.
- **Pattern synthesis & audience insights** — what the winners share and why it works with this audience.
- **New concept generation** — ready-to-brief ad concepts with hooks, scripts, and a clear "what to test".
- **Exports** — multi-sheet Excel report and a shareable written report, served as download endpoints.

---

## 🛠️ Tech Stack

Python · FastAPI · Uvicorn · HTML / CSS / vanilla JS · LLM API · pandas · openpyxl

---

## 🚀 Getting Started

```bash
git clone https://github.com/<your-username>/ai-ad-analyzer-api.git
cd ai-ad-analyzer-api
pip install -r requirements.txt

uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`, enter your API key, upload `sample_ads.csv` (or `sample_ads.json`), and run the analysis.

Interactive API docs are auto-generated at `http://127.0.0.1:8000/docs`.

---

## 🧩 API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | The web app |
| `POST` | `/api/analyze` | Multipart form: `file` (CSV or JSON), `api_key`, `metric`, `top_n`, `min_spend` → JSON results |
| `GET` | `/api/download/{report_id}/excel` | Download the Excel report |
| `GET` | `/api/download/{report_id}/report` | Download the written report |

---

## 📥 Input Format

Either a CSV or a JSON file, one record per ad, with fields: `ad_name, spend, impressions, clicks, conversions, revenue, transcript`.

- CSV: standard header row, e.g. `sample_ads.csv`.
- JSON: an array of objects with the same fields, e.g. `sample_ads.json`. This is the shape ad platform APIs (e.g. Meta Ads) typically return, so accepting it directly is a step toward pulling data straight from those APIs instead of exporting to CSV first.

The file type is detected from the upload's filename extension (`.csv` vs `.json`).

---

## 📂 Project Structure

```
.
├── main.py              # FastAPI backend (API + serves the UI)
├── ad_core.py           # Metrics, LLM analysis/synthesis, Excel & report export
├── static/
│   ├── index.html       # Frontend markup
│   ├── style.css         # Styles
│   └── app.js           # Frontend logic (calls the API)
├── sample_ads.csv        # Example dataset (CSV)
├── sample_ads.json       # Example dataset (JSON)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 🔌 Extending to live ad platforms

The same pipeline can be fed from ad platforms via API (e.g. Meta Ads or creative-analytics tools) and run on a schedule to deliver recurring reports to Slack, Notion, Google Docs, or a dashboard.

---

## 📄 License

Released under the [MIT License](LICENSE).
