from groq import Groq
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=1)

DATABASE = "database.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():

    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS knowledge(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS chat_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def create_admin():

    conn = get_db()

    admin = conn.execute(
        "SELECT * FROM admin"
    ).fetchone()

    if not admin:

        conn.execute(
            """
            INSERT INTO admin
            (username,password)
            VALUES (?,?)
            """,
            ("admin", "admin123")
        )

        conn.commit()

    conn.close()

def load_knowledge():

    conn = get_db()

    rows = conn.execute(
        """
        SELECT title, content
        FROM knowledge
        """
    ).fetchall()

    conn.close()

    knowledge = ""

    for row in rows:

        knowledge += f"""
Title: {row['title']}

Content:
{row['content']}

--------------------
"""

    return knowledge

def ask_groq(question):

    knowledge = load_knowledge()

    prompt = f"""
You are a friendly and helpful customer support assistant for our company. You aim to resolve the customer's query quickly and accurately.

### Rules of Engagement
- Always maintain a warm, empathetic, and professional tone.
- You may only use the information provided in the Knowledge Base below. 
- If a customer asks about a feature, policy, or detail not mentioned in the text, you cannot make it up or guess.
- If you can answer part of their question, do so, but let them know you don't have the details for the other part.

### When to use the fallback
If the Knowledge Base has absolutely zero relevant information regarding the customer's question, respond exactly with:
"I don't have information about that."

*(Note: For simple pleasantries like "Hi" or "Thank you", respond naturally as a helpful agent would. Do not use the fallback phrase for greetings.)*

---
Knowledge Base:
{knowledge}

Question:
{question}
"""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.3,
        max_tokens=500
    )

    return response.choices[0].message.content