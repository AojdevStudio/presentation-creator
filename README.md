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
- **Custom text input for slide generation:**
  - Use your own content to create slides
  - Support for plain text and markdown formats
  - Automatic format detection
  - Control over content density per slide
- Quality assurance tools:
  - Content validation (spelling, grammar, consistency checks)
  - Terminology consistency validation
  - Capitalization consistency checks

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

## Using Your Own Text Content

### Command Line Usage

The simplest way to generate slides from your own text is through the command line:

```bash
# From a text file:
python -m src.main text --file my_content.md --presenter "John Doe" --output "my_presentation.pptx"

# From direct text input:
python -m src.main text --text "# My Presentation\n\n## Introduction\n- Point 1\n- Point 2" --format markdown
```

#### Available Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--file` | Path to text file containing your content | `--file notes.txt` |
| `--text` | Direct text input (use quotes and \n for line breaks) | `--text "TITLE\n\n- Point 1\n- Point 2"` |
| `--format` | Input format: "text", "markdown", or "auto" (default) | `--format markdown` |
| `--presenter` | Presenter name for title slide | `--presenter "Jane Smith"` |
| `--date` | Presentation date (YYYY-MM-DD) | `--date "2024-04-01"` |
| `--density` | Content density: "low", "medium" (default), or "high" | `--density low` |
| `--output` | Output file path for the presentation | `--output "my_slides.pptx"` |

You must provide either `--file` OR `--text` but not both.

### Python API Usage

For more control, you can use the Python API:

```python
import asyncio
from src.core.presentation_builder import PresentationBuilder

async def main():
    builder = PresentationBuilder()
    await builder.initialize()
    
    # Option 1: Use a text file
    await builder.build_presentation_from_text_file(
        file_path="my_content.md",
        presenter="John Doe",
        date="2024-04-01",
        format_type="markdown",  # or None for auto-detection
        content_density="medium",  # "low", "medium", or "high"
        output_path="output.pptx"
    )
    
    # Option 2: Use direct text input
    my_text = """
    # My Custom Presentation
    
    ## Introduction
    This is a presentation created from my own text content.
    
    - Point 1: Important information
    - Point 2: Critical details
    - Point 3: Key insights
    
    ## Second Section
    More detailed information about the topic.
    
    1. First step in the process
    2. Second step in the process
    3. Final considerations
    """
    
    await builder.build_presentation_from_text(
        text=my_text,
        presenter="John Doe",
        date="2024-04-01",
        format_type="markdown",  # or None for auto-detection
        content_density="medium",  # "low", "medium", or "high"
        output_path="my_presentation.pptx"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Text Format Guidelines

### Markdown Format (Recommended)

Markdown is the recommended format as it provides clear structure:

```markdown
# Main Title

## First Section
This is an introduction paragraph.

- Bullet point 1
- Bullet point 2
- Bullet point 3

## Second Section

### Subsection
This becomes a subheading on the slide.

1. Numbered item 1
2. Numbered item 2

## Conclusion
Summary text goes here.

- Key takeaway 1
- Key takeaway 2
```

#### Markdown Formatting Rules:

- **# Main Title** - Becomes the presentation title
- **## Section Title** - Each becomes a new slide
- **### Subheading** - Becomes a subheading on the current slide
- **- Item** - Creates bullet points
- **1. Item** - Creates numbered lists
- **```code```** - Creates a code example slide
- **Bold** with `**text**` and *italics* with `*text*` are preserved

### Plain Text Format

For simple text files without markdown:

```
PRESENTATION TITLE

SECTION ONE
This is an introduction paragraph.

- This is a bullet point
- Another bullet point
- A third bullet point

SECTION TWO
More content here.

1. First numbered item
2. Second numbered item
```

#### Plain Text Formatting Rules:

- **LINES IN ALL CAPS** - Treated as slide titles
- **Empty lines** - Separate content blocks
- **Lines starting with - or •** - Treated as bullet points
- **Lines starting with numbers and a period (1.)** - Treated as numbered lists
- **Regular text** - Treated as paragraphs

### Content Density Options

Control how much content appears on each slide:

- **Low density**: 
  - Max 4 bullet points per slide
  - Shorter text blocks (300 characters max)
  - More slides with less content each

- **Medium density** (default):
  - Max 6 bullet points per slide
  - Medium text blocks (400 characters max)
  - Balanced number of slides

- **High density**:
  - Max 8 bullet points per slide
  - Longer text blocks (500 characters max)
  - Fewer slides with more content each

## Example Text Files

### Example 1: Basic Markdown Presentation

```markdown
# Project Status Update

