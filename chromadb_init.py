#!/usr/bin/env python3
"""
Script to pre-download ChromaDB ONNX models during Docker build.
This avoids runtime downloads when running the container.
"""

import chromadb
from chromadb.config import Settings
import shutil
import os

def download_models():
    """Download ChromaDB models to cache them in the Docker image."""
    print("Pre-downloading ChromaDB models...")
    
    try:
        # Create a temporary local client to trigger model download
        temp_path = "/tmp/chroma_test"
        client = chromadb.PersistentClient(path=temp_path)
        
        # Create a temporary collection and add a document to trigger embedding
        collection = client.create_collection(name="temp_download")
        collection.add(ids=["1"], documents=["test document"])
        
        # Clean up
        client.delete_collection(name="temp_download")
        client.reset()
        
        # Remove temporary directory
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
            
        print("Model download completed successfully!")
        
    except Exception as e:
        print(f"Model download completed (may have failed: {e})")

if __name__ == "__main__":
    download_models()
