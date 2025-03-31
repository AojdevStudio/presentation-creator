# PowerPoint Presentation Generator

A Python-based tool that automatically generates PowerPoint presentations using OpenAI's GPT-4 for content generation and python-pptx for slide creation.

## Features

- Automatic slide content generation using OpenAI's GPT-4
- Support for multiple slide types:
  - Title slides
  - Content slides with bullet points
  - Section transition slides
  - Summary slides
- PowerPoint template support
- Asynchronous content generation
- Error handling and retries
- Comprehensive logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/presentation-generator.git
cd presentation-generator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:
Create a `.env` file in the project root and add your API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Basic Usage

```python
import asyncio
from src.core.presentation_builder import PresentationBuilder

async def main():
    # Initialize the presentation builder
    builder = PresentationBuilder()
    await builder.initialize()
    
    # Define slide specifications
    slide_specs = [
        {
            "template_type": "title",
            "variables": {
                "title": "My Presentation",
                "subtitle": "An Example",
                "presenter": "John Doe",
                "date": "2024-03-31"
            }
        },
        {
            "template_type": "content",
            "variables": {
                "title": "Key Points",
                "key_points": [
                    "First point",
                    "Second point",
                    "Third point"
                ],
                "context": "Additional information"
            }
        }
    ]
    
    # Generate the presentation
    await builder.build_presentation(slide_specs, "output.pptx")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using an Outline

```python
import asyncio
from src.core.presentation_builder import PresentationBuilder

async def main():
    builder = PresentationBuilder()
    await builder.initialize()
    
    # Define presentation outline
    outline = [
        {
            "title": "Introduction",
            "content": [
                {
                    "title": "Background",
                    "points": ["Point 1", "Point 2"],
                    "context": "Background information"
                }
            ],
            "key_takeaway": "Important background concepts"
        },
        {
            "title": "Main Content",
            "content": [
                {
                    "title": "Key Findings",
                    "points": ["Finding 1", "Finding 2"],
                    "context": "Research results"
                }
            ],
            "key_takeaway": "Significant findings"
        }
    ]
    
    # Generate presentation from outline
    await builder.build_presentation_from_outline(
        title="My Presentation",
        outline=outline,
        presenter="John Doe",
        date="2024-03-31",
        output_path="output.pptx"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

Run the test suite:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=src
```

## Project Structure

```
presentation-generator/
├── src/
│   └── core/
│       ├── __init__.py
│       ├── slide_content_generator.py
│       ├── slide_generator.py
│       ├── presentation_builder.py
│       ├── openai_client.py
│       └── prompt_templates.py
├── tests/
│   ├── __init__.py
│   ├── test_slide_content_generator.py
│   ├── test_slide_generator.py
│   └── test_presentation_builder.py
├── templates/
│   └── default.pptx
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.