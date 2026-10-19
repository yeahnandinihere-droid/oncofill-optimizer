import pulp
from typing import Dict, List, Any
from src.config import DRUG_CATALOG


def solve_single_patient(dose_mg: float, vial_sizes: List[int], costs: Dict[int, float]) -> Dict[str, Any]:
    """Computes the isolated dispensing cost and waste (Standard Hospital Practice)."""
    prob = pulp.LpProblem("Single_Dose", pulp.LpMinimize)
    v_vars = {s: pulp.LpVariable(f"v_{s}", lowBound=0, cat="Integer") for s in vial_sizes}
    
    prob += pulp.lpSum(v_vars[s] * costs[s] for s in vial_sizes)
    prob += pulp.lpSum(v_vars[s] * s for s in vial_sizes) >= dose_mg
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    
    opened_vials = {s: int(v_vars[s].varValue or 0) for s in vial_sizes}
    total_opened_mg = sum(opened_vials[s] * s for s in vial_sizes)
    cost = sum(opened_vials[s] * costs[s] for s in vial_sizes)
    waste_mg = total_opened_mg - dose_mg
    
    return {"vials": opened_vials, "opened_mg": total_opened_mg, "waste_mg": waste_mg, "cost": cost}


def solve_pooled_batch(drug_name: str, patient_cohort: List[Dict[str, Any]], use_cstd: bool = False) -> Dict[str, Any]:
    """Solves the multi-vial integer knapsack problem across the synchronized cohort."""
    if drug_name not in DRUG_CATALOG:
        raise ValueError(f"Drug '{drug_name}' not found in catalog.")
        
    drug_info = DRUG_CATALOG[drug_name]
    vial_sizes = sorted(drug_info["vial_options_mg"])
    costs = drug_info["cost_per_vial"]
    
    total_prescribed_mg = sum(p["dose_mg"] for p in patient_cohort)
    
    # 1. Baseline: Isolated individual preparation
    base_cost = 0.0
    base_waste = 0.0
    base_vials = {s: 0 for s in vial_sizes}
    
    for p in patient_cohort:
        res = solve_single_patient(p["dose_mg"], vial_sizes, costs)
        base_cost += res["cost"]
        base_waste += res["waste_mg"]
        for s in vial_sizes:
            base_vials[s] += res["vials"][s]
            
    # 2. Optimized: Unified cleanroom batching
    prob_pool = pulp.LpProblem("Batch_Optimization", pulp.LpMinimize)
    pool_vars = {s: pulp.LpVariable(f"pool_v_{s}", lowBound=0, cat="Integer") for s in vial_sizes}
    
    prob_pool += pulp.lpSum(pool_vars[s] * costs[s] for s in vial_sizes)
    prob_pool += pulp.lpSum(pool_vars[s] * s for s in vial_sizes) >= total_prescribed_mg
    prob_pool.solve(pulp.PULP_CBC_CMD(msg=False))
    
    opt_vials = {s: int(pool_vars[s].varValue or 0) for s in vial_sizes}
    opt_opened_mg = sum(opt_vials[s] * s for s in vial_sizes)
    opt_cost = sum(opt_vials[s] * costs[s] for s in vial_sizes)
    opt_waste = opt_opened_mg - total_prescribed_mg
    
    savings_inr = base_cost - opt_cost
    savings_pct = (savings_inr / base_cost * 100) if base_cost > 0 else 0.0
    waste_eliminated_mg = base_waste - opt_waste
    efficiency_pct = (total_prescribed_mg / opt_opened_mg * 100) if opt_opened_mg > 0 else 100.0

    return {
        "drug_name": drug_name,
        "patient_count": len(patient_cohort),
        "total_prescribed_mg": total_prescribed_mg,
        "baseline": {
            "vials": base_vials,
            "cost_inr": base_cost,
            "waste_mg": base_waste,
        },
        "optimized": {
            "vials": opt_vials,
            "cost_inr": opt_cost,
            "waste_mg": opt_waste,
            "efficiency_pct": round(efficiency_pct, 2),
        },
        "delta": {
            "savings_inr": savings_inr,
            "savings_pct": round(savings_pct, 1),
            "waste_eliminated_mg": waste_eliminated_mg,
        },
        "sterility_window_hours": drug_info["stability_hours_cstd"] if use_cstd else drug_info["stability_hours_punctured"]
    }