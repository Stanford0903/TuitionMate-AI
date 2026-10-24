
# TuitionMate AI — Local FAQ Assistant

A local AI customer support demo for a fictional
Malaysian tuition centre.

## Technology
- Python
- FastAPI
- Ollama
- Qwen2.5 3B
- JSON FAQ database
- n8n (automation workflow)

## Features
1. Exact FAQ matching
2. Local AI semantic matching
3. Approved FAQ answer validation
4. Human handoff for unknown enquiries
5. Sensitive-question handoff
6. Automated API testing

## Local Setup

Install Python dependencies:

pip install fastapi uvicorn pydantic

Install Ollama and download:

ollama pull qwen2.5:3b

Start FastAPI:

python -m uvicorn main:app --host 127.0.0.1 --port 8000

Open:

http://127.0.0.1:8000/docs

## Test Results

- Rule-based FAQ tests: 10/10 PASS
- Standalone Ollama tests: 2/2 PASS
- FastAPI + Ollama integration: 3/3 scenarios PASS

These are small demo tests, not production accuracy measurements.

## Safety

- Demo data only
- No real student information
- No paid OpenAI API required
- No guaranteed answers to unknown questions
- Human handoff flag does not mean staff notification
- Business facts require verification before production

## Future Improvements

- Shared FAQ data for all modules
- Larger AI evaluation dataset
- Actual human notification integration
- Lead capture and booking workflow
- Docker deployment
- Authentication and logging
