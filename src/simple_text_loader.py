"""
Simple text-based content loader for CFA books
Much simpler than the complex JSON approach!
"""
import os
import random
from typing import Dict, List

def load_cfa_text_content() -> Dict:
    """Load CFA content from simple text files"""
    
    text_dir = "data/cfa_text_content"
    
    # Check if combined text file exists
    combined_file = os.path.join(text_dir, "all_cfa_content.txt")
    
    if os.path.exists(combined_file):
        print("📚 Loading CFA text content from combined file...")
        
        try:
            with open(combined_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content by book sections
            books = content.split('=== cfa-program')[1:]  # Skip first empty split
            
            # Create simple structure for question generation
            cfa_content = {
                'all_text': content,
                'books': {},
                'total_characters': len(content),
                'book_count': len(books)
            }
            
            # Process each book
            for i, book_content in enumerate(books):
                book_name = f"CFA_Book_{i+1}"
                cfa_content['books'][book_name] = book_content[:50000]  # First 50k chars per book
            
            print(f"✅ Loaded {len(content)} characters from {len(books)} CFA books")
            return cfa_content
            
        except Exception as e:
            print(f"❌ Error loading text content: {e}")
            return None
    
    else:
        print(f"❌ Text content not found at {combined_file}")
        return None

def get_random_cfa_content(content: Dict, topic: str = None, max_chars: int = 3000) -> str:
    """Get random content chunk for question generation"""
    
    if not content or 'all_text' not in content:
        return "Sample CFA Level III content about portfolio management and asset allocation."
    
    full_text = content['all_text']
    
    # Get random starting position
    max_start = max(0, len(full_text) - max_chars)
    start_pos = random.randint(0, max_start)
    
    # Extract chunk
    chunk = full_text[start_pos:start_pos + max_chars]
    
    # Clean up chunk (remove partial sentences at start/end)
    sentences = chunk.split('.')
    if len(sentences) > 2:
        chunk = '.'.join(sentences[1:-1]) + '.'
    
    return chunk

def get_content_summary(content: Dict) -> Dict:
    """Get summary of loaded content"""
    
    if not content:
        return {
            'total_files': 0,
            'total_characters': 0,
            'books': 0,
            'status': 'No content loaded'
        }
    
    return {
        'total_files': content.get('book_count', 0),
        'total_characters': content.get('total_characters', 0),
        'books': len(content.get('books', {})),
        'status': 'Text content loaded successfully'
    }

# Test function
if __name__ == "__main__":
    print("Testing simple text loader...")
    content = load_cfa_text_content()
    if content:
        summary = get_content_summary(content)
        print(f"Summary: {summary}")
        
        # Test random content
        sample = get_random_cfa_content(content)
        print(f"Sample content (first 200 chars): {sample[:200]}...")
