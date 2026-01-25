"""
Recovery and fatigue tracking module for athlete performance analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

class RecoveryTracker:
    """Track athlete recovery and fatigue based on training data."""
    
    def __init__(self, training_data: pd.DataFrame):
        """
        Initialize with training data.
        
        Args:
            training_data: DataFrame with columns including date, athlete_id, rpe, volume
        """
        self.data = training_data.copy()
        self.data['date'] = pd.to_datetime(self.data['date'])
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for recovery analysis."""
        # Calculate daily training load if not present
        if 'load' not in self.data.columns:
            if 'volume' in self.data.columns and 'rpe' in self.data.columns:
                self.data['load'] = self.data['volume'] * self.data['rpe']
            elif 'weight_kg' in self.data.columns and 'sets' in self.data.columns and 'reps' in self.data.columns and 'rpe' in self.data.columns:
                self.data['volume'] = self.data['weight_kg'] * self.data['sets'] * self.data['reps']
                self.data['load'] = self.data['volume'] * self.data['rpe']
        
        # Calculate daily load per athlete
        self.daily_load = self.data.groupby(['athlete_id', 'date'])['load'].sum().reset_index()
        self.daily_load = self.daily_load.sort_values(['athlete_id', 'date'])
    
    def calculate_acute_chronic_load(self, athlete_id: str, acute_days: int = 7, chronic_days: int = 28) -> pd.DataFrame:
        """
        Calculate Acute:Chronic Workload Ratio (ACWR).
        
        Args:
            athlete_id: ID of the athlete
            acute_days: Days for acute load calculation (default 7)
            chronic_days: Days for chronic load calculation (default 28)
        
        Returns:
            DataFrame with ACWR values
        """
        athlete_data = self.daily_load[self.daily_load['athlete_id'] == athlete_id].copy()
        
        # Calculate rolling averages
        athlete_data['acute_load'] = athlete_data['load'].rolling(window=acute_days, min_periods=1).mean()
        athlete_data['chronic_load'] = athlete_data['load'].rolling(window=chronic_days, min_periods=1).mean()
        
        # Calculate ACWR with safety check
        athlete_data['acwr'] = athlete_data['acute_load'] / athlete_data['chronic_load'].replace(0, np.nan)
        
        # Add fatigue zones
        athlete_data['fatigue_zone'] = athlete_data['acwr'].apply(self._get_fatigue_zone)
        
        return athlete_data
    
    def _get_fatigue_zone(self, acwr: float) -> str:
        """Determine fatigue zone based on ACWR."""
        if pd.isna(acwr):
            return 'insufficient_data'
        elif acwr < 0.8:
            return 'undertraining'
        elif acwr <= 1.0:
            return 'optimal'
        elif acwr <= 1.3:
            return 'caution'
        else:
            return 'high_risk'
    
    def calculate_recovery_score(self, athlete_id: str, days_back: int = 7) -> Dict:
        """
        Calculate comprehensive recovery score.
        
        Args:
            athlete_id: ID of the athlete
            days_back: Number of days to look back for recovery calculation
        
        Returns:
            Dictionary with recovery metrics
        """
        athlete_data = self.daily_load[self.daily_load['athlete_id'] == athlete_id].copy()
        
        # Get recent data
        recent_data = athlete_data.tail(days_back)
        
        if len(recent_data) < 3:
            return {'score': 50, 'status': 'insufficient_data', 'factors': {}}
        
        # Calculate recovery factors
        avg_load = recent_data['load'].mean()
        load_trend = self._calculate_load_trend(recent_data)
        load_variability = recent_data['load'].std()
        
        # Recovery score calculation (0-100)
        score = 50  # Base score
        
        # Load trend factor (-20 to +20)
        if load_trend < -0.1:  # Decreasing load (good for recovery)
            score += min(20, abs(load_trend) * 100)
        elif load_trend > 0.2:  # Rapidly increasing load (bad for recovery)
            score -= min(20, load_trend * 100)
        
        # Load variability factor (-15 to +15)
        if load_variability < avg_load * 0.2:  # Low variability (good)
            score += 15
        elif load_variability > avg_load * 0.5:  # High variability (bad)
            score -= 15
        
        # Recent load factor
        recent_avg = recent_data.tail(3)['load'].mean()
        if recent_avg < avg_load * 0.7:  # Recent deload
            score += 10
        elif recent_avg > avg_load * 1.3:  # Recent overload
            score -= 10
        
        score = max(0, min(100, score))
        
        return {
            'score': round(score),
            'status': self._get_recovery_status(score),
            'factors': {
                'load_trend': round(load_trend, 3),
                'avg_load': round(avg_load, 1),
                'load_variability': round(load_variability, 1),
                'recent_avg_load': round(recent_avg, 1)
            }
        }
    
    def _calculate_load_trend(self, data: pd.DataFrame) -> float:
        """Calculate load trend using linear regression."""
        if len(data) < 2:
            return 0.0
        
        x = np.arange(len(data))
        y = data['load'].values
        slope = np.polyfit(x, y, 1)[0]
        return slope / np.mean(y) if np.mean(y) != 0 else 0
    
    def _get_recovery_status(self, score: int) -> str:
        """Get recovery status based on score."""
        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'moderate'
        elif score >= 20:
            return 'poor'
        else:
            return 'critical'
    
    def get_recovery_recommendations(self, athlete_id: str) -> List[str]:
        """Get personalized recovery recommendations."""
        recovery_data = self.calculate_recovery_score(athlete_id)
        acwr_data = self.calculate_acute_chronic_load(athlete_id)
        
        recommendations = []
        
        # Based on recovery score
        if recovery_data['score'] < 40:
            recommendations.append("🛑 Consider a rest day or light recovery session")
            recommendations.append("💧 Focus on hydration and nutrition")
            recommendations.append("😴 Ensure 7-9 hours of quality sleep")
        elif recovery_data['score'] < 60:
            recommendations.append("⚠️ Reduce training intensity by 20-30%")
            recommendations.append("🧘 Add mobility work or light cardio")
        elif recovery_data['score'] > 80:
            recommendations.append("💪 Good recovery - maintain current training load")
            recommendations.append("🎯 Consider slight intensity increase if feeling strong")
        
        # Based on ACWR
        recent_acwr = acwr_data.tail(1)['acwr'].iloc[0] if len(acwr_data) > 0 else 1.0
        if recent_acwr > 1.3:
            recommendations.append("⚠️ High training stress - schedule deload week soon")
        elif recent_acwr < 0.8:
            recommendations.append("📈 Training load is low - consider gradual increase")
        
        return recommendations if recommendations else ["✅ Training load looks balanced - keep it up!"]
    
    def create_recovery_dashboard(self, athlete_id: str) -> Dict:
        """Create comprehensive recovery dashboard data."""
        recovery_score = self.calculate_recovery_score(athlete_id)
        acwr_data = self.calculate_acute_chronic_load(athlete_id)
        recommendations = self.get_recovery_recommendations(athlete_id)
        
        return {
            'recovery_score': recovery_score,
            'acwr_data': acwr_data,
            'recommendations': recommendations,
            'athlete_id': athlete_id
        }
    
    def create_recovery_visualization(self, athlete_id: str):
        """Create recovery visualization plot."""
        acwr_data = self.calculate_acute_chronic_load(athlete_id)
        
        fig = go.Figure()
        
        # Add ACWR line
        fig.add_trace(go.Scatter(
            x=acwr_data['date'],
            y=acwr_data['acwr'],
            mode='lines+markers',
            name='ACWR',
            line=dict(color='blue', width=2)
        ))
        
        # Add risk zones
        fig.add_hline(y=1.3, line_dash="dash", line_color="red", annotation_text="High Risk")
        fig.add_hline(y=1.0, line_dash="dash", line_color="green", annotation_text="Optimal")
        fig.add_hline(y=0.8, line_dash="dash", line_color="orange", annotation_text="Undertraining")
        
        fig.update_layout(
            title=f"Acute:Chronic Workload Ratio - {athlete_id}",
            xaxis_title="Date",
            yaxis_title="ACWR",
            hovermode='x unified'
        )
        
        return fig
