# Mock Data for Athlete Dashboard

This directory contains mock training data for 50 athletes across multiple performance levels, designed to test and demonstrate the Athlete Analytics Dashboard capabilities.

## Files Overview

### Individual Athlete Files (10 athletes each)
- `athletes_1_10.csv` - ATH001 to ATH010
- `athletes_11_20.csv` - ATH011 to ATH020  
- `athletes_21_30.csv` - ATH021 to ATH030
- `athletes_31_40.csv` - ATH031 to ATH040
- `athletes_41_50.csv` - ATH041 to ATH050

## Data Structure

Each CSV file contains the following columns:
- `athlete_id`: Unique identifier (ATH001-ATH050)
- `exercise`: Exercise name
- `date`: Training date (YYYY-MM-DD format)
- `weight_kg`: Weight lifted in kilograms
- `sets`: Number of sets performed
- `reps`: Repetitions per set
- `rpe`: Rate of Perceived Exertion (1-10 scale)

## Exercise Types Included

### Core Powerlifting Movements
- **Squat**: 3-5 sets, 3-15 reps, 45-100kg range
- **Deadlift**: 3-4 sets, 3-8 reps, 75-140kg range
- **Bench Press**: 3-5 sets, 6-15 reps, 30-70kg range

### Bodyweight/Accessory Exercises
- **Pull-ups**: 3-4 sets, 5-12 reps, 0-17.5kg weighted
- **Overhead Press**: 3-4 sets, 6-12 reps, 17-52kg range

### Strongman-Specific Events
- **Log Press**: 3 sets, 5-10 reps, 20-60kg range
- **Yoke Walk**: 3-4 sets, 12-26m distance, 110-250kg load
- **Stone Loading**: 3-4 sets, 2-5 reps, 62-120kg range

## Performance Levels

The 50 athletes represent various training levels:

### Beginner Level (ATH010, ATH020, ATH030, ATH040, ATH050)
- Lower weight ranges
- Higher rep ranges (10-15)
- RPE 5-7
- Basic exercise selection

### Intermediate Level (ATH005-ATH009, ATH015-ATH019, etc.)
- Moderate weight ranges
- Mixed rep ranges (6-12)
- RPE 6-8
- Including strongman events

### Advanced Level (ATH001-ATH004, ATH011-ATH014, etc.)
- Higher weight ranges
- Lower rep ranges (3-8)
- RPE 7-9
- Full strongman event training

### Elite Level (ATH003, ATH009, ATH013, ATH019, etc.)
- Maximum weight ranges
- Low rep ranges (3-6)
- RPE 8-10
- Competition-focused training

## Training Progression

Each athlete shows:
- **Progressive overload**: Weight increases over time
- **Realistic progression**: 2-5kg increases every 2-3 sessions
- **Plateau patterns**: Some athletes show stagnation
- **Recovery periods**: Varied RPE indicating different intensities

## Date Range
- **Training Period**: January 1-13, 2024
- **Frequency**: 2-3 sessions per week per athlete
- **Total Sessions**: ~20 sessions per athlete

## Usage Instructions

1. **Download individual files** for specific athlete groups
2. **Combine files** for full 50-athlete analysis
3. **Upload to dashboard** to test:
   - Individual athlete analysis
   - Team-wide insights
   - Progressive overload tracking
   - Recovery analysis
   - Coaching directives

## Data Quality Features

- **Consistent formatting**: All dates in YYYY-MM-DD
- **Realistic weights**: Appropriate for each performance level
- **Logical progression**: No unrealistic jumps in performance
- **Varied RPE**: Reflects different training intensities
- **Exercise variety**: Tests all dashboard features

## Testing Scenarios

This mock data is perfect for testing:
- ✅ Multi-athlete team analysis
- ✅ Performance level comparisons
- ✅ Progressive overload detection
- ✅ Plateau identification
- ✅ Recovery tracking
- ✅ Strongman event analysis
- ✅ Coaching directive generation

## File Size
- Each file: ~1,000-1,200 records
- Combined: ~5,000-6,000 records
- File size: ~200-300KB per file

This comprehensive dataset provides realistic testing scenarios for all dashboard features and analytics capabilities.
