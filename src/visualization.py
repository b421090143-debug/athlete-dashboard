"""
Advanced visualization utilities for AthleteInsight.

This module provides professional, publication-quality visualizations
for athlete training data, metrics, and predictions.
"""

from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from matplotlib import rcParams
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

# Set global style parameters
plt.style.use('seaborn-v0_8')
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
rcParams['figure.figsize'] = (12, 6)
rcParams['figure.facecolor'] = 'white'
rcParams['axes.grid'] = True
rcParams['grid.alpha'] = 0.3
rcParams['axes.facecolor'] = 'white'
rcParams['savefig.dpi'] = 300
rcParams['savefig.bbox'] = 'tight'

# Custom color palette
COLOR_PALETTE = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'success': '#3B8EA5',
    'warning': '#F4AC45',
    'danger': '#C73E1D',
    'light_gray': '#F5F5F5',
    'dark_gray': '#333333',
    'white': '#FFFFFF'
}

# Create colormaps
risk_cmap = LinearSegmentedColormap.from_list(
    'risk_cmap', [COLOR_PALETTE['success'], COLOR_PALETTE['warning'], COLOR_PALETTE['danger']]
)

class TrainingVisualizer:
    """Creates professional visualizations for athlete training data."""
    
    def __init__(self, weekly_metrics: pd.DataFrame, athlete_id: Optional[str] = None):
        """
        Initialize with weekly metrics data.
        
        Args:
            weekly_metrics: DataFrame containing weekly training metrics
            athlete_id: Optional athlete ID to filter data for a specific athlete
        """
        self.data = weekly_metrics.copy()
        self.athlete_id = athlete_id
        
        if athlete_id:
            self.data = self.data[self.data['athlete_id'] == athlete_id]
        
        # Ensure date is in datetime format
        if 'date' in self.data.columns and not pd.api.types.is_datetime64_any_dtype(self.data['date']):
            self.data['date'] = pd.to_datetime(self.data['date'])
    
    def plot_load_vs_rpe(self, figsize: Tuple[int, int] = (12, 6), 
                        interactive: bool = False) -> Union[plt.Figure, go.Figure]:
        """
        Plot training load vs. RPE with trend line.
        
        Args:
            figsize: Figure size (width, height) in inches
            interactive: If True, returns a Plotly figure
            
        Returns:
            Matplotlib or Plotly figure object
        """
        if interactive:
            return self._plotly_load_vs_rpe()
        
        # Matplotlib version
        plt.figure(figsize=figsize)
        
        # Create scatter plot
        scatter = plt.scatter(
            x=self.data['internal_load'],
            y=self.data['rpe_mean'],
            c=self.data['week_id'].astype('category').cat.codes,
            cmap='viridis',
            alpha=0.7,
            s=100,
            edgecolor='w',
            linewidth=0.5
        )
        
        # Add trend line
        z = np.polyfit(self.data['internal_load'], self.data['rpe_mean'], 1)
        p = np.poly1d(z)
        plt.plot(
            self.data['internal_load'], 
            p(self.data['internal_load']), 
            color=COLOR_PALETTE['danger'],
            linestyle='--',
            linewidth=2
        )
        
        # Add annotations
        plt.title('Training Load vs. Perceived Exertion', fontsize=16, pad=20)
        plt.xlabel('Internal Load (AU)', fontsize=12)
        plt.ylabel('Average RPE', fontsize=12)
        
        # Add colorbar for week
        cbar = plt.colorbar(scatter)
        cbar.set_label('Week', rotation=270, labelpad=15)
        
        # Style
        plt.grid(True, alpha=0.3)
        sns.despine()
        plt.tight_layout()
        
        return plt.gcf()
    
    def _plotly_load_vs_rpe(self) -> go.Figure:
        """Interactive version of load vs RPE plot using Plotly."""
        fig = px.scatter(
            self.data,
            x='internal_load',
            y='rpe_mean',
            color='week_id',
            hover_data=['exercise', 'date_min'],
            title='Training Load vs. Perceived Exertion',
            labels={
                'internal_load': 'Internal Load (AU)',
                'rpe_mean': 'Average RPE',
                'week_id': 'Week',
                'exercise': 'Exercise',
                'date_min': 'Week Start'
            },
            color_continuous_scale='Viridis'
        )
        
        # Add trend line
        z = np.polyfit(self.data['internal_load'], self.data['rpe_mean'], 1)
        fig.add_trace(
            go.Scatter(
                x=self.data['internal_load'],
                y=np.poly1d(z)(self.data['internal_load']),
                mode='lines',
                line=dict(color=COLOR_PALETTE['danger'], dash='dash'),
                name='Trend',
                showlegend=True
            )
        )
        
        # Update layout
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            hovermode='closest'
        )
        
        return fig
    
    def plot_workload_balance(self, figsize: Tuple[int, int] = (12, 6),
                            interactive: bool = False) -> Union[plt.Figure, go.Figure]:
        """
        Plot workload balance (ACWR) over time.
        
        Args:
            figsize: Figure size (width, height) in inches
            interactive: If True, returns a Plotly figure
            
        Returns:
            Matplotlib or Plotly figure object
        """
        if interactive:
            return self._plotly_workload_balance()
        
        # Matplotlib version
        plt.figure(figsize=figsize)
        
        # Plot ACWR line
        plt.plot(
            self.data['date_min'],
            self.data['acwr'],
            color=COLOR_PALETTE['primary'],
            marker='o',
            markersize=8,
            linewidth=2,
            label='ACWR'
        )
        
        # Add optimal zone (0.8-1.5)
        plt.axhspan(0.8, 1.5, alpha=0.1, color=COLOR_PALETTE['success'])
        plt.axhline(0.8, color=COLOR_PALETTE['success'], linestyle='--', alpha=0.5)
        plt.axhline(1.5, color=COLOR_PALETTE['warning'], linestyle='--', alpha=0.5)
        
        # Add annotations
        plt.title('Acute:Chronic Workload Ratio (ACWR)', fontsize=16, pad=20)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('ACWR', fontsize=12)
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.xticks(rotation=45)
        
        # Add legend and style
        plt.legend(loc='upper left')
        plt.grid(True, alpha=0.3)
        sns.despine()
        plt.tight_layout()
        
        return plt.gcf()
    
    def _plotly_workload_balance(self) -> go.Figure:
        """Interactive version of workload balance plot using Plotly."""
        fig = go.Figure()
        
        # Add ACWR line
        fig.add_trace(
            go.Scatter(
                x=self.data['date_min'],
                y=self.data['acwr'],
                mode='lines+markers',
                name='ACWR',
                line=dict(color=COLOR_PALETTE['primary'], width=2),
                marker=dict(size=8)
            )
        )
        
        # Add optimal zone
        fig.add_hrect(
            y0=0.8, y1=1.5,
            fillcolor=COLOR_PALETTE['success'],
            opacity=0.1,
            line_width=0,
            annotation_text="Optimal Zone",
            annotation_position="top left"
        )
        
        # Add threshold lines
        fig.add_hline(
            y=0.8, 
            line_dash="dash",
            line_color=COLOR_PALETTE['success'],
            opacity=0.7,
            annotation_text="0.8",
            annotation_position="bottom right"
        )
        
        fig.add_hline(
            y=1.5, 
            line_dash="dash",
            line_color=COLOR_PALETTE['warning'],
            opacity=0.7,
            annotation_text="1.5",
            annotation_position="top right"
        )
        
        # Update layout
        fig.update_layout(
            title='Acute:Chronic Workload Ratio (ACWR)',
            xaxis_title='Date',
            yaxis_title='ACWR',
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                tickformat='%b %d'
            ),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            hovermode='x unified'
        )
        
        return fig
    
    def plot_fatigue_risk_timeline(self, risk_scores: pd.DataFrame,
                                 figsize: Tuple[int, int] = (14, 6),
                                 interactive: bool = False) -> Union[plt.Figure, go.Figure]:
        """
        Plot fatigue risk scores over time.
        
        Args:
            risk_scores: DataFrame with columns ['date', 'fatigue_risk_score', 'risk_category']
            figsize: Figure size (width, height) in inches
            interactive: If True, returns a Plotly figure
            
        Returns:
            Matplotlib or Plotly figure object
        """
        if interactive:
            return self._plotly_fatigue_risk_timeline(risk_scores)
        
        # Matplotlib version
        plt.figure(figsize=figsize)
        
        # Create color mapping for risk categories
        risk_colors = {
            'low': COLOR_PALETTE['success'],
            'medium': COLOR_PALETTE['warning'],
            'high': COLOR_PALETTE['danger']
        }
        
        # Plot risk scores with color-coded points
        for category, color in risk_colors.items():
            mask = risk_scores['risk_category'] == category
            if mask.any():
                plt.scatter(
                    risk_scores.loc[mask, 'date'],
                    risk_scores.loc[mask, 'fatigue_risk_score'],
                    color=color,
                    s=100,
                    label=category.capitalize(),
                    edgecolor='white',
                    linewidth=0.5
                )
        
        # Connect points with line
        plt.plot(
            risk_scores['date'],
            risk_scores['fatigue_risk_score'],
            color=COLOR_PALETTE['primary'],
            alpha=0.3,
            linewidth=1
        )
        
        # Add threshold lines
        plt.axhline(0.3, color=COLOR_PALETTE['success'], linestyle='--', alpha=0.5)
        plt.axhline(0.7, color=COLOR_PALETTE['danger'], linestyle='--', alpha=0.5)
        
        # Add annotations
        plt.title('Fatigue Risk Timeline', fontsize=16, pad=20)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Fatigue Risk Score', fontsize=12)
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.xticks(rotation=45)
        
        # Add legend and style
        plt.legend(title='Risk Level')
        plt.grid(True, alpha=0.3)
        sns.despine()
        plt.tight_layout()
        
        return plt.gcf()
    
    def _plotly_fatigue_risk_timeline(self, risk_scores: pd.DataFrame) -> go.Figure:
        """Interactive version of fatigue risk timeline using Plotly."""
        # Create color mapping for risk categories
        risk_colors = {
            'low': COLOR_PALETTE['success'],
            'medium': COLOR_PALETTE['warning'],
            'high': COLOR_PALETTE['danger']
        }
        
        fig = go.Figure()
        
        # Add scatter points for each risk category
        for category, color in risk_colors.items():
            mask = risk_scores['risk_category'] == category
            if mask.any():
                fig.add_trace(
                    go.Scatter(
                        x=risk_scores.loc[mask, 'date'],
                        y=risk_scores.loc[mask, 'fatigue_risk_score'],
                        mode='markers',
                        name=category.capitalize(),
                        marker=dict(
                            color=color,
                            size=10,
                            line=dict(width=1, color='white')
                        ),
                        hovertemplate=
                            '<b>Date</b>: %{x|%b %d, %Y}<br>' +
                            '<b>Risk Score</b>: %{y:.2f}<br>' +
                            '<b>Risk Level</b>: ' + category.capitalize() +
                            '<extra></extra>'
                    )
                )
        
        # Add line connecting points
        fig.add_trace(
            go.Scatter(
                x=risk_scores['date'],
                y=risk_scores['fatigue_risk_score'],
                mode='lines',
                name='Trend',
                line=dict(color=COLOR_PALETTE['primary'], width=1),
                showlegend=False,
                hoverinfo='skip'
            )
        )
        
        # Add threshold lines
        fig.add_hline(
            y=0.3,
            line_dash="dash",
            line_color=COLOR_PALETTE['success'],
            opacity=0.7,
            annotation_text="Low Risk",
            annotation_position="bottom right"
        )
        
        fig.add_hline(
            y=0.7,
            line_dash="dash",
            line_color=COLOR_PALETTE['danger'],
            opacity=0.7,
            annotation_text="High Risk",
            annotation_position="top right"
        )
        
        # Add risk zones
        fig.add_hrect(
            y0=0, y1=0.3,
            fillcolor=COLOR_PALETTE['success'],
            opacity=0.1,
            line_width=0,
            annotation_text="Low Risk Zone",
            annotation_position="top left"
        )
        
        fig.add_hrect(
            y0=0.3, y1=0.7,
            fillcolor=COLOR_PALETTE['warning'],
            opacity=0.1,
            line_width=0,
            annotation_text="Moderate Risk Zone",
            annotation_position="top left"
        )
        
        fig.add_hrect(
            y0=0.7, y1=1.0,
            fillcolor=COLOR_PALETTE['danger'],
            opacity=0.1,
            line_width=0,
            annotation_text="High Risk Zone",
            annotation_position="top left"
        )
        
        # Update layout
        fig.update_layout(
            title='Fatigue Risk Timeline',
            xaxis_title='Date',
            yaxis_title='Fatigue Risk Score',
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                tickformat='%b %d'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                range=[0, 1]
            ),
            hovermode='x unified',
            legend_title_text='Risk Level'
        )
        
        return fig
    
    def create_athlete_dashboard(self, athlete_data: pd.DataFrame, 
                               risk_scores: pd.DataFrame) -> go.Figure:
        """
        Create a comprehensive dashboard for an athlete.
        
        Args:
            athlete_data: DataFrame with athlete's training data
            risk_scores: DataFrame with fatigue risk scores
            
        Returns:
            Plotly Figure with multiple subplots
        """
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Training Load vs. RPE',
                'Workload Balance (ACWR)',
                'Volume Progression',
                'Fatigue Risk Timeline',
                'Exercise Distribution',
                'Training Monotony'
            ),
            specs=[
                [{"type": "scatter"}, {"type": "xy"}],
                [{"type": "xy"}, {"type": "xy"}],
                [{"type": "pie"}, {"type": "xy"}]
            ],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 1. Training Load vs. RPE (top-left)
        load_rpe_fig = self._plotly_load_vs_rpe()
        for trace in load_rpe_fig.data:
            fig.add_trace(trace, row=1, col=1)
        
        # 2. Workload Balance (top-right)
        acwr_fig = self._plotly_workload_balance()
        for trace in acwr_fig.data:
            fig.add_trace(trace, row=1, col=2)
        
        # 3. Volume Progression (middle-left)
        volume_fig = self._plot_volume_progression(athlete_data)
        for trace in volume_fig.data:
            fig.add_trace(trace, row=2, col=1)
        
        # 4. Fatigue Risk Timeline (middle-right)
        risk_fig = self._plotly_fatigue_risk_timeline(risk_scores)
        for trace in risk_fig.data:
            fig.add_trace(trace, row=2, col=2)
        
        # 5. Exercise Distribution (bottom-left)
        ex_dist_fig = self._plot_exercise_distribution(athlete_data)
        for trace in ex_dist_fig.data:
            fig.add_trace(trace, row=3, col=1)
        
        # 6. Training Monotony (bottom-right)
        monotony_fig = self._plot_training_monotony(athlete_data)
        for trace in monotony_fig.data:
            fig.add_trace(trace, row=3, col=2)
        
        # Update layout
        fig.update_layout(
            height=1200,
            width=1200,
            title_text=f"Athlete Dashboard: {self.athlete_id}",
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100, b=50, l=50, r=50)
        )
        
        return fig
    
    def _plot_volume_progression(self, data: pd.DataFrame) -> go.Figure:
        """Plot training volume progression over time."""
        fig = px.line(
            data,
            x='date_min',
            y='total_volume',
            title='Training Volume Progression',
            labels={
                'date_min': 'Date',
                'total_volume': 'Total Volume (kg)'
            },
            color_discrete_sequence=[COLOR_PALETTE['primary']]
        )
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            showlegend=False
        )
        
        return fig
    
    def _plot_exercise_distribution(self, data: pd.DataFrame) -> go.Figure:
        """Plot exercise distribution as a pie chart."""
        # Calculate exercise distribution by volume
        ex_dist = data.groupby('exercise')['total_volume'].sum().reset_index()
        
        fig = px.pie(
            ex_dist,
            values='total_volume',
            names='exercise',
            title='Exercise Distribution by Volume',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>%{value:.0f} kg<br>%{percent}'
        )
        
        fig.update_layout(
            showlegend=False,
            margin=dict(t=50, b=20, l=20, r=20)
        )
        
        return fig
    
    def _plot_training_monotony(self, data: pd.DataFrame) -> go.Figure:
        """Plot training monotony over time."""
        fig = px.line(
            data,
            x='date_min',
            y='monotony',
            title='Training Monotony',
            labels={
                'date_min': 'Date',
                'monotony': 'Monotony Score'
            },
            color_discrete_sequence=[COLOR_PALETTE['secondary']]
        )
        
        # Add threshold line
        fig.add_hline(
            y=2.0,
            line_dash="dash",
            line_color=COLOR_PALETTE['warning'],
            opacity=0.7,
            annotation_text="High Monotony",
            annotation_position="top right"
        )
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            showlegend=False
        )
        
        return fig