## Introduction
This presentation provides an update on the current project status.

- Project started on January 15, 2024
- Currently in development phase
- On track for May delivery

## Current Progress
The team has completed several key milestones.

- Backend API is 90% complete
- Frontend components are 75% complete
- Database migration is finished

## Challenges
Some issues have emerged during development.

1. Integration with legacy systems
2. Performance bottlenecks in data processing
3. Resource constraints

## Next Steps

### Short-term
- Complete API documentation
- Finalize frontend design
- Begin QA testing

### Long-term
- Plan for phase 2 features
- Prepare training materials
- Schedule deployment

## Conclusion
The project is progressing well despite challenges.

- We are on track for the deadline
- Additional resources may be needed
- Regular updates will continue
```

### Example 2: Plain Text Format

```
PROJECT STATUS UPDATE

INTRODUCTION
This presentation provides an update on the current project status.

- Project started on January 15, 2024
- Currently in development phase
- On track for May delivery

CURRENT PROGRESS
The team has completed several key milestones.

- Backend API is 90% complete
- Frontend components are 75% complete
- Database migration is finished

CHALLENGES
Some issues have emerged during development.

1. Integration with legacy systems
2. Performance bottlenecks in data processing
3. Resource constraints

NEXT STEPS
These are our upcoming priorities.

- Complete API documentation
- Finalize frontend design
- Begin QA testing

CONCLUSION
The project is progressing well despite challenges.

- We are on track for the deadline
- Additional resources may be needed
- Regular updates will continue
```

## AI-Generated Content (Alternative Method)

If you prefer AI-generated content instead of your own text:

```bash
python -m src.main ai "My Presentation Topic" --style professional --num-slides 10 --presenter "Your Name" --company "Your Company"
```

## Quality Assurance Tools

The presentation generator includes powerful quality assurance tools to ensure your presentations are error-free and consistent.

#### Validating Presentation Content

```python
from src.qa.content_validator import ContentValidator

# Load your presentation data
presentation_data = {
    "slides": [
        {
            "title": "Introduction",
            "elements": [
                {
                    "type": "text",
                    "content": "This is the introduction to our topic."
                },
                {
                    "type": "bullet_list",
                    "content": [
                        "First key point",
                        "Second key point",
                        "Third key point"
                    ]
                }
            ]
        }
    ]
}

# Create a validator
validator = ContentValidator()

# Optional: Add custom dictionary words
validator = ContentValidator(custom_dictionary="my_custom_dictionary.txt")

# Run validation
validation_issues = validator.validate_presentation(presentation_data)

# Generate and print a report
report = validator.generate_validation_report(validation_issues, output_format="text")
print(report)

# Or get the report as JSON
json_report = validator.generate_validation_report(validation_issues, output_format="json")

# Or generate an HTML report
html_report = validator.generate_validation_report(validation_issues, output_format="html")
with open("validation_report.html", "w") as f:
    f.write(html_report)
```

#### Adding Custom Dictionary Words

1. Create a text file with one word per line:
```
customterm1
customterm2
technicalacryonym
```

2. Pass this file path when creating the validator:
```python
validator = ContentValidator(custom_dictionary="path/to/custom_dict.txt")
```

#### Using with Command Line Validation

There's also a simple command-line interface for validation:

```bash
python -m src.qa.content_validator my_presentation.json --output report.html
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
│   ├── core/
│   │   ├── __init__.py
│   │   ├── slide_content_generator.py
│   │   ├── slide_generator.py
│   │   ├── presentation_builder.py
│   │   ├── openai_client.py
│   │   └── prompt_templates.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_parser.py
│   │   └── content_mapper.py
│   ├── qa/
│   │   ├── __init__.py
│   │   └── content_validator.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_slide_content_generator.py
│   ├── test_slide_generator.py
│   ├── test_presentation_builder.py
│   └── test_content_validator.py
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