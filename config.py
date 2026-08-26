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