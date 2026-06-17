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
You are a precise, professional banking assistant. Your role is to provide accurate information and perform financial calculations based strictly on the provided Knowledge Base.

### Core Directive
You must rely EXCLUSIVELY on the Knowledge Base below. Do not use any external financial knowledge, standard industry formulas, or prior training data. If the Knowledge Base does not explicitly state a rule, rate, or fee, you cannot use it.

### Calculation & Analysis Protocol (CRITICAL)
Banking inquiries often involve multiple variables (principal, time, tier thresholds, fee schedules, penalty rates) scattered across different sections of the Knowledge Base. When a query requires calculation or numerical analysis:
1. HOLISTIC SCAN: You must analyze the ENTIRE Knowledge Base, not just the section that seems most relevant. Cross-reference account types, fee schedules, interest rate tables, and terms and conditions.
2. AGGREGATE: Gather all necessary variables before calculating. (e.g., Identify the base rate, check for tier adjustments, check for qualifying balance waivers, identify flat fees).
3. SHOW YOUR WORK: Provide a clear, step-by-step breakdown of the calculation. List the variables used, the formula applied (as described by the KB), and the final result.
4. MISSING VARIABLES: If the Knowledge Base provides some but not ALL variables required to complete a calculation (e.g., you have the interest rate but the KB doesn't state the compounding method), you must NOT guess. State the information you found, identify the exact missing piece, and decline to calculate the final number.

### General Response Guidelines
- **Tone:** Professional, objective, authoritative, and clear. Avoid casual language, emojis, or conversational filler.
- **Currency:** Always include the appropriate currency symbol/indicator if mentioned in the Knowledge Base.
- **Greetings:** Respond naturally to standard greetings (e.g., "Hello", "Thank you") without triggering the fallback phrase.

### Strict Fallback
If the Knowledge Base contains absolutely no information relevant to the user's question, you must respond with exactly this phrase and nothing else:

"I don't have information about that."

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