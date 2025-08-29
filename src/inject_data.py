#!/usr/bin/env python3
"""
Script to inject gRNA Addgene data into ChromaDB for RAG system.
This script reads the TSV file and creates embeddings for each entry.
"""

import pandas as pd
import chromadb
from chromadb.config import Settings
import os
import sys
from typing import List, Dict, Any
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_tsv_data(file_path: str) -> pd.DataFrame:
    """Read the TSV file and return a pandas DataFrame."""
    try:
        df = pd.read_csv(file_path, sep='\t')
        logger.info(f"Successfully read {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error reading TSV file: {e}")
        sys.exit(1)

def read_json_data(file_path: str) -> dict:
    with open(file_path, "r") as f:
        data = json.load(f)

    return data

def create_documents(plasmid_data: dict) -> List[Dict[str, Any]]:
    """Convert DataFrame rows to document format for ChromaDB."""
    documents = []
    
    for data in plasmid_data['plasmids']:
        idx = data['id']
        document_text = str(data)
        metadata = data
        
        documents.append({
            'id': idx,
            'text': document_text,
            'metadata': metadata
        })
    
    logger.info(f"Created {len(documents)} documents")
    return documents

def inject_into_chromadb(documents: List[Dict[str, Any]], collection_name: str = "grna_addgene"):
    """Inject documents into ChromaDB."""
    try:
        # Connect to ChromaDB
        host = os.getenv('CHROMADB_HOST', 'localhost')
        port = int(os.getenv('CHROMADB_PORT', '8000'))
        
        client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        try:
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": "gRNA Addgene database for CRISPR applications"}
            )
            logger.info(f"Created new collection: {collection_name}")
        except Exception:
            collection = client.get_collection(name=collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        
        # Prepare data for insertion
        ids = [doc['id'] for doc in documents]
        texts = [doc['text'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        
        # Add documents to collection
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
        logger.info(f"Successfully injected {len(documents)} documents into ChromaDB")
        
        # Print collection info
        collection_info = collection.count()
        logger.info(f"Collection now contains {collection_info} documents")
        
        return collection
        
    except Exception as e:
        logger.error(f"Error connecting to ChromaDB: {e}")
        logger.error("Make sure ChromaDB is running on localhost:8000")
        sys.exit(1)

def main():
    """Main function to orchestrate the data injection process."""
    # Check if data file exists
    data_file = "data/addgene_plasmid_data.json"
    if not os.path.exists(data_file):
        logger.error(f"Data file not found: {data_file}")
        sys.exit(1)
    
    # Read data
    addgene_dict = read_json_data(data_file)
    
    # Create documents
    documents = create_documents(addgene_dict)
    
    # Inject into ChromaDB
    collection = inject_into_chromadb(documents)
    
    logger.info("Data injection completed successfully!")
    logger.info("You can now query the database using the query_rag.py script")

if __name__ == "__main__":
    main()
