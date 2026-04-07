## Backend – Compiler Visual Tutor

This is the **FastAPI backend** for your compiler project. It is designed as a
**rule‑based compiler engine**:

- errors are detected by analyzers (lexical / syntax / semantic)
- errors are classified
- errors are mapped to specific **resolver routines**
- each resolver modifies the source code according to predefined rules

At every step, the behavior is deterministic and explainable (no ML).

### Folder structure

- `main.py` – FastAPI entry point, exposes `/analyze`
- `models.py` – `CompilerError` structured error representation
- `analyzer/` – pure analysis logic
  - `lexer.py` – placeholder for lexical analysis
  - `syntax.py` – missing‑semicolon detection for C‑style code
  - `semantic.py` – placeholder for semantic checks
  - `classifier.py` – orchestrates analyzers and chooses resolvers
- `resolver/` – code‑fix routines
  - `syntax.py` – auto‑adds missing semicolons
  - `lexical.py` – placeholder for lexical fixes
  - `semantic.py` – placeholder for semantic fixes
  - `base.py` – generic `Resolver` interface (for future extension)
- `utils.py` – shared helpers

### API contract

`POST /analyze`

Request body:

```json
{
  "language": "c",
  "source_code": "int main() { printf(\"Hello\"); return 0; }"
}
```

Response body:

```json
{
  "errors": [
    {
      "type": "Syntax Error",
      "code": "MISSING_SEMICOLON",
      "message": "Missing semicolon at end of line.",
      "line": 2,
      "column": 23,
      "hint": "Add a semicolon at the end of the statement."
    }
  ],
  "fixed_code": "/* auto‑fixed code as a single string */",
  "explanation": "Human‑friendly explanation of what was detected and how it was fixed."
}
```

This matches what the React frontend expects:

- `errors` → drives the error cards
- `fixed_code` → shown in the fixed‑code panel
- `explanation` → shown as narrative text

### Running the backend

From the `backend` folder:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

