# Automated Slide Creation System (ASCS)

A powerful tool that leverages OpenAI's Assistants API to automate the end-to-end process of creating professional presentations. This system eliminates the need for manual PowerPoint or Google Slides interaction, saving valuable time and effort.

## Features

- Automated content generation using AI
- Data visualization integration
- Smart template management
- Multi-format support

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Project Structure

```
src/
├── core/           # Core functionality
├── templates/      # Presentation templates
└── data_processing/# Data handling and visualization
```

## Usage

[Usage instructions will be added as features are implemented]

## Development

- Python 3.8+
- Dependencies managed via requirements.txt
- Environment variables in .env file

## License

[License information to be added]