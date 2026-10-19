import pytest
from src.core.knapsack_solver import solve_single_patient, solve_pooled_batch


def test_single_patient_solver():
    vial_sizes = [100]
    costs = {100: 215000}
    res = solve_single_patient(140.0, vial_sizes, costs)
    assert res["vials"][100] == 2
    assert res["opened_mg"] == 200.0
    assert res["waste_mg"] == 60.0
    assert res["cost"] == 430000


def test_pooled_savings():
    cohort = [
        {"patient_id": "P1", "dose_mg": 140.0},
        {"patient_id": "P2", "dose_mg": 60.0},
    ]
    res = solve_pooled_batch("Pembrolizumab (Keytruda)", cohort, use_cstd=False)
    assert res["baseline"]["vials"][100] == 3
    assert res["optimized"]["vials"][100] == 2
    assert res["delta"]["savings_inr"] == 215000
    assert res["optimized"]["waste_mg"] == 0.0