"""
Athlete Profile Management System
Handles athlete profiles, search functionality, and data enrichment
"""

import pandas as pd
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import re

class AthleteProfile:
    """Represents an athlete's comprehensive profile and training context"""
    
    def __init__(self, data: Dict[str, Any]):
        self.athlete_id = data.get('athlete_id', '')
        self.full_name = data.get('full_name', '')
        self.age = data.get('age', 0)
        self.gender = data.get('gender', '')
        self.height_cm = data.get('height_cm', 0)
        self.weight_kg = data.get('weight_kg', 0)
        self.sport = data.get('sport', '')
        self.training_age_years = data.get('training_age_years', 0)
        self.injury_history = data.get('injury_history', [])
        self.preferred_exercises = data.get('preferred_exercises', [])
        self.baseline_rpe = data.get('baseline_rpe', 7)
        self.performance_level = data.get('performance_level', 'intermediate')
        self.max_strength = data.get('max_strength', {})
        self.training_goals = data.get('training_goals', [])
        self.recovery_profile = data.get('recovery_profile', 'normal')
        
    def get_strength_level(self) -> str:
        """Determine strength level based on training age and performance"""
        if self.training_age_years < 1:
            return "beginner"
        elif self.training_age_years < 3:
            return "intermediate" 
        elif self.training_age_years < 5:
            return "advanced"
        else:
            return "elite"
    
    def get_rpe_tolerance(self) -> Dict[str, float]:
        """Get personalized RPE thresholds based on athlete profile"""
        base_tolerance = {
            'beginner': {'low': 6, 'moderate': 7, 'high': 8, 'critical': 9},
            'intermediate': {'low': 7, 'moderate': 8, 'high': 9, 'critical': 9.5},
            'advanced': {'low': 7.5, 'moderate': 8.5, 'high': 9.5, 'critical': 10},
            'elite': {'low': 8, 'moderate': 9, 'high': 9.5, 'critical': 10}
        }
        
        level = self.get_strength_level()
        return base_tolerance.get(level, base_tolerance['intermediate'])
    
    def get_injury_risk_factors(self) -> List[str]:
        """Extract injury risk factors from history"""
        risk_factors = []
        if self.injury_history:
            for injury in self.injury_history:
                if 'lower_back' in injury.lower():
                    risk_factors.append('deadlift_risk')
                if 'shoulder' in injury.lower():
                    risk_factors.append('overhead_risk')
                if 'knee' in injury.lower():
                    risk_factors.append('squat_risk')
        return risk_factors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return {
            'athlete_id': self.athlete_id,
            'full_name': self.full_name,
            'age': self.age,
            'gender': self.gender,
            'height_cm': self.height_cm,
            'weight_kg': self.weight_kg,
            'sport': self.sport,
            'training_age_years': self.training_age_years,
            'injury_history': self.injury_history,
            'preferred_exercises': self.preferred_exercises,
            'baseline_rpe': self.baseline_rpe,
            'performance_level': self.performance_level,
            'max_strength': self.max_strength,
            'training_goals': self.training_goals,
            'recovery_profile': self.recovery_profile,
            'strength_level': self.get_strength_level(),
            'rpe_tolerance': self.get_rpe_tolerance(),
            'injury_risk_factors': self.get_injury_risk_factors()
        }

