"""
Advanced training metrics and ML components for AthleteInsight.

This module provides advanced sports science metrics and machine learning
capabilities for athlete performance analysis.
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

class AdvancedMetrics:
    """Class for computing advanced sports science metrics from training data."""
    
    def __init__(self, athlete_data: pd.DataFrame):
        """
        Initialize with athlete training data.
        
        Args:
            athlete_data: DataFrame containing training data with columns:
                         ['athlete_id', 'date', 'exercise', 'weight_kg', 'sets', 'reps', 'rpe']
        """
        self.data = athlete_data.copy()
        self._preprocess_data()
        
    def _preprocess_data(self) -> None:
        """Preprocess the input data and calculate basic metrics."""
        # Ensure date is datetime
        self.data['date'] = pd.to_datetime(self.data['date'])
        
        # Calculate volume and load
        self.data['volume'] = self.data['weight_kg'] * self.data['sets'] * self.data['reps']
        self.data['load'] = self.data['volume'] * self.data['rpe']
        
        # Add week number
        self.data['week'] = self.data['date'].dt.isocalendar().week
        self.data['year'] = self.data['date'].dt.isocalendar().year
        self.data['week_id'] = self.data['year'].astype(str) + '-' + self.data['week'].astype(str)
    
    def calculate_weekly_metrics(self) -> pd.DataFrame:
        """
        Calculate weekly metrics for each athlete.
        
        Returns:
            DataFrame with weekly metrics including internal load, density, etc.
        """
        # Group by athlete and week
        weekly = self.data.groupby(['athlete_id', 'week_id', 'year', 'week']).agg({
            'load': 'sum',
            'volume': 'sum',
            'rpe': 'mean',
            'date': ['min', 'max', 'count']  # min/max date, session count
        })
        
        # Flatten multi-index columns
        weekly.columns = ['_'.join(col).strip('_') for col in weekly.columns.values]
        weekly = weekly.reset_index()
        
        # Calculate advanced metrics
        weekly['internal_load'] = weekly['volume_sum'] * weekly['rpe_mean']
        weekly['training_density'] = weekly['volume_sum'] / weekly['date_count']
        
        # Calculate monotony (using daily load variation)
        daily_load = self.data.groupby(['athlete_id', 'date'])['load'].sum().reset_index()
        daily_load['week_id'] = daily_load['date'].dt.isocalendar().year.astype(str) + '-' + \
                              daily_load['date'].dt.isocalendar().week.astype(str)
        
        monotony = daily_load.groupby(['athlete_id', 'week_id'])['load'].agg(['mean', 'std'])
        monotony['monotony'] = monotony['mean'] / (monotony['std'] + 1e-6)  # Add small value to avoid division by zero
        monotony = monotony.reset_index()[['athlete_id', 'week_id', 'monotony']]
        
        # Merge monotony back to weekly metrics
        weekly = weekly.merge(monotony, on=['athlete_id', 'week_id'], how='left')
        
        # Calculate ACWR (Acute:Chronic Workload Ratio)
        weekly = weekly.sort_values(['athlete_id', 'year', 'week'])
        weekly['chronic_load'] = weekly.groupby('athlete_id')['internal_load'].transform(
            lambda x: x.rolling(window=4, min_periods=1).mean()
        )
        weekly['acwr'] = weekly['internal_load'] / (weekly['chronic_load'] + 1e-6)
        
        # Clean up
        weekly = weekly.drop(columns=['year', 'week'])
        
        return weekly


class FatigueRiskModel:
    """Machine learning model for predicting fatigue risk in athletes."""
    
    def __init__(self, model_type: str = 'logistic'):
        """
        Initialize the fatigue risk prediction model.
        
        Args:
            model_type: Type of model to use ('logistic' or 'random_forest')
        """
        self.model_type = model_type
        self.model = self._initialize_model()
        self.scaler = StandardScaler()
        self.feature_columns = [
            'internal_load', 'training_density', 'monotony', 'acwr',
            'load_sum', 'volume_sum', 'rpe_mean'
        ]
    
    def _initialize_model(self):
        """Initialize the ML model based on model_type."""
        if self.model_type == 'logistic':
            return LogisticRegression(class_weight='balanced', max_iter=1000)
        elif self.model_type == 'random_forest':
            return RandomForestClassifier(n_estimators=100, class_weight='balanced')
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def preprocess_features(self, X: pd.DataFrame) -> np.ndarray:
        """
        Preprocess features for model training/prediction.
        
        Args:
            X: DataFrame containing the features
            
        Returns:
            Processed feature array
        """
        # Select and scale features
        X_processed = X[self.feature_columns].copy()
        
        # Handle missing values
        X_processed = X_processed.fillna(0)
        
        # Scale features
        if hasattr(self, 'fitted_scaler_'):
            X_scaled = self.fitted_scaler_.transform(X_processed)
        else:
            X_scaled = self.scaler.fit_transform(X_processed)
            self.fitted_scaler_ = self.scaler
            
        return X_scaled
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """
        Train the fatigue risk prediction model.
        
        Args:
            X: Training features (DataFrame with weekly metrics)
            y: Target variable (1 for high fatigue risk, 0 otherwise)
            
        Returns:
            Dictionary with training metrics
        """
        # Preprocess features
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.preprocess_features(X_train)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate on validation set
        X_val_scaled = self.preprocess_features(X_val)
        y_pred = self.model.predict(X_val_scaled)
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_val, y_pred),
            'report': classification_report(y_val, y_pred, output_dict=True)
        }
        
        return metrics
    
    def predict_risk(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Predict fatigue risk for new data.
        
        Args:
            X: DataFrame with weekly metrics for prediction
            
        Returns:
            DataFrame with risk scores and predictions
        """
        if not hasattr(self, 'fitted_scaler_'):
            raise RuntimeError("Model must be trained before making predictions")
            
        # Preprocess features
        X_scaled = self.preprocess_features(X)
        
        # Make predictions
        risk_prob = self.model.predict_proba(X_scaled)[:, 1]  # Probability of class 1 (high risk)
        predictions = self.model.predict(X_scaled)
        
        # Create result DataFrame
        results = X[['athlete_id', 'week_id']].copy()
        results['fatigue_risk_score'] = risk_prob
        results['fatigue_risk'] = predictions
        results['risk_category'] = pd.cut(
            risk_prob,
            bins=[0, 0.3, 0.7, 1.0],
            labels=['low', 'medium', 'high'],
            include_lowest=True
        )
        
        return results
    
    def save_model(self, filepath: str) -> None:
        """
        Save the trained model to disk.
        
        Args:
            filepath: Path to save the model file
        """
        model_data = {
            'model': self.model,
            'scaler': self.fitted_scaler_,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type
        }
        joblib.dump(model_data, filepath)
    
    @classmethod
    def load_model(cls, filepath: str) -> 'FatigueRiskModel':
        """
        Load a trained model from disk.
        
        Args:
            filepath: Path to the saved model file
            
        Returns:
            Loaded FatigueRiskModel instance
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
            
        model_data = joblib.load(filepath)
        
        model = cls(model_type=model_data['model_type'])
        model.model = model_data['model']
        model.fitted_scaler_ = model_data['scaler']
        model.feature_columns = model_data['feature_columns']
        
        return model


def generate_athlete_baselines(weekly_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Generate personalized baselines for each athlete.
    
    Args:
        weekly_metrics: DataFrame with weekly metrics from AdvancedMetrics
        
    Returns:
        DataFrame with athlete-specific baselines and z-scores
    """
    # Calculate rolling baselines (4-week moving average)
    baseline_cols = ['internal_load', 'training_density', 'monotony', 'acwr']
    
    # Sort by athlete and week for proper rolling
    weekly_sorted = weekly_metrics.sort_values(['athlete_id', 'week_id'])
    
    # Calculate rolling means and stds for each athlete
    for col in baseline_cols:
        weekly_sorted[f'{col}_baseline'] = weekly_sorted.groupby('athlete_id')[col].transform(
            lambda x: x.rolling(window=4, min_periods=1).mean()
        )
        weekly_sorted[f'{col}_std'] = weekly_sorted.groupby('athlete_id')[col].transform(
            lambda x: x.rolling(window=4, min_periods=2).std()
        )
        
        # Calculate z-scores
        weekly_sorted[f'{col}_zscore'] = (
            weekly_sorted[col] - weekly_sorted[f'{col}_baseline']
        ) / (weekly_sorted[f'{col}_std'] + 1e-6)  # Add small value to avoid division by zero
    
    return weekly_sorted
