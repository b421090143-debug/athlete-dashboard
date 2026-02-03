from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.personal_baseline import load_baseline, rpe_baseline

logger = logging.getLogger(__name__)


def _flag_enabled() -> bool:
    # Feature flag: default OFF to keep production behavior unchanged.
    return str(os.getenv("ENABLE_DECISION_LAYER", "0")).strip().lower() in {"1", "true", "yes", "on"}


def smoothed_load(load_by_week: pd.Series, window: int = 3) -> pd.Series:
    """Wrapper-based smoothing used ONLY inside the Decision Layer."""
    try:
        s = pd.to_numeric(load_by_week, errors="coerce")
        return s.rolling(window=window, min_periods=1).mean()
    except Exception:
        return load_by_week


def smoothed_rpe(rpe_by_week: pd.Series, window: int = 3) -> pd.Series:
    """Wrapper-based smoothing used ONLY inside the Decision Layer."""
    try:
        s = pd.to_numeric(rpe_by_week, errors="coerce")
        return s.rolling(window=window, min_periods=1).mean()
    except Exception:
        return rpe_by_week


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        v = float(value)
        if np.isnan(v):
            return default
        return v
    except Exception:
        return default


def compute_decision_layer_output(
    *,
    athlete_id: str,
    weekly_metrics: pd.DataFrame,
    metrics: Dict[str, Any],
    coach_tag: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Decision Layer (feature-flagged).

    Safety rules:
    - Additive only: consumes existing computed outputs (weekly_metrics + metrics dict).
    - If flag is OFF -> returns None.
    - If inputs are missing/invalid -> returns a low-confidence result or None, never raises.
    """

    if not _flag_enabled():
        return None

    try:
        if weekly_metrics is None or weekly_metrics.empty:
            return {
                "decision": "MAINTAIN",
                "risk_level": "MEDIUM",
                "reasons": ["Insufficient data: weekly metrics unavailable"],
                "confidence": 0.2,
            }

        required_cols = {"athlete_id", "week"}
        if not required_cols.issubset(set(weekly_metrics.columns)):
            return {
                "decision": "MAINTAIN",
                "risk_level": "MEDIUM",
                "reasons": ["Insufficient data: missing required weekly metric columns"],
                "confidence": 0.2,
            }

        athlete_weekly = weekly_metrics[weekly_metrics["athlete_id"].astype(str) == str(athlete_id)].copy()
        if athlete_weekly.empty:
            return {
                "decision": "MAINTAIN",
                "risk_level": "MEDIUM",
                "reasons": [f"Insufficient data: no weekly metrics found for {athlete_id}"],
                "confidence": 0.2,
            }

        # Prefer processed columns when present; fall back gracefully.
        load_col = "total_load" if "total_load" in athlete_weekly.columns else None
        rpe_col = "avg_rpe" if "avg_rpe" in athlete_weekly.columns else None

        # Aggregate per week to ensure a single load/RPE value per week.
        per_week = athlete_weekly.groupby("week", as_index=True)
        if load_col is not None:
            load_by_week = per_week[load_col].sum()
        else:
            load_by_week = pd.Series(index=sorted(athlete_weekly["week"].unique()), dtype=float)

        if rpe_col is not None:
            rpe_by_week = per_week[rpe_col].mean()
        else:
            rpe_by_week = pd.Series(index=sorted(athlete_weekly["week"].unique()), dtype=float)

        weeks_available = int(len(load_by_week.index.union(rpe_by_week.index)))
        reasons: List[str] = []

        # Baselines (athlete-specific when enough history exists).
        rpe_base = rpe_baseline(rpe_by_week)
        load_base = load_baseline(load_by_week)

        # Smoothed series used only for decision logic.
        load_sm = smoothed_load(load_by_week)
        rpe_sm = smoothed_rpe(rpe_by_week)

        # Early warning signals (read-only annotations).
        rpe_last = _safe_float(rpe_sm.dropna().iloc[-1] if len(rpe_sm.dropna()) else None, default=rpe_base.value)
        rpe_drift = rpe_last - rpe_base.value

        recent_load = _safe_float(load_sm.dropna().iloc[-1] if len(load_sm.dropna()) else None, default=load_base.value)
        load_ratio = (recent_load / load_base.value) if load_base.value > 0 else 1.0

        recent_window = load_sm.dropna().tail(4)
        load_volatility = float(recent_window.std() / recent_window.mean()) if len(recent_window) >= 2 and recent_window.mean() != 0 else 0.0

        if abs(rpe_drift) >= 0.75:
            reasons.append(f"Early warning: RPE drift {rpe_drift:+.2f} vs baseline ({rpe_base.method})")
        if load_volatility >= 0.25:
            reasons.append(f"Early warning: load volatility {load_volatility:.2f} (CV, last 4 weeks)")

        # Core risk from existing metrics (do not recompute).
        fatigue = _safe_float(metrics.get("fatigue_analysis", {}).get("avg_fatigue_risk"), default=0.0)
        injury_risk_sessions = int(_safe_float(metrics.get("fatigue_analysis", {}).get("injury_risk_sessions"), default=0.0))

        risk_level = "LOW"
        if fatigue >= 3.0 or injury_risk_sessions >= 2 or load_ratio >= 1.25:
            risk_level = "HIGH"
        elif fatigue >= 2.0 or injury_risk_sessions >= 1 or load_ratio >= 1.10 or abs(rpe_drift) >= 0.75:
            risk_level = "MEDIUM"

        # Intent awareness (tag-driven; never inferred).
        coach_tag_norm = str(coach_tag).strip().upper() if coach_tag else ""
        if coach_tag_norm in {"ACCUMULATION", "DELOAD", "TAPER"}:
            reasons.append(f"Coach intent tag: {coach_tag_norm}")

        decision = "MAINTAIN"
        if coach_tag_norm == "DELOAD":
            decision = "DELOAD"
        elif risk_level == "HIGH":
            decision = "DELOAD"
        elif coach_tag_norm == "TAPER":
            decision = "MAINTAIN"
        elif risk_level == "LOW" and coach_tag_norm == "ACCUMULATION":
            decision = "PUSH"
        elif risk_level == "LOW" and fatigue < 2.0 and load_ratio <= 1.10:
            decision = "PUSH"

        # Confidence: degrade when history is short or required signals are missing.
        confidence = 0.75
        if weeks_available < 4:
            reasons.insert(0, "Insufficient data: < 4 weeks of history")
            confidence = 0.25
        elif not rpe_base.sufficient_history or not load_base.sufficient_history:
            confidence = 0.55

        # Additional confidence penalty when metrics are missing.
        if "fatigue_analysis" not in metrics:
            reasons.insert(0, "Insufficient data: missing fatigue analysis metrics")
            confidence = min(confidence, 0.35)

        # Always return the minimal stable schema.
        return {
            "decision": decision,
            "risk_level": risk_level,
            "reasons": reasons[:8],
            "confidence": float(np.clip(confidence, 0.0, 1.0)),
        }

    except Exception as e:
        # Fail closed: disable silently and keep dashboard functional.
        logger.exception("Decision layer failed for athlete_id=%s: %s", athlete_id, str(e))
        return None