class AthleteRegistry:
    """Manages athlete profiles and search functionality"""
    
    def __init__(self):
        self.profiles: Dict[str, AthleteProfile] = {}
        self._load_mock_profiles()
    
    def _load_mock_profiles(self):
        """Load comprehensive mock athlete profiles"""
        mock_profiles = [
            {
                'athlete_id': 'ATH001',
                'full_name': 'John "The Beast" Smith',
                'age': 28,
                'gender': 'Male',
                'height_cm': 185,
                'weight_kg': 95,
                'sport': 'Powerlifting',
                'training_age_years': 6,
                'injury_history': ['Lower back strain 2021', 'Shoulder impingement 2022'],
                'preferred_exercises': ['Squat', 'Bench Press', 'Deadlift'],
                'baseline_rpe': 8,
                'performance_level': 'advanced',
                'max_strength': {'Squat': 220, 'Bench Press': 160, 'Deadlift': 280},
                'training_goals': ['Increase deadlift to 300kg', 'Improve bench press technique'],
                'recovery_profile': 'slow'
            },
            {
                'athlete_id': 'ATH002', 
                'full_name': 'Sarah "Thunder" Johnson',
                'age': 25,
                'gender': 'Female',
                'height_cm': 165,
                'weight_kg': 68,
                'sport': 'Olympic Weightlifting',
                'training_age_years': 4,
                'injury_history': ['Wrist sprain 2023'],
                'preferred_exercises': ['Clean & Jerk', 'Snatch', 'Squat'],
                'baseline_rpe': 7.5,
                'performance_level': 'advanced',
                'max_strength': {'Snatch': 85, 'Clean & Jerk': 105, 'Squat': 140},
                'training_goals': ['Qualify for national competition', 'Improve snatch technique'],
                'recovery_profile': 'normal'
            },
            {
                'athlete_id': 'ATH003',
                'full_name': 'Mike "Rookie" Chen',
                'age': 22,
                'gender': 'Male', 
                'height_cm': 175,
                'weight_kg': 75,
                'sport': 'Bodybuilding',
                'training_age_years': 1.5,
                'injury_history': [],
                'preferred_exercises': ['Bench Press', 'Squat', 'Deadlift', 'Overhead Press'],
                'baseline_rpe': 7,
                'performance_level': 'intermediate',
                'max_strength': {'Squat': 120, 'Bench Press': 80, 'Deadlift': 150},
                'training_goals': ['Build muscle mass', 'Improve symmetry'],
                'recovery_profile': 'fast'
            },
            {
                'athlete_id': 'ATH004',
                'full_name': 'Emily "Precision" Davis',
                'age': 30,
                'gender': 'Female',
                'height_cm': 170,
                'weight_kg': 72,
                'sport': 'CrossFit',
                'training_age_years': 5,
                'injury_history': ['Achilles tendinitis 2022'],
                'preferred_exercises': ['Pull-up', 'Barbell Row', 'Overhead Press'],
                'baseline_rpe': 8.5,
                'performance_level': 'advanced',
                'max_strength': {'Pull-up': 25, 'Squat': 130, 'Deadlift': 160},
                'training_goals': ['Improve gymnastics skills', 'Increase work capacity'],
                'recovery_profile': 'normal'
            },
            {
                'athlete_id': 'ATH005',
                'full_name': 'Alex "Powerhouse" Rodriguez',
                'age': 26,
                'gender': 'Male',
                'height_cm': 180,
                'weight_kg': 88,
                'sport': 'Strongman',
                'training_age_years': 3,
                'injury_history': ['Shoulder strain 2023'],
                'preferred_exercises': ['Deadlift', 'Overhead Press', 'Barbell Row'],
                'baseline_rpe': 9,
                'performance_level': 'advanced',
                'max_strength': {'Deadlift': 250, 'Log Press': 100, 'Squat': 200},
                'training_goals': ['Compete in regional strongman', 'Increase grip strength'],
                'recovery_profile': 'slow'
            }
        ]
        
        for profile_data in mock_profiles:
            profile = AthleteProfile(profile_data)
            self.profiles[profile.athlete_id] = profile
    
    def search_athletes(self, query: str) -> List[AthleteProfile]:
        """
        Search for athletes by ID or name (case-insensitive, partial match)
        
        Args:
            query: Search query (athlete_id or name)
            
        Returns:
            List of matching AthleteProfile objects
        """
        if not query:
            return []
        
        query = query.lower().strip()
        results = []
        
        for profile in self.profiles.values():
            # Exact ID match
            if query == profile.athlete_id.lower():
                results.append(profile)
                continue
            
            # Partial ID match
            if query in profile.athlete_id.lower():
                results.append(profile)
                continue
            
            # Name match (partial, case-insensitive)
            if query in profile.full_name.lower():
                results.append(profile)
                continue
        
        return results
    
    def get_athlete_profile(self, athlete_id: str) -> Optional[AthleteProfile]:
        """
        Get athlete profile by ID
        
        Args:
            athlete_id: Unique athlete identifier
            
        Returns:
            AthleteProfile object or None if not found
        """
        return self.profiles.get(athlete_id)
    
    def get_all_athletes(self) -> List[AthleteProfile]:
        """Get all athlete profiles"""
        return list(self.profiles.values())

# Global registry instance
athlete_registry = AthleteRegistry()

def get_athlete_profile(athlete_id: str) -> Optional[AthleteProfile]:
    """
    Convenience function to get athlete profile
    
    Args:
        athlete_id: Unique athlete identifier
        
    Returns:
        AthleteProfile object or None if not found
    """
    return athlete_registry.get_athlete_profile(athlete_id)

def search_athletes(query: str) -> List[AthleteProfile]:
    """
    Convenience function to search athletes
    
    Args:
        query: Search query
        
    Returns:
        List of matching AthleteProfile objects
    """
    return athlete_registry.search_athletes(query)
