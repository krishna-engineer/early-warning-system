"""
Scoring engine shared by notebooks 02, 03 and 04.

Notebook 02 is where these choices are argued; this module is the importable copy so the
evaluation notebook and the vessel-card notebook do not re-implement them. Same arrangement
as feature_builder.py, and for the same reason: one definition, several readers.
"""

import numpy as np
import pandas as pd

# tier boundaries, set from the gap structure in notebook 02 section 5
HIGH_CUT, MEDIUM_CUT = 55, 28

# a dimension counts as saturated at 90% of its own cap; drivers are capped at 4 for readability
SATURATION, MAX_DRIVERS, ELEVATED_PCTILE = 0.90, 4, 0.75

# features entering the score, and the two that need direction handling first
SCORING_INPUTS = ['repeat_count', 'max_repeat', 'concentration', 'trend_clipped',
                  'open_deficiencies', 'known_issue_occurrences', 'known_issues_unresolved',
                  'overdue_audit', 'overdue_maintenance', 'recent_joiners',
                  'experience_inv', 'equipment_repeats', 'equip_repeats_since_inspection']

DIMENSIONS = {
    'Repetition':    {'weight': 20, 'features': {'repeat_count': 0.6, 'max_repeat': 0.4}},
    'Trend':         {'weight': 20, 'features': {'trend_clipped': 1.0}},
    'Unresolved':    {'weight': 20, 'features': {'open_deficiencies': 0.45,
                                                 'known_issue_occurrences': 0.30,
                                                 'known_issues_unresolved': 0.15,
                                                 'overdue_audit': 0.10}},
    'Maintenance':   {'weight': 15, 'features': {'overdue_maintenance': 1.0}},
    'Concentration': {'weight': 15, 'features': {'concentration': 1.0}},
    'Crew':          {'weight':  5, 'features': {'recent_joiners': 0.5, 'experience_inv': 0.5}},
    'Equipment':     {'weight':  5, 'features': {'equipment_repeats': 0.5,
                                                 'equip_repeats_since_inspection': 0.5}},
}

assert sum(d['weight'] for d in DIMENSIONS.values()) == 100

CAPS = pd.Series({k: v['weight'] for k, v in DIMENSIONS.items()})


def minmax(s):
    """Scale to 0-1. A constant column returns all zeros rather than dividing by zero."""
    rng = s.max() - s.min()
    if rng == 0:
        return pd.Series(0.0, index=s.index)
    return (s - s.min()) / rng


def prepare(features):
    """Fix feature direction before scaling.

    trend is clipped at zero so the scale anchors on 'did not get worse' rather than on
    whichever vessel happened to improve most; experience is inverted because low
    experience is the risk and every other feature runs the other way.
    """
    p = features.copy()
    if 'trend' in p:
        p['trend_clipped'] = p['trend'].clip(lower=0)
    if 'avg_experience_months' in p:
        p['experience_inv'] = -p['avg_experience_months']
    return p


def normalise(features, inputs=SCORING_INPUTS):
    """Return the 0-1 table the score is built from."""
    p = prepare(features)
    return pd.DataFrame({c: minmax(p[c]) for c in inputs if c in p.columns})


def score_fleet(normalised, dimensions=DIMENSIONS):
    """Per-dimension point contributions plus the total score, one row per vessel."""
    out = {}
    for name, cfg in dimensions.items():
        sub = cfg['features']
        dim01 = sum(normalised[f] * w for f, w in sub.items()) / sum(sub.values())
        out[name] = dim01 * cfg['weight']
    contributions = pd.DataFrame(out)
    contributions['score'] = contributions.sum(axis=1)
    return contributions


def _top_flagged(row, flags, cap=None):
    """Dimension names where `flags` is True for this vessel, highest points first."""
    hits = row[flags.loc[row.name]].sort_values(ascending=False).index.tolist()
    return hits[:cap]


def rank_fleet(contributions, dimensions=DIMENSIONS):
    """Add rank, tier, drivers and saturation to a contributions table."""
    dims = list(dimensions)
    points = contributions[dims]
    caps = pd.Series({k: v['weight'] for k, v in dimensions.items()})

    elevated = points > points.quantile(ELEVATED_PCTILE)
    saturated = points / caps >= SATURATION

    r = contributions.round(1)
    r['rank'] = r.score.rank(ascending=False, method='min').astype(int)
    r['tier'] = pd.cut(r.score, [-np.inf, MEDIUM_CUT, HIGH_CUT, np.inf],
                       labels=['Low', 'Medium', 'High'], right=False)
    r['drivers'] = points.apply(_top_flagged, axis=1, flags=elevated, cap=MAX_DRIVERS)
    r['saturated'] = points.apply(_top_flagged, axis=1, flags=saturated)
    r['n_drivers'] = r.drivers.str.len()
    return r.sort_values('score', ascending=False)


def score_from_features(features, dimensions=DIMENSIONS):
    """features table in, ranked results out. The whole engine in one call."""
    return rank_fleet(score_fleet(normalise(features), dimensions), dimensions)


def rewindable(available, dimensions=DIMENSIONS):
    """The dimensions that can still be built from a reduced set of features.

    Used by the back-test. Rewound to a past cutoff, only inspection-derived features
    exist - maintenance, crew and equipment tables cannot be rewound - so some dimensions
    lose every feature and drop out entirely, and Unresolved loses three of its four.
    Deriving this from what is actually available beats hand-listing it, because the
    result then cannot drift out of step with DIMENSIONS.

    Sub-weights need no adjustment: score_fleet divides by the sub-weights present, so a
    dimension left with one feature simply weights it 1.0.
    """
    kept = {}
    for name, cfg in dimensions.items():
        feats = {f: w for f, w in cfg['features'].items() if f in available}
        if feats:
            kept[name] = {'weight': cfg['weight'], 'features': feats}
    return kept


def score_on(features, dimensions=DIMENSIONS):
    """Score a feature table on whichever dimensions it can support, rescaled to 0-100."""
    norm = normalise(features)
    dims = rewindable(norm.columns, dimensions)
    raw = score_fleet(norm, dims)['score']
    return (raw / sum(d['weight'] for d in dims.values()) * 100).round(1), dims
