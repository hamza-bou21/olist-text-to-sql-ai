import os
import sqlite3
import pandas as pd
import chromadb
from chromadb.errors import NotFoundError
from google import genai
from dotenv import load_dotenv

# Load environment variables (.env file)
load_dotenv()

def get_relevant_schemas(user_question):
    """Queries ChromaDB to find the tables most relevant to the user's question.
    Includes a self-healing fallback to initialize the collection if it doesn't exist.
    """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        # Attempt to grab the existing collection
        collection = chroma_client.get_collection(name="olist_schema_collection")
    except (NotFoundError, ValueError, Exception):
        # Fallback: Collection does not exist (Cloud environment cold-start init)
        print("⚠️ ChromaDB collection not found on server. Initializing vector embeddings on-the-fly...")
        collection = chroma_client.create_collection(name="olist_schema_collection")
        
        # Pull your raw schemas from schema_docs to build the collection dynamically
        from schema_docs import OLIST_SCHEMAS
        
        for table_name, schema_text in OLIST_SCHEMAS.items():
            collection.add(
                documents=[schema_text],
                metadatas=[{"table_name": table_name}],
                ids=[table_name]
            )
        print("✅ ChromaDB collection initialized and populated successfully.")

    # Search ChromaDB for the top 3 most relevant table schemas
    results = collection.query(
        query_texts=[user_question],
        n_results=3
    )
    
    # Combine the retrieved table descriptions into a single context string
    schemas_context = ""
    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
        table_name = metadata['table_name']
        schemas_context += f"Table: {table_name}\nDescription: {doc}\n\n"
        
    return schemas_context

def generate_sql(user_question, schemas_context):
    """Uses Gemini to translate the plain English question into structured SQL."""
    client = genai.Client()
    
    # The system prompt instructions that govern how Gemini writes the code
    system_prompt = (
        "You are an expert data analyst and SQLite database administrator.\n"
        "Your task is to convert a user's natural language question into a single, syntactically correct SQLite query.\n"
        "Use the provided table schemas to understand the database layout and column names.\n"
        "CRITICAL: Return ONLY the raw SQL query. Do not wrap it in markdown code blocks like ```sql ... ```. "
        "Do not include any explanations, text, or introductions. Just the SQL code."
    )
    
    user_prompt = f"""
    Database Table Schemas:
    {schemas_context}
    
    User Question:
    "{user_question}"
    
    SQL Query:
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=user_prompt,
        config={'system_instruction': system_prompt}
    )
    
    # Clean up any unexpected whitespaces or markdown blocks if the LLM slips up
    sql_query = response.text.strip().replace("```sql", "").replace("```", "")
    return sql_query

def execute_sql(sql_query):
    """Executes the generated SQL query against the local SQLite database in STRICT READ-ONLY mode."""
    
    # --- LAYER 1: Text-Level Guardrails ---
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "REPLACE"]
    query_upper = sql_query.upper()
    
    for keyword in forbidden_keywords:
        # Quick check to ensure the keyword isn't smuggled inside the query text
        if keyword in query_upper:
            return f"❌ Security Exception: Generated query attempted a forbidden action ({keyword})."
            
    # --- LAYER 2: Database-Level Read-Only Enforcement ---
    try:
        # Using a URI connection string with '?mode=ro' forces SQLite to reject any write operations
        db_uri = "file:olist.db?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        
        # Load the SQL query results into a Pandas DataFrame
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df
        
    except sqlite3.OperationalError as e:
        if "attempt to write a readonly database" in str(e):
            return "❌ Security Exception: Database is locked in read-only mode. Write actions are prohibited."
        return f"❌ SQL Operational Error: {e}"
        
    except Exception as e:
        return f"❌ Unexpected Error: {e}"

def ask_database(user_question):
    """The master pipeline combining retrieval, generation, and execution."""
    print(f"\n--- Processing Question: '{user_question}' ---")
    
    # Step 1: Semantic Retrieval from ChromaDB
    print("⏳ Retrieving table blueprints from ChromaDB...")
    context = get_relevant_schemas(user_question)
    
    # Step 2: Code Generation using Gemini
    print("🤖 Generating SQL query with Gemini...")
    sql = generate_sql(user_question, context)
    print(f"👉 Generated SQL:\n{sql}\n")
    
    # Step 3: Execution against SQLite
    print("📊 Executing query against olist.db...")
    result = execute_sql(sql)
    return result, sql

# Update the test harness at the very bottom of query_pipeline.py
if __name__ == "__main__":
    # A healthy, normal question to test your backend locally
    test_question = "What are the top 5 states with the highest total sales volume?"
    
    # Correctly unpack BOTH values from the tuple we just created
    df_result, generated_sql = ask_database(test_question)
    
    print("\n🤖 Generated SQL Query:")
    print(generated_sql)
    
    print("\n🏆 Results Table:")
    print(df_result)