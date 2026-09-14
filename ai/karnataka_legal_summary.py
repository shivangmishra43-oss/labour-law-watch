import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import types


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path(
    "downloads/karnataka/extracted"
)

OUTPUT_DIR = Path(
    "downloads/karnataka/ai_summaries"
)

MODEL_NAME = "gemini-3.6-flash"

MAX_RETRIES = 10

INITIAL_RETRY_DELAY = 15

DELAY_BETWEEN_FILES = 5


# ============================================================
# GEMINI CLIENT
# ============================================================

api_key = os.environ.get(
    "GEMINI_API_KEY"
)

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set."
    )

client = genai.Client(
    api_key=api_key
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an Indian labour-law research assistant.

You are analysing documents downloaded from the official
Karnataka e-Gazette.

Your task is to extract and summarise the legal information
contained in the supplied document.

IMPORTANT RULES:

1. Use ONLY the supplied document text.
2. Do not invent facts.
3. Do not rely on outside knowledge.
4. Distinguish carefully between:
   - final rules
   - draft rules
   - notifications
   - amendments
   - orders
   - acts
   - corrigenda
   - other documents.
5. If a document is clearly unrelated to labour law, set
   "is_labour_law_relevant" to false.
6. Preserve important Kannada legal terminology where useful.
7. If a field cannot be established from the document,
   use null or an empty array.
8. Dates must be in YYYY-MM-DD format wherever possible.
9. For "sections", list actual sections/rules/regulations
   identified in the document.
10. Do not treat a draft as a final law.
11. Do not call something an amendment unless the document
    actually indicates an amendment.
12. Keep the headline concise and useful to a lawyer.
13. The summary should explain what the document does.
14. "what_changed" should explain the substantive legal
    change or notification, if any.
15. "who_is_affected" should identify affected employers,
    employees, workers, establishments, authorities, etc.
16. "action_required" should state any practical action
    apparent from the document. If none is apparent, say so.
17. Pay close attention to whether the document is a
    corrigendum, amendment, notification or final rule.
18. Do not confuse the title of the underlying Act/Rules
    with the nature of the present Gazette document.

Return ONLY valid JSON.

Use exactly this structure:

{
  "headline": "",
  "summary": "",
  "what_changed": "",
  "document_type": "",
  "topic": "",
  "publication_date": null,
  "effective_date": null,
  "act_name": null,
  "rules_name": null,
  "sections": [],
  "who_is_affected": [],
  "action_required": "",
  "is_draft": false,
  "is_labour_law_relevant": true
}
"""


# ============================================================
# FILE HELPERS
# ============================================================

def load_json(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def save_json(file_path, data):

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def output_path_for(input_path):

    return OUTPUT_DIR / (
        input_path.stem + "_ai.json"
    )


# ============================================================
# GET DOCUMENT TEXT
# ============================================================

def get_document_text(document):

    # Primary field used by the Karnataka extractor.
    ai_input_text = document.get(
        "ai_input_text"
    )

    if (
        isinstance(ai_input_text, str)
        and ai_input_text.strip()
    ):

        return ai_input_text

    # Fallback for older extracted files.
    text = document.get(
        "text"
    )

    if (
        isinstance(text, str)
        and text.strip()
    ):

        return text

    return ""


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(document):

    metadata = document.get(
        "metadata",
        {}
    )

    title = document.get(
        "title",
        ""
    )

    text = get_document_text(
        document
    )

    return f"""
Analyse the following Karnataka e-Gazette document.

SOURCE METADATA
===============

Title:
{title}

Department:
{document.get('department')}

Organization:
{document.get('organization')}

Document number:
{document.get('document_number')}

Gazette year:
{document.get('gazette_year')}

Existing document type:
{document.get('document_type')}

Existing topics:
{json.dumps(
    document.get(
        "topics",
        []
    ),
    ensure_ascii=False
)}

Publication date:
{document.get('publication_date')}

Effective date:
{document.get('effective_date')}

Source URL:
{document.get('source_url')}

Document URL:
{document.get('document_url')}

DOCUMENT TEXT
=============

{text}

Return ONLY the requested JSON object.
"""


# ============================================================
# GEMINI CALL WITH RETRIES
# ============================================================

def call_gemini(prompt):

    delay = INITIAL_RETRY_DELAY

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"  Gemini attempt "
                f"{attempt}/{MAX_RETRIES}..."
            )

            response = client.models.generate_content(

                model=MODEL_NAME,

                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],

                config=types.GenerateContentConfig(

                    system_instruction=SYSTEM_PROMPT,

                    temperature=0.1,

                    max_output_tokens=5000,

                    response_mime_type="application/json"
                )
            )

            if not response.text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return json.loads(
                response.text
            )

        except Exception as error:

            error_text = str(
                error
            )

            print("")
            print(
                "  Gemini error:"
            )

            print(
                error_text[:1000]
            )

            temporary_error = (

                "503" in error_text

                or "UNAVAILABLE" in error_text

                or "429" in error_text

                or "RESOURCE_EXHAUSTED" in error_text

                or "500" in error_text

                or "INTERNAL" in error_text

                or "DEADLINE" in error_text

                or "TIMEOUT" in error_text
            )

            if not temporary_error:

                raise

            if attempt >= MAX_RETRIES:

                raise

            print(
                f"  Temporary error."
            )

            print(
                f"  Waiting {delay} seconds..."
            )

            time.sleep(
                delay
            )

            delay = min(
                delay * 2,
                300
            )

    raise RuntimeError(
        "Gemini failed after all retries."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    input_files = sorted(
        INPUT_DIR.glob("*.json")
    )

    print("")
    print("========================================")
    print("       KARNATAKA GEMINI LEGAL ANALYSIS")
    print("========================================")
    print("")

    print(
        f"Input files: {len(input_files)}"
    )

    print(
        f"Model: {MODEL_NAME}"
    )

    print("")

    successful = 0

    skipped_existing = 0

    failed = 0

    failed_files = []

    for index, input_file in enumerate(
        input_files,
        start=1
    ):

        print(
            f"[{index}/{len(input_files)}] "
            f"{input_file.name}"
        )

        output_file = output_path_for(
            input_file
        )

        # ------------------------------------------------
        # Already completed
        # ------------------------------------------------

        if output_file.exists():

            print(
                "  SKIPPED: AI summary already exists"
            )

            skipped_existing += 1

            print("")

            continue

        # ------------------------------------------------
        # Load JSON
        # ------------------------------------------------

        try:

            document = load_json(
                input_file
            )

        except Exception as error:

            print(
                f"  FAILED loading JSON: {error}"
            )

            failed += 1

            failed_files.append(
                input_file.name
            )

            print("")

            continue

        # ------------------------------------------------
        # Get actual extracted text
        # ------------------------------------------------

        text = get_document_text(
            document
        )

        print(
            f"  Text: {len(text):,} characters"
        )

        if not text.strip():

            print(
                "  FAILED: no extracted document text"
            )

            failed += 1

            failed_files.append(
                input_file.name
            )

            print("")

            continue

        # ------------------------------------------------
        # Send to Gemini
        # ------------------------------------------------

        print(
            "  Sending to Gemini..."
        )

        try:

            prompt = build_prompt(
                document
            )

            analysis = call_gemini(
                prompt
            )

            # Preserve source information.
            analysis[
                "_source_file"
            ] = input_file.name

            analysis[
                "_source_metadata"
            ] = {
                "source": document.get(
                    "source"
                ),
                "jurisdiction": document.get(
                    "jurisdiction"
                ),
                "department": document.get(
                    "department"
                ),
                "organization": document.get(
                    "organization"
                ),
                "document_number": document.get(
                    "document_number"
                ),
                "gazette_year": document.get(
                    "gazette_year"
                ),
                "source_url": document.get(
                    "source_url"
                ),
                "document_url": document.get(
                    "document_url"
                ),
                "publication_date": document.get(
                    "publication_date"
                ),
                "effective_date": document.get(
                    "effective_date"
                )
            }

            save_json(
                output_file,
                analysis
            )

            print("")
            print(
                f"  Headline: "
                f"{analysis.get('headline')}"
            )

            print(
                f"  Topic: "
                f"{analysis.get('topic')}"
            )

            print(
                f"  Type: "
                f"{analysis.get('document_type')}"
            )

            print(
                f"  Draft: "
                f"{analysis.get('is_draft')}"
            )

            print(
                f"  Labour relevant: "
                f"{analysis.get('is_labour_law_relevant')}"
            )

            print(
                f"  Saved: "
                f"{output_file.name}"
            )

            successful += 1

        except Exception as error:

            print("")
            print(
                f"  FAILED permanently: {error}"
            )

            failed += 1

            failed_files.append(
                input_file.name
            )

        print("")

        time.sleep(
            DELAY_BETWEEN_FILES
        )

    # ====================================================
    # FINAL REPORT
    # ====================================================

    print("")
    print("========================================")
    print("             ANALYSIS COMPLETE")
    print("========================================")
    print("")

    print(
        f"Successful: {successful}"
    )

    print(
        f"Skipped existing: {skipped_existing}"
    )

    print(
        f"Failed: {failed}"
    )

    print("")

    if failed_files:

        print(
            "Failed files:"
        )

        for filename in failed_files:

            print(
                f"  - {filename}"
            )

        print("")

    print(
        "AI summaries folder:"
    )

    print(
        OUTPUT_DIR.resolve()
    )

    print("")


if __name__ == "__main__":

    main()