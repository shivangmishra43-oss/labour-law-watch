import os
import json
import time
from pathlib import Path

from google import genai
from google.genai import types


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FOLDER = (
    BASE_DIR
    / "downloads"
    / "egazette"
    / "extracted"
)

OUTPUT_FOLDER = (
    BASE_DIR
    / "downloads"
    / "egazette"
    / "ai_summaries"
)

# Gemini model available to our API key
MODEL_NAME = "gemini-3.6-flash"

# Number of attempts for temporary API errors
MAX_ATTEMPTS = 4

# Seconds between retries
RETRY_DELAY = 8


# ============================================================
# CREATE OUTPUT FOLDER
# ============================================================

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CHECK API KEY
# ============================================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:

    print("")
    print("====================================")
    print("       GEMINI API KEY ERROR")
    print("====================================")
    print("")

    print("GEMINI_API_KEY was not found.")

    print("")
    print("Make sure:")
    print("1. Your Gemini API key was created")
    print("2. It was saved as GEMINI_API_KEY")
    print("3. VS Code was restarted after setting it")

    print("")

    raise SystemExit(1)


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=api_key
)


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are a legal research assistant working on an Indian Labour Law
Intelligence system.

You will receive text extracted from an official Indian Gazette
notification.

Your job is to accurately identify and summarize the legal update.

IMPORTANT RULES:

1. Do not invent facts.

2. Do not infer an effective date unless the notification supports it.

3. If something is not stated or cannot be determined, use null.

4. Preserve the exact legal names of Acts, Codes, Rules,
   Schemes and other legal instruments.

5. Distinguish between:
   - notification date
   - publication date
   - effective date

6. Identify the specific legal change wherever possible.

7. Identify who is likely to be affected.

8. Identify whether an employer, establishment, employee,
   EPFO, government authority or other party needs to take action.

9. Do not provide legal advice.

10. This is an information-extraction and summarisation task.

11. Return ONLY the requested JSON object.
"""


# ============================================================
# LOAD EXTRACTED JSON
# ============================================================

def load_extracted_file(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(data):

    gazette_id = data.get(
        "gazette_id"
    )

    notification_number = data.get(
        "notification_number"
    )

    act_name = data.get(
        "act_name"
    )

    sections_rules = data.get(
        "sections_rules",
        []
    )

    effective_date = data.get(
        "effective_date"
    )

    update_type = data.get(
        "update_type"
    )

    topic = data.get(
        "topic"
    )

    importance = data.get(
        "importance"
    )

    key_sentences = data.get(
        "key_sentences",
        []
    )

    source_text = "\n\n".join(
        key_sentences
    )

    prompt = f"""
Analyse the following Indian Gazette notification.

GAZETTE ID:
{gazette_id}

NOTIFICATION NUMBER:
{notification_number}

ACT / LAW IDENTIFIED BY PREVIOUS EXTRACTOR:
{act_name}

SECTIONS / RULES IDENTIFIED:
{sections_rules}

EFFECTIVE DATE IDENTIFIED BY PREVIOUS EXTRACTOR:
{effective_date}

UPDATE TYPE IDENTIFIED:
{update_type}

TOPIC IDENTIFIED:
{topic}

IMPORTANCE IDENTIFIED:
{importance}

EXTRACTED GAZETTE TEXT:
{source_text}


Return a JSON object with exactly these fields:

{{
    "headline": "",
    "gazette_id": "",
    "notification_number": "",
    "notification_date": null,
    "publication_date": null,
    "effective_date": null,
    "law_or_framework": "",
    "provisions_affected": [],
    "update_type": "",
    "what_changed": "",
    "who_is_affected": [],
    "action_required": [],
    "importance": "",
    "summary": ""
}}


INSTRUCTIONS:

headline:
A short, clear headline describing the legal change.

gazette_id:
Use the Gazette ID supplied above.

notification_number:
Use the notification number supplied above.

notification_date:
The date appearing as the date of the notification.
Use YYYY-MM-DD where possible.
If unavailable, use null.

publication_date:
The Gazette publication date if identifiable.
Use YYYY-MM-DD where possible.
If unavailable, use null.

effective_date:
The date on which the change takes effect.

Do NOT confuse this with notification date or publication date.

If the notification says that it comes into effect from
the date of publication and the publication date is known,
use that date.

If it gives another specific effective date, use that date.

Otherwise use null.

law_or_framework:
The principal Act, Code, Rule, Scheme, notification framework,
or other legal instrument affected.

provisions_affected:
List the relevant sections, rules, clauses, schedules,
tables, categories or other legal provisions actually affected.

update_type:
Use the most accurate description:

New Gazette
Amendment
Supersession
Notification
Clarification
Extension
Repeal
Other

what_changed:
Explain precisely what the notification changes.
Keep this concise but legally meaningful.

who_is_affected:
List the categories of persons, establishments, employers,
employees, authorities, funds, schemes or other entities affected.

action_required:
List practical actions that appear to be required.

If no action is apparent, return an empty array.

importance:
Use only:

High
Medium
Normal

summary:
Write a short professional summary suitable for display
on an Indian labour-law updates dashboard.

