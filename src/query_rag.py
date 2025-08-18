#!/usr/bin/env python3
"""
Interactive query interface for the gRNA Addgene RAG system.
This script allows users to search the ChromaDB collection using natural language queries.
"""

import chromadb
from chromadb.config import Settings
import os
import sys
import logging
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGQueryInterface:
    """Interface for querying the RAG system."""
    
    def __init__(self, collection_name: str = "grna_addgene"):
        """Initialize the query interface."""
        try:
            host = os.getenv('CHROMADB_HOST', 'localhost')
            port = int(os.getenv('CHROMADB_PORT', '8000'))
            
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Connected to collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {e}")
            logger.error("Make sure ChromaDB is running and the collection exists")
            sys.exit(1)
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search the collection using a text query."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                result = {
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def search_by_metadata(self, metadata_filter: Dict[str, str], n_results: int = 10) -> List[Dict[str, Any]]:
        """Search the collection using metadata filters."""
        try:
            results = self.collection.query(
                query_texts=[""],  # Empty query, just filter by metadata
                n_results=n_results,
                where=metadata_filter,
                include=['documents', 'metadatas']
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                result = {
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i]
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during metadata search: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            count = self.collection.count()
            return {
                'name': self.collection.name,
                'document_count': count,
                'metadata': self.collection.metadata
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def print_results(self, results: List[Dict[str, Any]], query: str):
        """Print search results in a formatted way."""
        if not results:
            print(f"\nNo results found for query: '{query}'")
            return
        
        print(f"\nFound {len(results)} results for query: '{query}'\n")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Document: {result['document']}")
            
            if 'metadata' in result:
                print("Metadata:")
                for key, value in result['metadata'].items():
                    if value:  # Only print non-empty values
                        print(f"  {key}: {value}")
            
            if 'distance' in result:
                print(f"Similarity Score: {1 - result['distance']:.4f}")
            
            print("-" * 40)

def interactive_mode():
    """Run the query interface in interactive mode."""
    print("🧬 gRNA Addgene RAG System Query Interface")
    print("=" * 50)
    
    # Initialize interface
    try:
        rag = RAGQueryInterface()
    except Exception:
        return
    
    # Show collection info
    info = rag.get_collection_info()
    if info:
        print(f"Connected to collection: {info['name']}")
        print(f"Total documents: {info['document_count']}")
        print(f"Description: {info.get('metadata', {}).get('description', 'N/A')}")
    
    print("\nCommands:")
    print("  /help     - Show this help message")
    print("  /info     - Show collection information")
    print("  /species  - Search by species")
    print("  /target   - Search by target gene")
    print("  /quit     - Exit the interface")
    print("\nOr just type your search query!")
    
    while True:
        try:
            query = input("\n🔍 Query: ").strip()
            
            if not query:
                continue
            
            if query.lower() == '/quit':
                print("Goodbye! 👋")
                break
            elif query.lower() == '/help':
                print("\nCommands:")
                print("  /help     - Show this help message")
                print("  /info     - Show collection information")
                print("  /species  - Search by species")
                print("  /target   - Search by target gene")
                print("  /quit     - Exit the interface")
                print("\nOr just type your search query!")
            elif query.lower() == '/info':
                info = rag.get_collection_info()
                if info:
                    print(f"\nCollection: {info['name']}")
                    print(f"Documents: {info['document_count']}")
                    print(f"Description: {info.get('metadata', {}).get('description', 'N/A')}")
            elif query.lower() == '/species':
                species = input("Enter species (e.g., H. sapiens, M. musculus): ").strip()
                if species:
                    results = rag.search_by_metadata({'species': species})
                    rag.print_results(results, f"species = {species}")
            elif query.lower() == '/target':
                target = input("Enter target gene (e.g., AAVS1, EGFP): ").strip()
                if target:
                    results = rag.search_by_metadata({'target': target})
                    rag.print_results(results, f"target = {target}")
            else:
                # Regular search
                results = rag.search(query)
                rag.print_results(results, query)
                
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except EOFError:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            logger.error(f"Error: {e}")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        # Command line mode
        query = " ".join(sys.argv[1:])
        rag = RAGQueryInterface()
        results = rag.search(query)
        rag.print_results(results, query)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
