---
title: "Intro to FastAPI"
subtitle: "Interacting with the DB and Web"
categories: [FastAPI, Python, SQL, PostgreSQL, Backend Development]
image_path: "../img"
---


## FastAPI Backend

At this stage, the backend is introduced as a **single-file FastAPI prototype**.

The goal is not yet full production integration. Instead, the goal is to define:

- the API idea,
- the request and response structure,
- the main endpoints,
- and how the frontend will later communicate with the backend.

This first version uses **dummy in-memory storage**, which means the API works without PostgreSQL. Later, the same structure can evolve into a full backend connected to the database.

---

## Overview

FastAPI is a modern Python framework for building APIs.

It is a strong choice for this project because it provides:

- simple endpoint creation,
- automatic validation with Pydantic,
- automatic API documentation,
- fast development for prototypes,
- and a clean path from MVP to production.

For our project, FastAPI will eventually sit between:

- the Streamlit frontend,
- and the PostgreSQL database.

```{mermaid}
flowchart TD
    A[Streamlit Frontend] --> B[FastAPI Backend]
    B --> C[PostgreSQL Database]
```

---

## Why FastAPI for This Project

FastAPI is useful here because the product needs structured communication between frontend and backend.

The frontend will later need to send requests such as:

- create a carousel,
- fetch available carousels,
- fetch the current visible alternatives,
- submit click or no-click feedback,
- request analytics for a carousel,
- reset or delete a project.

Instead of keeping this logic only inside Streamlit, FastAPI allows us to turn the product into a real service.

---

## What This Prototype Backend Does

This first backend version is intentionally simple.

It includes:

- one file only,
- all routes in one place,
- dummy in-memory storage,
- request and response models,
- and placeholder analytics logic.

This makes it easier to understand the API before splitting the project into:

- routers,
- services,
- schemas,
- and database layers.

---

## Planned API Endpoints

The prototype backend includes the following requests.

### General

- `GET /`
- `GET /health`

### Carousel Management

- `GET /carousels`
- `POST /carousels`
- `GET /carousels/{carousel_id}`
- `DELETE /carousels/{carousel_id}`
- `POST /carousels/{carousel_id}/reset`

### Carousel Interaction

- `GET /carousels/{carousel_id}/display`
- `POST /carousels/{carousel_id}/resample`
- `POST /carousels/{carousel_id}/feedback`
- `GET /carousels/{carousel_id}/events`

### Analytics

- `GET /carousels/{carousel_id}/analytics`

```{mermaid}
flowchart LR
    A[Create Carousel] --> B[Get Carousel]
    B --> C[Display Alternatives]
    C --> D[Submit Feedback]
    D --> E[Update Event History]
    E --> F[Request Analytics]
```

---

## Why a Single File First

At the prototype stage, keeping everything in one file is useful because it lets us focus on:

- the request flow,
- the endpoint names,
- the payload design,
- and the frontend-backend interaction.

Later, the same backend can be refactored into a more scalable structure.

A future version may look like:

```bash
app/backend/
├── main.py
├── routers/
├── schemas.py
├── db/
└── models/
```

But for now, one file is enough to validate the API design.

---

## Request and Response Design

FastAPI uses **Pydantic models** to validate requests and responses.

For example, when creating a carousel, the frontend should send:

- a carousel name,
- total number of alternatives,
- visible count.

When submitting feedback, the frontend should send:

- the selected carousel,
- and the clicked alternative id, or `null` for no click.

This makes the API predictable and safe.

---

## Full Dummy Backend in One File

Below is a simple one-file FastAPI backend that contains all the main prototype requests.

