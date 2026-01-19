"""
LLM-powered coaching insights and explanations for AthleteInsight.

This module provides natural language explanations of the analytics and ML outputs,
helping coaches understand the data and make informed decisions.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import json

class CoachingStyle(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"

@dataclass
class AthleteContext:
    """Contextual information about an athlete's training status."""
    athlete_id: str
    current_week: str
    metrics: Dict[str, float]  # Current week's metrics
    baseline: Dict[str, float]  # Baseline metrics
    trends: Dict[str, str]      # Trend indicators (e.g., 'increasing', 'decreasing')
    risk_score: float           # Fatigue risk score (0-1)
    risk_category: str          # 'low', 'medium', or 'high'
    recent_injuries: List[str]  # Recent injury history
    training_goals: List[str]   # Athlete's training goals

class CoachingInsightGenerator:
    """Generates human-readable coaching insights from analytics data."""
    
    def __init__(self, coaching_style: CoachingStyle = CoachingStyle.BALANCED):
        """
        Initialize the insight generator.
        
        Args:
            coaching_style: Coaching style (conservative, balanced, or aggressive)
        """
        self.coaching_style = coaching_style
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load coaching insight templates based on coaching style."""
        # Base templates that can be adjusted based on coaching style
        return {
            'risk_assessment': {
                'high': {
                    'conservative': (
                        "⚠️ **High Fatigue Risk Detected**\n"
                        "Your athlete is showing strong signs of accumulated fatigue. "
                        "Immediate deload is strongly recommended to prevent overtraining and injury. "
                        "Consider reducing volume by 40-50% this week and focusing on recovery."
                    ),
                    'balanced': (
                        "⚠️ **Elevated Fatigue Risk**\n"
                        "Your athlete is displaying elevated fatigue levels. "
                        "A deload week with 30-40% reduced volume would be beneficial. "
                        "Monitor closely for signs of overtraining."
                    ),
                    'aggressive': (
                        "⚠️ **Moderate Fatigue Risk**\n"
                        "Your athlete is handling the training load well but is approaching high fatigue. "
                        "Consider a 20-30% volume reduction or maintaining current load with careful monitoring. "
                        "This could be a good time to push through if they're feeling strong."
                    )
                },
                'medium': {
                    'conservative': (
                        "ℹ️ **Moderate Fatigue**\n"
                        "Your athlete is showing some signs of fatigue. "
                        "Consider a small deload (20% volume reduction) or maintaining current load with added recovery. "
                        "Pay attention to their feedback in the coming days."
                    ),
                    'balanced': (
                        "ℹ️ **Moderate Training Load**\n"
                        "Your athlete is adapting well to the current training load. "
                        "The current training stimulus is appropriate for continued progress. "
                        "Maintain or slightly increase volume next week if recovery is good."
                    ),
                    'aggressive': (
                        "ℹ️ **Optimal Training Zone**\n"
                        "Your athlete is in the optimal training zone. "
                        "This is a good time to push for performance gains. "
                        "Consider increasing volume or intensity by 5-10% next week."
                    )
                },
                'low': {
                    'conservative': (
                        "✅ **Well-Recovered**\n"
                        "Your athlete is well-recovered and handling the training load well. "
                        "A small increase in training stimulus (5-10%) would be appropriate "
                        "while maintaining good recovery practices."
                    ),
                    'balanced': (
                        "✅ **Fresh and Ready**\n"
                        "Your athlete is fresh and ready for increased training stimulus. "
                        "Consider increasing volume or intensity by 10-15% next week. "
                        "This is an opportunity for productive training."
                    ),
                    'aggressive': (
                        "✅ **Under-Trained**\n"
                        "Your athlete has recovery capacity for more training stimulus. "
                        "Consider a significant increase in volume (15-25%) or intensity. "
                        "This is an ideal time to push for new performance benchmarks."
                    )
                }
            },
            'trend_insights': {
                'internal_load': {
                    'increasing': "Training load has been increasing over the past few weeks.",
                    'decreasing': "Training load has been decreasing recently.",
                    'stable': "Training load has remained relatively stable."
                },
                'acwr': {
                    'high': "The workload ratio is elevated, indicating a potentially stressful training week.",
                    'optimal': "The workload ratio is in an optimal range for adaptation.",
                    'low': "The workload ratio is low, suggesting room for increased training stimulus."
                },
                'monotony': {
                    'high': "Training monotony is high; consider adding variety to the training program.",
                    'moderate': "Training monotony is at a moderate level.",
                    'low': "Training shows good variation, which helps prevent overuse injuries."
                }
            },
            'recommendations': {
                'strength': [
                    "Focus on compound lifts with progressive overload.",
                    "Incorporate deload weeks every 4-6 weeks.",
                    "Ensure adequate protein intake for muscle recovery.",
                    "Vary rep ranges to target different muscle fibers.",
                    "Include accessory work to address weaknesses."
                ],
                'endurance': [
                    "Gradually increase weekly mileage by no more than 10%.",
                    "Incorporate interval training for improved VO2 max.",
                    "Include long, slow distance sessions for aerobic base building.",
                    "Monitor heart rate zones to ensure proper training intensity.",
                    "Schedule regular recovery weeks to prevent overtraining."
                ],
                'recovery': [
                    "Prioritize sleep quality and quantity.",
                    "Consider active recovery sessions on rest days.",
                    "Ensure proper hydration and nutrition.",
                    "Incorporate mobility and flexibility work.",
                    "Monitor resting heart rate for signs of overreaching."
                ]
            }
        }
    
    def generate_insights(self, athlete_context: AthleteContext) -> Dict[str, Any]:
        """
        Generate coaching insights for an athlete.
        
        Args:
            athlete_context: Context object containing athlete data and metrics
            
        Returns:
            Dictionary containing structured insights and recommendations
        """
        insights = {
            'summary': self._generate_summary(athlete_context),
            'risk_assessment': self._assess_risk(athlete_context),
            'trend_analysis': self._analyze_trends(athlete_context),
            'recommendations': self._generate_recommendations(athlete_context),
            'alerts': self._generate_alerts(athlete_context)
        }
        
        return insights
    
    def _generate_summary(self, context: AthleteContext) -> str:
        """Generate a summary of the athlete's current training status."""
        risk_level = context.risk_category.lower()
        risk_templates = self.templates['risk_assessment'][risk_level]
        return risk_templates[self.coaching_style.value]
    
    def _assess_risk(self, context: AthleteContext) -> Dict[str, Any]:
        """Assess and explain the fatigue risk."""
        risk_score = context.risk_score
        risk_category = context.risk_category.lower()
        
        # Get risk explanation based on coaching style
        risk_explanation = self.templates['risk_assessment'][risk_category][self.coaching_style.value]
        
        # Add metrics contributing to risk
        risk_factors = []
        if context.metrics.get('acwr', 0) > 1.5:
            risk_factors.append("High acute:chronic workload ratio")
        if context.metrics.get('monotony', 0) > 2.0:
            risk_factors.append("High training monotony")
        if context.trends.get('internal_load') == 'increasing':
            risk_factors.append("Consistently increasing training load")
        
        return {
            'score': risk_score,
            'category': risk_category,
            'explanation': risk_explanation,
            'contributing_factors': risk_factors or ["No significant risk factors detected"],
            'confidence': self._calculate_confidence(risk_score, context.metrics)
        }
    
    def _analyze_trends(self, context: AthleteContext) -> Dict[str, str]:
        """Analyze and explain training trends."""
        trend_insights = {}
        
        # Analyze internal load trend
        load_trend = context.trends.get('internal_load', 'stable')
        trend_insights['load'] = self.templates['trend_insights']['internal_load'].get(
            load_trend, 
            "Training load trend analysis not available."
        )
        
        # Analyze ACWR
        acwr = context.metrics.get('acwr', 0)
        if acwr > 1.5:
            acwr_status = 'high'
        elif 0.8 <= acwr <= 1.5:
            acwr_status = 'optimal'
        else:
            acwr_status = 'low'
        trend_insights['workload_ratio'] = self.templates['trend_insights']['acwr'].get(
            acwr_status,
            f"Current workload ratio: {acwr:.2f}"
        )
        
        # Analyze monotony
        monotony = context.metrics.get('monotony', 0)
        if monotony > 2.0:
            mono_status = 'high'
        elif 1.0 <= monotony <= 2.0:
            mono_status = 'moderate'
        else:
            mono_status = 'low'
        trend_insights['monotony'] = self.templates['trend_insights']['monotony'].get(
            mono_status,
            f"Training monotony score: {monotony:.2f}"
        )
        
        return trend_insights
    
    def _generate_recommendations(self, context: AthleteContext) -> Dict[str, List[str]]:
        """Generate personalized training recommendations."""
        recommendations = {
            'strength': [],
            'endurance': [],
            'recovery': [],
            'other': []
        }
        
        # Add general recommendations based on risk level
        if context.risk_category == 'high':
            recommendations['recovery'].extend([
                "Prioritize recovery this week with reduced volume and intensity.",
                "Increase sleep duration by 30-60 minutes per night.",
                "Consider scheduling a sports massage or other recovery modalities."
            ])
        elif context.risk_category == 'medium':
            recommendations['strength'].extend([
                "Maintain current training load with focus on technique.",
                "Consider a small deload if fatigue persists."
            ])
        else:  # Low risk
            recommendations['strength'].extend([
                "Consider increasing training stimulus by 5-15% next week.",
                "This is a good time to focus on strength or performance goals."
            ])
        
        # Add specific recommendations based on metrics
        if context.metrics.get('acwr', 0) > 1.5:
            recommendations['recovery'].append(
                "Gradually reduce training load to bring ACWR back to optimal range (0.8-1.5)."
            )
        
        if context.metrics.get('monotony', 0) > 2.0:
            recommendations['strength'].append(
                "Add variety to training sessions to reduce monotony and prevent overuse injuries."
            )
        
        # Add general recommendations from templates
        for category in ['strength', 'endurance', 'recovery']:
            if category in recommendations:
                recommendations[category].extend(
                    self.templates['recommendations'][category][:2]  # Add top 2 from each category
                )
        
        return {k: v for k, v in recommendations.items() if v}  # Remove empty categories
    
    def _generate_alerts(self, context: AthleteContext) -> List[Dict[str, str]]:
        """Generate any critical alerts for the coach."""
        alerts = []
        
        # High fatigue risk alert
        if context.risk_category == 'high' and context.risk_score > 0.7:
            alerts.append({
                'level': 'high',
                'message': 'High fatigue risk detected. Immediate deload recommended.',
                'metric': 'fatigue_risk',
                'value': context.risk_score
            })
        
        # Spikes in training load
        if context.metrics.get('acwr', 0) > 1.8:
            alerts.append({
                'level': 'high',
                'message': f'Significant spike in training load (ACWR: {context.metrics["acwr"]:.2f})',
                'metric': 'acwr',
                'value': context.metrics['acwr']
            })
        
        # High training monotony
        if context.metrics.get('monotony', 0) > 2.5:
            alerts.append({
                'level': 'medium',
                'message': 'High training monotony detected. Consider adding more variety.',
                'metric': 'monotony',
                'value': context.metrics['monotony']
            })
        
        return alerts
    
    def _calculate_confidence(self, risk_score: float, metrics: Dict[str, float]) -> float:
        """Calculate confidence score for the risk assessment."""
        # Base confidence on how far the score is from 0.5 (neutral)
        confidence = abs(risk_score - 0.5) * 2  # 0-1 scale
        
        # Adjust based on data quality and completeness
        if all(k in metrics for k in ['internal_load', 'acwr', 'monotony']):
            confidence *= 1.1  # 10% boost for complete data
        
        return min(max(confidence, 0), 1.0)  # Ensure 0-1 range


