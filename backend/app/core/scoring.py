import os
import json
from typing import Dict, Any, Optional, List, Tuple

# Path to config file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config_data", "cbi_config.json")

def load_cbi_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

CBI_CONFIG = load_cbi_config()

def score_item(scale_name: str, answer_text: str, reverse: bool) -> float:
    scales = CBI_CONFIG["scales"]
    if scale_name not in scales:
        raise ValueError(f"Unknown scale name: {scale_name}")
    
    scale_dict = scales[scale_name]
    if answer_text not in scale_dict:
        raise ValueError(f"Invalid answer '{answer_text}' for scale '{scale_name}'. Valid: {list(scale_dict.keys())}")
    
    raw_val = scale_dict[answer_text]
    if reverse:
        return 100.0 - raw_val
    return float(raw_val)

def compute_cbi_scores(
    answers: Dict[str, str],
    client_contact_role: bool = True
) -> Dict[str, Any]:
    """
    Computes Copenhagen Burnout Inventory (CBI) subscales, composite score, and risk category.
    
    Args:
        answers: dict mapping item_id (e.g. 'P1', 'W7', 'C3', 'S1') to answer_text string.
        client_contact_role: if False, client subscale is disabled and set to None.
        
    Returns:
        Dict containing:
        - item_scores: dict mapping item_id to numeric float score
        - personal_score: float or None (non-responder if < 3 answered)
        - work_score: float or None (non-responder if < 4 answered)
        - client_score: float or None (non-responder if < 3 answered or disabled)
        - composite_score: float or None (mean of active subscales, project-defined summary)
        - risk_category: "Low", "Moderate", or "High"
        - supplementary_scores: dict mapping dimension name to float score
    """
    subscales_cfg = CBI_CONFIG["subscales"]
    item_scores: Dict[str, float] = {}
    
    # 1. Personal Subscale (P1..P6)
    personal_cfg = subscales_cfg["personal"]
    personal_item_values = []
    for item in personal_cfg["items"]:
        item_id = item["id"]
        if item_id in answers:
            score = score_item(item["scale"], answers[item_id], item["reverse"])
            item_scores[item_id] = score
            personal_item_values.append(score)
            
    personal_score: Optional[float] = None
    if len(personal_item_values) >= personal_cfg["min_responses_required"]:
        personal_score = round(sum(personal_item_values) / len(personal_item_values), 2)
        
    # 2. Work-related Subscale (W1..W7)
    work_cfg = subscales_cfg["work"]
    work_item_values = []
    for item in work_cfg["items"]:
        item_id = item["id"]
        if item_id in answers:
            score = score_item(item["scale"], answers[item_id], item["reverse"])
            item_scores[item_id] = score
            work_item_values.append(score)
            
    work_score: Optional[float] = None
    if len(work_item_values) >= work_cfg["min_responses_required"]:
        work_score = round(sum(work_item_values) / len(work_item_values), 2)

    # 3. Client-related Subscale (C1..C6)
    client_cfg = subscales_cfg["client"]
    client_score: Optional[float] = None
    if client_contact_role:
        client_item_values = []
        for item in client_cfg["items"]:
            item_id = item["id"]
            if item_id in answers:
                score = score_item(item["scale"], answers[item_id], item["reverse"])
                item_scores[item_id] = score
                client_item_values.append(score)
        if len(client_item_values) >= client_cfg["min_responses_required"]:
            client_score = round(sum(client_item_values) / len(client_item_values), 2)

    # 4. Supplementary Items (S1..S5)
    supplementary_scores: Dict[str, float] = {}
    for item in CBI_CONFIG["supplementary_items"]:
        item_id = item["id"]
        if item_id in answers:
            score = score_item(item["scale"], answers[item_id], item["reverse"])
            item_scores[item_id] = score
            supplementary_scores[item["dimension"]] = score

    # 5. Composite Score (mean of active subscales)
    active_subscales = [s for s in [personal_score, work_score, client_score] if s is not None]
    composite_score: Optional[float] = None
    risk_category: str = "Low"
    
    if active_subscales:
        composite_score = round(sum(active_subscales) / len(active_subscales), 2)
        low_mod = CBI_CONFIG["cutoffs"]["low_moderate_boundary"]
        high_mod = CBI_CONFIG["cutoffs"]["high_boundary"]
        
        if composite_score >= high_mod:
            risk_category = "High"
        elif composite_score >= low_mod:
            risk_category = "Moderate"
        else:
            risk_category = "Low"

    return {
        "item_scores": item_scores,
        "personal_score": personal_score,
        "work_score": work_score,
        "client_score": client_score,
        "composite_score": composite_score,
        "risk_category": risk_category,
        "supplementary_scores": supplementary_scores
    }

def get_interleaved_questionnaire(client_contact_role: bool = True) -> List[Dict[str, Any]]:
    """
    Returns all questionnaire items in a randomized/interleaved order (as recommended by CBI authors)
    to prevent response bias, while preserving exact item IDs.
    """
    import random
    all_items = []
    
    for item in CBI_CONFIG["subscales"]["personal"]["items"]:
        all_items.append({**item, "subscale": "personal", "options": list(CBI_CONFIG["scales"][item["scale"]].keys())})
        
    for item in CBI_CONFIG["subscales"]["work"]["items"]:
        all_items.append({**item, "subscale": "work", "options": list(CBI_CONFIG["scales"][item["scale"]].keys())})

    if client_contact_role:
        for item in CBI_CONFIG["subscales"]["client"]["items"]:
            all_items.append({**item, "subscale": "client", "options": list(CBI_CONFIG["scales"][item["scale"]].keys())})

    for item in CBI_CONFIG["supplementary_items"]:
        all_items.append({**item, "subscale": "supplementary", "options": list(CBI_CONFIG["scales"][item["scale"]].keys())})

    # Deterministic interleave / shuffle using standard seed or stable shuffle logic
    # We interleave items across subscales for smooth UX
    random.seed(42)  # stable pattern
    shuffled = all_items.copy()
    random.shuffle(shuffled)
    return shuffled
