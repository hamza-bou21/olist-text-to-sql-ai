import chromadb
from schema_docs import TABLE_SCHEMAS

def embed_database_schema():
    print("⏳ Initializing local ChromaDB storage...")
    # This creates a local folder named 'chroma_db' to store your data persistently
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create or fetch a collection to hold our table schemas
    collection = chroma_client.get_or_create_collection(name="olist_schema_collection")
    
    print("Preparing schema descriptions for vector storage...")
    
    # Loop through our schema dictionary and prepare lists for ChromaDB
    for table_name, description in TABLE_SCHEMAS.items():
        print(f" Packing vector data for table: '{table_name}'")
        
        collection.upsert(
            documents=[description],
            metadatas=[{"table_name": table_name}],
            ids=[table_name] # Using the table name as the unique ID
        )
        
    print("\n🎉 Success! All 5 table schemas have been embedded and saved into ChromaDB.")

if __name__ == "__main__":
    embed_database_schema()