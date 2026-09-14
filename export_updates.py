import json
import sqlite3
from pathlib import Path


DATABASE_NAME = "labourlawwatch.db"
OUTPUT_FILE = Path("data") / "updates.json"


def export_updates():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            jurisdiction,
            update_type,
            topic,
            title,
            description,
            publication_date,
            effective_date,
            source,
            source_url,
            document_url
        FROM updates
        ORDER BY publication_date DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    updates = []

    for row in rows:
        updates.append(
            {
                "id": row["id"],
                "jurisdiction": row["jurisdiction"],
                "update_type": row["update_type"],
                "topic": row["topic"],
                "title": row["title"],
                "description": row["description"],
                "publication_date": row["publication_date"],
                "effective_date": row["effective_date"],
                "source": row["source"],
                "source_url": row["source_url"],
                "document_url": row["document_url"],
            }
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output = {
        "count": len(updates),
        "updates": updates
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("")
    print("========================================")
    print("       UPDATE EXPORT COMPLETE")
    print("========================================")
    print("")
    print(f"Updates exported: {len(updates)}")
    print(f"Output file: {OUTPUT_FILE}")
    print("")


if __name__ == "__main__":
    export_updates()