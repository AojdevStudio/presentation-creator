"""
Tests for the chart generator module.
"""
import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from src.visualization.chart_generator import ChartGenerator
from src.core.theme_manager import ThemeManager

@pytest.fixture
def theme_manager():
    """Create a test theme manager."""
    return ThemeManager({
        "colors": {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "tertiary": "#2ca02c"
        },
        "fonts": {
            "title": "Arial",
            "body": "Calibri"
        },
        "spacing": {
            "paragraph": 1.15,
            "line": 1.0
        },
        "alignment": {
            "title": "center",
            "body": "left"
        }
    })

@pytest.fixture
def chart_generator(theme_manager):
    """Create a test chart generator."""
    return ChartGenerator(theme_manager)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return pd.DataFrame({
        'Category': ['A', 'B', 'C', 'D'],
        'Values': [10, 20, 15, 25],
        'Series2': [5, 15, 10, 20]
    }).set_index('Category')

def test_prepare_data_dataframe(chart_generator, sample_data):
    """Test preparing DataFrame input."""
    result = chart_generator._prepare_data(sample_data)
    assert isinstance(result, pd.DataFrame)
    assert result.equals(sample_data)

def test_prepare_data_dict(chart_generator):
    """Test preparing dictionary input."""
    data = {
        'x': [1, 2, 3],
        'y': [4, 5, 6]
    }
    result = chart_generator._prepare_data(data)
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ['x', 'y']

def test_prepare_data_list(chart_generator):
    """Test preparing list input."""
    data = [1, 2, 3, 4]
    result = chart_generator._prepare_data(data)
    assert isinstance(result, pd.DataFrame)
    assert 'values' in result.columns
    assert list(result['values']) == data

def test_get_theme_colors(chart_generator):
    """Test getting theme colors."""
    colors = chart_generator._get_theme_colors(2)
    assert len(colors) == 2
    assert colors[0] == "#1f77b4"  # primary color
    assert colors[1] == "#ff7f0e"  # secondary color

def test_create_bar_chart(chart_generator, sample_data):
    """Test creating a bar chart."""
    fig = chart_generator.create_bar_chart(
        sample_data,
        title="Test Bar Chart",
        x_label="Categories",
        y_label="Values"
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

def test_create_horizontal_bar_chart(chart_generator, sample_data):
    """Test creating a horizontal bar chart."""
    fig = chart_generator.create_bar_chart(
        sample_data,
        title="Test Horizontal Bar Chart",
        orientation='horizontal'
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

def test_create_stacked_bar_chart(chart_generator, sample_data):
    """Test creating a stacked bar chart."""
    fig = chart_generator.create_bar_chart(
        sample_data,
        title="Test Stacked Bar Chart",
        stacked=True
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

def test_create_line_chart(chart_generator, sample_data):
    """Test creating a line chart."""
    fig = chart_generator.create_line_chart(
        sample_data,
        title="Test Line Chart",
        x_label="Categories",
        y_label="Values"
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

def test_create_line_chart_no_markers(chart_generator, sample_data):
    """Test creating a line chart without markers."""
    fig = chart_generator.create_line_chart(
        sample_data,
        title="Test Line Chart",
        markers=False
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

def test_create_pie_chart(chart_generator, sample_data):
    """Test creating a pie chart."""
    fig = chart_generator.create_pie_chart(
        sample_data['Values'],
        title="Test Pie Chart"
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

def test_create_scatter_plot(chart_generator):
    """Test creating a scatter plot."""
    data = pd.DataFrame({
        'x': np.random.rand(10),
        'y': np.random.rand(10),
        'group': ['A'] * 5 + ['B'] * 5
    })
    
    fig = chart_generator.create_scatter_plot(
        data,
        title="Test Scatter Plot",
        x_column='x',
        y_column='y',
        color_column='group'
    )
    assert isinstance(fig, go.Figure)

def test_create_combo_chart(chart_generator, sample_data):
    """Test creating a combination chart."""
    fig = chart_generator.create_combo_chart(
        sample_data,
        title="Test Combo Chart",
        bar_columns=['Values'],
        line_columns=['Series2'],
        x_label="Categories",
        y1_label="Bar Values",
        y2_label="Line Values"
    )
    assert isinstance(fig, go.Figure)

def test_save_figure_to_bytes_matplotlib(chart_generator, sample_data):
    """Test saving matplotlib figure to bytes."""
    fig = chart_generator.create_bar_chart(
        sample_data,
        title="Test Chart"
    )
    image_data = chart_generator.save_figure_to_bytes(fig, format='png')
    assert isinstance(image_data, bytes)
    assert len(image_data) > 0
    plt.close(fig)

def test_save_figure_to_bytes_plotly(chart_generator):
    """Test saving plotly figure to bytes."""
    data = pd.DataFrame({
        'x': np.random.rand(10),
        'y': np.random.rand(10)
    })
    fig = chart_generator.create_scatter_plot(
        data,
        title="Test Chart",
        x_column='x',
        y_column='y'
    )
    image_data = chart_generator.save_figure_to_bytes(fig, format='png')
    assert isinstance(image_data, bytes)
    assert len(image_data) > 0 