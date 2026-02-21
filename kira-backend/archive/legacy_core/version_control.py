"""
Version Control System for Regulatory Policies
Manages policy versions, metadata, and change tracking
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

from .config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyVersionManager:
    """Manages policy versions and metadata"""
    
    def __init__(self):
        self.policies_path = Path(config.processing_config["policies_path"])
        
    def scan_policies(self) -> List[Dict]:
        """
        Scan all policies and return their version information
        Returns list of policies with their available versions
        """
        policies = []
        
        for authority_dir in self.policies_path.iterdir():
            if not authority_dir.is_dir():
                continue
                
            authority = authority_dir.name
            for policy_dir in authority_dir.iterdir():
                if not policy_dir.is_dir():
                    continue
                    
                policy_info = self._get_policy_info(policy_dir, authority)
                if policy_info:
                    policies.append(policy_info)
        
        return policies
    
    def _get_policy_info(self, policy_dir: Path, authority: str) -> Optional[Dict]:
        """Extract policy information from policy directory"""
        metadata_file = policy_dir / "metadata.json"
        
        # Load metadata if exists
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8-sig') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata for {policy_dir}: {e}")
        
        # Scan for version files
        version_files = []
        for file_path in policy_dir.glob("v*.txt"):
            version_match = re.match(r'v(\d+)\.txt', file_path.name)
            if version_match:
                version_num = int(version_match.group(1))
                version_files.append((version_num, file_path))
        
        if not version_files:
            return None
        
        # Sort by version number
        version_files.sort(key=lambda x: x[0])
        versions = [f"v{v[0]}" for v in version_files]
        latest_version = versions[-1]
        
        return {
            "policy_id": metadata.get("policy_id", policy_dir.name),
            "authority": authority,
            "policy_name": policy_dir.name,
            "policy_path": str(policy_dir),
            "available_versions": versions,
            "latest_version": latest_version,
            "last_processed_version": metadata.get("last_processed_version", ""),
            "metadata": metadata
        }
    
    def get_policy_content(self, policy_path: str, version: str) -> Optional[str]:
        """Get content of specific policy version"""
        version_file = Path(policy_path) / f"{version}.txt"
        
        if not version_file.exists():
            logger.error(f"Version file not found: {version_file}")
            return None
        
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read policy content: {e}")
            return None
    
    def update_metadata(self, policy_path: str, version: str, additional_data: Dict = None) -> bool:
        """Update policy metadata with new processed version"""
        metadata_file = Path(policy_path) / "metadata.json"
        
        # Load existing metadata
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing metadata: {e}")
        
        # Update metadata
        metadata["last_processed_version"] = version
        metadata["last_processed_date"] = datetime.now().isoformat()
        
        if additional_data:
            metadata.update(additional_data)
        
        # Save metadata
        try:
            with open(metadata_file, 'w', encoding='utf-8-sig') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            return False
    
    def get_new_versions(self) -> List[Tuple[Dict, str]]:
        """
        Get all policies that have new versions not yet processed
        Returns list of (policy_info, new_version) tuples
        """
        new_versions = []
        policies = self.scan_policies()
        
        for policy in policies:
            last_processed = policy.get("last_processed_version", "")
            latest_version = policy["latest_version"]
            
            # If no version processed or new version available
            if not last_processed or self._compare_versions(latest_version, last_processed) > 0:
                new_versions.append((policy, latest_version))
        
        return new_versions
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings (v1, v2, etc.)"""
        v1_num = int(version1.replace('v', ''))
        v2_num = int(version2.replace('v', ''))
        
        if v1_num > v2_num:
            return 1
        elif v1_num < v2_num:
            return -1
        else:
            return 0
    
    def get_previous_version(self, policy_path: str, current_version: str) -> Optional[str]:
        """Get the previous version of a policy"""
        version_num = int(current_version.replace('v', ''))
        if version_num <= 1:
            return None
        
        previous_version = f"v{version_num - 1}"
        previous_file = Path(policy_path) / f"{previous_version}.txt"
        
        return previous_version if previous_file.exists() else None

# Future REST API compatibility notes:
# TODO: Add API endpoints for version management
# TODO: Add version comparison API
# TODO: Add metadata search and filtering
# TODO: Add batch processing capabilities
# TODO: Add version rollback functionality
# TODO: Add policy change history tracking
