"""
Analytics Assistant endpoint.

Implements a deterministic, grounded analytics assistant.
Every answer is computed from the actual data in the database for the
selected analysis.  No LLM calls, no fabrication.

The assistant understands a set of known question intents and returns
structured, render-safe responses.  Unknown questions receive an honest
"cannot determine" reply.

All answers reference their source (which metric, which query) so the
frontend can display provenance.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_user_analysis
from app.models.analysis import Analysis
from app.models.performance import PerformanceRecord
from app.models.dna_insight import CreativeDNAInsight
from app.models.feature import CreativeFeature
from app.analytics.metrics import MetricsCalculator


router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AssistantRequest(BaseModel):
    question: str


class AssistantResponse(BaseModel):
    answer: str
    source: str           # What data was queried to produce this answer
    confidence: str       # "high" | "medium" | "low" | "unavailable"
    data: Optional[Dict[str, Any]] = None   # Structured data the UI can render


# ---------------------------------------------------------------------------
# Intent patterns
# (Checked in order; first match wins.)
# ---------------------------------------------------------------------------

_INTENTS: list[tuple[list[str], str]] = [
    # ── IMPORTANT: more-specific patterns must appear BEFORE general ones ──────
    # e.g. "which creative has the highest CTR?" must hit best_ctr, not ctr.

    # ── Best per-creative (specific — before scalar metrics) ─────────────────
    (["best ctr", "highest ctr", "top ctr", "highest click.through",
      "which creative.*ctr", "ctr.*creative", "creative.*highest.*ctr",
      "creative.*best.*ctr"],
     "best_ctr"),

    (["best roas", "highest roas", "top roas", "best return",
      "which creative.*roas", "roas.*creative", "creative.*highest.*roas",
      "creative.*best.*roas", r"\broas creative\b"],
     "best_roas"),

    (["best cvr", "highest cvr", "top cvr", "best conversion rate",
      "which creative.*cvr", "cvr.*creative", "creative.*highest.*cvr"],
     "best_cvr"),

    # ── Platform breakdowns (specific — before scalar metrics) ───────────────
    (["which platform.*revenue", "platform.*most revenue",
      "top platform.*revenue", "best platform.*revenue",
      "revenue.*platform", "platform.*generated.*revenue"],
     "platform_revenue"),

    (["which platform.*spend", "platform.*most spend",
      "top platform.*spend", "platform.*highest.*spend",
      "platform.*cost"],
     "platform_spend"),

    (["which platform.*ctr", "platform.*ctr", "best platform.*ctr",
      "platform.*highest.*ctr"],
     "platform_ctr"),

    # ── Scalar metrics (general — after per-creative and per-platform) ────────
    (["how much.*spend", r"\btotal spend\b", r"\btotal cost\b",
      r"^spend$", r"^total spend$"],
     "total_spend"),

    (["how much.*revenue", r"\btotal revenue\b", r"\btotal sales\b",
      r"^revenue$", r"^total revenue$"],
     "total_revenue"),

    (["what.*roas", r"\broas\b", "return on ad spend"],
     "roas"),

    (["what.*ctr", r"\bctr\b", "click.through rate",
      r"^ctr$"],
     "ctr"),

    (["what.*cvr", r"\bcvr\b", "conversion rate",
      r"^cvr$"],
     "cvr"),

    (["what.*cpc", r"\bcpc\b", "cost per click"],
     "cpc"),

    (["what.*cpm", r"\bcpm\b", r"cost per.{0,15}(thousand|mille)"],
     "cpm"),

    # ── Totals ────────────────────────────────────────────────────────────────
    (["total impression", "how many impression", r"^impressions?$"],
     "total_impressions"),

    (["total click", "how many click", r"^clicks?$"],
     "total_clicks"),

    (["total conversion", "how many conversion", r"^conversions?$"],
     "total_conversions"),

    # ── Counts ────────────────────────────────────────────────────────────────
    (["how many record", "how many row", "how many data", "row count",
      "record count", "data point"],
     "record_count"),

    (["how many creative", "creative count", "number of creative",
      "unique creative"],
     "creative_count"),

    # ── Creative DNA ──────────────────────────────────────────────────────────
    (["dna", "creative dna", "visual pattern", "visual insight",
      "which feature", "visual evidence", "dna insight", "dna finding"],
     "dna_summary"),

    # ── Visual features ───────────────────────────────────────────────────────
    (["visual feature", "image feature", "brightness", "contrast",
      "dominant color", "aspect ratio", "portrait", "landscape",
      "edge density"],
     "visual_features"),

    # ── Platforms list ────────────────────────────────────────────────────────
    (["which platform", "what platform", "list.*platform", "platform.*list"],
     "platforms_list"),

    # ── Date range ────────────────────────────────────────────────────────────
    (["date range", "time period", "what period", "when", "date",
      "start.*end", "from.*to"],
     "date_range"),
]


def _classify(question: str) -> Optional[str]:
    """Return the intent key for the question, or None if unrecognised."""
    q = question.lower().strip()
    for patterns, intent in _INTENTS:
        for pat in patterns:
            if re.search(pat, q):
                return intent
    return None


# ---------------------------------------------------------------------------
# Resolver functions — one per intent
# ---------------------------------------------------------------------------

def _fmt_currency(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    return f"${v:,.2f}"


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    return f"{v * 100:.2f}%"


def _fmt_mult(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    return f"{v:.2f}x"


def _resolve(intent: str, db: Session, analysis: Analysis) -> AssistantResponse:
    """Compute an answer for the recognised intent."""
    records = db.query(PerformanceRecord).filter(
        PerformanceRecord.analysis_id == analysis.id
    ).all()

    if not records:
        return AssistantResponse(
            answer="There are no performance records in this analysis yet.",
            source="performance_records table",
            confidence="high",
        )

    agg = MetricsCalculator.compute_aggregate_metrics(records)
    creative_metrics = MetricsCalculator.compute_creative_metrics(db, analysis.id)
    platform_metrics = MetricsCalculator.compute_platform_metrics(db, analysis.id)

    # ── Scalar metrics ────────────────────────────────────────────────────────
    if intent == "total_spend":
        v = agg["total_spend"]
        return AssistantResponse(
            answer=f"The total spend across all {len(records):,} records is {_fmt_currency(v)}.",
            source="SUM(spend) from performance_records",
            confidence="high",
            data={"total_spend": v},
        )

    if intent == "total_revenue":
        v = agg["total_revenue"]
        return AssistantResponse(
            answer=f"The total revenue is {_fmt_currency(v)}.",
            source="SUM(revenue) from performance_records",
            confidence="high",
            data={"total_revenue": v},
        )

    if intent == "roas":
        v = agg["roas"]
        if v is None:
            return AssistantResponse(
                answer="ROAS cannot be computed because total spend is 0.",
                source="SUM(revenue)/SUM(spend)",
                confidence="high",
            )
        return AssistantResponse(
            answer=f"The aggregate ROAS is {_fmt_mult(v)} "
                   f"(revenue {_fmt_currency(agg['total_revenue'])} ÷ spend {_fmt_currency(agg['total_spend'])}).",
            source="SUM(revenue)/SUM(spend) from performance_records",
            confidence="high",
            data={"roas": v},
        )

    if intent == "ctr":
        v = agg["ctr"]
        if v is None:
            return AssistantResponse(
                answer="CTR cannot be computed because total impressions is 0.",
                source="SUM(clicks)/SUM(impressions)",
                confidence="high",
            )
        return AssistantResponse(
            answer=f"The aggregate CTR is {_fmt_pct(v)} "
                   f"({agg['total_clicks']:,} clicks ÷ {agg['total_impressions']:,} impressions).",
            source="SUM(clicks)/SUM(impressions) from performance_records",
            confidence="high",
            data={"ctr": v},
        )

    if intent == "cvr":
        v = agg["cvr"]
        if v is None:
            return AssistantResponse(
                answer="CVR cannot be computed because total clicks is 0.",
                source="SUM(conversions)/SUM(clicks)",
                confidence="high",
            )
        return AssistantResponse(
            answer=f"The aggregate CVR is {_fmt_pct(v)} "
                   f"({agg['total_conversions']:,} conversions ÷ {agg['total_clicks']:,} clicks).",
            source="SUM(conversions)/SUM(clicks) from performance_records",
            confidence="high",
            data={"cvr": v},
        )

    if intent == "cpc":
        v = agg["cpc"]
        if v is None:
            return AssistantResponse(
                answer="CPC cannot be computed because total clicks is 0.",
                source="SUM(spend)/SUM(clicks)",
                confidence="high",
            )
        return AssistantResponse(
            answer=f"The average CPC is {_fmt_currency(v)} per click.",
            source="SUM(spend)/SUM(clicks) from performance_records",
            confidence="high",
            data={"cpc": v},
        )

    if intent == "cpm":
        v = agg["cpm"]
        if v is None:
            return AssistantResponse(
                answer="CPM cannot be computed because total impressions is 0.",
                source="SUM(spend)/SUM(impressions)*1000",
                confidence="high",
            )
        return AssistantResponse(
            answer=f"The CPM is {_fmt_currency(v)} per 1,000 impressions.",
            source="SUM(spend)/SUM(impressions)*1000 from performance_records",
            confidence="high",
            data={"cpm": v},
        )

    if intent == "total_impressions":
        v = agg["total_impressions"]
        return AssistantResponse(
            answer=f"Total impressions: {v:,}.",
            source="SUM(impressions) from performance_records",
            confidence="high",
            data={"total_impressions": v},
        )

    if intent == "total_clicks":
        v = agg["total_clicks"]
        return AssistantResponse(
            answer=f"Total clicks: {v:,}.",
            source="SUM(clicks) from performance_records",
            confidence="high",
            data={"total_clicks": v},
        )

    if intent == "total_conversions":
        v = agg["total_conversions"]
        return AssistantResponse(
            answer=f"Total conversions: {v:,}.",
            source="SUM(conversions) from performance_records",
            confidence="high",
            data={"total_conversions": v},
        )

    if intent == "record_count":
        return AssistantResponse(
            answer=f"This analysis contains {len(records):,} performance records.",
            source="COUNT(*) from performance_records",
            confidence="high",
            data={"record_count": len(records)},
        )

    if intent == "creative_count":
        n = len(creative_metrics)
        return AssistantResponse(
            answer=f"There are {n} unique creative IDs in this analysis.",
            source="COUNT(DISTINCT creative_id) from performance_records",
            confidence="high",
            data={"creative_count": n},
        )

    # ── Best per-creative metrics ─────────────────────────────────────────────
    if intent in ("best_ctr", "best_roas", "best_cvr"):
        metric_key = {"best_ctr": "ctr", "best_roas": "roas", "best_cvr": "cvr"}[intent]
        top = MetricsCalculator.get_top_creatives_by_metric(
            creative_metrics, metric_key, limit=1
        )
        if not top:
            return AssistantResponse(
                answer=f"Cannot determine the highest {metric_key.upper()} — no valid data.",
                source=f"creative-level {metric_key} from performance_records",
                confidence="low",
            )
        best = top[0]
        fmt = _fmt_pct if metric_key in ("ctr", "cvr") else _fmt_mult
        val_str = fmt(best.get(metric_key))
        return AssistantResponse(
            answer=f"The creative with the highest {metric_key.upper()} is "
                   f"'{best['creative_id']}' with {metric_key.upper()} = {val_str}.",
            source=f"Aggregate {metric_key.upper()} per creative_id from performance_records",
            confidence="high",
            data={"creative_id": best["creative_id"], metric_key: best.get(metric_key)},
        )

    # ── Platform breakdowns ───────────────────────────────────────────────────
    if intent in ("platform_revenue", "platform_spend", "platform_ctr"):
        if not platform_metrics:
            return AssistantResponse(
                answer="No platform data is available for this analysis.",
                source="platform_metrics from performance_records",
                confidence="high",
            )
        if intent == "platform_revenue":
            key, label = "total_revenue", "revenue"
            fmt_fn = _fmt_currency
        elif intent == "platform_spend":
            key, label = "total_spend", "spend"
            fmt_fn = _fmt_currency
        else:
            key, label = "ctr", "CTR"
            fmt_fn = _fmt_pct

        best_plat = max(
            platform_metrics.items(),
            key=lambda kv: kv[1].get(key) or 0.0,
        )
        name, metrics = best_plat
        val_str = fmt_fn(metrics.get(key))
        return AssistantResponse(
            answer=f"The platform with the highest {label} is '{name}' with {val_str}.",
            source=f"Aggregate {key} per platform from performance_records",
            confidence="high",
            data={"platform": name, key: metrics.get(key)},
        )

    if intent == "platforms_list":
        platforms = sorted(platform_metrics.keys())
        if not platforms:
            return AssistantResponse(
                answer="No platform data found in this analysis.",
                source="DISTINCT platform from performance_records",
                confidence="high",
            )
        return AssistantResponse(
            answer=f"Platforms in this analysis: {', '.join(platforms)}.",
            source="DISTINCT platform from performance_records",
            confidence="high",
            data={"platforms": platforms},
        )

    # ── Creative DNA ─────────────────────────────────────────────────────────
    if intent == "dna_summary":
        insights = (
            db.query(CreativeDNAInsight)
            .filter(CreativeDNAInsight.analysis_id == analysis.id)
            .all()
        )
        if not insights:
            # Count real assets that have actual feature values
            real_features = (
                db.query(CreativeFeature)
                .filter(
                    CreativeFeature.analysis_id == analysis.id,
                    CreativeFeature.brightness.isnot(None),  # None = placeholder
                )
                .all()
            )
            real_count = len(real_features)
            if real_count == 0:
                # Check if there are any (placeholder) features at all
                any_features = (
                    db.query(CreativeFeature)
                    .filter(CreativeFeature.analysis_id == analysis.id)
                    .first()
                )
                if any_features:
                    return AssistantResponse(
                        answer=(
                            "Creative DNA is unavailable because the registered assets "
                            "are placeholders with no real images. Upload actual creative "
                            "images via Cloudinary and re-run the analysis to enable "
                            "visual feature extraction and DNA insights."
                        ),
                        source="creative_features table",
                        confidence="high",
                    )
                return AssistantResponse(
                    answer=(
                        "No Creative DNA insights are available for this analysis. "
                        "DNA requires real creative images to be uploaded and analysed. "
                        "Placeholder assets do not produce visual features."
                    ),
                    source="creative_dna_insights + creative_features tables",
                    confidence="high",
                )
            elif real_count < 2:
                return AssistantResponse(
                    answer=(
                        f"Creative DNA requires multiple real creatives with visual "
                        f"features to compare visual characteristics against performance. "
                        f"This analysis has {real_count} real creative image — at least 2 "
                        f"are needed. Upload more images and re-run the analysis."
                    ),
                    source="creative_features table",
                    confidence="high",
                )
            else:
                return AssistantResponse(
                    answer=(
                        f"Visual features were extracted from {real_count} real image(s) "
                        f"but no statistically significant Creative DNA insights were "
                        f"generated. This typically means there are too few creatives per "
                        f"feature group (minimum 5 required per group for the statistical "
                        f"test). Add more creative images and re-run the analysis."
                    ),
                    source="creative_dna_insights table",
                    confidence="high",
                )

        # Sort by evidence strength
        tier_order = {
            "strong": 0, "moderate": 1, "weak": 2,
            "no_clear_evidence": 3, "insufficient_evidence": 4,
        }
        insights_sorted = sorted(
            insights,
            key=lambda i: (tier_order.get(i.evidence_tier, 9), -abs(i.percent_difference)),
        )
        top = insights_sorted[0]
        direction = "higher" if top.positive_median >= top.negative_median else "lower"
        pct = abs(top.percent_difference)
        feature = top.feature_name.replace("_", " ")
        # Compute display strings before the f-string — a conditional expression
        # inside a format specifier (e.g. :.4f if ... else ...) is not valid Python
        # syntax and raises ValueError at runtime.
        p_value_display = f"{top.p_value:.4f}" if top.p_value is not None else "N/A"
        answer = (
            f"This analysis has {len(insights)} Creative DNA finding(s). "
            f"The strongest ({top.evidence_tier.replace('_', ' ')}) is: "
            f"creatives with '{feature}' were associated with "
            f"{'+' if direction == 'higher' else '-'}{pct:.1f}% {direction} median "
            f"{top.metric_name.upper()} (n={top.sample_size_positive} vs "
            f"{top.sample_size_negative}, p={p_value_display}). "
            f"Association does not imply causation."
        )
        return AssistantResponse(
            answer=answer,
            source="creative_dna_insights table",
            confidence="high",
            data={
                "total_insights": len(insights),
                "top_feature": top.feature_name,
                "top_metric": top.metric_name,
                "evidence_tier": top.evidence_tier,
                "percent_difference": top.percent_difference,
            },
        )

    # ── Visual features ───────────────────────────────────────────────────────
    if intent == "visual_features":
        features = (
            db.query(CreativeFeature)
            .filter(CreativeFeature.analysis_id == analysis.id)
            .all()
        )
        if not features:
            return AssistantResponse(
                answer=(
                    "No visual features are available for this analysis. "
                    "Upload real creative images and re-run the analysis to "
                    "enable visual feature extraction."
                ),
                source="creative_features table",
                confidence="high",
            )
        real = [f for f in features if f.brightness is not None]
        placeholder = len(features) - len(real)
        if not real:
            return AssistantResponse(
                answer=(
                    f"This analysis has {len(features)} asset(s) registered, but all are "
                    "placeholders — no real images were analysed. Visual features are "
                    "marked as Unavailable."
                ),
                source="creative_features table",
                confidence="high",
            )
        avg_brightness = sum(f.brightness for f in real) / len(real)
        return AssistantResponse(
            answer=(
                f"Visual features were extracted from {len(real)} real image(s) "
                f"({placeholder} placeholder(s) skipped). "
                f"Average brightness: {avg_brightness:.3f}. "
                f"See the Creative Library for per-creative details."
            ),
            source="creative_features table",
            confidence="high",
            data={"real_assets": len(real), "placeholders": placeholder,
                  "avg_brightness": avg_brightness},
        )

    # ── Date range ────────────────────────────────────────────────────────────
    if intent == "date_range":
        dated = [r for r in records if r.date is not None]
        if not dated:
            return AssistantResponse(
                answer="No date information is available in this dataset.",
                source="date column from performance_records",
                confidence="high",
            )
        min_date = min(r.date for r in dated)
        max_date = max(r.date for r in dated)
        return AssistantResponse(
            answer=f"The dataset covers {min_date} to {max_date} ({len(dated):,} dated records).",
            source="MIN/MAX(date) from performance_records",
            confidence="high",
            data={"start_date": str(min_date), "end_date": str(max_date)},
        )

    # Fallback (should not be reached given intent classification above)
    return _unknown_response()


def _unknown_response() -> AssistantResponse:
    return AssistantResponse(
        answer=(
            "I don't have enough information in this analysis to answer that question. "
            "Try asking about spend, revenue, ROAS, CTR, CVR, CPC, CPM, record counts, "
            "creative performance, platform breakdowns, Creative DNA, or date ranges."
        ),
        source="N/A",
        confidence="unavailable",
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/{analysis_id}/assistant", response_model=AssistantResponse)
def ask_assistant(
    body: AssistantRequest,
    analysis: Analysis = Depends(get_user_analysis),
    db: Session = Depends(get_db),
) -> AssistantResponse:
    """
    Deterministic analytics assistant grounded in the selected analysis.

    Accepts a natural-language question and returns a structured answer
    computed from the actual database records for the analysis.

    No LLM is called.  No answers are fabricated.
    If the question cannot be answered from available data, the response
    clearly states that.

    Authorization: Only the analysis owner can query this endpoint.
    """
    question = (body.question or "").strip()
    if not question:
        return AssistantResponse(
            answer="Please enter a question.",
            source="N/A",
            confidence="unavailable",
        )

    intent = _classify(question)
    if intent is None:
        return _unknown_response()

    return _resolve(intent, db, analysis)