```python
from __future__ import annotations

import random
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(
    title="Bayesian Carousel Bandits API",
    version="0.1.0",
    description="Single-file FastAPI backend for the Streamlit MVP.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CAROUSELS: dict[str, dict[str, Any]] = {}
DEFAULT_ALPHA = 1.0
DEFAULT_BETA = 1.0


class CarouselCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    total_alternatives: int = Field(..., ge=2, le=1000)
    visible_count: int = Field(..., ge=1, le=100)


class FeedbackRequest(BaseModel):
    clicked_alt_id: Optional[int] = None


class AlternativeOut(BaseModel):
    alt_id: int
    title: str
    slot: int
    alpha: float
    beta: float
    impressions: int
    clicks: int
    posterior_mean: float
    empirical_ctr: float


class CarouselSummary(BaseModel):
    carousel_id: str
    name: str
    total_alternatives: int
    visible_count: int
    created_at: str
    round_number: int
    total_impressions: int
    total_clicks: int
    average_reward: float


class EventOut(BaseModel):
    timestamp: str
    round: int
    displayed: list[int]
    clicked: Optional[int]
    reward: int


class AnalyticsResponse(BaseModel):
    carousel_id: str
    name: str
    rounds: int
    total_impressions: int
    total_clicks: int
    average_reward: float
    champion_alt_id: Optional[int]
    champion_title: Optional[str]
    alternatives: list[dict[str, Any]]
    history: list[dict[str, Any]]


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_alternatives(total_alternatives: int) -> list[dict[str, Any]]:
    return [
        {
            "alt_id": i,
            "title": f"Alternative {i}",
            "alpha": DEFAULT_ALPHA,
            "beta": DEFAULT_BETA,
            "impressions": 0,
            "clicks": 0,
        }
        for i in range(1, total_alternatives + 1)
    ]


def get_carousel_or_404(carousel_id: str) -> dict[str, Any]:
    carousel = CAROUSELS.get(carousel_id)
    if not carousel:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return carousel


def get_stats(carousel: dict[str, Any]) -> list[dict[str, Any]]:
    stats: list[dict[str, Any]] = []
    for alt in carousel["alternatives"]:
        impressions = alt["impressions"]
        clicks = alt["clicks"]
        alpha = float(alt["alpha"])
        beta = float(alt["beta"])
        posterior_mean = alpha / (alpha + beta)
        empirical_ctr = (clicks / impressions) if impressions > 0 else 0.0

        row = dict(alt)
        row["posterior_mean"] = posterior_mean
        row["empirical_ctr"] = empirical_ctr
        stats.append(row)
    return stats


def sample_carousel(carousel: dict[str, Any]) -> list[int]:
    sampled: list[tuple[int, float]] = []
    for alt in carousel["alternatives"]:
        theta = random.betavariate(float(alt["alpha"]), float(alt["beta"]))
        sampled.append((int(alt["alt_id"]), theta))

    sampled.sort(key=lambda x: x[1], reverse=True)
    chosen = [alt_id for alt_id, _ in sampled[: carousel["visible_count"]]]
    carousel["current_display_ids"] = chosen
    return chosen


def current_display(carousel: dict[str, Any]) -> list[dict[str, Any]]:
    if not carousel["current_display_ids"]:
        sample_carousel(carousel)

    ids = carousel["current_display_ids"]
    stats = get_stats(carousel)
    selected = [row for row in stats if row["alt_id"] in ids]
    selected.sort(key=lambda row: ids.index(row["alt_id"]))

    out: list[dict[str, Any]] = []
    for idx, row in enumerate(selected, start=1):
        item = dict(row)
        item["slot"] = idx
        out.append(item)
    return out


def update_after_feedback(carousel: dict[str, Any], clicked_alt_id: Optional[int]) -> dict[str, Any]:
    displayed_ids = list(carousel["current_display_ids"])
    if not displayed_ids:
        displayed_ids = sample_carousel(carousel)

    found_clicked = False

    for alt in carousel["alternatives"]:
        if alt["alt_id"] in displayed_ids:
            alt["impressions"] += 1
            if clicked_alt_id is not None and alt["alt_id"] == clicked_alt_id:
                alt["alpha"] += 1
                alt["clicks"] += 1
                found_clicked = True
            else:
                alt["beta"] += 1

    if clicked_alt_id is not None and not found_clicked:
        raise HTTPException(status_code=400, detail="Clicked alternative is not in the current display")

    event = {
        "timestamp": now_str(),
        "round": carousel["round_number"],
        "displayed": displayed_ids,
        "clicked": clicked_alt_id,
        "reward": 1 if clicked_alt_id is not None else 0,
    }
    carousel["history"].append(event)
    carousel["round_number"] += 1
    sample_carousel(carousel)
    return event


def build_summary(carousel: dict[str, Any]) -> dict[str, Any]:
    stats = get_stats(carousel)
    total_impressions = sum(row["impressions"] for row in stats)
    total_clicks = sum(row["clicks"] for row in stats)
    average_reward = (total_clicks / total_impressions) if total_impressions else 0.0

    return {
        "carousel_id": carousel["carousel_id"],
        "name": carousel["name"],
        "total_alternatives": carousel["total_alternatives"],
        "visible_count": carousel["visible_count"],
        "created_at": carousel["created_at"],
        "round_number": carousel["round_number"],
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "average_reward": average_reward,
    }


def get_champion(stats: list[dict[str, Any]]) -> tuple[Optional[int], Optional[str]]:
    if not stats:
        return None, None
    champion = max(stats, key=lambda row: row["posterior_mean"])
    return champion["alt_id"], champion["title"]


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Bayesian Carousel Bandits API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/carousels", response_model=list[CarouselSummary])
def list_carousels() -> list[dict[str, Any]]:
    return [build_summary(carousel) for carousel in CAROUSELS.values()]


@app.post("/carousels", response_model=CarouselSummary)
def create_carousel(payload: CarouselCreate) -> dict[str, Any]:
    if payload.visible_count > payload.total_alternatives:
        raise HTTPException(
            status_code=400,
            detail="visible_count cannot be greater than total_alternatives",
        )

    carousel_id = str(uuid.uuid4())[:8]
    carousel = {
        "carousel_id": carousel_id,
        "name": payload.name,
        "total_alternatives": payload.total_alternatives,
        "visible_count": payload.visible_count,
        "created_at": now_str(),
        "round_number": 1,
        "alternatives": create_alternatives(payload.total_alternatives),
        "history": [],
        "current_display_ids": [],
    }

    sample_carousel(carousel)
    CAROUSELS[carousel_id] = carousel
    return build_summary(carousel)


@app.get("/carousels/{carousel_id}")
def get_carousel(carousel_id: str) -> dict[str, Any]:
    carousel = get_carousel_or_404(carousel_id)
    return {
        "carousel_id": carousel["carousel_id"],
        "name": carousel["name"],
        "total_alternatives": carousel["total_alternatives"],
        "visible_count": carousel["visible_count"],
        "created_at": carousel["created_at"],
        "round_number": carousel["round_number"],
        "alternatives": get_stats(carousel),
        "history_count": len(carousel["history"]),
    }


@app.delete("/carousels/{carousel_id}")
def delete_carousel(carousel_id: str) -> dict[str, str]:
    get_carousel_or_404(carousel_id)
    del CAROUSELS[carousel_id]
    return {"message": "Carousel deleted successfully"}


@app.post("/carousels/{carousel_id}/reset")
def reset_carousel(carousel_id: str) -> dict[str, str]:
    carousel = get_carousel_or_404(carousel_id)
    carousel["alternatives"] = create_alternatives(carousel["total_alternatives"])
    carousel["history"] = []
    carousel["current_display_ids"] = []
    carousel["round_number"] = 1
    sample_carousel(carousel)
    return {"message": "Carousel reset successfully"}


@app.get("/carousels/{carousel_id}/display", response_model=list[AlternativeOut])
def get_display(carousel_id: str) -> list[dict[str, Any]]:
    carousel = get_carousel_or_404(carousel_id)
    return current_display(carousel)


@app.post("/carousels/{carousel_id}/resample", response_model=list[AlternativeOut])
def resample_display(carousel_id: str) -> list[dict[str, Any]]:
    carousel = get_carousel_or_404(carousel_id)
    sample_carousel(carousel)
    return current_display(carousel)


@app.post("/carousels/{carousel_id}/feedback", response_model=EventOut)
def submit_feedback(carousel_id: str, payload: FeedbackRequest) -> dict[str, Any]:
    carousel = get_carousel_or_404(carousel_id)
    return update_after_feedback(carousel, payload.clicked_alt_id)


@app.get("/carousels/{carousel_id}/events", response_model=list[EventOut])
def get_events(carousel_id: str) -> list[dict[str, Any]]:
    carousel = get_carousel_or_404(carousel_id)
    return carousel["history"]


@app.get("/carousels/{carousel_id}/analytics", response_model=AnalyticsResponse)
def get_analytics(carousel_id: str) -> dict[str, Any]:
    carousel = get_carousel_or_404(carousel_id)
    stats = get_stats(carousel)
    stats_sorted = sorted(stats, key=lambda row: row["posterior_mean"], reverse=True)

    champion_alt_id, champion_title = get_champion(stats_sorted)

    total_impressions = sum(row["impressions"] for row in stats_sorted)
    total_clicks = sum(row["clicks"] for row in stats_sorted)
    average_reward = (total_clicks / total_impressions) if total_impressions else 0.0

    return {
        "carousel_id": carousel["carousel_id"],
        "name": carousel["name"],
        "rounds": max(carousel["round_number"] - 1, 0),
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "average_reward": average_reward,
        "champion_alt_id": champion_alt_id,
        "champion_title": champion_title,
        "alternatives": stats_sorted,
        "history": carousel["history"],
    }
```

