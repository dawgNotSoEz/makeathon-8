"""
Diff Engine for Regulatory Policy Change Detection
Compares policy versions and extracts structured differences
"""

import re
from typing import Dict, List, Tuple, Optional
from difflib import unified_diff
import logging

logger = logging.getLogger(__name__)

class PolicyDiffEngine:
    """Engine for detecting and structuring changes between policy versions"""
    
    def __init__(self):
        self.section_patterns = [
            r'^(\d+\.\s+)',  # Numbered sections (1. Section Title)
            r'^([A-Z][A-Z\s]*:)',  # All caps headers (SECTION TITLE:)
            r'^([IVX]+\.\s+)',  # Roman numerals (I. Section Title)
            r'^([A-Z]\.\s+)',  # Letter sections (A. Section Title)
            r'^(\d+\.\d+\s+)',  # Subsections (1.1 Section Title)
            r'^(\d+\.\d+\.\d+\s+)',  # Sub-subsections (1.1.1 Section Title)
        ]
    
    def compare_versions(self, old_content: str, new_content: str) -> Dict:
        """
        Compare two policy versions and return structured diff
        Returns dictionary with added, modified, and removed sections
        """
        if not old_content and new_content:
            # First version - everything is added
            return {
                "added_sections": self._extract_sections(new_content),
                "modified_sections": [],
                "removed_sections": [],
                "is_first_version": True
            }
        
        if old_content and not new_content:
            # Policy removed
            return {
                "added_sections": [],
                "modified_sections": [],
                "removed_sections": self._extract_sections(old_content),
                "is_first_version": False
            }
        
        # Extract sections from both versions
        old_sections = self._extract_sections(old_content)
        new_sections = self._extract_sections(new_content)
        
        # Compare sections
        added, modified, removed = self._compare_sections(old_sections, new_sections)
        
        return {
            "added_sections": added,
            "modified_sections": modified,
            "removed_sections": removed,
            "is_first_version": False
        }
    
    def _extract_sections(self, content: str) -> List[Dict]:
        """Extract structured sections from policy content"""
        if not content:
            return []
        
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            stripped_line = line.strip()
            
            # Check if this line is a section header
            section_title = self._identify_section_header(stripped_line)
            
            if section_title:
                # Save previous section if exists
                if current_section:
                    current_section["content"] = '\n'.join(current_content).strip()
                    if current_section["content"]:  # Only add non-empty sections
                        sections.append(current_section)
                
                # Start new section
                current_section = {
                    "title": section_title,
                    "content": "",
                    "line_number": len(sections) + 1
                }
                current_content = [stripped_line]
            else:
                # Add to current section content
                if current_section:
                    current_content.append(stripped_line)
                else:
                    # Content before first section - create default section
                    if not sections:
                        current_section = {
                            "title": "Preamble",
                            "content": "",
                            "line_number": 0
                        }
                        current_content = [stripped_line]
        
        # Save last section
        if current_section:
            current_section["content"] = '\n'.join(current_content).strip()
            if current_section["content"]:
                sections.append(current_section)
        
        return sections
    
    def _identify_section_header(self, line: str) -> Optional[str]:
        """Identify if a line is a section header and return the title"""
        for pattern in self.section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return line
        
        # Additional heuristics for section headers
        if (len(line) < 100 and  # Reasonably short
            line.isupper() and  # All caps
            not line.endswith('.') and  # Not a sentence
            any(char.isalpha() for char in line)):  # Contains letters
            return line
        
        return None
    
    def _compare_sections(self, old_sections: List[Dict], new_sections: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Compare sections and identify additions, modifications, and removals"""
        added = []
        modified = []
        removed = []
        
        # Create lookup dictionaries
        old_lookup = {self._normalize_title(s["title"]): s for s in old_sections}
        new_lookup = {self._normalize_title(s["title"]): s for s in new_sections}
        
        # Find added and modified sections
        for norm_title, new_section in new_lookup.items():
            if norm_title in old_lookup:
                # Section exists in both - check for modifications
                old_section = old_lookup[norm_title]
                if self._is_content_modified(old_section["content"], new_section["content"]):
                    modified.append({
                        "title": new_section["title"],
                        "old_content": old_section["content"],
                        "new_content": new_section["content"],
                        "change_summary": self._summarize_change(old_section["content"], new_section["content"])
                    })
            else:
                # New section added
                added.append(new_section)
        
        # Find removed sections
        for norm_title, old_section in old_lookup.items():
            if norm_title not in new_lookup:
                removed.append(old_section)
        
        return added, modified, removed
    
    def _normalize_title(self, title: str) -> str:
        """Normalize section title for comparison"""
        return re.sub(r'[^a-zA-Z0-9]', '', title.lower()).strip()
    
    def _is_content_modified(self, old_content: str, new_content: str) -> bool:
        """Check if content has been significantly modified"""
        if old_content == new_content:
            return False
        
        # Simple similarity check - can be enhanced with more sophisticated algorithms
        old_words = set(old_content.lower().split())
        new_words = set(new_content.lower().split())
        
        # If more than 20% of words are different, consider it modified
        total_words = len(old_words.union(new_words))
        if total_words == 0:
            return False
        
        common_words = len(old_words.intersection(new_words))
        similarity = common_words / total_words
        
        return similarity < 0.8
    
    def _summarize_change(self, old_content: str, new_content: str) -> str:
        """Generate a summary of changes between content"""
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        diff_lines = list(unified_diff(old_lines, new_lines, lineterm=''))
        
        # Extract only the actual changes (remove diff headers)
        changes = []
        for line in diff_lines:
            if line.startswith('+ ') and not line.startswith('+++'):
                changes.append(f"Added: {line[2:]}")
            elif line.startswith('- ') and not line.startswith('---'):
                changes.append(f"Removed: {line[2:]}")
        
        return '; '.join(changes[:5])  # Limit to first 5 changes
    
    def get_changed_content_for_embedding(self, diff_result: Dict) -> List[Dict]:
        """
        Extract content that needs to be embedded
        Returns list of content chunks with metadata
        """
        embed_content = []
        
        # Add new sections
        for section in diff_result["added_sections"]:
            embed_content.append({
                "content": section["content"],
                "title": section["title"],
                "change_type": "added",
                "line_number": section.get("line_number", 0)
            })
        
        # Add modified sections (use new content)
        for section in diff_result["modified_sections"]:
            embed_content.append({
                "content": section["new_content"],
                "title": section["title"],
                "change_type": "modified",
                "change_summary": section["change_summary"],
                "line_number": section.get("line_number", 0)
            })
        
        return embed_content
    
    def generate_diff_summary(self, diff_result: Dict) -> str:
        """Generate human-readable summary of changes"""
        summary_parts = []
        
        if diff_result["is_first_version"]:
            return "New policy document added."
        
        added_count = len(diff_result["added_sections"])
        modified_count = len(diff_result["modified_sections"])
        removed_count = len(diff_result["removed_sections"])
        
        if added_count > 0:
            summary_parts.append(f"{added_count} new section(s) added")
        
        if modified_count > 0:
            summary_parts.append(f"{modified_count} section(s) modified")
        
        if removed_count > 0:
            summary_parts.append(f"{removed_count} section(s) removed")
        
        if not summary_parts:
            return "No significant changes detected."
        
        return "; ".join(summary_parts) + "."

# Future REST API compatibility notes:
# TODO: Add API endpoint for diff comparison
# TODO: Add real-time diff streaming
# TODO: Add visual diff representation
# TODO: Add diff export in multiple formats (JSON, HTML, PDF)
# TODO: Add batch diff processing
# TODO: Add change impact scoring