def save_plot(fig: Union[plt.Figure, go.Figure], filename: str, 
             format: str = 'png', dpi: int = 300) -> None:
    """
    Save a plot to a file.
    
    Args:
        fig: Matplotlib or Plotly figure object
        filename: Output filename (without extension)
        format: Output format ('png', 'jpg', 'pdf', 'svg', 'html')
        dpi: Resolution in dots per inch (for static formats)
    """
    if isinstance(fig, plt.Figure):
        # Matplotlib figure
        fig.savefig(
            f"{filename}.{format}",
            format=format,
            dpi=dpi,
            bbox_inches='tight'
        )
    elif isinstance(fig, go.Figure):
        # Plotly figure
        if format == 'html':
            fig.write_html(f"{filename}.html")
        else:
            fig.write_image(
                f"{filename}.{format}",
                format=format,
                scale=dpi/100  # Convert DPI to scale factor
            )
    else:
        raise ValueError(f"Unsupported figure type: {type(fig)}")


def create_athlete_report(athlete_id: str, metrics: pd.DataFrame, 
                        risk_scores: pd.DataFrame, insights: Dict[str, Any],
                        output_dir: str = 'reports') -> str:
    """
    Create a comprehensive PDF report for an athlete.
    
    Args:
        athlete_id: Athlete ID
        metrics: DataFrame with athlete metrics
        risk_scores: DataFrame with fatigue risk scores
        insights: Dictionary with coaching insights
        output_dir: Output directory for the report
        
    Returns:
        Path to the generated report
    """
    from fpdf import FPDF
    import os
    import tempfile
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add title page
    pdf.add_page()
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 40, 'Athlete Performance Report', 0, 1, 'C')
    pdf.set_font('Arial', '', 16)
    pdf.cell(0, 10, f'Athlete: {athlete_id}', 0, 1, 'C')
    pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'C')
    
    # Add summary section
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Executive Summary', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    # Add summary text
    summary = insights.get('summary', 'No summary available.')
    pdf.multi_cell(0, 8, summary)
    
    # Add risk assessment
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Fatigue Risk Assessment', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    risk = insights.get('risk_assessment', {})
    risk_text = f"Risk Level: {risk.get('category', 'N/A').upper()}\n"
    risk_text += f"Confidence: {risk.get('confidence', 0):.1%}\n\n"
    risk_text += risk.get('explanation', 'No risk assessment available.')
    
    pdf.multi_cell(0, 8, risk_text)
    
    # Add visualizations (simplified for example)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create visualizations
        vis = TrainingVisualizer(metrics, athlete_id=athlete_id)
        
        # Save plots to temporary files
        load_rpe_path = os.path.join(tmpdir, 'load_rpe.png')
        load_rpe_fig = vis.plot_load_vs_rpe(interactive=False)
        save_plot(load_rpe_fig, load_rpe_path)
        
        acwr_path = os.path.join(tmpdir, 'acwr.png')
        acwr_fig = vis.plot_workload_balance(interactive=False)
        save_plot(acwr_fig, acwr_path)
        
        # Add visualizations to PDF
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Training Analysis', 0, 1)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Training Load vs. RPE', 0, 1)
        pdf.image(load_rpe_path, x=10, w=190)
        
        pdf.ln(5)
        pdf.cell(0, 10, 'Workload Balance (ACWR)', 0, 1)
        pdf.image(acwr_path, x=10, w=190)
    
    # Add recommendations
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Recommendations', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    recs = insights.get('recommendations', {})
    for category, items in recs.items():
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, category.title(), 0, 1)
        pdf.set_font('Arial', '', 12)
        
        for item in items:
            pdf.cell(10)  # Indent
            pdf.cell(0, 8, f"• {item}", 0, 1)
        pdf.ln(2)
    
    # Save the report
    report_path = os.path.join(output_dir, f"{athlete_id}_report_{datetime.now().strftime('%Y%m%d')}.pdf")
    pdf.output(report_path)
    
    return report_path
