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

### Using the Command Line Interface

The easiest way to use the tool is through the command line interface:

```bash
python -m src.main "My Presentation Topic" --style professional --num-slides 10 --author "Your Name" --company "Your Company"
```

This will generate a 10-slide professional presentation on your specified topic.

### Using Quality Assurance Tools

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

## Non-Technical Guide to Quality Assurance

### What is Content Validation?

Our content validation system checks your presentations for common issues:

1. **Spelling and grammar errors** - Identifies misspelled words and grammar mistakes
2. **Terminology consistency** - Ensures you use terms consistently (e.g., not mixing "website" and "web site")
3. **Capitalization consistency** - Checks that titles and headings use consistent capitalization 

### How to Use Quality Assurance

1. **Generate your presentation** using one of the methods above
2. **Run content validation** to check for issues:
   - Either use the Python code example above
   - Or use the command line validator
3. **Review the validation report** to see any issues found
4. **Fix identified problems** either manually or using suggested corrections

### Understanding Validation Reports

The validation report is organized by:

- **Issue type** - Spelling, grammar, consistency, etc.
- **Severity** - How important the issue is (INFO, WARNING, ERROR)
- **Location** - Which slide and element contains the issue
- **Suggestions** - Possible corrections for the issue

### Creating a Custom Dictionary

To prevent false positives for specialized terminology:

1. Create a text file with your custom terms (one per line)
2. Provide this file when running validation
3. Terms in your custom dictionary won't be flagged as spelling errors

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