"""
Verification Layer - Safety Conflict Detection
Ensures AI recommendations don't conflict with existing safety metrics
"""

from typing import Dict, List, Tuple, Any
import pandas as pd

class VerificationLayer:
    """
    Safety verification system that checks AI recommendations
    against existing risk management and safety metrics
    """
    
    def __init__(self):
        """Initialize verification layer with safety thresholds"""
        self.safety_thresholds = {
            "max_acwr": 1.5,
            "max_fatigue": 0.8,
            "high_risk_exercises": ["Deadlift", "Squat", "Log Press"],
            "critical_rpe": 9.0
        }
    
    def verify_ai_recommendation(self, 
                               ai_directive: Dict[str, Any],
                               existing_metrics: Dict[str, Any],
                               risk_flags: List[str]) -> Dict[str, Any]:
        """
        Verify AI recommendation against existing safety metrics
        
        Returns:
            Dict with verification results and safety warnings
        """
        
        verification_result = {
            "approved": True,
            "safety_warnings": [],
            "conflicts": [],
            "modified_recommendation": None,
            "verification_details": {}
        }
        
        # Extract AI recommendation details
        ai_rec = ai_directive.get("recommendation", "").lower()
        ai_confidence = ai_directive.get("confidence", 0.0)
        
        # Check 1: ACWR Safety
        acwr = existing_metrics.get("acwr", 0.0)
        if acwr > self.safety_thresholds["max_acwr"]:
            if "increase" in ai_rec or "add" in ai_rec:
                verification_result["approved"] = False
                verification_result["conflicts"].append(
                    f"AI recommends load increase but ACWR ({acwr:.2f}) exceeds safety threshold ({self.safety_thresholds['max_acwr']})"
                )
                verification_result["safety_warnings"].append("HIGH TRAINING STRESS RISK")
        
        # Check 2: Fatigue Safety
        fatigue = existing_metrics.get("fatigue", 0.0)
        if fatigue > self.safety_thresholds["max_fatigue"]:
            if "increase" in ai_rec or "intensity" in ai_rec:
                verification_result["approved"] = False
                verification_result["conflicts"].append(
                    f"AI recommends intensity increase but fatigue score ({fatigue:.2f}) is critical"
                )
                verification_result["safety_warnings"].append("FATIGUE OVERLOAD RISK")
        
        # Check 3: Risk Flags
        critical_risks = ["high_injury_risk", "overtraining_risk", "technical_failure"]
        for risk in risk_flags:
            if risk in critical_risks and "increase" in ai_rec:
                verification_result["approved"] = False
                verification_result["conflicts"].append(
                    f"AI recommends load increase but critical risk flag detected: {risk}"
                )
                verification_result["safety_warnings"].append("CRITICAL INJURY RISK")
        
        # Check 4: Exercise-Specific Safety
        if any(exercise.lower() in ai_rec for exercise in self.safety_thresholds["high_risk_exercises"]):
            if "increase" in ai_rec and acwr > 1.3:
                verification_result["approved"] = False
                verification_result["conflicts"].append(
                    f"AI recommends increase in high-risk exercise with elevated ACWR ({acwr:.2f})"
                )
                verification_result["safety_warnings"].append("HIGH-RISK EXERCISE SAFETY CONFLICT")
        
        # Generate modified recommendation if conflicts exist
        if not verification_result["approved"]:
            verification_result["modified_recommendation"] = self._generate_safe_alternative(
                ai_directive, existing_metrics, risk_flags
            )
        
        # Store verification details
        verification_result["verification_details"] = {
            "acwr": acwr,
            "fatigue": fatigue,
            "risk_flags": risk_flags,
            "ai_confidence": ai_confidence,
            "safety_thresholds_triggered": self._get_triggered_thresholds(existing_metrics)
        }
        
        return verification_result
    
    def _generate_safe_alternative(self, 
                                  ai_directive: Dict[str, Any],
                                  existing_metrics: Dict[str, Any],
                                  risk_flags: List[str]) -> str:
        """Generate safe alternative recommendation when conflicts exist"""
        
        acwr = existing_metrics.get("acwr", 0.0)
        fatigue = existing_metrics.get("fatigue", 0.0)
        
        if acwr > 1.5:
            return "REDUCE training volume by 20-25% for 7 days. Focus on recovery and technique work."
        elif fatigue > 0.8:
            return "IMPLEMENT recovery protocol: Reduce intensity by 15%, add mobility work, prioritize sleep."
        elif "high_injury_risk" in risk_flags:
            return "MODIFY exercises to reduce injury risk: Focus on technique, reduce load, address mobility limitations."
        else:
            return "MAINTAIN current training load with close monitoring. Focus on recovery and movement quality."
    
    def _get_triggered_thresholds(self, metrics: Dict[str, Any]) -> List[str]:
        """Get list of triggered safety thresholds"""
        triggered = []
        
        if metrics.get("acwr", 0.0) > self.safety_thresholds["max_acwr"]:
            triggered.append("ACWR_HIGH")
        
        if metrics.get("fatigue", 0.0) > self.safety_thresholds["max_fatigue"]:
            triggered.append("FATIGUE_HIGH")
        
        return triggered
    
    def get_safety_status_color(self, verification_result: Dict[str, Any]) -> str:
        """Get color code for safety status display"""
        if not verification_result["approved"]:
            return "🔴"  # Red - Not approved
        elif verification_result["safety_warnings"]:
            return "🟡"  # Yellow - Approved with warnings
        else:
            return "🟢"  # Green - Fully approved
