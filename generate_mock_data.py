import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_athlete_data(athlete_id, start_date, num_weeks=8):
    """Generate mock training data for a single athlete."""
    exercises = ['Bench Press', 'Squat', 'Deadlift', 'Overhead Press', 'Pull-up']
    data = []
    
    # Base performance levels (scaled by athlete ID for variety)
    base_weight = {
        'Bench Press': 40 + athlete_id * 5,
        'Squat': 60 + athlete_id * 8,
        'Deadlift': 80 + athlete_id * 10,
        'Overhead Press': 30 + athlete_id * 3,
        'Pull-up': athlete_id * 2  # bodyweight + added weight
    }
    
    # Generate data for each day
    current_date = start_date
    for week in range(1, num_weeks + 1):
        # Training 3-4 days per week
        training_days = sorted(random.sample(range(7), random.randint(3, 4)))
        
        for day in range(7):
            if day in training_days:
                # Select 2-3 exercises per session
                session_exercises = random.sample(exercises, random.randint(2, 3))
                
                for exercise in session_exercises:
                    # Progressive overload with some randomness
                    week_factor = 1 + (week - 1) * 0.03
                    weight = base_weight[exercise] * week_factor * random.uniform(0.95, 1.05)
                    
                    # Simulate good and bad days
                    if random.random() < 0.1:  # 10% chance of an off day
                        weight *= 0.9
                        rpe = random.randint(8, 10)
                    else:
                        rpe = random.randint(6, 9)
                    
                    # Generate sets and reps
                    sets = random.choice([3, 4, 5])
                    reps = random.choice([5, 6, 8, 10])
                    
                    data.append({
                        'date': current_date,
                        'athlete_id': athlete_id,
                        'exercise': exercise,
                        'weight_kg': round(weight / 2.5) * 2.5,  # Round to nearest 2.5kg
                        'sets': sets,
                        'reps': reps,
                        'rpe': rpe
                    })
            
            current_date += timedelta(days=1)
    
    return pd.DataFrame(data)

def generate_all_athletes(num_athletes=7, start_date='2024-01-01'):
    """Generate data for multiple athletes."""
    all_data = []
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    
    for athlete_id in range(1, num_athletes + 1):
        # Add some variation to start dates
        athlete_start = start_date + timedelta(days=random.randint(0, 7))
        df = generate_athlete_data(athlete_id, athlete_start)
        all_data.append(df)
    
    # Combine all data
    final_df = pd.concat(all_data).sort_values('date').reset_index(drop=True)
    
    # Save to file
    os.makedirs('data', exist_ok=True)
    final_df.to_csv('data/mock_data_7athletes.csv', index=False)
    print(f"Generated data for {num_athletes} athletes with {len(final_df)} total training sessions.")
    return final_df

if __name__ == "__main__":
    import os
    df = generate_all_athletes()
    print("\nSample data:")
    print(df.head())
