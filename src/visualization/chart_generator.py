"""
Module for generating charts and visualizations using matplotlib and plotly.
"""
import io
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..core.theme_manager import ThemeManager

class ChartGenerator:
    """Generates charts and visualizations using matplotlib and plotly."""
    
    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        """
        Initialize the chart generator.
        
        Args:
            theme_manager: Optional theme manager for styling charts
        """
        self.theme_manager = theme_manager or ThemeManager()
        
        # Set default matplotlib style based on theme
        plt.style.use('seaborn')
        if theme_manager:
            colors = list(theme_manager.theme["colors"].values())
            plt.rcParams['axes.prop_cycle'] = plt.cycler(color=colors)
            
    def _prepare_data(self, data: Union[pd.DataFrame, Dict[str, List[Any]], List[Any]]) -> pd.DataFrame:
        """
        Convert input data to pandas DataFrame.
        
        Args:
            data: Input data in various formats
            
        Returns:
            Pandas DataFrame
        """
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame(data)
        elif isinstance(data, list):
            if all(isinstance(x, dict) for x in data):
                return pd.DataFrame(data)
            else:
                return pd.DataFrame({'values': data})
        else:
            raise ValueError("Unsupported data format")
            
    def _get_theme_colors(self, num_colors: int) -> List[str]:
        """Get a list of colors from the theme."""
        if self.theme_manager:
            colors = list(self.theme_manager.theme["colors"].values())
            # Repeat colors if needed
            return (colors * ((num_colors // len(colors)) + 1))[:num_colors]
        return plt.rcParams['axes.prop_cycle'].by_key()['color'][:num_colors]
        
    def create_bar_chart(self, 
                        data: Union[pd.DataFrame, Dict[str, List[Any]], List[Any]],
                        title: str,
                        x_label: Optional[str] = None,
                        y_label: Optional[str] = None,
                        orientation: str = 'vertical',
                        stacked: bool = False) -> plt.Figure:
        """
        Create a bar chart using matplotlib.
        
        Args:
            data: Input data
            title: Chart title
            x_label: Label for x-axis
            y_label: Label for y-axis
            orientation: 'vertical' or 'horizontal'
            stacked: Whether to stack bars
            
        Returns:
            Matplotlib figure
        """
        df = self._prepare_data(data)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if orientation == 'vertical':
            if stacked:
                df.plot(kind='bar', stacked=True, ax=ax, color=self._get_theme_colors(len(df.columns)))
            else:
                df.plot(kind='bar', ax=ax, color=self._get_theme_colors(len(df.columns)))
        else:
            if stacked:
                df.plot(kind='barh', stacked=True, ax=ax, color=self._get_theme_colors(len(df.columns)))
            else:
                df.plot(kind='barh', ax=ax, color=self._get_theme_colors(len(df.columns)))
                
        ax.set_title(title)
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
            
        plt.tight_layout()
        return fig
        
    def create_line_chart(self,
                         data: Union[pd.DataFrame, Dict[str, List[Any]], List[Any]],
                         title: str,
                         x_label: Optional[str] = None,
                         y_label: Optional[str] = None,
                         markers: bool = True) -> plt.Figure:
        """
        Create a line chart using matplotlib.
        
        Args:
            data: Input data
            title: Chart title
            x_label: Label for x-axis
            y_label: Label for y-axis
            markers: Whether to show data point markers
            
        Returns:
            Matplotlib figure
        """
        df = self._prepare_data(data)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for i, column in enumerate(df.columns):
            if column != df.index.name:
                if markers:
                    ax.plot(df.index, df[column], marker='o', label=column, 
                           color=self._get_theme_colors(1)[0])
                else:
                    ax.plot(df.index, df[column], label=column,
                           color=self._get_theme_colors(1)[0])
                    
        ax.set_title(title)
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
            
        if len(df.columns) > 1:
            ax.legend()
            
        plt.tight_layout()
        return fig
        
    def create_pie_chart(self,
                        data: Union[pd.DataFrame, Dict[str, List[Any]], List[Any]],
                        title: str,
                        autopct: str = '%1.1f%%') -> plt.Figure:
        """
        Create a pie chart using matplotlib.
        
        Args:
            data: Input data
            title: Chart title
            autopct: Format string for percentage labels
            
        Returns:
            Matplotlib figure
        """
        df = self._prepare_data(data)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        values = df.iloc[:, 0] if isinstance(df, pd.DataFrame) else df
        labels = df.index if isinstance(df, pd.DataFrame) else range(len(df))
        
        ax.pie(values, labels=labels, autopct=autopct, colors=self._get_theme_colors(len(values)))
        ax.set_title(title)
        
        plt.tight_layout()
        return fig
        
    def create_scatter_plot(self,
                           data: Union[pd.DataFrame, Dict[str, List[Any]], List[Any]],
                           title: str,
                           x_column: str,
                           y_column: str,
                           color_column: Optional[str] = None,
                           x_label: Optional[str] = None,
                           y_label: Optional[str] = None) -> plt.Figure:
        """
        Create a scatter plot using plotly for interactivity.
        
        Args:
            data: Input data
            title: Chart title
            x_column: Column name for x-axis
            y_column: Column name for y-axis
            color_column: Optional column name for point colors
            x_label: Label for x-axis
            y_label: Label for y-axis
            
        Returns:
            Plotly figure
        """
        df = self._prepare_data(data)
        
        fig = go.Figure()
        
        if color_column and color_column in df.columns:
            for color in df[color_column].unique():
                mask = df[color_column] == color
                fig.add_trace(go.Scatter(
                    x=df[mask][x_column],
                    y=df[mask][y_column],
                    mode='markers',
                    name=str(color),
                    marker=dict(size=10)
                ))
        else:
            fig.add_trace(go.Scatter(
                x=df[x_column],
                y=df[y_column],
                mode='markers',
                marker=dict(
                    size=10,
                    color=self._get_theme_colors(1)[0]
                )
            ))
            
        fig.update_layout(
            title=title,
            xaxis_title=x_label or x_column,
            yaxis_title=y_label or y_column,
            showlegend=bool(color_column)
        )
        
        return fig
        
    def create_combo_chart(self,
                          data: Union[pd.DataFrame, Dict[str, List[Any]], List[Any]],
                          title: str,
                          bar_columns: List[str],
                          line_columns: List[str],
                          x_label: Optional[str] = None,
                          y1_label: Optional[str] = None,
                          y2_label: Optional[str] = None) -> plt.Figure:
        """
        Create a combination chart with bars and lines using plotly.
        
        Args:
            data: Input data
            title: Chart title
            bar_columns: Columns to show as bars
            line_columns: Columns to show as lines
            x_label: Label for x-axis
            y1_label: Label for primary y-axis
            y2_label: Label for secondary y-axis
            
        Returns:
            Plotly figure
        """
        df = self._prepare_data(data)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        colors = self._get_theme_colors(len(bar_columns) + len(line_columns))
        color_idx = 0
        
        # Add bars
        for column in bar_columns:
            fig.add_trace(
                go.Bar(
                    name=column,
                    x=df.index,
                    y=df[column],
                    marker_color=colors[color_idx]
                ),
                secondary_y=False
            )
            color_idx += 1
            
        # Add lines
        for column in line_columns:
            fig.add_trace(
                go.Scatter(
                    name=column,
                    x=df.index,
                    y=df[column],
                    mode='lines+markers',
                    line=dict(color=colors[color_idx])
                ),
                secondary_y=True
            )
            color_idx += 1
            
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            barmode='group'
        )
        
        fig.update_yaxes(title_text=y1_label, secondary_y=False)
        fig.update_yaxes(title_text=y2_label, secondary_y=True)
        
        return fig
        
    def save_figure_to_bytes(self, fig: Union[plt.Figure, go.Figure], format: str = 'png') -> bytes:
        """
        Save a figure to bytes for embedding in PowerPoint.
        
        Args:
            fig: Matplotlib or Plotly figure
            format: Output format ('png' or 'svg')
            
        Returns:
            Bytes containing the image data
        """
        if isinstance(fig, plt.Figure):
            buf = io.BytesIO()
            fig.savefig(buf, format=format, bbox_inches='tight', dpi=300)
            plt.close(fig)  # Close to free memory
            buf.seek(0)
            return buf.getvalue()
        else:  # Plotly figure
            if format == 'svg':
                return fig.to_image(format='svg')
            return fig.to_image(format='png') 