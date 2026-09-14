import json
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


# ============================================================
# DATABASE
# ============================================================

from database import (
    get_connection,
    create_database
)


# ============================================================
# DIRECTORIES
# ============================================================

EXTRACTED_DIR = (
    PROJECT_ROOT
    / "downloads"
    / "karnataka"
    / "extracted"
)

AI_DIR = (
    PROJECT_ROOT
    / "downloads"
    / "karnataka"
    / "ai_summaries"
)


# ============================================================
# SOURCE
# ============================================================

SOURCE_NAME = "Karnataka e-Gazette"

SOURCE_URL = (
    "https://erajyapatra.karnataka.gov.in/"
)


# ============================================================
# BASIC HELPERS
# ============================================================

def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def clean_text(value):

    if value is None:
        return ""

    return str(value).strip()


def get_document_text(document):

    text = document.get(
        "ai_input_text"
    )

    if (
        isinstance(text, str)
        and text.strip()
    ):

        return text.strip()

    text = document.get(
        "text"
    )

    if (
        isinstance(text, str)
        and text.strip()
    ):

        return text.strip()

    return ""


def get_ai_file(extracted_file):

    return AI_DIR / (
        extracted_file.stem
        + "_ai.json"
    )


# ============================================================
# GET GEMINI ANALYSIS
# ============================================================

def get_gemini_analysis(
    ai_file
):

    if not ai_file.exists():

        return None

    try:

        data = load_json(
            ai_file
        )

    except Exception as error:

        print(
            f"  Could not read AI file: {error}"
        )

        return None

    # IMPORTANT:
    # Gemini analysis is nested inside
    # the "analysis" field.

    analysis = data.get(
        "analysis"
    )

    if isinstance(
        analysis,
        dict
    ):

        return analysis

    return None


# ============================================================
# NON-LABOUR DOCUMENTS
# ============================================================

def is_known_non_labour_document(
    document
):

    title = clean_text(
        document.get(
            "title"
        )
    ).lower()

    text = get_document_text(
        document
    ).lower()

    combined = (
        title
        + " "
        + text
    )

    # --------------------------------------------------------
    # Traffic / flyover
    # --------------------------------------------------------

    traffic_terms = [
        "flyover",
        "flyovers",
        "traffic restriction",
        "traffic restrictions",
        "ಸರಕು ಸಾಗಾಣಿಕೆ",
        "ದ್ವಿಚಕ್ರ ವಾಹನ"
    ]

    for term in traffic_terms:

        if term.lower() in combined:

            return True

    # --------------------------------------------------------
    # Veterinary seniority list
    # --------------------------------------------------------

    veterinary_terms = [
        "veterinary",
        "veterinary officer",
        "ಪಶುವೈದ್ಯ",
        "ಪಶುಪಾಲನಾ",
        "ಜೇಷ್ಠತಾ ಪಟ್ಟಿ"
    ]

    for term in veterinary_terms:

        if term.lower() in combined:

            return True

    return False


# ============================================================
# FALLBACK ANALYSIS
# ============================================================

