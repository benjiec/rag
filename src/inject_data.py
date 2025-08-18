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

def create_documents(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert DataFrame rows to document format for ChromaDB."""
    documents = []
    
    for idx, row in df.iterrows():
        # Create a comprehensive text representation of each entry
        text_parts = []
        
        if pd.notna(row['Target']):
            text_parts.append(f"Target: {row['Target']}")
        if pd.notna(row['Species']):
            text_parts.append(f"Species: {row['Species']}")
        if pd.notna(row['gRNA sequence']):
            text_parts.append(f"gRNA sequence: {row['gRNA sequence']}")
        if pd.notna(row['Addgene Plasmid ID']):
            text_parts.append(f"Addgene Plasmid ID: {row['Addgene Plasmid ID']}")
        if pd.notna(row['Application']):
            text_parts.append(f"Application: {row['Application']}")
        if pd.notna(row['Cas9 species']):
            text_parts.append(f"Cas9 species: {row['Cas9 species']}")
        if pd.notna(row['Pubmed ID']):
            text_parts.append(f"Pubmed ID: {row['Pubmed ID']}")
        if pd.notna(row['Author/Lab']):
            text_parts.append(f"Author/Lab: {row['Author/Lab']}")
        
        # Combine all parts into a single text document
        document_text = " | ".join(text_parts)
        
        # Create metadata
        metadata = {
            'target': str(row['Target']) if pd.notna(row['Target']) else '',
            'species': str(row['Species']) if pd.notna(row['Species']) else '',
            'grna_sequence': str(row['gRNA sequence']) if pd.notna(row['gRNA sequence']) else '',
            'addgene_id': str(row['Addgene Plasmid ID']) if pd.notna(row['Addgene Plasmid ID']) else '',
            'application': str(row['Application']) if pd.notna(row['Application']) else '',
            'cas9_species': str(row['Cas9 species']) if pd.notna(row['Cas9 species']) else '',
            'pubmed_id': str(row['Pubmed ID']) if pd.notna(row['Pubmed ID']) else '',
            'author_lab': str(row['Author/Lab']) if pd.notna(row['Author/Lab']) else '',
            'row_index': idx
        }
        
        documents.append({
            'id': f"entry_{idx}",
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
    data_file = "data/grna_addgene.tsv"
    if not os.path.exists(data_file):
        logger.error(f"Data file not found: {data_file}")
        sys.exit(1)
    
    # Read data
    df = read_tsv_data(data_file)
    
    # Create documents
    documents = create_documents(df)
    
    # Inject into ChromaDB
    collection = inject_into_chromadb(documents)
    
    logger.info("Data injection completed successfully!")
    logger.info("You can now query the database using the query_rag.py script")

if __name__ == "__main__":
    main()
