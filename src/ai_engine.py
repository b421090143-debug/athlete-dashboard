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
        if all(col in recent_sessions.columns for col in ['weight_kg', 'sets', 'reps']):
            total_volume = float((recent_sessions['weight_kg'] * recent_sessions['sets'] * recent_sessions['reps']).sum())
        else:
            total_volume = 0
        
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

    def generate_structured_coaching_package(self, context: Dict[str, Any], athlete_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate structured, system-ready coaching outputs for the AI Coach Brain tab."""

        athlete_profile = athlete_profile or {}
        athlete_id = athlete_profile.get('athlete_id', 'UNKNOWN')
        athlete_name = athlete_profile.get('full_name', f"Athlete {athlete_id}")
        level = athlete_profile.get('level', 'intermediate')

        acwr = float(context['metrics'].get('acwr', 1.0) or 1.0)
        fatigue = float(context['metrics'].get('fatigue', 0.5) or 0.5)
        risk_flags = [r for r in context['metrics'].get('risk_flags', []) if str(r).strip()]

        overload_status = context['metrics'].get('overload_status', {}) or {}
        plateau_items = []
        if isinstance(overload_status, dict):
            plateau_items = overload_status.get('plateaus', []) or overload_status.get('plateau_detection', {}).get('plateaus', []) if isinstance(overload_status.get('plateau_detection', {}), dict) else []

        progression = context.get('training_patterns', {}).get('recent_progression', 'stable')

        # Top-line recommendation (must acknowledge metrics)
        if acwr > 1.3 or fatigue > 0.7:
            recommendation = f"ACWR is {acwr:.2f} and fatigue is {fatigue:.2f} — pull back training stress and prioritize recovery."
        elif plateau_items:
            recommendation = f"Plateau signals detected with ACWR {acwr:.2f} and fatigue {fatigue:.2f} — adjust stimulus (variation/intensity cycling) while controlling weekly load."
        elif acwr < 0.8 and progression in ['stable', 'declining']:
            recommendation = f"ACWR is {acwr:.2f} (low) and fatigue {fatigue:.2f} — room to increase stimulus with controlled overload."
        else:
            recommendation = f"ACWR is {acwr:.2f} and fatigue {fatigue:.2f} — maintain trajectory with small, measurable progressions."

        performance_status = {
            'objective': 'Assess readiness and stress balance using existing metrics',
            'current_status': {
                'readiness': 'needs_recovery' if (acwr > 1.3 or fatigue > 0.7) else 'on_track',
                'progression': progression,
                'primary_constraint': 'fatigue_management' if fatigue > 0.7 else 'overload_quality' if plateau_items else 'none_detected'
            },
            'key_metrics': {
                'acwr': round(acwr, 2),
                'fatigue': round(fatigue, 2),
                'risk_flags': risk_flags
            }
        }

        # Primary Focus Areas
        focus_areas = []
        if plateau_items:
            focus_areas.append({
                'area': 'Break Plateau: Stimulus Variation',
                'priority': 'high',
                'objective': 'Reintroduce adaptation while protecting recovery capacity',
                'prescription': {
                    'frequency': '2-3x/week primary lift exposure',
                    'exercises': [
                        {'name': 'Tempo Squat (3-0-1)', 'sets': 4, 'reps': 5},
                        {'name': 'Paused Deadlift (1-2s off floor)', 'sets': 4, 'reps': 3},
                        {'name': 'Close-Grip Bench Press', 'sets': 4, 'reps': 6},
                    ],
                    'progression_rule': 'Hold RPE 7-8; add 2.5kg weekly if bar speed and technique stay consistent.'
                }
            })
        if acwr > 1.3 or fatigue > 0.7:
            focus_areas.append({
                'area': 'Recovery & Fatigue Control',
                'priority': 'high',
                'objective': 'Reduce systemic fatigue and restore readiness',
                'prescription': {
                    'frequency': '7-10 days',
                    'exercises': [
                        {'name': 'Technique Work (main lift)', 'sets': 3, 'reps': 5},
                        {'name': 'Breathing + Mobility', 'sets': 1, 'reps': 15},
                    ],
                    'progression_rule': 'Drop volume 20-30%; cap RPE at 6-7 until ACWR returns ≤1.1.'
                }
            })

        if not focus_areas:
            focus_areas.append({
                'area': 'Consistent Progressive Overload',
                'priority': 'medium',
                'objective': 'Continue strength improvements without spiking stress',
                'prescription': {
                    'frequency': 'weekly',
                    'exercises': [
                        {'name': 'Top Set + Backoffs (main lift)', 'sets': 1, 'reps': 3},
                        {'name': 'Backoff Sets', 'sets': 3, 'reps': 5},
                    ],
                    'progression_rule': 'Increase top set 2.5-5kg when RPE ≤8; otherwise add 1 rep to backoffs.'
                }
            })

        # Training Adjustments
        training_adjustments = []
        if acwr > 1.3 or fatigue > 0.7:
            training_adjustments.append({
                'adjustment_type': 'volume_reduction',
                'objective': 'Lower training stress while preserving skill',
                'prescription': {
                    'action': 'Reduce weekly sets 20-30% on primary lifts; keep intensity moderate',
                    'method': f"Because ACWR={acwr:.2f} and fatigue={fatigue:.2f}, cap intensity at RPE 6-7."
                }
            })
        else:
            training_adjustments.append({
                'adjustment_type': 'controlled_overload',
                'objective': 'Increase stimulus without creating risk spikes',
                'prescription': {
                    'action': 'Add 1 set to the primary movement or +2.5kg to top set',
                    'method': f"Only progress if ACWR stays ≤1.2 (current {acwr:.2f}) and fatigue ≤0.7 (current {fatigue:.2f})."
                }
            })

        # Risk Management
        risk_management = []
        if 'high_injury_risk' in risk_flags:
            risk_management.append({
                'risk_type': 'injury_risk',
                'severity': 'high',
                'interventions': [
                    {'exercise': 'Face Pulls', 'sets': 4, 'reps': 15},
                    {'exercise': 'Hip Airplane / Hip CARs', 'sets': 3, 'reps': 6},
                ],
                'temporary_adjustment': {
                    'action': 'Avoid maximal attempts; reduce heavy singles; emphasize technical quality',
                    'duration': '7-14 days'
                }
            })

        if not risk_management:
            risk_management.append({
                'risk_type': 'load_spike_monitoring',
                'severity': 'moderate' if acwr > 1.1 else 'low',
                'interventions': [
                    {'exercise': 'Warm-up ramp discipline', 'sets': 1, 'reps': 1},
                    {'exercise': 'Bracing practice', 'sets': 3, 'reps': 5},
                ],
                'temporary_adjustment': {
                    'action': 'Keep weekly load changes gradual; avoid sudden volume jumps',
                    'duration': 'ongoing'
                }
            })

        sport_specific_programming = {
            'sport': 'Strongman',
            'competition_focus': 'Event strength + work capacity under fatigue',
            'event_specialization': {
                'frequency': '1-2x/week',
                'events': [
                    {'name': 'Yoke Walk', 'sessions': 1, 'focus': 'speed + bracing'},
                    {'name': "Farmer's Walk", 'sessions': 1, 'focus': 'grip endurance'},
                    {'name': 'Log Press', 'sessions': 1, 'focus': 'overhead stability'},
                ],
                'progression_rules': {
                    'event_load': 'Increase event load 2-5% only when ACWR and fatigue remain in safe range',
                    'event_volume': 'Progress distance/time first; add load second'
                }
            }
        }

        # Minimal summary directive used for verification layer
        summary_directive = {
            'recommendation': recommendation,
            'reasoning': f"Elite Strongman Coach readout for {athlete_name}: ACWR={acwr:.2f}, fatigue={fatigue:.2f}, progression={progression}.",
            'confidence': 0.65 if (acwr <= 1.2 and fatigue <= 0.7) else 0.8,
            'action_items': [
                'Keep a weekly log of ACWR/fatigue trend and adjust sets if trend rises',
                'Prioritize event practice with strict technique and bracing standards',
            ],
            'safety_conflicts': []
        }

        package = {
            'summary': summary_directive,
            'directives': {
                'performance_status': performance_status,
                'primary_focus_areas': focus_areas,
                'training_adjustments': training_adjustments,
                'risk_management': risk_management,
                'sport_specific_programming': sport_specific_programming
            }
        }

        self._store_recommendation(athlete_id, context, package)
        return package
    
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
