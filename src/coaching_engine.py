"""
Professional Coaching Feedback Engine for advanced strength athletes.
Structured dashboard outputs for competitive strongman training.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

class CoachingEngine:
    """Professional coaching feedback system for advanced athletes."""
    
    def __init__(self, athlete_data: pd.DataFrame, athlete_profile: Dict = None):
        self.data = athlete_data.copy()
        self.data['date'] = pd.to_datetime(self.data['date'])
        self.athlete_profile = athlete_profile or {}
        self._analyze_performance()
    
    def _analyze_performance(self):
        """Analyze current performance status and trends."""
        if 'volume' not in self.data.columns:
            self.data['volume'] = self.data['weight_kg'] * self.data['sets'] * self.data['reps']
        
        self.data['estimated_1rm'] = self.data.apply(lambda row: row['weight_kg'] * (1 + row['reps'] / 30) if row['reps'] > 1 else row['weight_kg'], axis=1)
        
        recent_data = self.data[self.data['date'] >= (datetime.now() - timedelta(days=28))]
        
        self.performance_analysis = {
            'strength_trend': self._calculate_strength_trend(recent_data),
            'limitations': self._identify_limitations(recent_data)
        }
    
    def _calculate_strength_trend(self, data: pd.DataFrame) -> Dict:
        """Calculate strength progression trend."""
        if len(data) < 4:
            return {'status': 'insufficient_data', 'trend': 0}
        
        trends = []
        for exercise in data['exercise'].unique():
            exercise_data = data[data['exercise'] == exercise].sort_values('date')
            if len(exercise_data) >= 3:
                first_1rm = exercise_data.iloc[0]['estimated_1rm']
                last_1rm = exercise_data.iloc[-1]['estimated_1rm']
                weeks = (exercise_data.iloc[-1]['date'] - exercise_data.iloc[0]['date']).days / 7
                
                if weeks > 0:
                    trends.append((last_1rm - first_1rm) / weeks)
        
        avg_trend = np.mean(trends) if trends else 0
        
        return {
            'status': 'positive' if avg_trend > 0.5 else 'neutral' if avg_trend > 0 else 'negative',
            'trend_kg_per_week': avg_trend
        }
    
    def _identify_limitations(self, data: pd.DataFrame) -> List[Dict]:
        """Identify current performance limitations."""
        limitations = []
        
        for exercise in data['exercise'].unique():
            exercise_data = data[data['exercise'] == exercise].sort_values('date')
            
            if len(exercise_data) >= 4:
                weights = exercise_data['weight_kg'].values
                recent_weights = weights[-4:]
                
                if np.std(recent_weights) / np.mean(recent_weights) < 0.05:
                    limitations.append({
                        'type': 'plateau',
                        'exercise': exercise,
                        'severity': 'moderate'
                    })
        
        pull_exercises = data[data['exercise'].str.contains('pull|row', case=False, na=False)]
        if len(pull_exercises) > 0:
            avg_pull_volume = pull_exercises['volume'].mean()
            if avg_pull_volume < 1000:
                limitations.append({
                    'type': 'grip_strength',
                    'severity': 'moderate'
                })
        
        return limitations
    
    def generate_coaching_directives(self) -> Dict:
        """Generate structured coaching directives for dashboard."""
        return {
            'performance_status': self._generate_performance_status(),
            'primary_focus_areas': self._generate_focus_areas(),
            'training_adjustments': self._generate_training_adjustments(),
            'risk_management': self._generate_risk_management(),
            'sport_specific_programming': self._generate_sport_specific()
        }
    
    def _generate_performance_status(self) -> Dict:
        """Generate performance status section."""
        strength_trend = self.performance_analysis['strength_trend']
        
        return {
            'objective': 'Assess current competitive readiness',
            'current_status': {
                'strength_progression': strength_trend['status'],
                'competition_readiness': 'on_track' if strength_trend['status'] == 'positive' else 'needs_attention'
            },
            'key_metrics': {
                'strength_gain_rate_kg_week': round(strength_trend['trend_kg_per_week'], 2)
            },
            'current_limitations': [lim['type'] for lim in self.performance_analysis['limitations']]
        }
    
    def _generate_focus_areas(self) -> List[Dict]:
        """Generate primary focus areas section."""
        focus_areas = []
        
        grip_limitations = [lim for lim in self.performance_analysis['limitations'] if lim['type'] == 'grip_strength']
        if grip_limitations:
            focus_areas.append({
                'area': 'Grip Strength Development',
                'priority': 'high',
                'objective': 'Improve grip endurance and maximal hold strength',
                'prescription': {
                    'frequency': '3x/week',
                    'exercises': [
                        {'name': "Farmer's Walks", 'sets': 4, 'reps': '30m carries'},
                        {'name': 'Thick Bar Deadlifts', 'sets': 3, 'reps': '5'},
                        {'name': 'Plate Pinches', 'sets': 3, 'reps': '10s hold'}
                    ],
                    'progression_rule': 'Increase load weekly while maintaining carry distance'
                }
            })
        
        return focus_areas
    
    def _generate_training_adjustments(self) -> List[Dict]:
        """Generate training adjustments section."""
        return [{
            'adjustment_type': 'volume_optimization',
            'objective': 'Optimize training volume for progression',
            'prescription': {
                'action': 'Adjust volume based on recovery',
                'method': 'Monitor fatigue and adjust sets accordingly'
            }
        }]
    
    def _generate_risk_management(self) -> List[Dict]:
        """Generate risk management section."""
        return [{
            'risk_type': 'overhead_stability',
            'severity': 'moderate',
            'interventions': [
                {'exercise': 'Face Pulls', 'sets': 4, 'reps': 15},
                {'exercise': 'Band External Rotations', 'sets': 3, 'reps': 12},
                {'exercise': 'Scapular Wall Slides', 'sets': 3, 'reps': 12}
            ],
            'temporary_adjustment': {
                'action': 'Reduce overhead pressing volume by 20%',
                'duration': '2 weeks'
            }
        }]
    
    def _generate_sport_specific(self) -> Dict:
        """Generate strongman-specific programming."""
        return {
            'sport': 'Strongman',
            'competition_focus': 'Regional Qualification',
            'event_specialization': {
                'frequency': '2x/week event practice',
                'events': [
                    {'name': 'Log Press', 'sessions': 2, 'focus': 'Technique'},
                    {'name': 'Stone Loading', 'sessions': 1, 'focus': 'Speed'},
                    {'name': 'Yoke Walk', 'sessions': 1, 'focus': 'Load progression'}
                ],
                'progression_rules': {
                    'technique_events': 'Master movement before adding load',
                    'strength_events': 'Increase load weekly with good form'
                }
            }
        }
