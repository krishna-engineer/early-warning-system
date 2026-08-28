"""
Evidence and recommendation layers for the vessel card.

Nothing here models anything. Every function is a lookup against the source tables, so each
line on a card can be traced to the record IDs it came from. That separation is deliberate:
the score says which vessel, this module says why and what to do, and the two are computed
independently so a disputed recommendation can be checked without re-running the score.
"""

import pandas as pd

from feature_builder import (
    deficiencies, defs_dated, inspections, maintenance, equipment, crew, audits,
    REFERENCE_DATE,
)
from config import ACTIONS

# driver -> what to do, who owns it, how urgent.
# The owning functions are those named in the brief: Marine, Technical, Crewing, Operations,
# Vessel. 



def _rows(df, cols, limit=None):
    """Small helper: return a list of dicts for display, optionally truncated."""
    out = df[cols].to_dict('records')
    return out[:limit] if limit else out


def evidence_for(vessel_id, driver, as_of=REFERENCE_DATE, limit=5):
    """Source records supporting one driver on one vessel.

    Returns a dict with a one-line summary and the record IDs behind it. The IDs matter more
    than the summary - they are what lets a superintendent open the underlying record and
    disagree with the system.
    """
    as_of = pd.Timestamp(as_of)
    d = defs_dated[defs_dated.vessel_id == vessel_id]

    if driver == 'Repetition':
        counts = d.groupby('deficiency_description').size()
        repeats = counts[counts > 1].sort_values(ascending=False)
        if repeats.empty:
            return None
        worst = repeats.index[0]
        rows = d[d.deficiency_description == worst]
        return {
            'summary': f'"{worst}" recorded {repeats.iloc[0]} times across '
                       f'{rows.inspection_id.nunique()} inspections',
            'detail': repeats.head(3).to_dict(),
            'record_ids': rows.deficiency_id.tolist()[:limit],
        }

    if driver == 'Trend':
        per_insp = (d.groupby(['inspection_id', 'inspection_date']).size()
                     .reset_index(name='n').sort_values('inspection_date'))
        if len(per_insp) < 2:
            return None
        first, last = per_insp.iloc[0], per_insp.iloc[-1]
        return {
            'summary': f'{first.n} finding(s) at {first.inspection_date.date()} '
                       f'{"rising" if last.n >= first.n else "falling"} to '
                       f'{last.n} at {last.inspection_date.date()}',
            'detail': {r.inspection_id: int(r.n) for r in per_insp.itertuples()},
            'record_ids': per_insp.inspection_id.tolist(),
        }

    if driver == 'Unresolved':
        open_defs = d[(d.deficiency_closed_date.isna()) | (d.deficiency_closed_date > as_of)]
        known = audits[(audits.vessel_id == vessel_id) &
                       (audits.audit_finding_status.isin(['Open', 'Overdue']))]
        overlap = set(known.audit_finding_description) & set(open_defs.deficiency_description)
        if open_defs.empty and known.empty:
            return None
        last_insp = inspections[inspections.vessel_id == vessel_id].inspection_date.max()
        carried = open_defs[open_defs.inspection_date < last_insp]
        return {
            'summary': f'{len(open_defs)} deficiencies still open, {len(carried)} of them raised '
                       f'before the most recent inspection; {len(known)} internal audit findings '
                       f'unresolved, {len(overlap)} matching an open deficiency',
            'detail': {'carried_over': carried.deficiency_id.tolist(),
                       'known_internally': sorted(overlap)},
            'record_ids': open_defs.deficiency_id.tolist()[:limit] +
                          known.audit_id.tolist()[:limit],
        }

    if driver == 'Maintenance':
        od = maintenance[(maintenance.vessel_id == vessel_id) &
                         (maintenance.maintenance_status == 'Overdue')]
        if od.empty:
            return None
        oldest = od.maintenance_due_date.min()
        return {
            'summary': f'{len(od)} planned jobs overdue, oldest due {oldest.date()} '
                       f'({(as_of - oldest).days} days ago)',
            'detail': od.maintenance_equipment_name.value_counts().to_dict(),
            'record_ids': od.maintenance_id.tolist()[:limit],
        }

    if driver == 'Concentration':
        per_cat = d.groupby('deficiency_category').size().sort_values(ascending=False)
        if per_cat.empty:
            return None
        top = per_cat.index[0]
        rows = d[d.deficiency_category == top]
        return {
            'summary': f'{per_cat.iloc[0]} of {len(d)} findings in {top} '
                       f'({per_cat.iloc[0] / len(d):.0%} of all findings)',
            'detail': rows.deficiency_description.value_counts().to_dict(),
            'record_ids': rows.deficiency_id.tolist()[:limit],
        }

    if driver == 'Crew':
        c = crew[crew.vessel_id == vessel_id]
        recent = c[c.join_date > as_of - pd.Timedelta(days=90)]
        return {
            'summary': f'{len(recent)} crew joined in the last 90 days; average rank experience '
                       f'{c.rank_experience_months.mean() / 12:.1f} years',
            'detail': recent.groupby('rank').size().to_dict(),
            'record_ids': recent.crew_id.tolist()[:limit],
        }

    if driver == 'Equipment':
        e = equipment[equipment.vessel_id == vessel_id]
        per_equip = e.groupby('equipment_name').size()
        repeats = per_equip[per_equip > 1].sort_values(ascending=False)
        if repeats.empty:
            return None
        rows = e[e.equipment_name.isin(repeats.index)]
        return {
            'summary': f'{len(repeats)} items failed more than once; worst is '
                       f'{repeats.index[0]} at {repeats.iloc[0]} failures',
            'detail': repeats.head(3).to_dict(),
            'record_ids': rows.failure_id.tolist()[:limit],
        }

    return None


