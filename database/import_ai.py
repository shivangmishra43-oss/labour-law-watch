import json
import sqlite3
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_NAME = "labourlawwatch.db"

AI_SUMMARY_FOLDER = (
    Path("downloads")
    / "egazette"
    / "ai_summaries"
)

SOURCE_NAME = "eGazette"

SOURCE_SEARCH_URL = (
    "https://egazette.gov.in/SearchMenu.aspx"
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# HELPERS
# ============================================================

def load_json(file_path):
    """Load one AI summary JSON file."""

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def get_gazette_id(data, file_path):
    """
    Get Gazette ID from the AI JSON.

    If the JSON does not contain it, derive it from
    the filename.
    """

    gazette_id = data.get("gazette_id")

    if gazette_id:
        return str(gazette_id).strip()

    filename = file_path.stem

    if filename.endswith("_ai"):
        filename = filename[:-3]

    return filename


def get_pdf_url(data, gazette_id):
    """
    Get the actual eGazette PDF URL.

    First, use a PDF URL already present in the JSON.

    If one is not present, construct the correct eGazette
    URL from the Gazette ID.

    Example:

    CG-DL-E-09092026-276091

    becomes:

    https://egazette.gov.in/WriteReadData/2026/276091.pdf
    """

    possible_keys = [
        "document_url",
        "pdf_url",
        "gazette_pdf_url"
    ]

    for key in possible_keys:

        value = data.get(key)

        if value:

            value = str(value).strip()

            if ".pdf" in value.lower():

                return value

    # --------------------------------------------------------
    # Construct URL from Gazette ID
    # --------------------------------------------------------

    if gazette_id.startswith("CG-DL-E-"):

        parts = gazette_id.split("-")

        # Expected:
        #
        # CG-DL-E-DDMMYYYY-NNNNNN
        #
        # Example:
        #
        # CG-DL-E-09092026-276091

        if len(parts) >= 5:

            date_part = parts[3]
            document_number = parts[4]

            if (
                date_part.isdigit()
                and len(date_part) == 8
                and document_number.isdigit()
            ):

                year = date_part[-4:]

                return (
                    "https://egazette.gov.in/"
                    f"WriteReadData/{year}/"
                    f"{document_number}.pdf"
                )

    return ""


def get_source_url():
    """Official eGazette search page."""

    return SOURCE_SEARCH_URL


def combine_description(data):
    """
    Combine AI-generated information into one database
    description.

    This allows the existing database schema to remain
    simple while retaining the useful AI analysis.
    """

    parts = []

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = data.get("summary")

    if summary:

        parts.append(
            "Summary:\n"
            + str(summary).strip()
        )

    # --------------------------------------------------------
    # What changed
    # --------------------------------------------------------

    what_changed = data.get("what_changed")

    if what_changed:

        parts.append(
            "What changed:\n"
            + str(what_changed).strip()
        )

    # --------------------------------------------------------
    # Provisions
    # --------------------------------------------------------

    provisions = data.get("provisions")

    if provisions:

        if isinstance(provisions, list):

            provisions_text = "\n".join(
                f"- {item}"
                for item in provisions
            )

        else:

            provisions_text = str(provisions)

        parts.append(
            "Provisions:\n"
            + provisions_text.strip()
        )

    # --------------------------------------------------------
    # Who is affected
    # --------------------------------------------------------

    affected = data.get("affected")

    if affected:

        if isinstance(affected, list):

            affected_text = "\n".join(
                f"- {item}"
                for item in affected
            )

        else:

            affected_text = str(affected)

        parts.append(
            "Who is affected:\n"
            + affected_text.strip()
        )

    # --------------------------------------------------------
    # Action required
    # --------------------------------------------------------

    actions = data.get("actions")

    if actions:

        if isinstance(actions, list):

            actions_text = "\n".join(
                f"- {item}"
                for item in actions
            )

        else:

            actions_text = str(actions)

        parts.append(
            "Action required:\n"
            + actions_text.strip()
        )

    return "\n\n".join(parts)


def find_existing_gazette(cursor, gazette_id):
    """
    Find an existing database record for this Gazette.

    We primarily identify a Gazette using its PDF URL or
    Gazette ID.
    """

    pdf_url = get_pdf_url(
        {},
        gazette_id
    )

    # --------------------------------------------------------
    # First: search by PDF URL
    # --------------------------------------------------------

    if pdf_url:

        cursor.execute(
            """
            SELECT *
            FROM updates
            WHERE source = ?
            AND document_url = ?
            LIMIT 1
            """,
            (
                SOURCE_NAME,
                pdf_url
            )
        )

        row = cursor.fetchone()

        if row:
            return row

    # --------------------------------------------------------
    # Second: search for Gazette ID anywhere in the
    # source/document URLs.
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM updates
        WHERE source = ?
        AND (
            source_url LIKE ?
            OR document_url LIKE ?
        )
        LIMIT 1
        """,
        (
            SOURCE_NAME,
            f"%{gazette_id}%",
            f"%{gazette_id}%"
        )
    )

    return cursor.fetchone()


# ============================================================
# UPDATE EXISTING RECORD
# ============================================================

def update_existing_record(
    cursor,
    existing_row,
    data,
    gazette_id
):
    """
    Update the existing Gazette record with the AI
    information.

    IMPORTANT:

    We preserve existing good metadata such as publication
    date, effective date and topic when the AI JSON does not
    contain those values.
    """

    # --------------------------------------------------------
    # Existing values
    # --------------------------------------------------------

    existing_publication_date = (
        existing_row["publication_date"]
    )

    existing_effective_date = (
        existing_row["effective_date"]
    )

    existing_topic = (
        existing_row["topic"]
    )

    existing_update_type = (
        existing_row["update_type"]
    )

    existing_importance = (
        existing_row["importance"]
    )

    # --------------------------------------------------------
    # AI values
    # --------------------------------------------------------

    publication_date = data.get(
        "publication_date"
    )

    if not publication_date:
        publication_date = existing_publication_date

    effective_date = data.get(
        "effective_date"
    )

    if not effective_date:
        effective_date = existing_effective_date

    topic = data.get("topic")

    if not topic or topic == "Other":
        topic = existing_topic

    update_type = data.get(
        "update_type"
    )

    if not update_type:
        update_type = existing_update_type

    importance = data.get(
        "importance"
    )

    if not importance:
        importance = existing_importance

    # --------------------------------------------------------
    # Better title from AI
    # --------------------------------------------------------

    title = (
        data.get("headline")
        or data.get("title")
        or existing_row["title"]
    )

    # --------------------------------------------------------
    # AI description
    # --------------------------------------------------------

    description = combine_description(
        data
    )

    if not description:

        description = existing_row[
            "description"
        ]

    # --------------------------------------------------------
    # PDF URL
    # --------------------------------------------------------

    pdf_url = get_pdf_url(
        data,
        gazette_id
    )

    if not pdf_url:

        pdf_url = existing_row[
            "document_url"
        ]

    # --------------------------------------------------------
    # Source URL
    # --------------------------------------------------------

    source_url = get_source_url()

    # --------------------------------------------------------
    # UPDATE database row
    # --------------------------------------------------------

    cursor.execute(
        """
        UPDATE updates

        SET
            update_type = ?,
            topic = ?,
            title = ?,
            description = ?,
            publication_date = ?,
            effective_date = ?,
            source_url = ?,
            document_url = ?,
            importance = ?

        WHERE id = ?
        """,
        (
            update_type,
            topic,
            title,
            description,
            publication_date,
            effective_date,
            source_url,
            pdf_url,
            importance,
            existing_row["id"]
        )
    )

    print(
        f"UPDATED: {gazette_id}"
    )

    print(
        f"  Database ID: {existing_row['id']}"
    )

    print(
        f"  Title: {title}"
    )

    print(
        f"  Topic: {topic}"
    )

    print(
        f"  Publication: {publication_date}"
    )

    print(
        f"  Effective: {effective_date}"
    )

    print(
        f"  PDF: {pdf_url}"
    )

    return "updated"


# ============================================================
# IMPORT NEW RECORD
# ============================================================

def insert_new_record(
    cursor,
    data,
    gazette_id
):
    """
    Insert a Gazette only when it genuinely does not
    already exist in the database.
    """

    jurisdiction = data.get(
        "jurisdiction",
        "Central"
    )

    update_type = data.get(
        "update_type",
        "Notification"
    )

    topic = data.get(
        "topic",
        "Other"
    )

    title = (
        data.get("headline")
        or data.get("title")
        or gazette_id
    )

    description = combine_description(
        data
    )

    publication_date = data.get(
        "publication_date"
    )

    effective_date = data.get(
        "effective_date"
    )

    importance = data.get(
        "importance",
        "Normal"
    )

    source_url = get_source_url()

    pdf_url = get_pdf_url(
        data,
        gazette_id
    )

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
            jurisdiction,
            update_type,
            topic,
            title,
            description,
            publication_date,
            effective_date,
            SOURCE_NAME,
            source_url,
            pdf_url,
            importance
        )
    )

    print(
        f"IMPORTED NEW: {gazette_id}"
    )

    print(
        f"  Title: {title}"
    )

    print(
        f"  PDF: {pdf_url}"
    )

    return "imported"


# ============================================================
# PROCESS ONE FILE
# ============================================================

def process_file(cursor, file_path):

    data = load_json(
        file_path
    )

    gazette_id = get_gazette_id(
        data,
        file_path
    )

    if not gazette_id:

        raise ValueError(
            "Could not determine Gazette ID."
        )

    # --------------------------------------------------------
    # Look for existing Gazette
    # --------------------------------------------------------

    existing_row = find_existing_gazette(
        cursor,
        gazette_id
    )

    if existing_row:

        return update_existing_record(
            cursor,
            existing_row,
            data,
            gazette_id
        )

    # --------------------------------------------------------
    # If it doesn't exist, insert it
    # --------------------------------------------------------

    return insert_new_record(
        cursor,
        data,
        gazette_id
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("")
    print("========================================")
    print("       AI → DATABASE IMPORTER")
    print("========================================")
    print("")

    if not AI_SUMMARY_FOLDER.exists():

        print(
            "ERROR: AI summary folder does not exist:"
        )

        print(
            AI_SUMMARY_FOLDER.resolve()
        )

        return

    files = sorted(
        AI_SUMMARY_FOLDER.glob(
            "*_ai.json"
        )
    )

    print(
        f"AI summary files found: {len(files)}"
    )

    if not files:

        print("")
        print(
            "Nothing to import."
        )

        return

    connection = get_connection()
    cursor = connection.cursor()

    updated = 0
    imported = 0
    failed = 0

    for file_path in files:

        try:

            result = process_file(
                cursor,
                file_path
            )

            if result == "updated":
                updated += 1

            elif result == "imported":
                imported += 1

        except Exception as error:

            failed += 1

            print("")
            print(
                f"FAILED: {file_path.name}"
            )

            print(
                f"  Error: {error}"
            )

    connection.commit()
    connection.close()

    print("")
    print("========================================")
    print("              IMPORT COMPLETE")
    print("========================================")
    print("")

    print(
        f"Updated existing: {updated}"
    )

    print(
        f"Imported new:     {imported}"
    )

    print(
        f"Failed:           {failed}"
    )

    print("")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()