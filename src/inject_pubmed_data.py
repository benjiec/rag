#!/usr/bin/env python3
"""
Script to inject PubMed abstract data into ChromaDB for RAG system.
This script reads the addgene data collection and creates embeddings for each entry.
"""

from numpy import insert
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

# Set up PubMed collection config
created_collection = False


def read_addgene_collection(collection_name: str = "grna_addgene"):
    """Read the ChromaDB Addgene collection"""
    # Connect to ChromaDB
    host = os.getenv('CHROMADB_HOST', 'localhost')
    port = int(os.getenv('CHROMADB_PORT', '8000'))

    client = chromadb.HttpClient(
        host=host,
        port=port,
        settings=Settings(anonymized_telemetry=False)
        )

    try:
        addgene_collection = client.get_collection(name=collection_name)
        results = addgene_collection.get()['metadatas']
        logger.info(f"Successfully read {len(results)} documents from {collection_name}")
        return results
    except Exception as e:
        logger.error(f"Error reading Addgene collection: {e}")
        logger.error(f"Make sure the Addgene collection has been created before running this script")
        sys.exit(1)

def read_pubmed_collection(collection_name: str = "pubmed_abstracts"):
    """Read the ChromaDB PubMed collection""" # Connect to ChromaDB
    global created_collection
    host = os.getenv('CHROMADB_HOST', 'localhost')
    port = int(os.getenv('CHROMADB_PORT', '8000'))

    client = chromadb.HttpClient(
        host=host,
        port=port,
        settings=Settings(anonymized_telemetry=False)
        )


    try:
        pubmed_collection = client.create_collection(name=collection_name)
        created_collection = True
        logger.info(f"Successfully created collection {collection_name}")
        return []
    except Exception:
        try:
            pubmed_collection = client.get_collection(name=collection_name)
            results = pubmed_collection.get()['metadatas']
            logger.info(f"Successfully read {len(results)} documents from {collection_name}")
            return results
        except Exception as e:
            logger.error(f"Error reading PubMed collection: {e}")
            sys.exit(1)

def filter_addgene_data(addgene_data, pubmed_data):
    global created_collection
    if not addgene_data:
        logger.error("No addgene data provided to filter_addgene_data")
    if not pubmed_data:
        logger.error("No PubMed data provided to filter_addgene_data")

    if created_collection:
        for result in addgene_data:
            print(result)
            exit()


# def create_documents(plasmid_data: dict) -> List[Dict[str, Any]]:
#     """Convert json data to document format for ChromaDB."""
#     documents = []
#     
#     for index, data in enumerate(plasmid_data['plasmids']):
#         if index % 10 != 0:
#             continue
#
#         idx = str(data['id'])
#         document_text = str(data)
#         metadata = {
#                 'bacterial_resistance': data['bacterial_resistance'],
#                 'cloning_backbone': data['cloning']['backbone'],
#                 'resistance_markers': ','.join(data['resistance_markers']),
#                 'vector_types': ','.join(data['cloning']['vector_types'])
#                 }
#         
#         documents.append({
#             'id': idx,
#             'text': document_text,
#             'metadata': metadata
#         })
#     
#     logger.info(f"Created {len(documents)} documents")
#     return documents

def insert_documents(documents, collection):
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

def inject_into_chromadb(documents: List[Dict[str, Any]], collection_name: str = "pubmed_abstracts"):
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
                metadata={"description": "PubMed Abstracts database for additional information into Addgene plasmids"}
            )
            logger.info(f"Created new collection: {collection_name}")
        except Exception:
            collection = client.get_collection(name=collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        
        for i in range(0, len(documents), 2000):
            insert_documents(documents[i:i+2000], collection)

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
    logger.error("This function has not been created yet")

    addgene_data = read_addgene_collection()  # read the ChromaDB collection with addgene's data
    pubmed_data = read_pubmed_collection()  # read the ChromaDB collection with the PubMed data
    filtered_addgene_data = filter_addgene_data(addgene_data, pubmed_data)  # filter the addgene data for plasmids not in pubmed collection
    pmids = get_pubmed_ids(filtered_addgene_data)  # get the PubMed IDs for the plasmids not in pubmed collection
    documents = create_documents(pmids)  # convert PubMed IDs into injectable documents
    collection = inject_into_chromadb(documents)  # inject the documents into chromadb

    logger.info("Data injection completed sucessfully!")


if __name__ == "__main__":
    addgene_data = read_addgene_collection()
    pubmed_data = read_pubmed_collection()
    filter_addgene_data(addgene_data, pubmed_data)
