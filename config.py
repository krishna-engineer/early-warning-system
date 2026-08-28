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


# This is a lookup table, not a model. No ML anywhere near the recommendation.
ACTIONS = {
    'Repetition': {
        'action': 'Root-cause the recurring defect rather than re-closing it. Verify the last '
                  'rectification actually held, and record objective evidence of the repair.',
        'owner': 'Technical',
        'window': 'Before next port call',
    },
    'Trend': {
        'action': 'Review why inspection outcomes are deteriorating. Superintendent attendance '
                  'at the next port, with a pre-inspection walkthrough against the last report.',
        'owner': 'Marine',
        'window': '30 days',
    },
    'Unresolved': {
        'action': 'Close outstanding findings and produce rectification evidence. Findings open '
                  'across more than one inspection are the first thing a PSC officer verifies.',
        'owner': 'Vessel / Technical',
        'window': '14 days',
    },
    'Maintenance': {
        'action': 'Clear the overdue planned maintenance backlog, prioritising statutory and '
                  'safety-critical equipment. Escalate any job that cannot be closed in window.',
        'owner': 'Technical',
        'window': '30 days',
    },
    'Concentration': {
        'action': 'Findings are clustered in one area, which points at a system rather than bad '
                  'luck. Audit the procedures and competence behind that area specifically.',
        'owner': 'Marine',
        'window': '30 days',
    },
    'Crew': {
        'action': 'Review senior officer experience and turnover. Confirm familiarisation is '
                  'complete and consider overlap or a riding-squad visit before inspection.',
        'owner': 'Crewing',
        'window': 'Before next crew change',
    },
    'Equipment': {
        'action': 'Investigate repeat failures of the same equipment. Recurrence indicates the '
                  'repair, not the equipment, is the problem.',
        'owner': 'Technical',
        'window': '30 days',
    },
}