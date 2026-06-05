import streamlit as st
import pandas as pd
from query_pipeline import ask_database

# 1. Page Configurations
st.set_page_config(
    page_title="Olist Text-to-SQL AI", 
    page_icon="📊", 
    layout="wide"
)

# 2. Sidebar Architecture Info
with st.sidebar:
    st.header("⚙️ System Architecture")
    st.markdown("""
    This application leverages a modern RAG (Retrieval-Augmented Generation) pipeline to safely query database systems using natural language.
    
    * **Vector Routing:** ChromaDB
    * **LLM Core:** Gemini 2.5 Flash
    * **SQL Database:** SQLite
    """)
    st.divider()
    st.subheader("🛡️ Security Guardrails")
    st.success("Strict Read-Only connection enforced (`mode=ro`). Destructive queries are automatically intercepted and blocked.")

# 3. Main Dashboard Header
st.title("📊 Olist E-Commerce AI Data Assistant")
st.markdown("Ask your database analytical questions in plain English. The AI will find the correct tables, write the SQL query, and execute it securely.")
st.divider()

# 4. Search Bar Input
user_question = st.text_input(
    label="Enter your analytical question:",
    placeholder="e.g., What are the top 5 states with the highest total sales volume?",
    help="Type any question regarding sales, payments, categories, reviews, or shipping delays."
)

# 5. Core Execution Pipeline
if user_question:
    with st.spinner("🤖 AI is inspecting schema blueprints and generating SQL query..."):
        
        # Call your modified backend master pipeline (now catching both variables)
        result, generated_sql = ask_database(user_question)
        
        # --- NEW FEATURE: Display the generated query section ---
        with st.expander("🔍 Inspect & Share Generated SQL Query", expanded=True):
            st.markdown("You can review, copy, or share this raw SQLite query directly with your data team:")
            st.code(generated_sql, language="sql")
        
        # Check if the result returned a security exception string or a successful dataframe
        if isinstance(result, str):
            if "❌ Security Exception" in result:
                st.error(result)
            else:
                st.warning(result)
        else:
            st.success("✅ Query executed successfully!")
            
            # Create two clean columns for the presentation layout
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📋 Tabular Results")
                if not result.empty:
                    st.dataframe(result, use_container_width=True)
                else:
                    st.info("The query executed perfectly, but returned 0 matching rows for this criteria.")
                    
            with col2:
                st.subheader("📈 Automated Visualization")
                
                # Dynamically check if the dataframe can be turned into a chart
                numeric_cols = result.select_dtypes(include=['number']).columns.tolist()
                categorical_cols = result.select_dtypes(include=['object']).columns.tolist()
                
                if len(numeric_cols) > 0 and len(categorical_cols) > 0:
                    st.bar_chart(data=result, x=categorical_cols[0], y=numeric_cols[0], use_container_width=True)
                elif len(numeric_cols) > 1:
                    st.line_chart(data=result[numeric_cols], use_container_width=True)
                else:
                    st.info("Data schema isn't ideal for a bar chart representation, but you can inspect the full table on the left.")