def format_insights_for_display(insights: Dict[str, Any]) -> str:
    """
    Format insights into a human-readable markdown string.
    
    Args:
        insights: Dictionary of insights from generate_insights()
        
    Returns:
        Formatted markdown string
    """
    markdown = []
    
    # Summary section
    markdown.append("## 🏋️ Training Status Summary")
    markdown.append(insights['summary'])
    
    # Risk assessment
    risk = insights['risk_assessment']
    markdown.append(f"\n## ⚠️ Fatigue Risk Assessment ({risk['category'].title()}: {risk['score']:.1%} confidence)")
    markdown.append(risk['explanation'])
    
    if risk['contributing_factors']:
        markdown.append("\n**Key Factors:**")
        for factor in risk['contributing_factors']:
            markdown.append(f"- {factor}")
    
    # Trend analysis
    markdown.append("\n## 📈 Trend Analysis")
    for metric, insight in insights['trend_analysis'].items():
        markdown.append(f"- **{metric.replace('_', ' ').title()}**: {insight}")
    
    # Recommendations
    markdown.append("\n## 🎯 Recommendations")
    for category, recs in insights['recommendations'].items():
        if recs:
            markdown.append(f"\n### {category.title()}")
            for rec in recs:
                markdown.append(f"- {rec}")
    
    # Alerts
    if insights['alerts']:
        markdown.append("\n## 🚨 Alerts")
        for alert in insights['alerts']:
            level_emoji = '🔴' if alert['level'] == 'high' else '🟠' if alert['level'] == 'medium' else '🟡'
            markdown.append(f"{level_emoji} **{alert['level'].title()}**: {alert['message']} ({alert['metric']}: {alert['value']:.2f})")
    
    return "\n".join(markdown)
