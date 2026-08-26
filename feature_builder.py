"""
Feature builder shared by notebooks 02 and 03.

The function bodies are lifted verbatim from notebook 01 so there is a single
definition of every feature. Notebook 01 remains self-contained and unchanged;
this module exists so the later notebooks (which need to rebuild features at a
past cutoff date for back-testing) do not have to re-implement them.
"""

import numpy as np
import pandas as pd
from pathlib import Path


def find_project_root() -> Path:
    current = Path.cwd().resolve()
    for directory in (current, *current.parents):
        if (directory / "pyproject.toml").exists():
            return directory
    raise FileNotFoundError("Project root containing pyproject.toml not found")


PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "sample_dataset"
REFERENCE_DATE = pd.Timestamp("2026-08-24")

vessels = pd.read_csv(DATA_DIR / "VesselMaster.csv")
inspections = pd.read_csv(DATA_DIR / "Inspections.csv", parse_dates=["inspection_date"])
deficiencies = pd.read_csv(DATA_DIR / "Deficiencies.csv", parse_dates=["deficiency_closed_date"])
detentions = pd.read_csv(DATA_DIR / "Detentions.csv", parse_dates=["detention_date"])
maintenance = pd.read_csv(DATA_DIR / "Maintenance.csv",
                          parse_dates=["maintenance_due_date", "maintenance_completed_date"])
equipment = pd.read_csv(DATA_DIR / "EquipmentFailures.csv", parse_dates=["equipment_failure_date"])
crew = pd.read_csv(DATA_DIR / "Crew.csv", parse_dates=["join_date"])
audits = pd.read_csv(DATA_DIR / "AuditFindings.csv")

VESSEL_IDS = sorted(vessels.vessel_id.unique())

defs_dated = deficiencies.merge(
    inspections[["inspection_id", "inspection_date", "inspection_authority", "inspection_result"]],
    on="inspection_id", how="left", validate="many_to_one")


def _align(series, fill=0):
    """Reindex a per-vessel series onto the full vessel list so every vessel appears exactly once."""
    return pd.Series(series).reindex(VESSEL_IDS).fillna(fill)


def inspection_features(as_of_date):
    """Vessel-level inspection features using only records dated on or before as_of_date."""
    as_of = pd.Timestamp(as_of_date)
    insp = inspections[inspections.inspection_date <= as_of]
    defs = defs_dated[defs_dated.inspection_date <= as_of]

    n_insp = _align(insp.groupby("vessel_id").size())
    n_def = _align(defs.groupby("vessel_id").size())

    per_desc = defs.groupby(["vessel_id", "deficiency_description"]).size()
    repeat_count = _align(per_desc.groupby("vessel_id").apply(lambda g: (g[g > 1] - 1).sum()))
    max_repeat = _align(per_desc.groupby("vessel_id").max())

    per_cat = defs.groupby(["vessel_id", "deficiency_category"]).size()
    largest_cat = _align(per_cat.groupby("vessel_id").max())
    concentration = (largest_cat / n_def.replace(0, np.nan)).fillna(0)
    top_category = _align(per_cat.groupby("vessel_id").idxmax()
                                 .apply(lambda t: t[1] if isinstance(t, tuple) else None), fill=None)

    per_insp = (defs.groupby(["vessel_id", "inspection_id", "inspection_date"]).size()
                    .reset_index(name="n").sort_values("inspection_date"))
    trend = _align(per_insp.groupby("vessel_id").n.last() - per_insp.groupby("vessel_id").n.first())

    open_as_of = defs[(defs.deficiency_closed_date.isna()) | (defs.deficiency_closed_date > as_of)]
    open_def = _align(open_as_of.groupby("vessel_id").size())
    oldest = _align((as_of - open_as_of.groupby("vessel_id").inspection_date.min()).dt.days)

    last_insp = insp.groupby("vessel_id").inspection_date.max()
    carried = open_as_of.merge(last_insp.rename("last_insp"), on="vessel_id")
    carried = carried[carried.inspection_date < carried.last_insp]

    days_since = _align((as_of - last_insp).dt.days)

    return pd.DataFrame({
        "n_inspections": n_insp.astype(int),
        "n_deficiencies": n_def.astype(int),
        "repeat_count": repeat_count.astype(int),
        "max_repeat": max_repeat.astype(int),
        "top_category": top_category,
        "concentration": concentration.round(3),
        "trend": trend.astype(int),
        "open_deficiencies": open_def.astype(int),
        "oldest_open_deficiency_days": oldest.astype(int),
        "open_from_earlier_inspections": _align(carried.groupby("vessel_id").size()).astype(int),
        "days_since_last_inspection": days_since.astype(int),
    })


def operational_features(reference_date=REFERENCE_DATE):
    """Vessel-level current-state features. No cutoff parameter."""
    ref = pd.Timestamp(reference_date)

    overdue_maint = _align(maintenance[maintenance.maintenance_status == "Overdue"]
                           .groupby("vessel_id").size())
    open_audit = _align(audits[audits.audit_finding_status == "Open"].groupby("vessel_id").size())
    overdue_audit = _align(audits[audits.audit_finding_status == "Overdue"].groupby("vessel_id").size())

    unresolved = audits[audits.audit_finding_status.isin(["Open", "Overdue"])]
    linked = unresolved.merge(deficiencies,
                              left_on=["vessel_id", "audit_finding_description"],
                              right_on=["vessel_id", "deficiency_description"],
                              how="inner")
    known_issues = _align(linked.groupby("vessel_id").audit_finding_description.nunique())
    known_occurrences = _align(linked.groupby("vessel_id").size())

    per_equip = equipment.groupby(["vessel_id", "equipment_name"]).size()
    equip_repeats = _align(per_equip.groupby("vessel_id").apply(lambda g: (g[g > 1] - 1).sum()))

    recent = crew[crew.join_date > ref - pd.Timedelta(days=90)]
    recent_joiners = _align(recent.groupby("vessel_id").size())
    avg_experience_months = _align(crew.groupby("vessel_id").rank_experience_months.mean())

    last_insp = inspections.groupby("vessel_id").inspection_date.max()
    e = equipment.merge(last_insp.rename("last_insp"), on="vessel_id")
    since = e[(e.equipment_failure_date > e.last_insp) & (e.equipment_failure_date <= ref)]
    per_since = since.groupby(["vessel_id", "equipment_name"]).size()

    return pd.DataFrame({
        "overdue_maintenance": overdue_maint.astype(int),
        "open_audit": open_audit.astype(int),
        "overdue_audit": overdue_audit.astype(int),
        "known_issues_unresolved": known_issues.astype(int),
        "known_issue_occurrences": known_occurrences.astype(int),
        "equipment_repeats": equip_repeats.astype(int),
        "recent_joiners": recent_joiners.astype(int),
        "avg_experience_months": avg_experience_months.round(1),
        "equip_failures_since_inspection": _align(since.groupby("vessel_id").size()).astype(int),
        "equip_repeats_since_inspection": _align((per_since[per_since > 1] - 1)
                                                 .groupby("vessel_id").sum()).astype(int),
    })


def build_features(as_of_date=REFERENCE_DATE, reference_date=REFERENCE_DATE):
    """One row per vessel: particulars + inspection features + operational features."""
    base = (vessels.set_index("vessel_id")
                   .loc[VESSEL_IDS, ["vessel_name", "vessel_type", "build_year", "flag_state"]])
    base["vessel_age"] = pd.Timestamp(reference_date).year - base.build_year
    out = base.join(inspection_features(as_of_date)).join(operational_features(reference_date))
    out.index.name = "vessel_id"
    return out
