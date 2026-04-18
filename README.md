# agricultural-ai
Agricultural ChatGPT - Intelligent farming advisor

## Book processing to JSON

Process agricultural books (PDF/EPUB/TXT/DOCX) into structured JSON and local embeddings:

```bash
python book_processor.py --input data/books --output data/json_output --embeddings data/embeddings
```

API endpoint:

- `POST /api/v1/books/process` (multipart `books[]`) to ingest books and refresh local chat knowledge.
