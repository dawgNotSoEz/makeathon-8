"""
Incremental Ingestion System for Regulatory Policies
Processes new/changed policy sections and embeds them in vector database
"""

import json
import hashlib
import uuid
from typing import Dict, List, Optional
from datetime import datetime
import logging

import chromadb

from .config import config
from .version_control import PolicyVersionManager
from .diff_engine import PolicyDiffEngine
from .gemini_utils import get_gemini_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyIngester:
    """Handles incremental ingestion of policy changes"""
    
    def __init__(self):
        # Initialize Gemini API
        self.gemini_api = get_gemini_api()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=config.vector_store_path)
        self.collection = self._get_or_create_collection()
        
        # Initialize components
        self.version_manager = PolicyVersionManager()
        self.diff_engine = PolicyDiffEngine()
        
        # Track processed documents to avoid duplicates
        self.processed_hashes = set()
        self._load_existing_hashes()
    
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection for policies"""
        try:
            collection = self.chroma_client.get_collection("regulatory_policies")
            logger.info("Found existing collection 'regulatory_policies'")
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
            # Get all existing documents
            results = self.collection.get(include=["metadatas"])
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    if "content_hash" in metadata:
                        self.processed_hashes.add(metadata["content_hash"])
            logger.info(f"Loaded {len(self.processed_hashes)} existing document hashes")
        except Exception as e:
            logger.warning(f"Failed to load existing hashes: {e}")
    
    def ingest_all_policies(self):
        """Process all policies and ingest new/changed content"""
        logger.info("Starting policy ingestion process...")
        
        # Get policies with new versions
        new_versions = self.version_manager.get_new_versions()
        
        if not new_versions:
            logger.info("No new policy versions found")
            return
        
        logger.info(f"Found {len(new_versions)} policies with new versions")
        
        total_processed = 0
        for policy_info, new_version in new_versions:
            try:
                processed_count = self._process_policy_version(policy_info, new_version)
                total_processed += processed_count
                
                # Update metadata to mark as processed
                self.version_manager.update_metadata(
                    policy_info["policy_path"], 
                    new_version,
                    {"processing_status": "completed", "processed_chunks": processed_count}
                )
                
            except Exception as e:
                logger.error(f"Failed to process policy {policy_info['policy_id']}: {e}")
                continue
        
        logger.info(f"Ingestion completed. Processed {total_processed} chunks total")
    
    def _process_policy_version(self, policy_info: Dict, version: str) -> int:
        """Process a single policy version and return number of chunks processed"""
        policy_id = policy_info["policy_id"]
        authority = policy_info["authority"]
        policy_path = policy_info["policy_path"]
        
        logger.info(f"Processing policy {policy_id} version {version}")
        
        # Get current and previous version content
        current_content = self.version_manager.get_policy_content(policy_path, version)
        if not current_content:
            raise ValueError(f"Could not read policy content for {policy_id} v{version}")
        
        previous_version = self.version_manager.get_previous_version(policy_path, version)
        previous_content = None
        if previous_version:
            previous_content = self.version_manager.get_policy_content(policy_path, previous_version)
        
        # Compare versions to identify changes
        diff_result = self.diff_engine.compare_versions(previous_content, current_content)
        
        # Get content that needs embedding
        content_to_embed = self.diff_engine.get_changed_content_for_embedding(diff_result)
        
        if not content_to_embed:
            logger.info(f"No new content to embed for {policy_id} v{version}")
            return 0
        
        # Create enriched chunks with metadata
        chunks = self._create_enriched_chunks(content_to_embed, policy_info, version, diff_result)
        
        # Filter out already processed chunks
        new_chunks = [chunk for chunk in chunks if chunk["content_hash"] not in self.processed_hashes]
        
        if not new_chunks:
            logger.info(f"All chunks already processed for {policy_id} v{version}")
            return 0
        
        # Embed and store new chunks
        self._embed_and_store_chunks(new_chunks)
        
        logger.info(f"Embedded {len(new_chunks)} new chunks for {policy_id} v{version}")
        return len(new_chunks)
    
    def _create_enriched_chunks(self, content_to_embed: List[Dict], policy_info: Dict, version: str, diff_result: Dict) -> List[Dict]:
        """Create enriched chunks with full metadata"""
        chunks = []
        
        # Base metadata from policy
        base_metadata = {
            "policy_id": policy_info["policy_id"],
            "authority": policy_info["authority"],
            "policy_name": policy_info["policy_name"],
            "version": version,
            "sector_tags": ",".join(policy_info["metadata"].get("sector_tags", [])),  # Convert list to string
            "effective_date": policy_info["metadata"].get("effective_date", ""),
            "processing_date": datetime.now().isoformat()
        }
        
        for content_item in content_to_embed:
            # Create unique content hash
            content_hash = self._generate_content_hash(
                content_item["content"], 
                policy_info["policy_id"], 
                version
            )
            
            # Enriched metadata
            chunk_metadata = {
                **base_metadata,
                "section_title": content_item["title"],
                "change_type": content_item["change_type"],
                "content_hash": content_hash,
                "chunk_length": len(content_item["content"])
            }
            
            # Add change summary for modified sections
            if content_item["change_type"] == "modified" and "change_summary" in content_item:
                chunk_metadata["change_summary"] = content_item["change_summary"]
            
            chunk = {
                "id": str(uuid.uuid4()),
                "content": content_item["content"],
                "metadata": chunk_metadata,
                "content_hash": content_hash
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _generate_content_hash(self, content: str, policy_id: str, version: str) -> str:
        """Generate unique hash for content to avoid duplicates"""
        hash_input = f"{policy_id}:{version}:{content}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def _embed_and_store_chunks(self, chunks: List[Dict]):
        """Embed chunks and store in ChromaDB"""
        if not chunks:
            return
        
        # Prepare batch data
        texts = [chunk["content"] for chunk in chunks]
        ids = [chunk["id"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        try:
            # Generate embeddings in batches
            embeddings = []
            batch_size = 100  # Gemini API limit
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self._generate_embeddings(batch_texts)
                embeddings.extend(batch_embeddings)
            
            # Add to ChromaDB
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            # Update processed hashes
            for chunk in chunks:
                self.processed_hashes.add(chunk["content_hash"])
            
        except Exception as e:
            logger.error(f"Failed to embed and store chunks: {e}")
            raise
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Gemini API"""
        return self.gemini_api.generate_embeddings_batch(texts)
    
    def get_ingestion_stats(self) -> Dict:
        """Get statistics about the ingestion process"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": "regulatory_policies",
                "vector_store_path": config.vector_store_path,
                "processed_hashes": len(self.processed_hashes)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self):
        """Clear all data from collection (for testing/reset)"""
        try:
            self.chroma_client.delete_collection("regulatory_policies")
            self.collection = self._get_or_create_collection()
            self.processed_hashes.clear()
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")

def main():
    """Main ingestion function"""
    try:
        ingester = PolicyIngester()
        
        # Print current stats
        stats = ingester.get_ingestion_stats()
        print(f"Current stats: {json.dumps(stats, indent=2)}")
        
        # Run ingestion
        ingester.ingest_all_policies()
        
        # Print updated stats
        updated_stats = ingester.get_ingestion_stats()
        print(f"Updated stats: {json.dumps(updated_stats, indent=2)}")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

# Future REST API compatibility notes:
# TODO: Add API endpoints for ingestion control
# TODO: Add real-time ingestion status monitoring
# TODO: Add batch processing API
# TODO: Add ingestion scheduling
# TODO: Add ingestion rollback functionality
# TODO: Add embedding quality metrics
