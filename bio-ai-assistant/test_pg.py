import os
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

TZ_INFO = os.getenv("TZ", "Australia/Melbourne")
tz = ZoneInfo(TZ_INFO)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS feedback")
            cur.execute("DROP TABLE IF EXISTS conversations")

            cur.execute("""
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    response_time FLOAT NOT NULL,
                    relevance TEXT NOT NULL,
                    relevance_explanation TEXT NOT NULL,
                    prompt_characters INTEGER NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    candidates_characters INTEGER NOT NULL,
                    candidates_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    eval_prompt_tokens INTEGER NOT NULL,
                    eval_candidates_tokens INTEGER NOT NULL,
                    eval_total_tokens INTEGER NOT NULL,
                    gemini_cost FLOAT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE feedback (
                    id SERIAL PRIMARY KEY,
                    conversation_id TEXT REFERENCES conversations(id),
                    feedback INTEGER NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()

def save_conversation(conversation_id, question, answer_data, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(tz)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations
                (id, question, answer, model_used, response_time, relevance,
                relevance_explanation, prompt_characters, prompt_tokens, candidates_characters, candidates_tokens, total_tokens,
                eval_prompt_tokens, eval_candidates_tokens, eval_total_tokens, gemini_cost, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    conversation_id,
                    question,
                    answer_data["answer"],
                    answer_data["model_used"],
                    answer_data["response_time"],
                    answer_data["relevance"],
                    answer_data["relevance_explanation"],
                    answer_data["prompt_characters"],
                    answer_data["prompt_tokens"],
                    answer_data["candidates_characters"],
                    answer_data["candidates_tokens"],
                    answer_data["total_tokens"],
                    answer_data["eval_prompt_tokens"],
                    answer_data["eval_candidates_tokens"],
                    answer_data["eval_total_tokens"],
                    answer_data["gemini_cost"],
                    timestamp
                ),
            )
        conn.commit()
        return True  # Return True to indicate successful save
    except (Exception, psycopg2.Error) as error:
        # Log the error or handle it as needed
        print(f"Error saving conversation: {error}")
        return False  # Return False to indicate an error occurred
    finally:
        conn.close()

def save_feedback(conversation_id, feedback, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(tz)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedback (conversation_id, feedback, timestamp) VALUES (%s, %s, COALESCE(%s, CURRENT_TIMESTAMP))",
                (conversation_id, feedback, timestamp),
            )
        conn.commit()
        return True  # Return True to indicate successful save
    except (Exception, psycopg2.Error) as error:
        # Log the error or handle it as needed
        print(f"Error saving feedback: {error}")
        return False  # Return False to indicate an error occurred
    finally:
        conn.close()

def check_tables():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = cur.fetchall()
            print("Tables in the public schema:")
            for table in tables:
                print(table[0])
    finally:
        conn.close()

if __name__ == "__main__":
    print("Initializing database...")
    #init_db()

    print("Checking tables...")
    check_tables()

    print("Saving a test conversation...")
    test_conversation_id = "test_conversation_2"
    test_question = "What is the capital of France?"
    test_answer_data = {
        "answer": "Paris",
        "model_used": "test_model",
        "response_time": 0.1,
        "relevance": "high",
        "relevance_explanation": "test explanation",
        "prompt_characters": 10,
        "prompt_tokens": 5,
        "candidates_characters": 20,
        "candidates_tokens": 10,
        "total_tokens": 15,
        "eval_prompt_tokens": 5,
        "eval_candidates_tokens": 10,
        "eval_total_tokens": 15,
        "gemini_cost": 0.01,
    }
    status = save_conversation(test_conversation_id, test_question, test_answer_data)
    if status:
        print("Conversation saved successfully.")
    else:
        print("Failed to save conversation.")

    print("Saving a test feedback...")
    test_feedback = 1
    status = save_feedback(test_conversation_id, test_feedback)
    if status:
        print("Feedback saved successfully.")
    else:
        print("Failed to save feedback.")