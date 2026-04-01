# Compiler Visual Tutor – Frontend

This is the React frontend for your compiler project. It focuses on **visually explaining lexical, syntax, and semantic errors**, and showing how the backend's resolution routines fix them.

## Main ideas

- **Source Code Panel** – text editor where the learner pastes or types code.
- **Error & Explanation Panel** – shows each detected error with type, location, message, and a friendly hint.
- **Fixed Code Panel** – shows the corrected version of the code plus a human-friendly explanation.

The layout is designed for students and beginners learning how compilers detect and resolve errors.

## Running the frontend

From the `compiler_pbl` folder:

```bash
npm install
npm run dev
```

By default, Vite will start the app on port `5173`.

## Hooking up the FastAPI backend

In `src/App.jsx`, the `handleAnalyze` function currently uses a mocked response so you can see the full UI behavior without a running backend.

Once your FastAPI API is ready, replace the mock with a real request:

```js
const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ language: 'c', source_code: sourceCode })
});
const data = await response.json();
setErrors(data.errors);
setFixedCode(data.fixed_code);
setExplanation(data.explanation);
```

Adjust the URL and payload to match your actual backend design.

