# agricultural-ai
Agricultural ChatGPT - Intelligent farming advisor

## Book processing to JSON

Process agricultural books (PDF/EPUB/TXT/DOCX) into structured JSON and local embeddings:

```bash
python book_processor.py --input data/books --output data/json_output --embeddings data/embeddings
```

API endpoint:

- `POST /api/v1/books/process` (multipart `books[]`) to ingest books and refresh local chat knowledge.
- `POST /api/v1/crop-health/predict` for structured crop-health prediction.
- `POST /api/v1/weather/recommendations` for weather-based farm recommendations.
- `POST /api/v1/soil/analyze` for soil nutrient analysis.
