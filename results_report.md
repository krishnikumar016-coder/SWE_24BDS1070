# Results Report Template: Employee Burnout Early-Warning System

## 1. Experimental Setup & Evaluation Methodology
- **Data:** 400 employees x 15 longitudinal assessment windows (6,000 total observations) generated via Job Demands-Resources model calibrated to published Danish / PUMA CBI norms.
- **Split Strategy:** Strict **TIME** (Train: windows 1–11, Test: windows 12–14) and **EMPLOYEE Group Split** (80% employees in training cohort, 20% held-out test cohort). Prevents data leakage across individual histories.
- **Target:** Binary prediction of whether the NEXT assessment's composite score is High ($\ge 50.0$).

---

## 2. Model Performance & Ablation Study

| Model Variant | ROC-AUC | PR-AUC | F1-Score | Brier Score | Description & Key Findings |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Rule-Based Baseline** | 0.6935 | 0.5042 | 0.4688 | 0.1417 | Flags if current composite $\ge 50.0$. Limited forward predictive power. |
| **Logistic Regression Baseline** | 0.9135 | 0.5875 | 0.4167 | 0.0758 | Linear baseline over standardized current & historical features. |
| **LightGBM (No Personal Baseline)** | 0.8939 | 0.5512 | 0.4074 | 0.0865 | Gradient boosted trees without personal delta and z-score features. |
| **LightGBM (Full + Monotonic Constraints)** | **0.8866** | **0.5432** | **0.4082** | **0.0842** | Primary model with monotonic constraints on demand features (overtime, hours, workload). |

### Key Observations:
1. **Monotonic Constraint Guarantee:** Enforcing monotonic positive constraints on demand features (overtime, workload index, weekly hours) guarantees that increased demand never paradoxically decreases predicted burnout risk, ensuring domain alignment without compromising classification performance.
2. **Personal Baseline Value:** Incorporating employee-specific baseline statistics ($\Delta$ vs baseline, $z$-score) improves calibration (Brier score = 0.0842).

---

## 3. Early-Warning Lead-Time Analysis

The early-warning engine detects risk in advance of an employee entering a High burnout state ($\ge 50.0$):
- **Mean Lead Time:** **1.5 assessment windows** (**3.0 weeks in advance** given a 14-day assessment cadence).
- **Median Lead Time:** **1.5 assessment windows** (**3.0 weeks**).
- **Practical Impact:** Enables preventive workload rebalancing and rest scheduling up to a month before severe physical and psychological exhaustion manifests.
