"""
Cognitive Coaching Brain - AI Intelligence Layer
Sits downstream from existing analytics, enhances without replacing
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

class CognitiveCoachingBrain:
    """
    AI-powered coaching intelligence that processes existing analytics
    and provides adaptive reasoning while preserving all original logic
    """
    
    def __init__(self, db_path: str = "ai_coaching_memory.db"):
        """Initialize the AI coaching brain with memory storage"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for adaptive feedback storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for AI recommendations and athlete responses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                athlete_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_context TEXT NOT NULL,
                ai_recommendation TEXT NOT NULL,
                confidence_score REAL,
                implemented BOOLEAN DEFAULT FALSE,
                outcome_metrics TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS athlete_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id INTEGER,
                athlete_id TEXT NOT NULL,
                response_date DATE,
                performance_change REAL,
                rpe_change REAL,
                feedback_notes TEXT,
                FOREIGN KEY (recommendation_id) REFERENCES ai_recommendations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def package_coach_context(self, 
                            athlete_data: pd.DataFrame,
                            acwr_value: float,
                            fatigue_value: float,
                            overload_status: Dict,
                            risk_flags: List[str],
                            athlete_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Package existing analytics into structured intelligence payload
        without modifying original calculations
        """
        
        # Calculate derived metrics from existing data
        recent_sessions = athlete_data.tail(7)  # Last 7 sessions
        avg_rpe = recent_sessions['rpe'].mean() if 'rpe' in recent_sessions.columns else 7.0
        total_volume = recent_sessions['weight_kg'].sum() * recent_sessions['sets'].sum() * recent_sessions['reps'].sum() if all(col in recent_sessions.columns for col in ['weight_kg', 'sets', 'reps']) else 0
        
        context = {
            "metrics": {
                "acwr": acwr_value,
                "fatigue": fatigue_value,
                "overload_status": overload_status,
                "avg_rpe_7days": avg_rpe,
                "total_volume_7days": total_volume,
                "risk_flags": risk_flags
            },
            "metadata": {
                "athlete_type": "Strongman",
                "days_to_comp": 42,  # Placeholder for future integration
                "data_points": len(athlete_data),
                "analysis_date": datetime.now().isoformat()
            },
            "training_patterns": {
                "exercise_distribution": athlete_data['exercise'].value_counts().to_dict() if 'exercise' in athlete_data.columns else {},
                "recent_progression": self._calculate_progression_trend(athlete_data)
            }
        }
        
        return context
    
    def _calculate_progression_trend(self, athlete_data: pd.DataFrame) -> str:
        """Calculate progression trend from existing data"""
        if 'weight_kg' not in athlete_data.columns or len(athlete_data) < 4:
            return "insufficient_data"
        
        # Simple linear trend on last 4 sessions
        recent_weights = athlete_data.tail(4)['weight_kg'].values
        if len(recent_weights) < 2:
            return "insufficient_data"
        
        trend = (recent_weights[-1] - recent_weights[0]) / len(recent_weights)
        
        if trend > 1.0:
            return "strong_progression"
        elif trend > 0.2:
            return "moderate_progression"
        elif trend > -0.2:
            return "stable"
        else:
            return "declining"
    
    def generate_ai_coaching_directive(self, 
                                     context: Dict[str, Any],
                                     athlete_id: str) -> Dict[str, Any]:
        """
        Generate AI coaching directive using existing metrics
        This simulates LLM integration - replace with actual API call
        """
        
        # Extract key metrics for reasoning
        acwr = context["metrics"]["acwr"]
        fatigue = context["metrics"]["fatigue"]
        risk_flags = context["metrics"]["risk_flags"]
        progression = context["training_patterns"]["recent_progression"]
        
        # Elite Strongman Coach reasoning logic
        directive = {
            "recommendation": "",
            "reasoning": "",
            "confidence": 0.0,
            "action_items": [],
            "safety_conflicts": []
        }
        
        # Primary decision tree based on existing metrics
        if acwr > 1.5:
            directive["recommendation"] = "Reduce training volume by 20-25% for 7-10 days"
            directive["reasoning"] = f"ACWR of {acwr:.2f} indicates excessive training stress. Risk of overtraining is high."
            directive["confidence"] = 0.85
            directive["action_items"] = ["Reduce sets by 25%", "Lower RPE target to 6-7", "Add extra rest day"]
            
        elif fatigue > 0.7:
            directive["recommendation"] = "Implement recovery protocol with reduced intensity"
            directive["reasoning"] = f"Fatigue score of {fatigue:.2f} suggests accumulated stress requiring recovery focus."
            directive["confidence"] = 0.80
            directive["action_items"] = ["Reduce weight by 15%", "Focus on technique", "Increase sleep to 8+ hours"]
            
        elif progression == "declining":
            directive["recommendation"] = "Deload week followed by program adjustment"
            directive["reasoning"] = "Recent performance decline indicates need for recovery and program reassessment."
            directive["confidence"] = 0.75
            directive["action_items"] = ["50% volume for 1 week", "Re-evaluate training goals", "Address recovery factors"]
            
        elif progression == "stable" and acwr < 1.0:
            directive["recommendation"] = "Gradually increase training load to stimulate adaptation"
            directive["reasoning"] = f"ACWR of {acwr:.2f} is below optimal range. Progressive overload needed."
            directive["confidence"] = 0.70
            directive["action_items"] = ["Increase weight by 2.5-5kg", "Add 1-2 reps per set", "Monitor recovery closely"]
            
        else:
            directive["recommendation"] = "Maintain current training approach with minor optimizations"
            directive["reasoning"] = "Current metrics indicate training is on track for continued progress."
            directive["confidence"] = 0.60
            directive["action_items"] = ["Focus on weak points", "Maintain consistency", "Track progress metrics"]
        
        # Check for safety conflicts with existing risk flags
        if "high_injury_risk" in risk_flags and "increase" in directive["recommendation"].lower():
            directive["safety_conflicts"].append("AI recommends load increase but injury risk is high")
        
        if "overtraining_risk" in risk_flags and "increase" in directive["recommendation"].lower():
            directive["safety_conflicts"].append("AI recommends load increase but overtraining risk detected")
        
        # Store recommendation in database
        self._store_recommendation(athlete_id, context, directive)
        
        return directive
    
    def _store_recommendation(self, 
                            athlete_id: str, 
                            context: Dict[str, Any], 
                            directive: Dict[str, Any]):
        """Store AI recommendation for adaptive learning"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_recommendations 
            (athlete_id, session_context, ai_recommendation, confidence_score)
            VALUES (?, ?, ?, ?)
        ''', (
            athlete_id,
            json.dumps(context),
            json.dumps(directive),
            directive["confidence"]
        ))
        
        conn.commit()
        conn.close()
    
    def record_athlete_response(self,
                              recommendation_id: int,
                              athlete_id: str,
                              performance_change: float,
                              rpe_change: float,
                              feedback_notes: str = ""):
        """Record athlete response to AI recommendation for learning"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO athlete_responses 
            (recommendation_id, athlete_id, response_date, performance_change, rpe_change, feedback_notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            recommendation_id,
            athlete_id,
            datetime.now().date(),
            performance_change,
            rpe_change,
            feedback_notes
        ))
        
        conn.commit()
        conn.close()
    
    def get_adaptive_insights(self, athlete_id: str) -> Dict[str, Any]:
        """Get adaptive insights from historical AI recommendations"""
        
        conn = sqlite3.connect(self.db_path)
        
        # Get recent recommendations and outcomes
        query = '''
            SELECT ar.*, ar.performance_change, ar.rpe_change
            FROM ai_recommendations ar
            LEFT JOIN athlete_responses arsp ON ar.id = arsp.recommendation_id
            WHERE ar.athlete_id = ?
            ORDER BY ar.created_at DESC
            LIMIT 10
        '''
        
        df = pd.read_sql_query(query, conn, params=(athlete_id,))
        conn.close()
        
        if df.empty:
            return {"insights": "No historical data available for adaptive learning"}
        
        # Calculate success metrics
        successful_recs = df[df['performance_change'] > 0]
        success_rate = len(successful_recs) / len(df) if len(df) > 0 else 0
        
        return {
            "total_recommendations": len(df),
            "success_rate": success_rate,
            "avg_performance_change": df['performance_change'].mean() if 'performance_change' in df.columns else 0,
            "recent_trend": "positive" if success_rate > 0.7 else "needs_adjustment" if success_rate < 0.4 else "stable"
        }
