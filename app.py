from flask import *
from groq import Groq
from dotenv import load_dotenv
import sqlite3
import os
from decorators import create_admin, get_db, init_db, ask_groq

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

DATABASE = "database.db"

@app.route("/admin/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        admin = conn.execute(
            """
            SELECT * FROM admin
            WHERE username=? AND password=?
            """,
            (username, password)
        ).fetchone()

        conn.close()

        if admin:

            session["admin"] = admin["id"]

            return redirect("/admin")

        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/")

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/")

    conn = get_db()

    knowledge = conn.execute(
        "SELECT * FROM knowledge ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        knowledge=knowledge
    )

@app.route("/add_knowledge", methods=["POST"])
def add_knowledge():

    if "admin" not in session:
        return redirect("/")

    title = request.form["title"]
    content = request.form["content"]

    conn = get_db()

    conn.execute(
        """
        INSERT INTO knowledge
        (title, content)
        VALUES (?, ?)
        """,
        (title, content)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/api/knowledge/<int:id>", methods=["GET"])
def get_knowledge(id):

    if "admin" not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = get_db()

    item = conn.execute(
        """
        SELECT *
        FROM knowledge
        WHERE id=?
        """,
        (id,)
    ).fetchone()

    conn.close()

    if not item:
        return jsonify({
            "success": False,
            "message": "Knowledge not found"
        }), 404

    return jsonify({
        "success": True,
        "data": {
            "id": item["id"],
            "title": item["title"],
            "content": item["content"]
        }
    })

@app.route("/api/knowledge/<int:id>", methods=["PUT"])
def update_knowledge(id):

    if "admin" not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json()

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        return jsonify({
            "success": False,
            "message": "Title and content are required"
        }), 400

    conn = get_db()

    cursor = conn.execute(
        """
        UPDATE knowledge
        SET title=?, content=?
        WHERE id=?
        """,
        (title, content, id)
    )

    conn.commit()

    updated = cursor.rowcount > 0

    conn.close()

    if not updated:
        return jsonify({
            "success": False,
            "message": "Knowledge not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Knowledge updated successfully"
    })

@app.route("/api/knowledge/<int:id>", methods=["DELETE"])
def delete_knowledge(id):

    if "admin" not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = get_db()

    cursor = conn.execute(
        "DELETE FROM knowledge WHERE id=?",
        (id,)
    )

    conn.commit()

    deleted = cursor.rowcount > 0

    conn.close()

    if not deleted:
        return jsonify({
            "success": False,
            "message": "Knowledge not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Knowledge deleted successfully"
    })

@app.route("/")
def chat_page():
    return render_template("chat.html")

@app.route("/api/ask", methods=["POST"])
def ask_api():
    data = request.get_json()

    question = data.get("message", "").strip()

    if not question:
        return jsonify({
            "success": False,
            "message": "Question is required"
        }), 400

    answer = ask_groq(question)

    conn = get_db()

    conn.execute(
        """
        INSERT INTO chat_history (question, answer)
        VALUES (?, ?)
        """,
        (question, answer)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "answer": answer
    })


if __name__ == "__main__":
    init_db()
    create_admin()
    app.run(debug=True)