AI_USAGE

Gemini Vision (gemini-2.5-flash)

This model is the core LLM vision service.

It handles attributes that require contextual understanding of the item (e.g., recognizing a “Polo shirt” as the category, detecting brand logos, or describing style).

These attributes aren’t trivial to extract from pixels alone; they require higher-level reasoning, which Gemini provides.

In your pipeline, Gemini produces most of the descriptive metadata (category, brand, material, fit, style, condition, gender, season, pattern).

Google Cloud Vision

A specialized vision service, lightweight and accurate for low-level tasks.

In your case, it is used specifically for color classification.

This is a deliberate trade-off: instead of overloading Gemini for basic tasks, you use a cheaper, faster tool where it excels.

Meta LLaMA model

A language/vision model that complements Gemini.

It is assigned attributes that benefit from structured pattern recognition but don’t require full semantic reasoning.

For your service, it extracts sleeve_length, neckline, and closure_type — clothing-specific details that LLaMA handles efficiently.

Postgres (JSONB storage)

Once models return their results, they are normalized into JSON structures.

These are stored in a Postgres database with JSONB columns, which makes querying (e.g., “find all Polo shirts with long sleeves”) efficient.

Storing raw inference metadata ensures auditability and flexibility for future analysis.

Orchestrator

The orchestrator is the “brains” of the system.

It decides which model handles which attribute, runs them in parallel threads, merges results, and ensures consistent output format.

It also logs latency per model and overall processing time, so you know the performance of each component.