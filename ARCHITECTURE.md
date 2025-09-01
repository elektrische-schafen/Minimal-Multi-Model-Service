ARCHITECTURE
The system follows a modular microservice-inspired architecture where each component has a clear responsibility. This separation makes the system scalable, maintainable, and testable.
________________________________________
Components
1.	FastAPI Backend (Backend.py)
o	Acts as the orchestrator service.
o	Accepts API requests from the frontend (/v1/items/analyze).
o	Validates input (ensures exactly 4 valid, publicly accessible image URLs).
o	Calls three different model services in parallel threads:
	Gemini Vision (gemini-2.5-flash) → extracts semantic attributes such as category, brand, material, style, fit.
	Google Cloud Vision → specialized for low-level tasks, here used for color classification.
	Meta LLaMA → handles structured clothing attributes like sleeve length, neckline, closure type.
o	Aggregates responses from all models, logs timing for each, and prepares a unified JSON response.
2.	PostgreSQL Database
o	Stores inference results in a table called inference_results.
o	Uses JSONB columns for attributes, model_info, and processing metadata.
o	This makes it efficient to query attributes (e.g., “find all Polo shirts with long sleeves”) and easy to extend if more attributes are added later.
o	Provides persistence so results are not lost between API calls.
3.	Streamlit Frontend (frontend.py)
o	Lightweight UI for end-users.
o	Allows users to paste or upload 4 image URLs.
o	Sends a request to the FastAPI backend and displays the results (category, brand, color, style, etc.) in a clean dashboard format.
o	Useful for demos, validation, and quick iteration.
________________________________________
Data Flow
1.	User Interaction
o	The user enters 4 image URLs into the Streamlit UI.
2.	Request Validation
o	The frontend sends a POST request to the FastAPI backend.
o	Backend ensures images are valid, publicly accessible, and ≤10MB.
o	If validation fails, an error JSON is returned.
3.	Model Orchestration
o	FastAPI launches 3 worker threads (Gemini, Cloud Vision, LLaMA).
o	Each thread processes its assigned attributes.
o	Failures in any single model are logged, and default "unknown" values are returned to maintain schema consistency.
4.	Response Assembly
o	Backend merges all model outputs into a single attributes JSON object.
o	Attaches model_info (model names, attributes handled, latency) and processing (total latency, per-model timings, status).
5.	Persistence
o	Results are inserted into Postgres (inference_results table).
o	This enables historical queries, analytics, and auditing.
6.	Frontend Display
o	Backend returns final JSON to Streamlit.
o	Streamlit renders the structured attributes in a human-readable UI for the user.
________________________________________
