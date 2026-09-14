import sqlite3


DATABASE_NAME = "labourlawwatch.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)

    connection.row_factory = sqlite3.Row

    return connection


def create_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS updates (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            jurisdiction TEXT NOT NULL,

            update_type TEXT NOT NULL,

            topic TEXT,

            title TEXT NOT NULL,

            description TEXT,

            publication_date TEXT,

            effective_date TEXT,

            source TEXT NOT NULL,

            source_url TEXT,

            document_url TEXT,

            importance TEXT DEFAULT 'Normal',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    connection.commit()

    connection.close()


if __name__ == "__main__":

    create_database()

    print("Database created successfully!")
    print("Database file: labourlawwatch.db")