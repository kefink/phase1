from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Literal, Tuple
from decimal import Decimal, ROUND_HALF_UP

MissingStatus = Literal["ABS", "EXC", "MED", "NA", "INC"]
RoundingMode = Literal["ROUND_HALF_UP", "FLOOR", "CEIL", "TRUNC"]
Treatment = Literal["zero", "exclude", "proxy"]


@dataclass
class AssessmentEntry:
    assessment_code: str  # e.g., "OPENER", "MIDTERM", "ENDTERM"
    score: Optional[float] = None
    max_score: Optional[float] = None
    status: Optional[MissingStatus] = None  # when set, score/max_score should be None


@dataclass
class Weight:
    assessment_code: str
    weight: float  # percentage weight, e.g., 10.0 for 10%


@dataclass
class GradeBand:
    min_inclusive: float
    max_inclusive: float
    grade: str
    points: float
    remark: Optional[str] = None


@dataclass
class MissingPolicy:
    status_code: MissingStatus
    treatment: Treatment  # "zero" | "exclude" | "proxy"
    requires_comment: bool = False


@dataclass
class CalculationInput:
    school_id: int
    subject_id: int
    level: Optional[str]
    rounding_mode: RoundingMode
    weights: List[Weight]
    grade_bands: List[GradeBand]
    missing_policies: Dict[MissingStatus, MissingPolicy]
    entries: List[AssessmentEntry]


@dataclass
class BreakdownItem:
    assessment_code: str
    normalized: Optional[float]  # 0..100 for numeric entries; None for status entries
    weight: float
    contribution: Optional[float]  # normalized * weight / sum_weights (or None)
    status: Optional[MissingStatus]
    note: Optional[str] = None


@dataclass
class CalculationOutput:
    final_numeric: Optional[float]
    final_grade: Optional[str]
    final_points: Optional[float]
    breakdown: List[BreakdownItem]
    warnings: List[str]
    applied_policies: Dict[str, str]


class MarkCalculator:
    """
    A pure, deterministic calculator for final marks.
    - Does not touch the database.
    - Accepts all configuration as input.
    - Handles missing status treatment and rounding.

    Usage: Instantiate and call `compute(input)`.
    """

    def compute(self, data: CalculationInput) -> CalculationOutput:
        # This is a skeleton with correct data contracts and placeholder logic.
        # Implementations will:
        # 1) Normalize numeric entries to 0..100
        # 2) Determine effective weights for included entries
        # 3) Apply missing policies (zero/exclude/proxy)
        # 4) Compute weighted final, then apply rounding and grading bands
        warnings: List[str] = []
        applied: Dict[str, str] = {}
        breakdown: List[BreakdownItem] = []

        # Build weight lookup
        weight_map: Dict[str, float] = {w.assessment_code: w.weight for w in data.weights}

        # Evaluate entries
        included_weights: float = 0.0
        partials: List[Tuple[BreakdownItem, float]] = []  # (item, included_weight)

        for e in data.entries:
            weight = weight_map.get(e.assessment_code, 0.0)
            if e.status:
                policy = data.missing_policies.get(e.status)
                if not policy:
                    warnings.append(f"No policy for status {e.status}; excluding from final")
                    breakdown.append(BreakdownItem(e.assessment_code, None, weight, None, e.status))
                    continue
                applied[f"status:{e.assessment_code}"] = f"{e.status}:{policy.treatment}"
                if policy.treatment == "exclude":
                    breakdown.append(BreakdownItem(e.assessment_code, None, weight, None, e.status))
                    continue
                elif policy.treatment == "zero":
                    normalized = 0.0
                    # This contributes with zero value but counts in denominator
                    included_weights += weight
                    item = BreakdownItem(e.assessment_code, normalized, weight, 0.0, e.status)
                    breakdown.append(item)
                else:  # proxy
                    # Placeholder: proxy not implemented in P0
                    warnings.append(f"Proxy treatment not implemented for {e.assessment_code}; excluding")
                    breakdown.append(BreakdownItem(e.assessment_code, None, weight, None, e.status))
                continue

            # Numeric entry path
            if e.score is None or e.max_score is None or e.max_score == 0:
                warnings.append(f"Invalid numeric entry for {e.assessment_code}; excluding")
                breakdown.append(BreakdownItem(e.assessment_code, None, weight, None, None))
                continue

            normalized = max(0.0, min(100.0, (e.score / e.max_score) * 100.0))
            included_weights += weight
            item = BreakdownItem(e.assessment_code, normalized, weight, None, None)
            partials.append((item, weight))

        # Combine contributions
        final_numeric: Optional[float] = None
        if included_weights > 0:
            total = 0.0
            for item, w in partials:
                contrib = (item.normalized or 0.0) * (w / included_weights)
                item.contribution = contrib
                breakdown.append(item)
                total += contrib
            # zero-treated entries already appended with contribution 0.0
            final_numeric = total
        else:
            warnings.append("No included assessments; final is undefined")

        # Apply rounding (placeholder: pass-through)
        rounded = self._apply_rounding(final_numeric, data.rounding_mode) if final_numeric is not None else None

        # Map to grade band
        final_grade, final_points = self._map_grade(rounded, data.grade_bands) if rounded is not None else (None, None)

        return CalculationOutput(
            final_numeric=rounded,
            final_grade=final_grade,
            final_points=final_points,
            breakdown=breakdown,
            warnings=warnings,
            applied_policies=applied,
        )

    def _apply_rounding(self, value: float, mode: RoundingMode) -> float:
        # Implement common rounding modes using Decimal for deterministic behavior
        if mode == "ROUND_HALF_UP":
            return float(Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
        elif mode == "FLOOR":
            # round down to 1 decimal place
            d = Decimal(value)
            q = (d * Decimal('10')).to_integral_value(rounding='ROUND_FLOOR') / Decimal('10')
            return float(q)
        elif mode == "CEIL":
            d = Decimal(value)
            q = (d * Decimal('10')).to_integral_value(rounding='ROUND_CEILING') / Decimal('10')
            return float(q)
        elif mode == "TRUNC":
            d = Decimal(value)
            q = (d * Decimal('10')).to_integral_value(rounding='ROUND_DOWN') / Decimal('10')
            return float(q)
        else:
            return value

    def _map_grade(self, value: float, bands: List[GradeBand]) -> Tuple[Optional[str], Optional[float]]:
        for b in bands:
            if b.min_inclusive <= value <= b.max_inclusive:
                return b.grade, b.points
        return None, None
