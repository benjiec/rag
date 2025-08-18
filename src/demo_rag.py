#!/usr/bin/env python3
"""
Demo script for the gRNA Addgene RAG system.
This script demonstrates various query capabilities and shows example results.
"""

import os
import chromadb
from chromadb.config import Settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_queries():
    """Run a series of demo queries to showcase the RAG system."""
    print("🧬 gRNA Addgene RAG System Demo")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        host = os.getenv('CHROMADB_HOST', 'localhost')
        port = int(os.getenv('CHROMADB_PORT', '8000'))
        
        client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_collection(name="grna_addgene")
        print(f"✅ Connected to collection: {collection.name}")
        print(f"📊 Total documents: {collection.count()}")
        
        # Demo queries
        demo_queries = [
            "CRISPR Cas9 human genome editing",
            "EGFP fluorescent protein",
            "AAVS1 safe harbor locus",
            "mouse gene knockout",
            "yeast genetic engineering",
            "plant genome editing",
            "bacterial CRISPR applications"
        ]
        
        print("\n🔍 Running Demo Queries...")
        print("=" * 50)
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n{i}. Query: '{query}'")
            print("-" * 40)
            
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=3,
                    include=['documents', 'metadatas', 'distances']
                )
                
                if results['documents'][0]:
                    for j, (doc, metadata, distance) in enumerate(zip(
                        results['documents'][0], 
                        results['metadatas'][0], 
                        results['distances'][0]
                    )):
                        similarity = 1 - distance
                        print(f"   Result {j+1} (Score: {similarity:.3f}):")
                        print(f"   Target: {metadata.get('target', 'N/A')}")
                        print(f"   Species: {metadata.get('species', 'N/A')}")
                        print(f"   Application: {metadata.get('application', 'N/A')}")
                        print(f"   gRNA: {metadata.get('grna_sequence', 'N/A')[:30]}...")
                        print()
                else:
                    print("   No results found")
                    
            except Exception as e:
                print(f"   Error: {e}")
        
        # Show some metadata-based searches
        print("\n🔍 Metadata-Based Searches...")
        print("=" * 50)
        
        # Search by species
        print("\n1. All human (H. sapiens) entries:")
        try:
            human_results = collection.query(
                query_texts=[""],
                n_results=5,
                where={"species": "H. sapiens"},
                include=['metadatas']
            )
            
            for metadata in human_results['metadatas'][0]:
                print(f"   - {metadata.get('target', 'N/A')} ({metadata.get('application', 'N/A')})")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Search by application
        print("\n2. All 'cut' applications:")
        try:
            cut_results = collection.query(
                query_texts=[""],
                n_results=5,
                where={"application": "cut"},
                include=['metadatas']
            )
            
            for metadata in cut_results['metadatas'][0]:
                print(f"   - {metadata.get('target', 'N/A')} ({metadata.get('species', 'N/A')})")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n✅ Demo completed successfully!")
        print("\n💡 Try running 'python query_rag.py' for interactive queries!")
        
    except Exception as e:
        logger.error(f"Error during demo: {e}")
        print("❌ Make sure ChromaDB is running and the collection exists")

if __name__ == "__main__":
    demo_queries()
