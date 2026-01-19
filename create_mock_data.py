import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_mock_training_data():
    """Generate comprehensive mock training data for testing the athlete analytics dashboard."""
    
    # Athletes with different skill levels
    athletes = [
        {'id': 'ATH001', 'name': 'John Smith', 'level': 'intermediate'},
        {'id': 'ATH002', 'name': 'Sarah Johnson', 'level': 'advanced'},
        {'id': 'ATH003', 'name': 'Mike Chen', 'level': 'beginner'},
        {'id': 'ATH004', 'name': 'Emily Davis', 'level': 'intermediate'},
        {'id': 'ATH005', 'name': 'Alex Rodriguez', 'level': 'advanced'}
    ]
    
    # Exercises with realistic weight ranges
    exercises = {
        'Squat': {'beginner': (40, 80), 'intermediate': (80, 140), 'advanced': (120, 200)},
        'Bench Press': {'beginner': (30, 60), 'intermediate': (60, 100), 'advanced': (80, 150)},
        'Deadlift': {'beginner': (50, 90), 'intermediate': (90, 160), 'advanced': (140, 250)},
        'Overhead Press': {'beginner': (20, 40), 'intermediate': (40, 70), 'advanced': (50, 90)},
        'Barbell Row': {'beginner': (30, 50), 'intermediate': (50, 80), 'advanced': (70, 120)},
        'Pull-up': {'beginner': (0, 10), 'intermediate': (10, 25), 'advanced': (20, 40)}  # Added weight
    }
    
    data = []
    start_date = datetime(2024, 1, 1)
    
    for athlete in athletes:
        # Generate 12 weeks of training data
        for week in range(12):
            # 3-4 training sessions per week
            sessions_per_week = random.randint(3, 4)
            session_days = random.sample(range(7), sessions_per_week)
            
            for day in session_days:
                current_date = start_date + timedelta(weeks=week, days=day)
                
                # 2-3 exercises per session
                session_exercises = random.sample(list(exercises.keys()), random.randint(2, 3))
                
                for exercise in session_exercises:
                    # Get weight range based on athlete level
                    min_weight, max_weight = exercises[exercise][athlete['level']]
                    
                    # Progressive overload with some randomness
                    week_factor = 1 + (week * 0.03)  # 3% progression per week
                    base_weight = random.uniform(min_weight, max_weight) * week_factor
                    
                    # Add some realistic variation
                    weight_variation = random.uniform(0.9, 1.1)
                    final_weight = base_weight * weight_variation
                    
                    # Round to realistic plate increments
                    if exercise == 'Pull-up':
                        final_weight = max(0, round(final_weight / 2.5) * 2.5)
                    else:
                        final_weight = round(final_weight / 2.5) * 2.5
                    
                    # Generate sets and reps based on exercise type
                    if exercise in ['Squat', 'Bench Press', 'Deadlift']:
                        sets = random.choice([3, 4, 5])
                        reps = random.choice([5, 6, 8])
                    else:  # Assistance exercises
                        sets = random.choice([3, 4])
                        reps = random.choice([8, 10, 12])
                    
                    # RPE based on intensity and athlete level
                    if athlete['level'] == 'beginner':
                        rpe = random.randint(6, 8)
                    elif athlete['level'] == 'intermediate':
                        rpe = random.randint(7, 9)
                    else:  # advanced
                        rpe = random.randint(8, 10)
                    
                    # Occasionally simulate bad days or PR attempts
                    if random.random() < 0.1:  # 10% chance of off day
                        final_weight *= 0.9
                        rpe = max(rpe, 8)
                    elif random.random() < 0.05:  # 5% chance of PR attempt
                        final_weight *= 1.05
                        rpe = min(10, rpe + 1)
                    
                    data.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'athlete_id': athlete['id'],
                        'exercise': exercise,
                        'weight_kg': final_weight,
                        'sets': sets,
                        'reps': reps,
                        'rpe': rpe
                    })
    
    # Create DataFrame and sort
    df = pd.DataFrame(data)
    df = df.sort_values(['date', 'athlete_id']).reset_index(drop=True)
    
    return df

# Generate the data
print("🏋️ Generating mock training data...")
mock_data = generate_mock_training_data()

# Save to CSV
mock_data.to_csv('mock_training_data.csv', index=False)

# Display statistics
print(f"\n📊 Dataset Statistics:")
print(f"Total training sessions: {len(mock_data)}")
print(f"Number of athletes: {mock_data['athlete_id'].nunique()}")
print(f"Number of exercises: {mock_data['exercise'].nunique()}")
print(f"Date range: {mock_data['date'].min()} to {mock_data['date'].max()}")
print(f"Training weeks: {(pd.to_datetime(mock_data['date']).max() - pd.to_datetime(mock_data['date']).min()).days // 7 + 1}")

print(f"\n🎯 Athlete Breakdown:")
for athlete_id in mock_data['athlete_id'].unique():
    athlete_data = mock_data[mock_data['athlete_id'] == athlete_id]
    print(f"{athlete_id}: {len(athlete_data)} sessions, {athlete_data['date'].nunique()} training days")

print(f"\n💪 Exercise Distribution:")
exercise_counts = mock_data['exercise'].value_counts()
for exercise, count in exercise_counts.items():
    avg_weight = mock_data[mock_data['exercise'] == exercise]['weight_kg'].mean()
    print(f"{exercise}: {count} sessions, avg weight: {avg_weight:.1f}kg")

print(f"\n✅ Mock data saved as 'mock_training_data.csv'")
print(f"📁 You can now upload this file to test the athlete analytics dashboard!")