def build_fallback_analysis(
    document
):

    title = clean_text(
        document.get(
            "title"
        )
    )

    document_number = clean_text(
        document.get(
            "document_number"
        )
    )

    existing_type = clean_text(
        document.get(
            "document_type"
        )
    )

    topics = document.get(
        "topics",
        []
    )

    publication_date = document.get(
        "publication_date"
    )

    effective_date = document.get(
        "effective_date"
    )

    text = get_document_text(
        document
    )

    lower_text = text.lower()

    # --------------------------------------------------------
    # DOCUMENT TYPE
    # --------------------------------------------------------

    document_type = existing_type

    if (
        "corrigendum" in lower_text
        or "corrigendum" in title.lower()
    ):

        document_type = "Corrigendum"

    elif (
        "draft" in title.lower()
        or "draft" in lower_text[:5000]
    ):

        document_type = "Draft Rules"

    elif (
        "rules" in title.lower()
        or "ನಿಯಮ" in title
    ):

        document_type = "Rules"

    elif (
        "notification" in title.lower()
        or "notification" in lower_text[:3000]
        or "ಅಧಿಸೂಚನೆ" in title
    ):

        document_type = "Notification"

    if not document_type:

        document_type = "Notification"

    # --------------------------------------------------------
    # TOPIC
    # --------------------------------------------------------

    topic = "Other Labour Law"

    if isinstance(
        topics,
        list
    ) and topics:

        topic = " / ".join(
            str(item)
            for item in topics
        )

    elif topics:

        topic = str(
            topics
        )

    if (
        "minimum wage" in lower_text
        or "minimum wages" in lower_text
        or "ಕನಿಷ್ಠ ವೇತನ" in text
    ):

        topic = "Wages / Minimum Wages"

    elif (
        "gig worker" in lower_text
        or "gig workers" in lower_text
        or "ಗಿಗ್ ಕಾರ್ಮಿಕ" in text
    ):

        topic = "Social Security"

    elif (
        "motor transport" in lower_text
        or "motor transport worker" in lower_text
    ):

        topic = "Motor Transport Workers"

    # --------------------------------------------------------
    # DRAFT
    # --------------------------------------------------------

    is_draft = False

    if (
        "draft" in title.lower()
        or "draft" in lower_text[:5000]
    ):

        is_draft = True

    # --------------------------------------------------------
    # HEADLINE
    # --------------------------------------------------------

    headline = title

    # Known 9467 corrigendum.
    if (
        document_number == "9467"
    ):

        headline = (
            "Karnataka issues corrigendum "
            "to Platform Based Gig Workers "
            "(Social Security and Welfare) "
            "Rules, 2025"
        )

    # --------------------------------------------------------
    # SPECIAL TITLES FOR DOCUMENTS WHERE
    # THE WEBSITE SEARCH RETURNED ONLY
    # "DEPUTY SECRETARY TWO"
    # --------------------------------------------------------

    if title == "DEPUTY SECRETARY TWO":

        if document_number == "9848":

            headline = (
                "Karnataka Labour Department "
                "publishes Gazette notification "
                "dated 30 January 2026"
            )

        elif document_number == "9865":

            headline = (
                "Karnataka Labour Department "
                "publishes notification concerning "
                "motor transport workers"
            )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    if (
        document_number == "9467"
    ):

        summary = (
            "The Karnataka e-Gazette publishes "
            "a corrigendum to the Karnataka "
            "Platform Based Gig Workers "
            "(Social Security and Welfare) "
            "Rules, 2025."
        )

    elif is_draft:

        summary = (
            "The Karnataka e-Gazette publishes "
            "a draft labour-law instrument for "
            "public consideration."
        )

    else:

        summary = (
            "The Karnataka e-Gazette publishes "
            "a labour-related notification or "
            "rules under the Karnataka Labour "
            "Department."
        )

    # --------------------------------------------------------
    # WHAT CHANGED
    # --------------------------------------------------------

    what_changed = (
        "The Gazette document contains the "
        "legal text of the notification or "
        "rules and should be read in full."
    )

    if (
        document_number == "9467"
    ):

        what_changed = (
            "The corrigendum removes the words "
            "\"Ride Hailing-2W Including SAS "
            "model\" from the 'Category' heading "
            "in Part-B of Form A of the "
            "Karnataka Platform Based Gig "
            "Workers (Social Security and "
            "Welfare) Rules, 2025."
        )

    # --------------------------------------------------------
    # AFFECTED PERSONS
    # --------------------------------------------------------

    affected = []

    if (
        "gig worker" in lower_text
        or "gig workers" in lower_text
        or "ಗಿಗ್ ಕಾರ್ಮಿಕ" in text
    ):

        affected = [
            "Platform-based gig workers",
            "Relevant aggregators/platforms"
        ]

    elif (
        "minimum wage" in lower_text
        or "minimum wages" in lower_text
        or "ಕನಿಷ್ಠ ವೇತನ" in text
    ):

        affected = [
            "Employers",
            "Workers covered by the relevant "
            "minimum wages"
        ]

    elif (
        "motor transport" in lower_text
    ):

        affected = [
            "Motor transport workers",
            "Relevant employers"
        ]

    # --------------------------------------------------------
    # ACTION
    # --------------------------------------------------------

    if (
        document_number == "9467"
    ):

        action_required = (
            "Review the corrigendum together "
            "with the underlying Karnataka "
            "Platform Based Gig Workers Rules, "
            "2025."
        )

    else:

        action_required = (
            "Review the Gazette document to "
            "determine whether any action is "
            "required."
        )

    # --------------------------------------------------------
    # ACT / RULE NAME
    # --------------------------------------------------------

    act_name = None

    rules_name = None

    if (
        "rules" in title.lower()
        or "ನಿಯಮ" in title
    ):

        rules_name = title

    elif (
        "act" in title.lower()
        or "ಅಧಿನಿಯಮ" in title
    ):

        act_name = title

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "headline": headline,

        "summary": summary,

        "what_changed": what_changed,

        "document_type": document_type,

        "topic": topic,

        "publication_date": publication_date,

        "effective_date": effective_date,

        "act_name": act_name,

        "rules_name": rules_name,

        "sections": [],

        "who_is_affected": affected,

        "action_required": action_required,

        "is_draft": is_draft,

        "is_labour_law_relevant": True
    }


