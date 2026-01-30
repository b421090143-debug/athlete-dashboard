"""
Data Enrichment Module
Merges athlete profiles with training data for personalized analytics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.athlete_profiles import get_athlete_profile, AthleteProfile, build_fallback_profile

class DataEnricher:
    """Enriches training data with athlete-specific context and personalized metrics"""
    
    def __init__(self):
        self.enrichment_cache = {}
    
    def enrich_training_data(self, training_df: pd.DataFrame, athlete_id: str) -> pd.DataFrame:
        """
        Enrich training data with athlete profile information
        
        Args:
            training_df: Raw training data
            athlete_id: Target athlete ID
            
        Returns:
            Enriched DataFrame with athlete-specific columns
        """
        profile = get_athlete_profile(athlete_id)
        if not profile:
            profile = build_fallback_profile(athlete_id=athlete_id, training_df=training_df)
        
        enriched_df = training_df.copy()
        
        # Add athlete profile columns
        enriched_df['athlete_name'] = profile.full_name
        enriched_df['athlete_age'] = profile.age
        enriched_df['athlete_gender'] = profile.gender
        enriched_df['athlete_sport'] = profile.sport
        enriched_df['training_age_years'] = profile.training_age_years
        enriched_df['performance_level'] = profile.get_strength_level()
        enriched_df['recovery_profile'] = profile.recovery_profile
        
        # Add personalized RPE analysis
        enriched_df = self._add_personalized_rpe_analysis(enriched_df, profile)
        
        # Add injury risk flags
        enriched_df = self._add_injury_risk_flags(enriched_df, profile)
        
        # Add exercise preference scoring
        enriched_df = self._add_exercise_preference_scores(enriched_df, profile)
        
        # Add relative intensity calculations
        enriched_df = self._add_relative_intensity(enriched_df, profile)
        
        return enriched_df
    
    def _add_personalized_rpe_analysis(self, df: pd.DataFrame, profile: AthleteProfile) -> pd.DataFrame:
        """Add personalized RPE analysis based on athlete profile"""
        rpe_tolerance = profile.get_rpe_tolerance()
        
        # RPE deviation from baseline - handle both raw and processed data
        if 'rpe' in df.columns:
            df['rpe_deviation'] = df['rpe'] - profile.baseline_rpe
            rpe_values = df['rpe']
        elif 'avg_rpe' in df.columns:
            df['rpe_deviation'] = df['avg_rpe'] - profile.baseline_rpe
            rpe_values = df['avg_rpe']
        else:
            # Skip RPE analysis if no RPE data available
            return df
        
        # Personalized RPE zones
        def get_rpe_zone(rpe):
            if rpe <= rpe_tolerance['low']:
                return 'low_intensity'
            elif rpe <= rpe_tolerance['moderate']:
                return 'moderate_intensity'
            elif rpe <= rpe_tolerance['high']:
                return 'high_intensity'
            else:
                return 'critical_intensity'
        
        df['rpe_zone'] = rpe_values.apply(get_rpe_zone)
        
        # Personalized fatigue risk score
        def calculate_fatigue_risk(row):
            base_risk = 0
            
            # RPE-based risk - handle both raw and processed data
            rpe_value = row['rpe'] if 'rpe' in row.index else row.get('avg_rpe', 5)
            if rpe_value > rpe_tolerance['critical']:
                base_risk += 3
            elif rpe_value > rpe_tolerance['high']:
                base_risk += 2
            elif rpe_value > rpe_tolerance['moderate']:
                base_risk += 1
            
            # Recovery profile adjustment
            if profile.recovery_profile == 'slow':
                base_risk += 1
            elif profile.recovery_profile == 'fast':
                base_risk -= 1
            
            # Training age adjustment
            if profile.training_age_years < 2:
                base_risk += 1
            elif profile.training_age_years > 5:
                base_risk -= 1
            
            return min(base_risk, 5)  # Cap at 5
        
        df['fatigue_risk_score'] = df.apply(calculate_fatigue_risk, axis=1)
        
        return df
    
    def _add_injury_risk_flags(self, df: pd.DataFrame, profile: AthleteProfile) -> pd.DataFrame:
        """Add injury risk flags based on athlete history"""
        risk_factors = profile.get_injury_risk_factors()
        
        # Initialize risk flags
        df['injury_risk_flag'] = 'normal'
        df['risk_factors'] = [[] for _ in range(len(df))]
        
        for idx, row in df.iterrows():
            exercise = row['exercise'].lower()
            current_risks = []
            
            # Check exercise-specific risks
            rpe_value = row['rpe'] if 'rpe' in row.index else row.get('avg_rpe', 5)
            
            if 'deadlift_risk' in risk_factors and 'deadlift' in exercise:
                current_risks.append('lower_back')
                if rpe_value > 8:
                    df.at[idx, 'injury_risk_flag'] = 'high'
            
            if 'squat_risk' in risk_factors and 'squat' in exercise:
                current_risks.append('knee')
                if rpe_value > 8.5:
                    df.at[idx, 'injury_risk_flag'] = 'high'
            
            if 'overhead_risk' in risk_factors and any(x in exercise for x in ['overhead', 'press']):
                current_risks.append('shoulder')
                if rpe_value > 8:
                    df.at[idx, 'injury_risk_flag'] = 'high'
            
            df.at[idx, 'risk_factors'] = current_risks
        
        return df
    
    def _add_exercise_preference_scores(self, df: pd.DataFrame, profile: AthleteProfile) -> pd.DataFrame:
        """Add preference scores based on athlete's preferred exercises"""
        preferred = [ex.lower() for ex in profile.preferred_exercises]
        
        def get_preference_score(exercise):
            exercise_lower = exercise.lower()
            if exercise_lower in preferred:
                return 1.0  # Preferred exercise
            elif any(pref in exercise_lower for pref in preferred):
                return 0.8  # Related to preferred
            else:
                return 0.5  # Neutral exercise
        
        df['preference_score'] = df['exercise'].apply(get_preference_score)
        
        return df
    
    def _add_relative_intensity(self, df: pd.DataFrame, profile: AthleteProfile) -> pd.DataFrame:
        """Add relative intensity calculations based on athlete's max strength"""
        max_strength = profile.max_strength
        
        def get_relative_intensity(row):
            exercise = row['exercise']
            weight = row['weight_kg'] if 'weight_kg' in row.index else row.get('avg_weight', 0)
            
            # Map exercise to max strength
            exercise_map = {
                'squat': 'Squat',
                'bench press': 'Bench Press', 
                'deadlift': 'Deadlift',
                'overhead press': 'Overhead Press',
                'barbell row': 'Barbell Row',
                'pull-up': 'Pull-up'
            }
            
            mapped_exercise = exercise_map.get(exercise.lower())
            if mapped_exercise and mapped_exercise in max_strength:
                max_weight = max_strength[mapped_exercise]
                if max_weight > 0:
                    return (weight / max_weight) * 100
            
            return None
        
        df['relative_intensity_percent'] = df.apply(get_relative_intensity, axis=1)
        
        return df
    
    def calculate_personalized_metrics(self, enriched_df: pd.DataFrame, athlete_id: str) -> Dict[str, Any]:
        """
        Calculate personalized metrics based on enriched data
        
        Args:
            enriched_df: Enriched training data
            athlete_id: Athlete identifier
            
        Returns:
            Dictionary of personalized metrics
        """
        profile = get_athlete_profile(athlete_id)
        if not profile:
            # Return basic metrics if profile not found
            return {
                'athlete_context': {
                    'name': 'Unknown Athlete',
                    'sport': 'Unknown',
                    'level': 'unknown',
                    'training_age': 0,
                    'recovery_profile': 'normal'
                },
                'personalized_rpe_stats': {
                    'avg_rpe': enriched_df['rpe'].mean() if 'rpe' in enriched_df.columns else 0,
                    'baseline_deviation': 0,
                    'high_intensity_sessions': 0,
                    'critical_sessions': 0
                },
                'fatigue_analysis': {
                    'avg_fatigue_risk': 0,
                    'high_risk_sessions': 0,
                    'injury_risk_sessions': 0
                },
                'performance_analysis': {
                    'avg_relative_intensity': 0,
                    'preference_compliance': 0,
                    'volume_distribution': {}
                },
                'injury_risk_summary': {
                    'total_risk_factors': 0,
                    'high_risk_exercises': []
                }
            }
        
        metrics = {
            'athlete_context': {
                'name': profile.full_name,
                'sport': profile.sport,
                'level': profile.get_strength_level(),
                'training_age': profile.training_age_years,
                'recovery_profile': profile.recovery_profile
            },
            'personalized_rpe_stats': {
                'avg_rpe': enriched_df['rpe'].mean(),
                'baseline_deviation': enriched_df['rpe_deviation'].mean(),
                'high_intensity_sessions': len(enriched_df[enriched_df['rpe_zone'] == 'high_intensity']),
                'critical_sessions': len(enriched_df[enriched_df['rpe_zone'] == 'critical_intensity'])
            },
            'fatigue_analysis': {
                'avg_fatigue_risk': enriched_df['fatigue_risk_score'].mean(),
                'high_risk_sessions': len(enriched_df[enriched_df['fatigue_risk_score'] >= 3]),
                'injury_risk_sessions': len(enriched_df[enriched_df['injury_risk_flag'] == 'high'])
            },
            'performance_analysis': {
                'avg_relative_intensity': enriched_df['relative_intensity_percent'].mean(),
                'preference_compliance': enriched_df['preference_score'].mean(),
                'volume_distribution': enriched_df.groupby('exercise')['weight_kg'].sum().to_dict()
            },
            'injury_risk_summary': {
                'total_risk_factors': len(profile.get_injury_risk_factors()),
                'high_risk_exercises': enriched_df[enriched_df['injury_risk_flag'] == 'high']['exercise'].unique().tolist()
            }
        }
        
        return metrics

# Global enricher instance
data_enricher = DataEnricher()

def enrich_athlete_data(training_df: pd.DataFrame, athlete_id: str) -> pd.DataFrame:
    """
    Convenience function to enrich athlete training data
    
    Args:
        training_df: Raw training data
        athlete_id: Athlete identifier
        
    Returns:
        Enriched DataFrame
    """
    return data_enricher.enrich_training_data(training_df, athlete_id)

def calculate_personalized_metrics(enriched_df: pd.DataFrame, athlete_id: str) -> Dict[str, Any]:
    """
    Convenience function to calculate personalized metrics
    
    Args:
        enriched_df: Enriched training data
        athlete_id: Athlete identifier
        
    Returns:
        Dictionary of personalized metrics
    """
    return data_enricher.calculate_personalized_metrics(enriched_df, athlete_id)
