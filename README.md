# Company Information Enrichment Tool

This tool automatically scrapes company websites, extracts relevant information, and enriches your dataset using AI-powered analysis.

## Features

- Web scraping of company websites
- Text chunking and embedding storage
- AI-powered information extraction using LLaMA 3
- Parallel processing for faster results
- Supabase integration for vector storage

## Prerequisites

Before running the tool, ensure you have:

1. Python 3.7+ installed
2. Ollama installed and running with LLaMA 3 model pulled (`ollama pull llama3`)
3. Supabase account with a table set up for embeddings
4. `.env` file with your Supabase credentials

## Installation

1. Clone this repository
2. Install the required packages:


```bash
pip install pandas requests beautifulsoup4 sentence-transformers supabase python-dotenv ollama
```

## Usage

1. Prepare your input Excel file (`Book1.xlsx`) with at least these columns:
   - `Company Name`
   - `Company URL`
   - (Any other columns you want to fill)

2. Run the script:

```bash
python final3.py
```

3. The script will:
   - Scrape each company's website
   - Store text embeddings in Supabase
   - Use LLaMA 3 to fill missing information
   - Save results to `updated_company_data_filled_v2 (1) 3.xslx`

## Configuration

Edit these variables in the script as needed:

```python
CHUNK_SIZE = 300  # Adjust chunk size for text processing
TOP_K = 1         # Number of similar chunks to retrieve
OLLAMA_MODEL = "llama3"  # Change if using a different Ollama model
```

## Output

The script creates `updated_company_data_filled_v2 (1) 3.xlsx` with all columns filled based on website content analysis.

## Performance Notes

- Processing time depends on number of companies and website sizes
- ThreadPoolExecutor uses 4 workers by default (adjust as needed)
- Random delays are added to be polite to web servers

## Troubleshooting

- If scraping fails, check if websites block bots
- Ensure Ollama is running (`ollama serve`)
- Verify Supabase credentials in `.env` file
- Check table structure matches what the script expects

## Customization

To modify the information extraction:
1. Adjust the prompt template in `get_prompt()` function
2. Change the columns in your input Excel file
3. Modify the similarity search parameters
