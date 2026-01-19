# 🏋️ Athlete Analytics Dashboard - Quick Start Guide

## 🚀 Getting Started

### 1. **Run the Streamlit Dashboard**
```bash
streamlit run app.py
```
Upload your CSV/Excel file with columns: `athlete_id`, `exercise`, `date`, `weight_kg`, `sets`, `reps`, `rpe`

### 2. **Generate Full Analysis**
```bash
python demo_pipeline.py
```
Processes mock data and generates `athlete_report.txt`

### 3. **View Interactive Visualizations**
Open `visualizations/` folder and click any HTML file:
- `01_dashboard.html` - Overview analytics
- `02_performance_analysis.html` - Performance trends  
- `03_athlete_deep_dive.html` - Individual athlete analysis
- `04_trend_heatmaps.html` - Trend heatmaps

---

## 📊 Key Insights from Current Data

### **Top Performers**
- **Athlete 2**: Excellent progress across all exercises (Bench Press, Deadlift, Squat)
- **Strong Progress**: Load and volume increasing with controlled RPE

### **Athletes Needing Attention**
- **Athlete 1**: Fatigue risk detected on Bench Press and Squat
- **Recommendation**: Consider reducing load/volume for 1-2 sessions, prioritize recovery

### **Training Patterns**
- **Most Popular Exercises**: Deadlift, Squat, Bench Press
- **Average RPE**: 6-8 (moderate to high intensity)
- **Training Frequency**: 3-4 sessions per week per athlete

---

## 🎯 Action Items

### For Coaches
1. **Review Athlete 1's training load** - implement recovery strategies
2. **Maintain Athlete 2's current program** - excellent progression
3. **Monitor RPE trends** across all athletes weekly

### For Athletes
1. **Track your RPE** honestly - it's crucial for fatigue detection
2. **Focus on progressive overload** - small, consistent increases
3. **Prioritize recovery** when fatigue risk is flagged

---

## 📈 Performance Status Summary

| Athlete | Strong Progress | Fatigue Risk | Neutral |
|---------|----------------|--------------|---------|
| Athlete 1 | 0 exercises | 2 exercises | 1 exercise |
| Athlete 2 | 3 exercises | 0 exercises | 0 exercises |

---

## 🔧 Technical Details

### Data Processing Pipeline
```
Raw Data → Week Calculation → Weekly Metrics → Trend Analysis → LLM Facts → Insights
```

### Key Metrics
- **Volume**: Weight × Sets × Reps
- **Load**: Volume × RPE (intensity-adjusted)
- **Trends**: Week-over-week percentage changes
- **Status**: Excellent/Needs Attention/Neutral/Monitor Fatigue

---

## 📱 Share This Analysis

### For Colleagues
- Share `PROJECT_ANALYSIS_REPORT.md` for comprehensive documentation
- Use interactive HTML dashboards for presentations
- Reference `athlete_report.txt` for detailed individual insights

### For Investors
- Highlight the **automated fatigue detection** system
- Showcase **personalized recommendation engine**
- Demonstrate **scalable analytics** for multiple athletes

---

## 🆘 Troubleshooting

### Common Issues
- **Missing columns**: Ensure your data has all required columns
- **Date format**: Use YYYY-MM-DD format for dates
- **RPE values**: Must be between 1-10

### Get Help
- Check `requirements.txt` for dependencies
- Review `demo_pipeline.py` for processing steps
- Examine `src/preprocessing.py` for data validation

---

*Generated on: $(date)*
*Data points: 481 training sessions*
*Analysis period: 8 weeks*
*Athletes analyzed: 7*
