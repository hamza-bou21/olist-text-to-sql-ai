import os
import sqlite3
import pandas as pd
import chromadb
from chromadb.errors import NotFoundError
from google import genai
from google.genai import types
from groq import Groq  # Imported Groq SDK
from dotenv import load_dotenv
from schema_docs import TABLE_SCHEMAS

# Load environment variables (.env file)
load_dotenv()

def get_gemini_embedding(text):
    """Calls Google's cloud API to translate text into a mathematical vector.
    Kept here because Groq doesn't provide an embedding model endpoint.
    This keeps your local RAM 100% free of heavy machine learning models!
    """
    client = genai.Client()
    response = client.models.embed_content(
        model="gemini-embedding-001",  # Google's standard high-performance text embedding model
        contents=[text]
    )
    return response.embeddings[0].values

def get_relevant_schemas(user_question):
    """Queries ChromaDB to find the tables most relevant to the user's question.
    Uses cloud-offloaded vectors to stay 100% stable under cloud memory constraints.
    """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        collection = chroma_client.get_collection(name="olist_cloud_collection")
        if collection.count() != len(TABLE_SCHEMAS):
            chroma_client.delete_collection("olist_cloud_collection")
            raise NotFoundError
    except (NotFoundError, ValueError, Exception):
        print("⚠️ ChromaDB cache empty or out of sync. Initializing cloud-offloaded embeddings...")
        try:
            chroma_client.delete_collection("olist_cloud_collection")
        except Exception:
            pass
            
        collection = chroma_client.create_collection(name="olist_cloud_collection")
        
        # Loop through your tables from schema_docs.py
        for table_name, schema_text in TABLE_SCHEMAS.items():
            # Calculate the math vector using Google's cloud server
            table_vector = get_gemini_embedding(str(schema_text))
            
            # Pass the text AND the cloud-calculated vector directly to ChromaDB
            collection.add(
                documents=[str(schema_text)],
                embeddings=[table_vector],  
                metadatas=[{"table_name": table_name}],
                ids=[table_name]
            )
        print("✅ ChromaDB initialized safely using pure API cloud embeddings!")

    # 1. Turn the user's plain English question into a vector using Gemini API
    question_vector = get_gemini_embedding(user_question)
    
    # 2. Tell ChromaDB to search using that cloud-calculated vector list
    results = collection.query(
        query_embeddings=[question_vector],
        n_results=3
    )
    
    # Combine the retrieved table descriptions into a single context string
    schemas_context = ""
    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
        table_name = metadata['table_name']
        schemas_context += f"Table: {table_name}\nDescription: {doc}\n\n"
        
    return schemas_context

def generate_sql(user_question, schemas_context):
    """Uses Groq to translate the plain English question into structured SQL."""
    # Automatically initializes using GROQ_API_KEY from environment variables
    client = Groq()
    
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
    
    # Using Groq's Chat Completion with Llama 3.3 (incredible for code and reasoning tasks)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0  # Kept strict/deterministic for raw code generation
    )
    
    raw_output = response.choices[0].message.content.strip()
    
    # Post-processing cleanup in case the LLM accidentally wraps code in markdown blocks
    sql_query = raw_output.replace("```sql", "").replace("```", "").strip()
    return sql_query

def execute_sql(sql_query):
    """Executes the generated SQL query against the local SQLite database in STRICT READ-ONLY mode."""
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "REPLACE"]
    query_upper = sql_query.upper()
    
    for keyword in forbidden_keywords:
        if keyword in query_upper:
            return f"❌ Security Exception: Generated query attempted a forbidden action ({keyword})."
            
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "olist.db")
        db_uri = f"file:{db_path}?mode=ro"
        
        conn = sqlite3.connect(db_uri, uri=True)
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
    
    # Step 1: Semantic Retrieval from ChromaDB (Using Cloud Embeddings)
    context = get_relevant_schemas(user_question)
    
    # Step 2: Code Generation using Groq
    try:
        sql = generate_sql(user_question, context)
        print(f"👉 Generated SQL:\n{sql}\n")
    except Exception as api_error:
        return f"❌ AI Service Error: {api_error}", "-- API Error Fallback"
        
    # Step 3: Execution against SQLite
    result = execute_sql(sql)
    return result, sql

if __name__ == "__main__":
    test_question = "What are the top 5 states with the highest total sales volume?"
    df_result, generated_sql = ask_database(test_question)
    print(df_result)