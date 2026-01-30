"""
Personalized Insights Engine
Generates athlete-specific coaching insights and recommendations
"""

from typing import Dict, List, Any, Optional
from src.athlete_profiles import get_athlete_profile, AthleteProfile
from src.data_enrichment import calculate_personalized_metrics
import pandas as pd

class PersonalizedInsightsEngine:
    """Generates deeply personalized coaching insights based on athlete profile and enriched data"""
    
    def __init__(self):
        self.insight_templates = self._load_insight_templates()
    
    def _load_insight_templates(self) -> Dict[str, List[str]]:
        """Load coaching insight templates for different scenarios"""
        return {
            'fatigue_risk': [
                "{name}, your RPE has been consistently high. Given your {level} experience and {recovery} recovery profile, consider reducing intensity by 10-15% for the next 3-4 sessions.",
                "Based on your {sport} background and current fatigue indicators, I recommend prioritizing recovery. Your {age} age and {training_age} years of training suggest you need more deload periods.",
                "{name}, your injury history with {injury_areas} combined with current RPE trends indicates elevated risk. Let's focus on technique work and volume reduction."
            ],
            'progression_positive': [
                "Excellent progress, {name}! Your {level} level is showing in your consistent strength gains. Keep this trajectory and you'll reach your {goals} soon.",
                "Your {sport} experience is really showing, {name}. The personalized programming is working well for your {recovery} recovery profile.",
                "Great work adapting the training to your {age} age and {training_age} years experience. Your {injury_areas} are handling the load well."
            ],
            'plateau_detection': [
                "{name}, I'm seeing a plateau in your {exercise} performance. Given your {level} level, let's introduce some variation - perhaps tempo work or accessory exercises?",
                "Your {sport} background suggests you might benefit from periodization. With your {training_age} years of experience, a 3-week intensity block could break through this plateau.",
                "Considering your {injury_areas} history, let's try a different approach. Maybe focus on volume for {exercise} while maintaining intensity on other movements."
            ],
            'injury_prevention': [
                "{name}, your {injury_areas} require careful monitoring. I recommend reducing load on {risky_exercises} and increasing mobility work.",
                "Given your {age} and {injury_areas} history, let's prioritize longevity over intensity. Your {sport} goals are achievable with smarter programming.",
                "Your injury risk factors suggest we should modify your {exercise} technique. With your {level} experience, you'll adapt quickly to safer movement patterns."
            ],
            'recovery_guidance': [
                "{name}, your {recovery} recovery profile means you need extra attention to sleep and nutrition. Consider adding an extra rest day this week.",
                "Based on your {age} and current training load, I recommend implementing active recovery sessions. Your {sport} performance will benefit from this.",
                "Your fatigue indicators suggest we need to respect your {recovery} recovery needs. Let's reduce training density for the next week."
            ]
        }
    
    def generate_personalized_insights(self, enriched_df: pd.DataFrame, athlete_id: str) -> List[str]:
        """
        Generate personalized insights for an athlete
        
        Args:
            enriched_df: Enriched training data
            athlete_id: Athlete identifier
            
        Returns:
            List of personalized coaching insights
        """
        profile = get_athlete_profile(athlete_id)
        if not profile:
            profile = self._build_fallback_profile(enriched_df, athlete_id)
        
        metrics = calculate_personalized_metrics(enriched_df, athlete_id)
        insights = []
        
        # Generate insights based on different analysis categories
        insights.extend(self._analyze_fatigue_risk(profile, metrics))
        insights.extend(self._analyze_progression(profile, metrics, enriched_df))
        insights.extend(self._analyze_injury_risk(profile, metrics, enriched_df))
        insights.extend(self._analyze_recovery_needs(profile, metrics))
        insights.extend(self._analyze_performance_trends(profile, metrics, enriched_df))
        insights.extend(self._generate_personalized_recommendations(profile, metrics))
        
        return insights

    def _build_fallback_profile(self, enriched_df: pd.DataFrame, athlete_id: str) -> AthleteProfile:
        sport = "Strength"
        if 'exercise' in enriched_df.columns:
            ex = set(enriched_df['exercise'].dropna().astype(str).unique().tolist())
            strongman_markers = {
                'Log Press',
                'Yoke Walk',
                "Farmer's Walk",
                'Atlas Stone Load',
                'Sandbag Carry',
            }
            if any(e in strongman_markers for e in ex):
                sport = "Strongman"

        baseline_rpe = 7
        if 'rpe' in enriched_df.columns and len(enriched_df) > 0:
            try:
                baseline_rpe = float(pd.to_numeric(enriched_df['rpe'], errors='coerce').dropna().mean())
                if pd.isna(baseline_rpe):
                    baseline_rpe = 7
                baseline_rpe = max(5.5, min(9.5, baseline_rpe))
            except Exception:
                baseline_rpe = 7

        training_age_years = 1.0
        if 'date' in enriched_df.columns and len(enriched_df) > 1:
            try:
                dates = pd.to_datetime(enriched_df['date'], errors='coerce').dropna()
                if len(dates) > 1:
                    span_days = (dates.max() - dates.min()).days
                    training_age_years = max(0.5, min(6.0, span_days / 365.0))
            except Exception:
                training_age_years = 1.0

        profile_data = {
            'athlete_id': athlete_id,
            'full_name': f"Athlete {athlete_id}",
            'age': 28,
            'gender': '',
            'height_cm': 0,
            'weight_kg': 0,
            'sport': sport,
            'training_age_years': training_age_years,
            'injury_history': [],
            'preferred_exercises': [],
            'baseline_rpe': baseline_rpe,
            'performance_level': 'intermediate',
            'max_strength': {},
            'training_goals': ['Improve strength', 'Improve conditioning'],
            'recovery_profile': 'normal'
        }
        return AthleteProfile(profile_data)
    
    def _analyze_fatigue_risk(self, profile: AthleteProfile, metrics: Dict[str, Any]) -> List[str]:
        """Analyze fatigue risk and generate personalized recommendations"""
        insights = []
        context = self._get_context_variables(profile)
        
        fatigue_score = metrics['fatigue_analysis']['avg_fatigue_risk']
        high_risk_sessions = metrics['fatigue_analysis']['high_risk_sessions']
        
        if fatigue_score >= 3:
            template = self.insight_templates['fatigue_risk'][0]
            insights.append(template.format(**context))
        elif high_risk_sessions > 2:
            template = self.insight_templates['fatigue_risk'][1]
            insights.append(template.format(**context))
        
        return insights
    
    def _analyze_progression(self, profile: AthleteProfile, metrics: Dict[str, Any], df: pd.DataFrame) -> List[str]:
        """Analyze progression patterns and provide feedback"""
        insights = []
        context = self._get_context_variables(profile)
        
        # Check for positive progression
        if metrics['personalized_rpe_stats']['baseline_deviation'] < 0.5:
            template = self.insight_templates['progression_positive'][0]
            insights.append(template.format(**context))
        
        # Check for plateaus
        if len(df) > 10:  # Need sufficient data for plateau detection
            recent_performance = df.tail(5)['weight_kg'].mean()
            earlier_performance = df.head(5)['weight_kg'].mean()
            
            if abs(recent_performance - earlier_performance) < 5:
                context['exercise'] = df['exercise'].iloc[0]  # Primary exercise
                template = self.insight_templates['plateau_detection'][0]
                insights.append(template.format(**context))
        
        return insights
    
    def _analyze_injury_risk(self, profile: AthleteProfile, metrics: Dict[str, Any], df: pd.DataFrame) -> List[str]:
        """Analyze injury risk factors and provide prevention guidance"""
        insights = []
        context = self._get_context_variables(profile)
        
        high_risk_sessions = metrics['fatigue_analysis']['injury_risk_sessions']
        risky_exercises = metrics['injury_risk_summary']['high_risk_exercises']
        
        if high_risk_sessions > 1:
            context['injury_areas'] = ', '.join(profile.get_injury_risk_factors())
            context['risky_exercises'] = ', '.join(risky_exercises[:2])  # Limit to 2 exercises
            template = self.insight_templates['injury_prevention'][0]
            insights.append(template.format(**context))
        
        return insights
    
    def _analyze_recovery_needs(self, profile: AthleteProfile, metrics: Dict[str, Any]) -> List[str]:
        """Analyze recovery needs and provide guidance"""
        insights = []
        context = self._get_context_variables(profile)
        
        if profile.recovery_profile == 'slow' and metrics['personalized_rpe_stats']['avg_rpe'] > 8:
            template = self.insight_templates['recovery_guidance'][0]
            insights.append(template.format(**context))
        
        return insights
    
    def _analyze_performance_trends(self, profile: AthleteProfile, metrics: Dict[str, Any], df: pd.DataFrame) -> List[str]:
        """Analyze performance trends and provide sport-specific insights"""
        insights = []
        context = self._get_context_variables(profile)
        
        # Sport-specific insights
        if profile.sport == 'Powerlifting':
            if metrics['performance_analysis']['avg_relative_intensity'] > 85:
                insights.append(f"{context['name']}, your relative intensity is excellent for powerlifting. Focus on technique refinement at these intensities.")
        
        elif profile.sport == 'Olympic Weightlifting':
            if metrics['performance_analysis']['preference_compliance'] > 0.8:
                insights.append(f"Great consistency with your preferred weightlifting movements, {context['name']}. This specificity will serve you well in competition.")
        
        elif profile.sport == 'Bodybuilding':
            if metrics['performance_analysis']['avg_relative_intensity'] < 70:
                insights.append(f"{context['name']}, consider increasing your training intensity slightly. Your current relative intensity might be too low for optimal hypertrophy.")
        
        return insights
    
    def _generate_personalized_recommendations(self, profile: AthleteProfile, metrics: Dict[str, Any]) -> List[str]:
        """Generate personalized training recommendations"""
        insights = []
        context = self._get_context_variables(profile)
        
        # Goal-specific recommendations
        if 'strength' in str(profile.training_goals).lower():
            insights.append(f"For your strength goals, {context['name']}, I recommend focusing on compound movements 3x per week with your current {context['level']} level.")
        
        if 'competition' in str(profile.training_goals).lower():
            insights.append(f"Given your competition goals, {context['name']}, let's implement a 12-week peaking cycle tailored to your {context['sport']} requirements.")
        
        # Age-specific recommendations
        if profile.age > 30:
            insights.append(f"At {context['age']}, {context['name']}, prioritize joint health and recovery. Consider adding mobility work 3x per week.")
        
        return insights
    
    def _get_context_variables(self, profile: AthleteProfile) -> Dict[str, str]:
        """Get context variables for insight templates"""
        injury_areas = ', '.join(profile.get_injury_risk_factors()).replace('_', ' ').title()
        goals = ', '.join(profile.training_goals[:2]) if profile.training_goals else 'performance improvement'
        
        return {
            'name': profile.full_name.split()[0],  # First name for personalization
            'level': profile.get_strength_level(),
            'age': profile.age,
            'training_age': profile.training_age_years,
            'sport': profile.sport,
            'recovery': profile.recovery_profile,
            'injury_areas': injury_areas if injury_areas else 'no significant injury history',
            'goals': goals
        }
    
    def generate_athlete_summary(self, enriched_df: pd.DataFrame, athlete_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive athlete summary
        
        Args:
            enriched_df: Enriched training data
            athlete_id: Athlete identifier
            
        Returns:
            Comprehensive athlete summary
        """
        profile = get_athlete_profile(athlete_id)
        if not profile:
            profile = self._build_fallback_profile(enriched_df, athlete_id)
        
        metrics = calculate_personalized_metrics(enriched_df, athlete_id)
        
        summary = {
            'athlete_profile': profile.to_dict(),
            'training_metrics': metrics,
            'key_insights': self.generate_personalized_insights(enriched_df, athlete_id),
            'performance_status': self._determine_performance_status(metrics),
            'coaching_priorities': self._determine_coaching_priorities(profile, metrics)
        }
        
        return summary
    
    def _determine_performance_status(self, metrics: Dict[str, Any]) -> str:
        """Determine overall performance status"""
        fatigue_score = metrics['fatigue_analysis']['avg_fatigue_risk']
        progression_score = 1 - abs(metrics['personalized_rpe_stats']['baseline_deviation'])
        
        if fatigue_score >= 3:
            return "needs_recovery"
        elif progression_score > 0.8:
            return "excellent_progress"
        elif progression_score > 0.5:
            return "steady_progress"
        else:
            return "needs_adjustment"
    
    def _determine_coaching_priorities(self, profile: AthleteProfile, metrics: Dict[str, Any]) -> List[str]:
        """Determine coaching priorities based on athlete data"""
        priorities = []
        
        if metrics['fatigue_analysis']['avg_fatigue_risk'] >= 3:
            priorities.append("Recovery and fatigue management")
        
        if len(profile.get_injury_risk_factors()) > 0:
            priorities.append("Injury prevention and movement quality")
        
        if metrics['performance_analysis']['avg_relative_intensity'] < 60:
            priorities.append("Increase training intensity")
        
        if profile.training_age_years < 2:
            priorities.append("Technique development and consistency")
        
        return priorities

# Global insights engine instance
insights_engine = PersonalizedInsightsEngine()

def generate_personalized_insights(enriched_df: pd.DataFrame, athlete_id: str) -> List[str]:
    """
    Convenience function to generate personalized insights
    
    Args:
        enriched_df: Enriched training data
        athlete_id: Athlete identifier
        
    Returns:
        List of personalized coaching insights
    """
    return insights_engine.generate_personalized_insights(enriched_df, athlete_id)

def generate_athlete_summary(enriched_df: pd.DataFrame, athlete_id: str) -> Dict[str, Any]:
    """
    Convenience function to generate comprehensive athlete summary
    
    Args:
        enriched_df: Enriched training data
        athlete_id: Athlete identifier
        
    Returns:
        Comprehensive athlete summary
    """
    return insights_engine.generate_athlete_summary(enriched_df, athlete_id)
