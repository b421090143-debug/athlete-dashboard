"""
Progressive overload tracking module for strength and performance analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class ProgressiveOverloadTracker:
    """Track progressive overload and strength gains for athletes."""
    
    def __init__(self, training_data: pd.DataFrame):
        """
        Initialize with training data.
        
        Args:
            training_data: DataFrame with columns including date, athlete_id, exercise, weight_kg, sets, reps
        """
        self.data = training_data.copy()
        self.data['date'] = pd.to_datetime(self.data['date'])
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for progressive overload analysis."""
        # Calculate volume if not present
        if 'volume' not in self.data.columns:
            self.data['volume'] = self.data['weight_kg'] * self.data['sets'] * self.data['reps']
        
        # Calculate 1RM estimation using Epley formula
        self.data['estimated_1rm'] = self.data.apply(self._estimate_1rm, axis=1)
        
        # Sort by athlete, exercise, and date
        self.data = self.data.sort_values(['athlete_id', 'exercise', 'date'])
    
    def _estimate_1rm(self, row) -> float:
        """Estimate 1RM using Epley formula."""
        if row['reps'] == 1:
            return row['weight_kg']
        return row['weight_kg'] * (1 + row['reps'] / 30)
    
    def calculate_volume_progression(self, athlete_id: str, exercise: str = None) -> pd.DataFrame:
        """
        Calculate volume progression for an athlete.
        
        Args:
            athlete_id: ID of the athlete
            exercise: Specific exercise (optional)
        
        Returns:
            DataFrame with volume progression data
        """
        athlete_data = self.data[self.data['athlete_id'] == athlete_id].copy()
        
        if exercise:
            athlete_data = athlete_data[athlete_data['exercise'] == exercise]
        
        # Group by week and calculate weekly volume
        athlete_data['week'] = ((athlete_data['date'] - athlete_data['date'].min()).dt.days // 7) + 1
        
        if exercise:
            # For specific exercise, show each session
            weekly_volume = athlete_data.groupby(['date', 'exercise']).agg({
                'volume': 'sum',
                'weight_kg': 'max',
                'estimated_1rm': 'max',
                'reps': 'max'
            }).reset_index()
        else:
            # For all exercises, show weekly totals
            weekly_volume = athlete_data.groupby(['week', 'exercise']).agg({
                'volume': 'sum',
                'weight_kg': 'max',
                'estimated_1rm': 'max',
                'reps': 'max'
            }).reset_index()
            
            # Also calculate total weekly volume
            total_weekly = athlete_data.groupby('week').agg({
                'volume': 'sum'
            }).reset_index()
            total_weekly['exercise'] = 'TOTAL'
            weekly_volume = pd.concat([weekly_volume, total_weekly], ignore_index=True)
        
        # Calculate trends
        weekly_volume = weekly_volume.sort_values(['exercise', 'week'] if 'week' in weekly_volume.columns else ['exercise', 'date'])
        
        # Add rolling averages and trends
        for exercise_name in weekly_volume['exercise'].unique():
            mask = weekly_volume['exercise'] == exercise_name
            weekly_volume.loc[mask, 'volume_4week_avg'] = weekly_volume.loc[mask, 'volume'].rolling(window=4, min_periods=1).mean()
            weekly_volume.loc[mask, 'volume_trend'] = weekly_volume.loc[mask, 'volume'].pct_change(periods=4)
        
        return weekly_volume
    
    def detect_plateaus(self, athlete_id: str, exercise: str = None, weeks_to_check: int = 4) -> Dict:
        """
        Detect training plateaus for an athlete.
        
        Args:
            athlete_id: ID of the athlete
            exercise: Specific exercise (optional)
            weeks_to_check: Number of recent weeks to analyze
        
        Returns:
            Dictionary with plateau detection results
        """
        volume_data = self.calculate_volume_progression(athlete_id, exercise)
        
        if exercise:
            # Check specific exercise
            exercise_data = volume_data[volume_data['exercise'] == exercise].tail(weeks_to_check)
            if len(exercise_data) < weeks_to_check:
                return {'status': 'insufficient_data', 'plateaus': []}
            
            return self._analyze_plateau(exercise_data, exercise)
        else:
            # Check all exercises
            results = {'status': 'analyzed', 'plateaus': []}
            
            for exercise_name in volume_data['exercise'].unique():
                if exercise_name == 'TOTAL':
                    continue
                    
                exercise_data = volume_data[volume_data['exercise'] == exercise_name].tail(weeks_to_check)
                if len(exercise_data) >= weeks_to_check:
                    plateau_result = self._analyze_plateau(exercise_data, exercise_name)
                    if plateau_result['plateaus']:
                        results['plateaus'].extend(plateau_result['plateaus'])
            
            return results
    
    def _analyze_plateau(self, data: pd.DataFrame, exercise: str) -> Dict:
        """Analyze plateau for specific exercise data."""
        plateaus = []
        
        # Volume plateau check
        if len(data) >= 4:
            volume_trend = stats.linregress(range(len(data)), data['volume']).slope
            if abs(volume_trend) < 0.1:  # Very little change
                plateaus.append({
                    'exercise': exercise,
                    'type': 'volume',
                    'severity': 'moderate' if abs(volume_trend) < 0.05 else 'mild',
                    'trend': volume_trend,
                    'recommendation': self._get_plateau_recommendation('volume', volume_trend)
                })
        
        # Strength plateau check (1RM progression)
        if len(data) >= 3:
            strength_trend = stats.linregress(range(len(data)), data['estimated_1rm']).slope
            if strength_trend < 0.5:  # Less than 0.5kg gain per period
                plateaus.append({
                    'exercise': exercise,
                    'type': 'strength',
                    'severity': 'moderate' if strength_trend < 0.2 else 'mild',
                    'trend': strength_trend,
                    'recommendation': self._get_plateau_recommendation('strength', strength_trend)
                })
        
        return {'status': 'analyzed', 'plateaus': plateaus}
    
    def _get_plateau_recommendation(self, plateau_type: str, trend: float) -> str:
        """Get recommendation for plateau type."""
        if plateau_type == 'volume':
            if trend < 0:
                return "📉 Volume decreasing - consider deload then rebuild"
            else:
                return "📊 Volume stagnant - try exercise variation or intensity increase"
        elif plateau_type == 'strength':
            if trend < 0:
                return "💪 Strength decreasing - check recovery and nutrition"
            else:
                return "🎯 Strength plateau - implement progressive overload techniques"
        
        return "🔍 Analyze training variables and adjust program"
    
    def calculate_strength_velocity(self, athlete_id: str, exercise: str = None) -> Dict:
        """
        Calculate strength gain velocity for an athlete.
        
        Args:
            athlete_id: ID of the athlete
            exercise: Specific exercise (optional)
        
        Returns:
            Dictionary with strength velocity metrics
        """
        athlete_data = self.data[self.data['athlete_id'] == athlete_id].copy()
        
        if exercise:
            athlete_data = athlete_data[athlete_data['exercise'] == exercise]
        
        if len(athlete_data) < 4:
            return {'status': 'insufficient_data'}
        
        # Group by exercise and calculate strength progression
        strength_data = []
        
        for exercise_name in athlete_data['exercise'].unique():
            exercise_data = athlete_data[athlete_data['exercise'] == exercise_name].copy()
            exercise_data = exercise_data.sort_values('date')
            
            # Calculate strength velocity (1RM gain per week)
            if len(exercise_data) >= 4:
                first_1rm = exercise_data.iloc[0]['estimated_1rm']
                last_1rm = exercise_data.iloc[-1]['estimated_1rm']
                weeks = (exercise_data.iloc[-1]['date'] - exercise_data.iloc[0]['date']).days / 7
                
                if weeks > 0:
                    velocity = (last_1rm - first_1rm) / weeks
                    
                    strength_data.append({
                        'exercise': exercise_name,
                        'first_1rm': first_1rm,
                        'last_1rm': last_1rm,
                        'total_gain': last_1rm - first_1rm,
                        'weeks': weeks,
                        'velocity_kg_per_week': velocity,
                        'velocity_percent_per_week': (velocity / first_1rm * 100) if first_1rm > 0 else 0
                    })
        
        if not strength_data:
            return {'status': 'insufficient_data'}
        
        # Calculate overall velocity
        df_strength = pd.DataFrame(strength_data)
        
        return {
            'status': 'calculated',
            'exercises': df_strength.to_dict('records'),
            'avg_velocity_kg_per_week': df_strength['velocity_kg_per_week'].mean(),
            'avg_velocity_percent_per_week': df_strength['velocity_percent_per_week'].mean(),
            'best_exercise': df_strength.loc[df_strength['velocity_kg_per_week'].idxmax(), 'exercise'],
            'total_exercises_analyzed': len(df_strength)
        }
    
    def get_progressive_overload_recommendations(self, athlete_id: str) -> List[str]:
        """Get personalized progressive overload recommendations."""
        recommendations = []
        
        # Check for plateaus
        plateau_analysis = self.detect_plateaus(athlete_id)
        if plateau_analysis['plateaus']:
            recommendations.append("⚠️ **Plateaus Detected:**")
            for plateau in plateau_analysis['plateaus'][:3]:
                recommendations.append(f"• {plateau['exercise']}: {plateau['recommendation']}")
        
        # Check strength velocity
        velocity_analysis = self.calculate_strength_velocity(athlete_id)
        if velocity_analysis['status'] == 'calculated':
            avg_velocity = velocity_analysis['avg_velocity_kg_per_week']
            if avg_velocity < 0.1:
                recommendations.append("📈 **Progressive Overload:** Consider increasing training intensity by 2-5% weekly")
            elif avg_velocity > 1.0:
                recommendations.append("🚀 **Excellent Progress:** Maintain current progression rate")
            else:
                recommendations.append("💪 **Good Progress:** Continue current training approach")
        
        # Volume analysis
        volume_data = self.calculate_volume_progression(athlete_id)
        if 'TOTAL' in volume_data['exercise'].values:
            total_volume = volume_data[volume_data['exercise'] == 'TOTAL']
            if len(total_volume) >= 4:
                recent_trend = total_volume['volume'].tail(4).pct_change().mean()
                if recent_trend < -0.05:
                    recommendations.append("📉 **Volume Trend:** Recent volume decrease - check recovery and stress levels")
                elif recent_trend > 0.1:
                    recommendations.append("📊 **Volume Progression:** Good volume increase - monitor for overtraining")
        
        return recommendations if recommendations else ["✅ **Progressive Overload:** Training progression looks optimal!"]
    
    def create_progressive_overload_dashboard(self, athlete_id: str) -> Dict:
        """Create comprehensive progressive overload dashboard."""
        volume_progression = self.calculate_volume_progression(athlete_id)
        plateau_analysis = self.detect_plateaus(athlete_id)
        strength_velocity = self.calculate_strength_velocity(athlete_id)
        recommendations = self.get_progressive_overload_recommendations(athlete_id)
        
        return {
            'volume_progression': volume_progression,
            'plateau_analysis': plateau_analysis,
            'strength_velocity': strength_velocity,
            'recommendations': recommendations,
            'athlete_id': athlete_id
        }
    
    def create_volume_progression_chart(self, athlete_id: str, exercise: str = None) -> go.Figure:
        """Create volume progression visualization."""
        volume_data = self.calculate_volume_progression(athlete_id, exercise)
        
        fig = go.Figure()
        
        if exercise:
            # Single exercise chart
            exercise_data = volume_data[volume_data['exercise'] == exercise]
            fig.add_trace(go.Scatter(
                x=exercise_data['date'],
                y=exercise_data['volume'],
                mode='lines+markers',
                name=f'{exercise} Volume',
                line=dict(width=2)
            ))
            
            if 'volume_4week_avg' in exercise_data.columns:
                fig.add_trace(go.Scatter(
                    x=exercise_data['date'],
                    y=exercise_data['volume_4week_avg'],
                    mode='lines',
                    name='4-Week Average',
                    line=dict(dash='dash')
                ))
        else:
            # Multiple exercises chart
            for exercise_name in volume_data['exercise'].unique():
                if exercise_name == 'TOTAL':
                    continue
                    
                exercise_data = volume_data[volume_data['exercise'] == exercise_name]
                if 'week' in exercise_data.columns:
                    fig.add_trace(go.Scatter(
                        x=exercise_data['week'],
                        y=exercise_data['volume'],
                        mode='lines+markers',
                        name=exercise_name,
                        line=dict(width=2)
                    ))
        
        fig.update_layout(
            title=f"Volume Progression - {athlete_id}" + (f" ({exercise})" if exercise else ""),
            xaxis_title="Week" if not exercise else "Date",
            yaxis_title="Training Volume (kg × reps × sets)",
            hovermode='x unified'
        )
        
        return fig
    
    def create_strength_velocity_chart(self, athlete_id: str) -> go.Figure:
        """Create strength velocity visualization."""
        velocity_data = self.calculate_strength_velocity(athlete_id)
        
        if velocity_data['status'] != 'calculated':
            return go.Figure()
        
        df = pd.DataFrame(velocity_data['exercises'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['exercise'],
            y=df['velocity_kg_per_week'],
            name='Strength Gain (kg/week)',
            marker_color='lightblue'
        ))
        
        fig.add_hline(y=0.5, line_dash="dash", line_color="green", 
                     annotation_text="Target: 0.5 kg/week")
        
        fig.update_layout(
            title=f"Strength Gain Velocity - {athlete_id}",
            xaxis_title="Exercise",
            yaxis_title="Strength Gain (kg per week)",
            xaxis_tickangle=-45
        )
        
        return fig
