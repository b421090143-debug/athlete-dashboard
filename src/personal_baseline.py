from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BaselineResult:
    value: float
    method: str
    sufficient_history: bool


def rpe_baseline(
    rpe_by_week: pd.Series,
    *,
    min_weeks: int = 4,
    default: float = 7.5,
) -> BaselineResult:
    """Compute an athlete-specific baseline for weekly RPE.

    Safety design:
    - Additive helper only (no changes to existing metric calculations).
    - If history is insufficient or input is invalid, returns a safe default.
    """

    try:
        s = pd.to_numeric(rpe_by_week, errors="coerce").dropna()
        if len(s) < min_weeks:
            return BaselineResult(value=float(default), method="default", sufficient_history=False)

        # Median is robust to occasional high-RPE spikes.
        baseline = float(np.median(s.values))
        baseline = float(np.clip(baseline, 5.5, 9.5))
        return BaselineResult(value=baseline, method="median", sufficient_history=True)
    except Exception:
        return BaselineResult(value=float(default), method="default", sufficient_history=False)


def load_baseline(
    load_by_week: pd.Series,
    *,
    min_weeks: int = 4,
    default: Optional[float] = None,
) -> BaselineResult:
    """Compute an athlete-specific baseline for weekly training load.

    Safety design:
    - Returns default/None when history is insufficient.
    - Never raises.
    """

    try:
        s = pd.to_numeric(load_by_week, errors="coerce").dropna()
        if len(s) < min_weeks:
            if default is None:
                # If load is unknown, default to the observed mean when available, else 0.
                fallback = float(s.mean()) if len(s) > 0 else 0.0
                return BaselineResult(value=fallback, method="fallback_mean", sufficient_history=False)
            return BaselineResult(value=float(default), method="default", sufficient_history=False)

        baseline = float(np.median(s.values))
        baseline = max(0.0, baseline)
        return BaselineResult(value=baseline, method="median", sufficient_history=True)
    except Exception:
        if default is None:
            return BaselineResult(value=0.0, method="default", sufficient_history=False)
        return BaselineResult(value=float(default), method="default", sufficient_history=False)
