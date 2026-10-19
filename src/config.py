"""
Clinical Drug Master Catalog & Compounding Parameters.
Prices reflect representative Indian market costs (INR).
Sterility windows conform to USP <797> standards.
"""

DRUG_CATALOG = {
    "Pembrolizumab (Keytruda)": {
        "vial_options_mg": [100],
        "cost_per_vial": {100: 215000},
        "stability_hours_punctured": 6,
        "stability_hours_cstd": 24,
        "dose_unit": "mg",
    },
    "Nivolumab (Opdivo)": {
        "vial_options_mg": [40, 100],
        "cost_per_vial": {40: 38000, 100: 89000},
        "stability_hours_punctured": 8,
        "stability_hours_cstd": 24,
        "dose_unit": "mg",
    },
    "Trastuzumab (Herceptin)": {
        "vial_options_mg": [150, 440],
        "cost_per_vial": {150: 22000, 440: 58000},
        "stability_hours_punctured": 8,
        "stability_hours_cstd": 48,
        "dose_unit": "mg",
    },
    "Rituximab (MabThera)": {
        "vial_options_mg": [100, 500],
        "cost_per_vial": {100: 18000, 500: 75000},
        "stability_hours_punctured": 8,
        "stability_hours_cstd": 24,
        "dose_unit": "mg",
    },
}