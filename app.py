from flask import Flask, jsonify, send_from_directory

from database import get_connection, create_database


app = Flask(
    __name__,
    static_folder="frontend",
    static_url_path=""
)


# ============================================================
# DATABASE
# ============================================================

create_database()


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def home():

    return send_from_directory(
        "frontend",
        "index.html"
    )


# ============================================================
# API — ALL UPDATES
# ============================================================

@app.route("/api/updates")
def get_updates():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM updates
        ORDER BY publication_date DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()


    updates = []

    for row in rows:

        updates.append(
            dict(row)
        )


    return jsonify(
        {
            "count": len(updates),
            "updates": updates
        }
    )


# ============================================================
# API — SINGLE UPDATE
# ============================================================

@app.route("/api/updates/<int:update_id>")
def get_update(
    update_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM updates
        WHERE id = ?
        """,
        (
            update_id,
        )
    )

    row = cursor.fetchone()

    connection.close()


    if row is None:

        return jsonify(
            {
                "error":
                    "Update not found"
            }
        ), 404


    return jsonify(
        dict(row)
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("")
    print("====================================")
    print("        LABOUR LAW WATCH")
    print("====================================")
    print("")
    print("Website:")
    print("http://localhost:8000")
    print("")
    print("API:")
    print("http://localhost:8000/api/updates")
    print("")
    print("")

    app.run(
        host="localhost",
        port=8000,
        debug=True
    )