Do not include Markdown.

Do not include ```json.

Return JSON only.
"""


    return prompt


# ============================================================
# CALL GEMINI
# ============================================================

def generate_summary(data):

    prompt = build_prompt(data)

    last_error = None

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        print("")
        print(
            f"Gemini attempt {attempt}/{MAX_ATTEMPTS}..."
        )

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(

                    # Force Gemini to return JSON.
                    response_mime_type="application/json",

                    system_instruction=SYSTEM_INSTRUCTION,

                    # Low temperature improves consistency
                    # for structured legal extraction.
                    temperature=0.1,

                    max_output_tokens=2500
                )
            )

            if not response.text:

                raise ValueError(
                    "Gemini returned an empty response."
                )

            raw_text = response.text.strip()

            # ------------------------------------------------
            # Parse JSON directly.
            #
            # Because response_mime_type is JSON, Gemini
            # should return valid JSON without Markdown fences.
            # ------------------------------------------------

            result = json.loads(
                raw_text
            )

            return result

        except json.JSONDecodeError as error:

            last_error = error

            print("")
            print(
                "Gemini returned invalid JSON."
            )

            print(error)

            # Retry because the model may have produced
            # an incomplete response.

            if attempt < MAX_ATTEMPTS:

                print("")
                print(
                    f"Waiting {RETRY_DELAY} seconds "
                    "before retry..."
                )

                time.sleep(
                    RETRY_DELAY
                )

        except Exception as error:

            last_error = error

            print("")
            print(
                "Gemini request failed:"
            )

            print(error)

            if attempt < MAX_ATTEMPTS:

                print("")
                print(
                    f"Waiting {RETRY_DELAY} seconds "
                    "before retry..."
                )

                time.sleep(
                    RETRY_DELAY
                )

    raise last_error


# ============================================================
# PROCESS ONE GAZETTE
# ============================================================

def process_file(file_path):

    print("")
    print("------------------------------------")
    print(
        f"Processing: {file_path.name}"
    )
    print("------------------------------------")

    data = load_extracted_file(
        file_path
    )

    gazette_id = data.get(
        "gazette_id"
    )

    if not gazette_id:

        print("")
        print(
            "ERROR: Gazette ID missing."
        )

        return False


    # --------------------------------------------------------
    # Output file
    # --------------------------------------------------------

    output_file = (
        OUTPUT_FOLDER
        / f"{gazette_id}_ai.json"
    )


    # --------------------------------------------------------
    # Don't call Gemini again if we already have a result.
    # This saves free-tier quota.
    # --------------------------------------------------------

    if output_file.exists():

        print("")
        print(
            "AI summary already exists."
        )

        print(
            "Skipping Gemini request."
        )

        print("")
        print(
            "Existing file:"
        )

        print(
            output_file
        )

        return True


    # --------------------------------------------------------
    # Generate summary
    # --------------------------------------------------------

    try:

        result = generate_summary(
            data
        )


        # ----------------------------------------------------
        # Save result
        # ----------------------------------------------------

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=4
            )


        print("")
        print(
            "AI summary generated successfully."
        )

        print("")
        print(
            "Saved to:"
        )

        print(
            output_file
        )

        return True


    except json.JSONDecodeError as error:

        print("")
        print(
            "ERROR: Gemini returned invalid JSON."
        )

        print(error)

        return False


    except Exception as error:

        print("")
        print(
            "ERROR after all Gemini attempts:"
        )

        print(error)

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    print("")
    print("====================================")
    print("     LABOUR LAW WATCH - AI")
    print("====================================")
    print("")

    print("Input folder:")
    print(
        INPUT_FOLDER
    )

    print("")
    print("Output folder:")
    print(
        OUTPUT_FOLDER
    )

    print("")
    print("Gemini model:")
    print(
        MODEL_NAME
    )

    print("")
    print(
        "Response format:"
    )

    print(
        "JSON"
    )

    print("")
    print(
        "Checking extracted Gazette files..."
    )


    # --------------------------------------------------------
    # Find JSON files
    # --------------------------------------------------------

    json_files = sorted(
        INPUT_FOLDER.glob(
            "*.json"
        )
    )


    if not json_files:

        print("")
        print(
            "No extracted JSON files found."
        )

        print("")
        print(
            "Expected folder:"
        )

        print(
            INPUT_FOLDER
        )

        print("")

        return


    print("")
    print(
        f"Found {len(json_files)} "
        "extracted Gazette file(s)."
    )


    successful = 0
    failed = 0


    # --------------------------------------------------------
    # Process all Gazettes
    # --------------------------------------------------------

    for file_path in json_files:

        success = process_file(
            file_path
        )

        if success:

            successful += 1

        else:

            failed += 1


    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    print("")
    print("====================================")
    print("           AI PROCESSING DONE")
    print("====================================")
    print("")

    print(
        f"Total files: {len(json_files)}"
    )

    print(
        f"Successful: {successful}"
    )

    print(
        f"Failed: {failed}"
    )

    print("")
    print(
        "AI summaries:"
    )

    print(
        OUTPUT_FOLDER
    )

    print("")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()