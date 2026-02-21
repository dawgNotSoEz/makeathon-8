"""
Dynamic Ingestion System for Regulatory Intelligence
Handles all data sources: structured policies + gazetted data + raw data
"""

import json
import os
import hashlib
import uuid
from typing import Dict, List, Optional
from datetime import datetime
import logging
from pathlib import Path

import chromadb
from .config import config
from .version_control import PolicyVersionManager
from .diff_engine import PolicyDiffEngine
from .gemini_utils import get_gemini_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamicIngester:
    """Handles ingestion from multiple data sources"""
    
    def __init__(self):
        self.gemini_api = get_gemini_api()
        self.chroma_client = chromadb.PersistentClient(path=config.vector_store_path)
        self.collection = self._get_or_create_collection()
        self.version_manager = PolicyVersionManager()
        self.diff_engine = PolicyDiffEngine()
        self.processed_hashes = set()
        self._load_existing_hashes()
    
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection"""
        try:
            collection = self.chroma_client.get_collection("regulatory_policies")
            logger.info("Found existing collection 'regulatory_policies'")
            return collection
        except Exception:
            collection = self.chroma_client.create_collection(
                name="regulatory_policies",
                metadata={"description": "Regulatory policy embeddings"}
            )
            logger.info("Created new collection 'regulatory_policies'")
            return collection
    
    def _load_existing_hashes(self):
        """Load existing document hashes to avoid duplicates"""
        try:
            results = self.collection.get(include=["metadatas"])
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    if "content_hash" in metadata:
                        self.processed_hashes.add(metadata["content_hash"])
            logger.info(f"Loaded {len(self.processed_hashes)} existing document hashes")
        except Exception as e:
            logger.warning(f"Failed to load existing hashes: {e}")
    
    def ingest_all_data_sources(self):
        """Ingest from all available data sources"""
        logger.info("Starting dynamic data ingestion...")
        
        # 1. Process structured policies (existing system)
        self._ingest_structured_policies()
        
        # 2. Process gazetted data
        self._ingest_gazetted_data()
        
        # 3. Process raw data files
        self._ingest_raw_data()
        
        # 4. Process any JSON files in Policies folder
        self._ingest_json_files()
        
        # Print final stats
        self._print_final_stats()
    
    def _ingest_structured_policies(self):
        """Process traditional structured policies"""
        logger.info("Processing structured policies...")
        try:
            new_versions = self.version_manager.get_new_versions()
            
            for policy_info, new_version in new_versions:
                try:
                    processed_count = self._process_policy_version(policy_info, new_version)
                    logger.info(f"Processed {processed_count} chunks from structured policy {policy_info['policy_id']} v{new_version}")
                except Exception as e:
                    logger.error(f"Failed to process structured policy {policy_info['policy_id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Structured policy processing failed: {e}")
    
    def _ingest_gazetted_data(self):
        """Process gazetted data from JSON file"""
        logger.info("Processing gazetted data...")
        gazetted_file = Path(config.processing_config["policies_path"]) / "Gazetted_data_18-02-2026.json"
        
        if not gazetted_file.exists():
            logger.warning("Gazetted data file not found")
            return
        
        try:
            with open(gazetted_file, 'r', encoding='utf-8') as f:
                gazetted_data = json.load(f)
            
            logger.info(f"Found {len(gazetted_data)} gazetted notifications")
            
            for i, item in enumerate(gazetted_data[:10]):  # Process first 10 for demo
                try:
                    self._process_gazetted_item(item, i)
                except Exception as e:
                    logger.error(f"Failed to process gazetted item {i}: {e}")
                    
        except Exception as e:
            logger.error(f"Gazetted data processing failed: {e}")
    
    def _process_gazetted_item(self, item: Dict, index: int):
        """Process individual gazetted notification"""
        # Extract content
        content = item.get('text', '')
        if not content:
            return
        
        # Create metadata
        metadata = {
            "policy_id": f"GAZETTED_{item.get('id', f'item_{index}')}",
            "authority": "GAZETTE_OF_INDIA",
            "policy_name": f"Notification_{index}",
            "version": "2026-02-18",
            "sector_tags": "government,regulatory",
            "effective_date": "2026-02-18",
            "processing_date": datetime.now().isoformat(),
            "source": "gazetted",
            "subject": item.get('subject', ''),
            "url": item.get('url', '')
        }
        
        # Create content hash
        content_hash = self._generate_content_hash(content, metadata["policy_id"], metadata["version"])
        
        if content_hash in self.processed_hashes:
            logger.debug(f"Skipping duplicate gazetted item: {metadata['policy_id']}")
            return
        
        # Generate embedding
        embedding = self.gemini_api.generate_embedding(content)
        if not embedding:
            logger.error(f"Failed to generate embedding for gazetted item {index}")
            return
        
        # Store in ChromaDB
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[str(uuid.uuid4())],
                embeddings=[embedding]
            )
            self.processed_hashes.add(content_hash)
            logger.info(f"Stored gazetted item {index}: {item.get('subject', 'Unknown subject')[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to store gazetted item {index}: {e}")
    
    def _ingest_raw_data(self):
        """Process raw data files"""
        logger.info("Processing raw data files...")
        policies_path = Path(config.processing_config["policies_path"])
        
        # Look for .txt files in Policies root
        for txt_file in policies_path.glob("*.txt"):
            if txt_file.name in ['org_data.json']:  # Skip config files
                try:
                    self._process_raw_file(txt_file)
                except Exception as e:
                    logger.error(f"Failed to process raw file {txt_file.name}: {e}")
    
    def _process_raw_file(self, file_path: Path):
        """Process individual raw text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create metadata
            metadata = {
                "policy_id": f"RAW_{file_path.stem}",
                "authority": "RAW_SOURCE",
                "policy_name": file_path.stem,
                "version": "2026-02-21",
                "sector_tags": "raw,unstructured",
                "effective_date": datetime.now().strftime('%Y-%m-%d'),
                "processing_date": datetime.now().isoformat(),
                "source": "raw_file",
                "file_path": str(file_path)
            }
            
            # Create content hash
            content_hash = self._generate_content_hash(content, metadata["policy_id"], metadata["version"])
            
            if content_hash in self.processed_hashes:
                logger.debug(f"Skipping duplicate raw file: {file_path.name}")
                return
            
            # Generate embedding and store
            embedding = self.gemini_api.generate_embedding(content)
            if embedding:
                self.collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[str(uuid.uuid4())],
                    embeddings=[embedding]
                )
                self.processed_hashes.add(content_hash)
                logger.info(f"Stored raw file: {file_path.name}")
                
        except Exception as e:
            logger.error(f"Failed to process raw file {file_path.name}: {e}")
    
    def _ingest_json_files(self):
        """Process additional JSON files in Policies folder"""
        logger.info("Processing additional JSON files...")
        policies_path = Path(config.processing_config["policies_path"])
        
        for json_file in policies_path.glob("*.json"):
            if json_file.name in ['Gazetted_data_18-02-2026.json']:  # Skip already processed
                try:
                    self._process_json_file(json_file)
                except Exception as e:
                    logger.error(f"Failed to process JSON file {json_file.name}: {e}")
    
    def _process_json_file(self, file_path: Path):
        """Process individual JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                for i, item in enumerate(data[:5]):  # Process first 5 items
                    self._process_json_item(item, f"{file_path.stem}_item_{i}", file_path)
            elif isinstance(data, dict):
                self._process_json_item(data, file_path.stem, file_path)
            
        except Exception as e:
            logger.error(f"Failed to process JSON file {file_path.name}: {e}")
    
    def _process_json_item(self, item: Dict, item_id: str, source_file: Path):
        """Process individual JSON item"""
        # Extract content
        content = str(item)  # Convert entire item to string
        
        # Create metadata
        metadata = {
            "policy_id": item_id,
            "authority": "JSON_SOURCE",
            "policy_name": source_file.stem,
            "version": "2026-02-21",
            "sector_tags": "json,structured",
            "effective_date": datetime.now().strftime('%Y-%m-%d'),
            "processing_date": datetime.now().isoformat(),
            "source": "json_file",
            "source_file": str(source_file)
        }
        
        # Create content hash
        content_hash = self._generate_content_hash(content, metadata["policy_id"], metadata["version"])
        
        if content_hash in self.processed_hashes:
            return
        
        # Generate embedding and store
        embedding = self.gemini_api.generate_embedding(content)
        if embedding:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[str(uuid.uuid4())],
                embeddings=[embedding]
            )
            self.processed_hashes.add(content_hash)
            logger.info(f"Stored JSON item: {item_id}")
    
    def _generate_content_hash(self, content: str, policy_id: str, version: str) -> str:
        """Generate unique hash for content"""
        hash_input = f"{policy_id}:{version}:{content}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def _print_final_stats(self):
        """Print final ingestion statistics"""
        try:
            count = self.collection.count()
            logger.info(f"Dynamic ingestion completed. Total documents: {count}")
            
            # Get source breakdown
            results = self.collection.get(include=["metadatas"])
            source_counts = {}
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    source = metadata.get("source", "unknown")
                    source_counts[source] = source_counts.get(source, 0) + 1
            
            print("\n" + "="*60)
            print("DYNAMIC INGESTION SUMMARY")
            print("="*60)
            print(f"Total Documents Stored: {count}")
            print("\nSource Breakdown:")
            for source, count in source_counts.items():
                print(f"  {source}: {count} documents")
            print("="*60)
            
        except Exception as e:
            logger.error(f"Failed to get final stats: {e}")

def main():
    """Main dynamic ingestion function"""
    try:
        ingester = DynamicIngester()
        ingester.ingest_all_data_sources()
    except Exception as e:
        logger.error(f"Dynamic ingestion failed: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
