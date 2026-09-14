import sqlite3


DATABASE_NAME = "labourlawwatch.db"


def main():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    print("")
    print("========================================")
    print("       FINAL DATABASE CLEANUP")
    print("========================================")
    print("")

    # Show current count
    cursor.execute("SELECT COUNT(*) FROM updates")
    before_count = cursor.fetchone()[0]

    print(f"Records before cleanup: {before_count}")

    # --------------------------------------------------------
    # Delete the two duplicate AI-imported records
    # --------------------------------------------------------

    cursor.execute("""
        DELETE FROM updates
        WHERE id IN (13, 14)
    """)

    deleted = cursor.rowcount

    connection.commit()

    # --------------------------------------------------------
    # Show final count
    # --------------------------------------------------------

    cursor.execute("SELECT COUNT(*) FROM updates")
    after_count = cursor.fetchone()[0]

    print(f"Duplicate records deleted: {deleted}")
    print(f"Records after cleanup: {after_count}")

    # --------------------------------------------------------
    # Display remaining records
    # --------------------------------------------------------

    print("")
    print("REMAINING RECORDS")
    print("-" * 70)

    cursor.execute("""
        SELECT
            id,
            title,
            topic,
            update_type,
            publication_date,
            effective_date,
            importance,
            source,
            document_url
        FROM updates
        ORDER BY publication_date DESC
    """)

    rows = cursor.fetchall()

    for row in rows:

        print(f"ID: {row[0]}")
        print(f"Title: {row[1]}")
        print(f"Topic: {row[2]}")
        print(f"Type: {row[3]}")
        print(f"Publication date: {row[4]}")
        print(f"Effective date: {row[5]}")
        print(f"Importance: {row[6]}")
        print(f"Source: {row[7]}")
        print(f"PDF: {row[8]}")
        print("-" * 70)

    connection.close()

    print("")
    print("========================================")
    print("         CLEANUP COMPLETE")
    print("========================================")
    print("")


if __name__ == "__main__":
    main()