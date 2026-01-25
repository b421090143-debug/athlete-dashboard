import pandas as pd
from typing import Dict, List, Any
from datetime import datetime, timedelta

def add_week_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add a week number column to the dataframe based on the date."""
    df = df.copy()
    # Ensure date is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Calculate week number starting from the minimum date
    min_date = df['date'].min()
    df['week'] = ((df['date'] - min_date).dt.days // 7) + 1
    return df

def compute_weekly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute weekly metrics for each athlete and exercise."""
    if 'week' not in df.columns:
        df = add_week_column(df)
    
    # Check if data is already processed (has aggregated columns)
    processed_columns = ['total_load', 'total_volume', 'avg_rpe', 'avg_weight', 'total_sets']
    if all(col in df.columns for col in processed_columns):
        # Data is already processed, just return it
        return df
    
    # Calculate volume and load for raw data
    if all(col in df.columns for col in ['weight_kg', 'sets', 'reps', 'rpe']):
        df['volume'] = df['weight_kg'] * df['sets'] * df['reps']
        df['load'] = df['volume'] * df['rpe']
        
        # Group by athlete, exercise, and week to calculate weekly metrics
        weekly_metrics = df.groupby(['athlete_id', 'exercise', 'week']).agg({
            'load': 'sum',
            'volume': 'sum',
            'rpe': 'mean',
            'weight_kg': 'mean',
            'sets': 'sum',
            'date': 'first'  # Keep the first date of the week for reference
        }).reset_index()
    else:
        # Missing required columns for raw processing
        raise ValueError("Data must contain either raw format (weight_kg, sets, reps, rpe) or processed format (total_load, total_volume, avg_rpe, avg_weight, total_sets)")
    
    # Rename columns for clarity
    weekly_metrics = weekly_metrics.rename(columns={
        'load': 'total_load',
        'volume': 'total_volume',
        'rpe': 'avg_rpe',
        'weight_kg': 'avg_weight',
        'sets': 'total_sets'
    })
    
    return weekly_metrics

def analyze_exercise_trends(weekly_metrics: pd.DataFrame) -> Dict[str, Any]:
    """Analyze trends for each athlete and exercise."""
    # Calculate week-to-week changes
    weekly_metrics = weekly_metrics.sort_values(['athlete_id', 'exercise', 'week'])
    
    # Calculate percentage changes
    for metric in ['total_load', 'total_volume', 'avg_rpe']:
        weekly_metrics[f'{metric}_pct_change'] = weekly_metrics.groupby(
            ['athlete_id', 'exercise']
        )[metric].pct_change() * 100
    
    # Initialize trend analysis dictionary
    trend_analysis = {}
    
    # Analyze trends for each athlete and exercise
    for (athlete_id, exercise), group in weekly_metrics.groupby(['athlete_id', 'exercise']):
        if len(group) < 2:  # Need at least 2 data points for trend analysis
            continue
            
        # Calculate average weekly changes
        avg_load_change = group['total_load_pct_change'].mean()
        avg_volume_change = group['total_volume_pct_change'].mean()
        avg_rpe_change = group['avg_rpe_pct_change'].mean()
        
        # Determine trend direction
        def get_trend(change: float, threshold: float = 5.0) -> str:
            if change > threshold:
                return 'progression'
            elif change < -threshold:
                return 'regression'
            else:
                return 'plateau'
        
        trend_analysis[f"{exercise}_athlete_{athlete_id}"] = {
            'athlete_id': athlete_id,
            'exercise': exercise,
            'load_trend': get_trend(avg_load_change),
            'volume_trend': get_trend(avg_volume_change),
            'rpe_trend': get_trend(avg_rpe_change, threshold=2.5),  # Smaller threshold for RPE
            'avg_load_change': avg_load_change,
            'avg_volume_change': avg_volume_change,
            'avg_rpe_change': avg_rpe_change,
            'num_weeks': len(group)
        }
    
    return trend_analysis

def generate_llm_facts(trend_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate structured facts for LLM processing."""
    llm_facts = []
    
    for key, analysis in trend_analysis.items():
        # Initialize flags
        flags = {
            'fatigue_risk': False,
            'strong_progress': False,
            'accumulation_phase': False
        }
        
        # Set flags based on trends
        if analysis['load_trend'] == 'progression' and analysis['volume_trend'] == 'progression':
            flags['strong_progress'] = True
            
        if analysis['rpe_trend'] == 'progression' and analysis['load_trend'] in ['plateau', 'regression']:
            flags['fatigue_risk'] = True
            
        if analysis['load_trend'] == 'progression' and analysis['volume_trend'] == 'plateau':
            flags['accumulation_phase'] = True
        
        # Determine final status
        if flags['strong_progress'] and not flags['fatigue_risk']:
            final_status = "excellent_progress"
        elif flags['fatigue_risk']:
            final_status = "needs_attention"
        elif flags['strong_progress'] and flags['fatigue_risk']:
            final_status = "monitor_fatigue"
        else:
            final_status = "neutral"
        
        # Create LLM fact
        llm_fact = {
            'athlete_id': analysis['athlete_id'],
            'exercise': analysis['exercise'],
            'load_trend': analysis['load_trend'],
            'volume_trend': analysis['volume_trend'],
            'rpe_trend': analysis['rpe_trend'],
            'flags': flags,
            'final_status': final_status,
            'metrics': {
                'avg_load_change': analysis['avg_load_change'],
                'avg_volume_change': analysis['avg_volume_change'],
                'avg_rpe_change': analysis['avg_rpe_change'],
                'num_weeks': analysis['num_weeks']
            }
        }
        
        llm_facts.append(llm_fact)
    
    return llm_facts