def since_last_inspection(vessel_id, as_of=REFERENCE_DATE):
    """What has changed on this vessel since the last inspector was aboard.

    This is the block that fills a card for a vessel with no elevated drivers. Every vessel in
    the fleet is 415-455 days past its last inspection, so this window is never empty - and
    none of it was visible to the last inspector while all of it will be visible to the next.
    """
    as_of = pd.Timestamp(as_of)
    last = inspections[inspections.vessel_id == vessel_id].inspection_date.max()

    e = equipment[(equipment.vessel_id == vessel_id) &
                  (equipment.equipment_failure_date > last) &
                  (equipment.equipment_failure_date <= as_of)]
    d = defs_dated[defs_dated.vessel_id == vessel_id]
    still_open = d[(d.deficiency_closed_date.isna()) | (d.deficiency_closed_date > as_of)]
    od = maintenance[(maintenance.vessel_id == vessel_id) &
                     (maintenance.maintenance_status == 'Overdue')]
    unresolved_audit = audits[(audits.vessel_id == vessel_id) &
                              (audits.audit_finding_status.isin(['Open', 'Overdue']))]
    joiners = crew[(crew.vessel_id == vessel_id) &
                   (crew.join_date > last) & (crew.join_date <= as_of)]

    return {
        'last_inspection': last.date(),
        'days_since': (as_of - last).days,
        'equipment_failures': len(e),
        'equipment_detail': e.equipment_name.value_counts().head(3).to_dict(),
        'deficiencies_still_open': len(still_open),
        'overdue_maintenance': len(od),
        'unresolved_audit_findings': len(unresolved_audit),
        'crew_joined': len(joiners),
    }


def recommendations_for(drivers, tier):
    """Turn a driver list into prioritised tasks. Order follows the driver order, which is
    points descending, so the first task is the largest contributor to the score."""
    urgency = {'High': 'Immediate', 'Medium': 'Planned', 'Low': 'Routine'}
    out = []
    for i, driver in enumerate(drivers, start=1):
        spec = ACTIONS[driver]
        out.append({
            'priority': i,
            'driver': driver,
            'action': spec['action'],
            'owner': spec['owner'],
            'window': spec['window'],
            'urgency': urgency.get(str(tier), 'Routine'),
        })
    return out
