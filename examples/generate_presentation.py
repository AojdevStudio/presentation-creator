#!/usr/bin/env python3
"""
Example script demonstrating how to use the presentation generation pipeline.

This script provides examples of:
1. Simple command-line usage
2. Programmatic API usage with detailed configuration
3. Using a configuration file
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import PresentationGenerator
from src.core.pipeline_factory import PipelineFactory

async def example_1_simple_cli():
    """Example 1: Run the pipeline using command-line arguments."""
    print("\n=== Example 1: Simple Command-Line Usage ===")
    print("Running: python -m src.main 'Artificial Intelligence Trends' --style academic --num-slides 8")
    
    # Note: In a real CLI environment, you would run this command directly in the terminal
    # For this example, we'll just show what arguments would be passed
    print("This would generate an 8-slide academic presentation on AI trends")

async def example_2_programmatic_api():
    """Example 2: Use the programmatic API with detailed configuration."""
    print("\n=== Example 2: Programmatic API Usage ===")
    
    # Create input data
    input_data = {
        "topic": "Climate Change Solutions",
        "style": "professional",
        "num_slides": 12,
        "author": "Environmental Research Team",
        "company": "Green Future Initiative",
        "keywords": ["climate", "sustainability", "solutions", "technology"],
        "subtopics": [
            "Current Climate Challenges",
            "Renewable Energy Technologies",
            "Policy Approaches",
            "Individual Actions"
        ]
    }
    
    # Create configuration
    config = {
        "theme": "nature",
        "output_format": "pptx",
        "max_retries": 2,
        "checkpoints_enabled": True,
        "fallback_templates_enabled": True,
        "base_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    }
    
    # Create generator and generate presentation
    generator = PresentationGenerator()
    
    try:
        print(f"Generating presentation on '{input_data['topic']}'...")
        output_path = await generator.generate_presentation(input_data)
        print(f"✓ Presentation generated successfully: {output_path}")
    except Exception as e:
        print(f"✗ Failed to generate presentation: {e}")

async def example_3_with_config_file():
    """Example 3: Use a configuration file."""
    print("\n=== Example 3: Using a Configuration File ===")
    
    # Create a temporary configuration file
    config = {
        "theme": "corporate",
        "output_format": "pptx",
        "max_retries": 3,
        "checkpoints_enabled": True,
        "fallback_templates_enabled": True,
        "base_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
        "templates_dir": "templates/corporate"
    }
    
    config_path = Path("examples/temp_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Create input data
    input_data = {
        "topic": "Digital Marketing Strategies",
        "style": "professional",
        "num_slides": 15,
        "author": "Marketing Team",
        "company": "Digital Innovations Inc."
    }
    
    # Create generator with config file and generate presentation
    generator = PresentationGenerator(config_path)
    
    try:
        print(f"Generating presentation using configuration file...")
        output_path = await generator.generate_presentation(input_data)
        print(f"✓ Presentation generated successfully: {output_path}")
    except Exception as e:
        print(f"✗ Failed to generate presentation: {e}")
    
    # Clean up temporary config file
    if config_path.exists():
        os.remove(config_path)

async def example_4_advanced_pipeline_usage():
    """Example 4: Advanced usage with direct pipeline factory access."""
    print("\n=== Example 4: Advanced Pipeline Usage ===")
    
    # Create pipeline factory
    factory = PipelineFactory()
    
    # Create custom pipeline with configuration
    config = {
        "theme": "minimal",
        "output_format": "pptx"
    }
    pipeline = await factory.create_pipeline(config)
    
    # Input data
    input_data = {
        "topic": "Quantum Computing Basics",
        "style": "academic",
        "num_slides": 10,
        "author": "Quantum Research Group"
    }
    
    # Add additional context data directly
    pipeline.context.set_data("title", "Introduction to Quantum Computing")
    pipeline.context.set_data("author", input_data["author"])
    pipeline.context.set_data("footer", "Confidential - Research Purposes Only")
    
    try:
        print(f"Executing custom pipeline configuration...")
        context = await pipeline.execute(input_data)
        
        # Extract the result from the context
        output_path = context.get_data("stage_input_data")
        if output_path:
            print(f"✓ Presentation generated successfully: {output_path}")
        else:
            print("✗ No output path found in the pipeline context")
    except Exception as e:
        print(f"✗ Failed to execute pipeline: {e}")

async def main():
    """Run all examples."""
    print("Presentation Generation Pipeline Examples")
    print("========================================")
    
    await example_1_simple_cli()
    await example_2_programmatic_api()
    await example_3_with_config_file()
    await example_4_advanced_pipeline_usage()

if __name__ == "__main__":
    asyncio.run(main()) 