---

## How to Run the Prototype Backend

Save the file as:

```text
app/back/main.py
```

Then run:

```bash
uvicorn main:app --reload
```

The API will usually be available at:

```text
http://localhost:8000
```

The automatic FastAPI documentation will be available at:

```text
http://localhost:8000/docs
```

---

## How the Frontend Will Use These Requests Later

Later, the Streamlit frontend will call these endpoints.

For example:

- the Create Carousels page will call `POST /carousels`
- the Interaction page will call `GET /carousels/{carousel_id}/display`
- feedback buttons will call `POST /carousels/{carousel_id}/feedback`
- the Analytics page will call `GET /carousels/{carousel_id}/analytics`

This means the frontend can stay focused on UI while FastAPI handles the application logic.

---

## Example Backend Flow

A simple interaction flow is:

1. create a carousel
2. fetch the currently displayed alternatives
3. submit click feedback
4. request updated analytics

```{mermaid}
sequenceDiagram
    participant F as Frontend
    participant B as FastAPI

    F->>B: POST /carousels
    B-->>F: carousel_id

    F->>B: GET /carousels/{id}/display
    B-->>F: visible alternatives

    F->>B: POST /carousels/{id}/feedback
    B-->>F: event result

    F->>B: GET /carousels/{id}/analytics
    B-->>F: updated metrics
```

---

## Why This Prototype Matters

This backend version is useful because it already defines:

- the API structure,
- the request names,
- the request payloads,
- the expected responses,
- and the future frontend-backend contract.

Even though it is still dummy and in-memory, it is a strong first step toward the full implementation.

---

## Later Evolution

Later, this prototype backend can evolve into a real full-stack backend by adding:

- PostgreSQL persistence,
- SQLAlchemy models,
- routers,
- service layers,
- database sessions,
- and proper business logic separation.

At that point, the same endpoints can remain, but their internal implementation will become production-style.

```{mermaid}
flowchart LR
    A[Single File FastAPI Prototype] --> B[Modular Routers]
    B --> C[Database Integration]
    C --> D[Production Backend]
```

---

## Summary

This FastAPI prototype provides a clean backend introduction for the project.

It includes:

- one-file setup,
- all main dummy requests,
- request and response models,
- interaction flow,
- and a clear path for later full implementation.

This is the right stage for learning how the backend should work before moving into database-connected production code.