# ============================================================
# DESCRIPTION
# ============================================================

def build_description(
    analysis
):

    summary = clean_text(
        analysis.get(
            "summary"
        )
    )

    what_changed = clean_text(
        analysis.get(
            "what_changed"
        )
    )

    action_required = clean_text(
        analysis.get(
            "action_required"
        )
    )

    parts = []

    if summary:

        parts.append(
            summary
        )

    if what_changed:

        parts.append(
            "What changed: "
            + what_changed
        )

    if action_required:

        parts.append(
            "Action: "
            + action_required
        )

    return "\n\n".join(
        parts
    )


# ============================================================
# IMPORT / UPDATE DATABASE RECORD
# ============================================================

def import_record(
    connection,
    analysis,
    metadata
):

    cursor = connection.cursor()

    document_url = clean_text(
        metadata.get(
            "document_url"
        )
    )

    publication_date = (
        analysis.get(
            "publication_date"
        )
        or metadata.get(
            "publication_date"
        )
    )

    effective_date = (
        analysis.get(
            "effective_date"
        )
        or metadata.get(
            "effective_date"
        )
    )

    title = (
        clean_text(
            analysis.get(
                "headline"
            )
        )
        or clean_text(
            metadata.get(
                "title"
            )
        )
    )

    update_type = (
        clean_text(
            analysis.get(
                "document_type"
            )
        )
        or "Notification"
    )

    topic = clean_text(
        analysis.get(
            "topic"
        )
    )

    description = build_description(
        analysis
    )

    source_url = (
        metadata.get(
            "source_url"
        )
        or SOURCE_URL
    )

    # --------------------------------------------------------
    # EXISTING RECORD BY DOCUMENT URL
    # --------------------------------------------------------

    if document_url:

        cursor.execute(
            """
            SELECT id
            FROM updates
            WHERE document_url = ?
            """,
            (
                document_url,
            )
        )

        existing = cursor.fetchone()

        if existing:

            cursor.execute(
                """
                UPDATE updates
                SET
                    jurisdiction = ?,
                    update_type = ?,
                    topic = ?,
                    title = ?,
                    description = ?,
                    publication_date = ?,
                    effective_date = ?,
                    source = ?,
                    source_url = ?,
                    document_url = ?
                WHERE id = ?
                """,
                (
                    "Karnataka",
                    update_type,
                    topic,
                    title,
                    description,
                    publication_date,
                    effective_date,
                    SOURCE_NAME,
                    source_url,
                    document_url,
                    existing["id"]
                )
            )

            return (
                "updated",
                existing["id"]
            )

    # --------------------------------------------------------
    # INSERT
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT INTO updates (
            jurisdiction,
            update_type,
            topic,
            title,
            description,
            publication_date,
            effective_date,
            source,
            source_url,
            document_url,
            importance
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Karnataka",
            update_type,
            topic,
            title,
            description,
            publication_date,
            effective_date,
            SOURCE_NAME,
            source_url,
            document_url,
            "Normal"
        )
    )

    return (
        "inserted",
        cursor.lastrowid
    )


# ============================================================
# CLEAN OLD BAD KARNATAKA RECORDS
# ============================================================

def clean_old_bad_records(
    connection
):

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Remove the raw search-table artifact.
    # --------------------------------------------------------

    cursor.execute(
        """
        DELETE FROM updates
        WHERE jurisdiction = 'Karnataka'
        AND title LIKE 'ಕ್ರ.ಸಂ.%'
        """
    )

    raw_deleted = cursor.rowcount

    # --------------------------------------------------------
    # Remove the old bad "DEPUTY SECRETARY TWO"
    # records. They will be re-imported correctly.
    # --------------------------------------------------------

    cursor.execute(
        """
        DELETE FROM updates
        WHERE jurisdiction = 'Karnataka'
        AND title = 'DEPUTY SECRETARY TWO'
        """
    )

    deputy_deleted = cursor.rowcount

    return (
        raw_deleted,
        deputy_deleted
    )


# ============================================================
# MAIN
# ============================================================

