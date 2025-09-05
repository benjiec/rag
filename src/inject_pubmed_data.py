#!/usr/bin/env python3
"""
Script to inject PubMed abstract data into ChromaDB for RAG system.
This script reads the addgene data collection and creates embeddings for each entry.
"""

import chromadb
from chromadb.config import Settings
import os
import sys
from typing import List, Dict, Any
import logging
import requests
import xml.etree.ElementTree as ET

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
    host = os.getenv('CHROMADB_HOST', 'localhost')
    port = int(os.getenv('CHROMADB_PORT', '8000'))

    client = chromadb.HttpClient(
        host=host,
        port=port,
        settings=Settings(anonymized_telemetry=False)
        )


    try:
        pubmed_collection = client.create_collection(name=collection_name)
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

def get_pubmed_abstract(pubmed_id: str):
    if not pubmed_id:
        logger.error(f"No pubmed_id passed to get_pubmed_abstract")
        sys.exit(1)

    if pubmed_id.startswith("PMC"):
        url_conv = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
        params = {
            "dbfrom": "pmc",
            "id": pubmed_id,
            "db": "pubmed",
            "retmode": "xml"
        }
        r = requests.get(url_conv, params=params)
        root = ET.fromstring(r.text)

        pmid = None
        for elem in root.findall(".//LinkSetDb/Link/Id"):
            pmid = elem.text
            break

        if not pmid:
            raise ValueError(f"No PMID found for {pubmed_id}")
    else:
        pmid = pubmed_id

    
    url_fetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "rettype": "abstract",
        "retmode": "xml"
    }

    r = requests.get(url_fetch, params=params)
    root = ET.fromstring(r.text)

    abstracts = [abst.text for abst in root.findall(".//AbstractText") if abst.text]
    return " ".join(abstracts)

def filter_addgene_data(addgene_data, pubmed_data):
    if pubmed_data:
        if not addgene_data:
            logger.error("No addgene data provided to filter_addgene_data")
            sys.exit(1)
        if not pubmed_data:
            logger.error("No PubMed data provided to filter_addgene_data")
            sys.exit(1)

        new_pubmed_data = pubmed_data.copy()
        cur_pubmed_ids = [id for id in [document['pubmed_id'] for document in new_pubmed_data]]
        for result in addgene_data:
            if not result['pubmed_id']: continue
            if result['pubmed_id'] in cur_pubmed_ids: continue

            pubmed_idx = result['pubmed_id']
            pubmed_abstract = get_pubmed_abstract(pubmed_idx)
            new_document = {
                    "pubmed_id": pubmed_idx,
                    "abstract": pubmed_abstract
                    }
            new_pubmed_data.append(new_document)
            
        return new_pubmed_data
    else:
        new_pubmed_data = []
        for result in addgene_data:
            if not result['pubmed_id']: continue
            pubmed_idx = result['pubmed_id']
            pubmed_abstract = get_pubmed_abstract(pubmed_idx)
            new_document = {
                    "pubmed_id": pubmed_idx,
                    "abstract": pubmed_abstract
                    }
            new_pubmed_data.append(new_document)
            
        return new_pubmed_data


def create_documents(pubmed_data: list) -> List[Dict[str, Any]]:
    """Convert json data to document format for ChromaDB."""
    documents = []
    
    for index, data in enumerate(pubmed_data):
        if index % 10 != 0:
            continue

        idx = data['pubmed_id']
        document_text = str(data)
        
        documents.append({
            'id': idx,
            'text': document_text,
            'metadata': data
        })
    
    logger.info(f"Created {len(documents)} documents")
    return documents

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
    documents = create_documents(filtered_addgene_data)  # convert filtered_addgene_data into injectable documents
    collection = inject_into_chromadb(documents)  # inject the documents into chromadb

    logger.info("Data injection completed sucessfully!")


if __name__ == "__main__":
    main()
