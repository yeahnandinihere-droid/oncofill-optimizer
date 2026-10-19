from datetime import datetime, timedelta
from typing import Dict, List, Any


def generate_compounding_schedule(batch_result: Dict[str, Any], start_time: datetime = None) -> List[Dict[str, Any]]:
    """Calculates chronological compounding milestones and USP <797> expiry timestamps."""
    if start_time is None:
        start_time = datetime.now()
        
    window_hours = batch_result["sterility_window_hours"]
    expiry_time = start_time + timedelta(hours=window_hours)
    
    steps = [
        {
            "action": "Laminar Flow Hood Sanitization",
            "timestamp": start_time.strftime("%H:%M"),
            "detail": "Verify ISO Class 5 air velocity and negative pressure."
        },
        {
            "action": "Vial Puncture & Pooling",
            "timestamp": (start_time + timedelta(minutes=15)).strftime("%H:%M"),
            "detail": f"Unseal {batch_result['optimized']['vials']} vials. Begin open-vial timer."
        },
        {
            "action": "Infusion Bag Aliquoting",
            "timestamp": (start_time + timedelta(minutes=30)).strftime("%H:%M"),
            "detail": f"Distribute exact mg doses across {batch_result['patient_count']} patient bags."
        },
        {
            "action": "USP <797> Hard Expiry",
            "timestamp": expiry_time.strftime("%H:%M"),
            "detail": f"Remaining unallocated volume ({batch_result['optimized']['waste_mg']} mg) invalid after this point."
        }
    ]
    return steps