def main():

    create_database()

    connection = get_connection()

    print("")
    print("========================================")
    print("       KARNATAKA DATABASE IMPORT")
    print("========================================")
    print("")

    print(
        f"Extracted directory:"
    )

    print(
        EXTRACTED_DIR
    )

    print("")

    print(
        f"AI directory:"
    )

    print(
        AI_DIR
    )

    print("")

    # --------------------------------------------------------
    # CLEAN OLD BAD DATA
    # --------------------------------------------------------

    raw_deleted, deputy_deleted = (
        clean_old_bad_records(
            connection
        )
    )

    print(
        f"Removed old raw-table records: "
        f"{raw_deleted}"
    )

    print(
        f"Removed old DEPUTY SECRETARY TWO "
        f"records: {deputy_deleted}"
    )

    print("")

    # --------------------------------------------------------
    # FILES
    # --------------------------------------------------------

    extracted_files = sorted(
        EXTRACTED_DIR.glob("*.json")
    )

    print(
        f"Extracted files found: "
        f"{len(extracted_files)}"
    )

    print("")

    inserted = 0

    updated = 0

    skipped = 0

    # ========================================================
    # PROCESS
    # ========================================================

    for index, extracted_file in enumerate(
        extracted_files,
        start=1
    ):

        print(
            f"[{index}/{len(extracted_files)}] "
            f"{extracted_file.name}"
        )

        # ----------------------------------------------------
        # LOAD
        # ----------------------------------------------------

        try:

            document = load_json(
                extracted_file
            )

        except Exception as error:

            print(
                f"  ERROR: {error}"
            )

            print("")

            continue

        title = clean_text(
            document.get(
                "title"
            )
        )

        document_number = clean_text(
            document.get(
                "document_number"
            )
        )

        print(
            f"  Document number: "
            f"{document_number}"
        )

        print(
            f"  Original title: "
            f"{title}"
        )

        # ----------------------------------------------------
        # RAW SEARCH TABLE
        # ----------------------------------------------------

        if (
            "ಕ್ರ.ಸಂ." in title
            or (
                "Labour Department" in title
                and
                "DEPUTY SECRETARY TWO" in title
            )
        ):

            print(
                "  SKIPPED: raw search-result table"
            )

            skipped += 1

            print("")

            continue

        # ----------------------------------------------------
        # NON-LABOUR
        # ----------------------------------------------------

        if is_known_non_labour_document(
            document
        ):

            print(
                "  SKIPPED: non-labour document"
            )

            skipped += 1

            print("")

            continue

        # ----------------------------------------------------
        # GET GEMINI ANALYSIS
        # ----------------------------------------------------

        ai_file = get_ai_file(
            extracted_file
        )

        analysis = get_gemini_analysis(
            ai_file
        )

        if analysis is not None:

            print(
                "  Analysis: Gemini"
            )

        else:

            print(
                "  Analysis: fallback"
            )

            analysis = (
                build_fallback_analysis(
                    document
                )
            )

        # ----------------------------------------------------
        # LABOUR RELEVANCE
        # ----------------------------------------------------

        if (
            analysis.get(
                "is_labour_law_relevant"
            ) is False
        ):

            print(
                "  SKIPPED: Gemini marked "
                "this as non-labour"
            )

            skipped += 1

            print("")

            continue

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        metadata = {

            "title": document.get(
                "title"
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

        # ----------------------------------------------------
        # IMPORT
        # ----------------------------------------------------

        result, record_id = import_record(
            connection,
            analysis,
            metadata
        )

        if result == "inserted":

            inserted += 1

            print(
                f"  INSERTED: database ID "
                f"{record_id}"
            )

        else:

            updated += 1

            print(
                f"  UPDATED: database ID "
                f"{record_id}"
            )

        print(
            f"  Website title: "
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

        print("")

    # ========================================================
    # COMMIT
    # ========================================================

    connection.commit()

    # ========================================================
    # FINAL COUNT
    # ========================================================

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            jurisdiction,
            COUNT(*) AS count
        FROM updates
        GROUP BY jurisdiction
        ORDER BY jurisdiction
        """
    )

    jurisdiction_counts = (
        cursor.fetchall()
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM updates
        """
    )

    total = cursor.fetchone()[0]

    connection.close()

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("")
    print("========================================")
    print("          IMPORT COMPLETE")
    print("========================================")
    print("")

    print(
        f"Inserted: {inserted}"
    )

    print(
        f"Updated: {updated}"
    )

    print(
        f"Skipped: {skipped}"
    )

    print("")

    print(
        "Records by jurisdiction:"
    )

    for row in jurisdiction_counts:

        print(
            f"  {row['jurisdiction']}: "
            f"{row['count']}"
        )

    print("")

    print(
        f"Total records in database: "
        f"{total}"
    )

    print("")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()