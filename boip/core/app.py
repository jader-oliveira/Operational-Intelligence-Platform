"""boip-core — the FastAPI monolith from ADR 0016.

Run:  uvicorn boip.core.app:app --reload
Needs BOIP_DB_DSN (same as the collector) and the schema already applied.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from . import investigate as investigate_module
from . import queries

app = FastAPI(title="boip-core", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


class CreateIncident(BaseModel):
    title: str
    asset: str
    source_alert: dict = {}


class InvestigateRequest(BaseModel):
    lookback_hours: int = 24


@app.post("/incidents")
def create_incident(body: CreateIncident):
    return queries.create_incident(body.title, body.asset, body.source_alert)


@app.get("/incidents/{incident_id}")
def read_incident(incident_id: int):
    incident = queries.get_incident(incident_id)
    if incident is None:
        raise HTTPException(404, "incident not found")
    incident["evidence"] = queries.list_evidence(incident_id)
    return incident


@app.post("/incidents/{incident_id}/investigate")
def run_investigation(incident_id: int, body: InvestigateRequest = InvestigateRequest()):
    try:
        return investigate_module.investigate(incident_id, body.lookback_hours)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    incidents = queries.list_incidents()
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "incidents": incidents}
    )


@app.get("/incidents/{incident_id}/report", response_class=HTMLResponse)
def report_page(request: Request, incident_id: int):
    incident = queries.get_incident(incident_id)
    if incident is None:
        raise HTTPException(404, "incident not found")
    evidence = queries.list_evidence(incident_id)
    report = next((e["content"] for e in reversed(evidence) if e["kind"] == "investigation_report"), None)
    return templates.TemplateResponse(
        "report.html", {"request": request, "incident": incident, "report": report}
    )
