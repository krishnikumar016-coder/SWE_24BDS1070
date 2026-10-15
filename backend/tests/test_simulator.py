import pytest
from app.core.simulator_engine import run_what_if_simulation

def test_simulator_monotonicity_overtime():
    """
    Verifies that increasing overtime_hours monotonic constraint holds:
    Increasing overtime should strictly increase or maintain predicted burnout risk probability.
    """
    res_base = run_what_if_simulation(
        overtime_hours=2.0,
        avg_weekly_hours=40.0,
        workload_index=0.5,
        wfh_days_ratio=0.2,
        leave_days_taken=0.0
    )
    
    res_high_overtime = run_what_if_simulation(
        overtime_hours=15.0,
        avg_weekly_hours=52.0,
        workload_index=0.85,
        wfh_days_ratio=0.2,
        leave_days_taken=0.0
    )

    prob_low = res_base["simulated_risk_prob"]
    prob_high = res_high_overtime["simulated_risk_prob"]

    assert prob_high >= prob_low, (
        f"Monotonic constraint violated! High demand risk ({prob_high}) is lower than low demand risk ({prob_low})"
    )

def test_simulator_disclaimer_present():
    res = run_what_if_simulation(
        overtime_hours=5.0,
        avg_weekly_hours=42.0,
        workload_index=0.6,
        wfh_days_ratio=0.3,
        leave_days_taken=0.0
    )
    assert "disclaimer" in res
    assert "Model-estimated association" in res["disclaimer"]
    assert len(res["confidence_interval"]) == 2
    assert res["confidence_interval"][0] <= res["simulated_risk_prob"] <= res["confidence_interval"][1]
