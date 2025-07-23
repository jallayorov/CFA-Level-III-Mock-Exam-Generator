"""
Content loader utility for handling compressed pre-processed CFA content
"""
import json
import gzip
import os
from typing import Dict, Optional

def load_preprocessed_content() -> Optional[Dict]:
    """
    Load pre-processed CFA content from compressed file
    Falls back to uncompressed if needed
    """
    # Try compressed file first (for cloud deployment)
    compressed_file = "data/processed/financial_books_content.json.gz"
    uncompressed_file = "data/processed/financial_books_content.json"
    
    try:
        # Try compressed file
        if os.path.exists(compressed_file):
            print("📦 Loading compressed pre-processed CFA content...")
            with gzip.open(compressed_file, 'rt', encoding='utf-8') as f:
                content = json.load(f)
            print(f"✅ Loaded {len(content.get('all_chunks', []))} chunks from compressed file")
            return content
            
        # Fall back to uncompressed file
        elif os.path.exists(uncompressed_file):
            print("📄 Loading uncompressed pre-processed CFA content...")
            with open(uncompressed_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            print(f"✅ Loaded {len(content.get('all_chunks', []))} chunks from uncompressed file")
            return content
            
        else:
            print("❌ No pre-processed content found")
            return None
            
    except Exception as e:
        print(f"❌ Error loading pre-processed content: {e}")
        return None

def get_content_summary(content: Dict) -> Dict:
    """Get summary statistics of the loaded content"""
    if not content:
        return {}
    
    return {
        "total_files": len(content.get('processed_files', [])),
        "total_chunks": len(content.get('all_chunks', [])),
        "topics": len(content.get('topic_distribution', {})),
        "topic_distribution": content.get('topic_distribution', {}),
        "has_chunks_by_topic": 'chunks_by_topic' in content,
        "total_tokens": content.get('total_tokens', 0)
    }

def ensure_chunks_by_topic(content: Dict) -> Dict:
    """Ensure content has chunks_by_topic structure for question generation"""
    if not content:
        return content
        
    if 'chunks_by_topic' not in content and 'all_chunks' in content:
        print("🔧 Creating chunks_by_topic structure...")
        chunks_by_topic = {}
        
        for chunk in content['all_chunks']:
            topic = chunk.get('topic', 'General')
            if topic not in chunks_by_topic:
                chunks_by_topic[topic] = []
            chunks_by_topic[topic].append(chunk)
        
        content['chunks_by_topic'] = chunks_by_topic
        print(f"✅ Created chunks_by_topic with {len(chunks_by_topic)} topics")
    
    return content
