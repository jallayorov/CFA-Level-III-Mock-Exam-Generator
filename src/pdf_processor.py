"""
PDF processing and content extraction for CFA books
"""
import os
import re
from typing import List, Dict, Tuple
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import tiktoken
from config.topics import TOPIC_KEYWORDS

class CFAPDFProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and headers/footers
        text = re.sub(r'Page \d+|\d+\s*$', '', text, flags=re.MULTILINE)
        # Remove special characters but keep mathematical symbols
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\{\}\-\+\=\%\$\@\#\&\*\/\\]', '', text)
        return text.strip()
    
    def classify_chunk_topic(self, chunk: str) -> str:
        """Classify a text chunk into CFA topics based on keywords"""
        chunk_lower = chunk.lower()
        topic_scores = {}
        
        for topic, keywords in TOPIC_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Count keyword occurrences with word boundaries
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = len(re.findall(pattern, chunk_lower))
                score += matches
            topic_scores[topic] = score
        
        # Return topic with highest score, or "General" if no clear match
        if max(topic_scores.values()) > 0:
            return max(topic_scores, key=topic_scores.get)
        return "General"
    
    def extract_eoc_questions(self, text: str) -> List[Dict]:
        """Extract End of Chapter questions if available"""
        eoc_questions = []
        
        # Common patterns for EOC sections
        eoc_patterns = [
            r"end of chapter questions",
            r"practice problems",
            r"review questions",
            r"problems and solutions",
            r"chapter \d+ problems"
        ]
        
        for pattern in eoc_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract text after the EOC header
                start_pos = match.end()
                # Look for next chapter or section
                next_section = re.search(r"chapter \d+|section \d+", text[start_pos:], re.IGNORECASE)
                end_pos = next_section.start() + start_pos if next_section else len(text)
                
                eoc_text = text[start_pos:end_pos]
                questions = self._parse_questions_from_text(eoc_text)
                eoc_questions.extend(questions)
        
        return eoc_questions
    
    def _parse_questions_from_text(self, text: str) -> List[Dict]:
        """Parse individual questions from EOC text"""
        questions = []
        
        # Pattern to identify numbered questions
        question_pattern = r'(\d+\.)\s*(.+?)(?=\d+\.|$)'
        matches = re.findall(question_pattern, text, re.DOTALL)
        
        for number, content in matches:
            # Clean up the question content
            content = self.clean_text(content)
            if len(content) > 50:  # Filter out very short matches
                questions.append({
                    "number": number.strip('.'),
                    "content": content,
                    "type": "eoc_question",
                    "source": "extracted"
                })
        
        return questions
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """Process a single PDF and return structured content"""
        filename = os.path.basename(pdf_path)
        print(f"Processing {filename}...")
        
        # Extract text
        raw_text = self.extract_text_from_pdf(pdf_path)
        if not raw_text:
            return {"error": f"Could not extract text from {filename}"}
        
        # Clean text
        clean_text = self.clean_text(raw_text)
        
        # Extract EOC questions
        eoc_questions = self.extract_eoc_questions(clean_text)
        
        # Create chunks
        documents = self.text_splitter.create_documents([clean_text])
        
        # Classify chunks by topic
        classified_chunks = []
        for i, doc in enumerate(documents):
            topic = self.classify_chunk_topic(doc.page_content)
            chunk_data = {
                "chunk_id": f"{filename}_{i}",
                "content": doc.page_content,
                "topic": topic,
                "source_file": filename,
                "token_count": len(self.encoding.encode(doc.page_content))
            }
            classified_chunks.append(chunk_data)
        
        return {
            "source_file": filename,
            "total_chunks": len(classified_chunks),
            "chunks": classified_chunks,
            "eoc_questions": eoc_questions,
            "topics_found": list(set([chunk["topic"] for chunk in classified_chunks])),
            "total_tokens": sum([chunk["token_count"] for chunk in classified_chunks])
        }
    
    def process_multiple_pdfs(self, pdf_paths: List[str]) -> Dict:
        """Process multiple PDFs and combine results"""
        all_results = {
            "processed_files": [],
            "all_chunks": [],
            "all_eoc_questions": [],
            "topic_distribution": {},
            "total_tokens": 0
        }
        
        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                result = self.process_pdf(pdf_path)
                if "error" not in result:
                    all_results["processed_files"].append(result["source_file"])
                    all_results["all_chunks"].extend(result["chunks"])
                    all_results["all_eoc_questions"].extend(result["eoc_questions"])
                    all_results["total_tokens"] += result["total_tokens"]
                    
                    # Update topic distribution
                    for chunk in result["chunks"]:
                        topic = chunk["topic"]
                        if topic not in all_results["topic_distribution"]:
                            all_results["topic_distribution"][topic] = 0
                        all_results["topic_distribution"][topic] += 1
                else:
                    print(f"Error processing {pdf_path}: {result['error']}")
            else:
                print(f"File not found: {pdf_path}")
        
        return all_results

def ingest_pdfs(pdf_list: List[str], output_format: str = "chunked_text_by_topic") -> Dict:
    """
    Main function to ingest PDFs as specified in requirements
    """
    processor = CFAPDFProcessor()
    results = processor.process_multiple_pdfs(pdf_list)
    
    if output_format == "chunked_text_by_topic":
        # Organize chunks by topic
        topic_chunks = {}
        for chunk in results["all_chunks"]:
            topic = chunk["topic"]
            if topic not in topic_chunks:
                topic_chunks[topic] = []
            topic_chunks[topic].append(chunk)
        
        results["chunks_by_topic"] = topic_chunks
    
    return results
