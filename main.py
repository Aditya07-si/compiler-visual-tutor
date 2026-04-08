from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from analyzer.classifier import analyze_code


app = FastAPI(title="Compiler PBL Backend", version="0.1.0")


class AnalyzeRequest(BaseModel):
    language: str
    source_code: str


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    Analyze the provided source code and return:
    - detected errors
    - auto-fixed code (if applicable)
    - plain‑English explanation
    """
    # For now, language is unused but kept for future extension (C/C++/Java)
    result = analyze_code(req.source_code)
    return result


# Allow calls from the React dev server by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

