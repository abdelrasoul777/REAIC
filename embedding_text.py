import os
import json
import fitz
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_nomic import NomicEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter

class PDFEmbedder:
    def __init__(self, vector_db_path="vector_db"):
        """Initialize the PDF embedder with vector store."""
        try:
            self.vector_db_path = vector_db_path
            os.makedirs(vector_db_path, exist_ok=True)
            
            # Initialize the document tracking file
            self.doc_tracking_path = os.path.join(vector_db_path, "document_tracking.json")
            self.doc_tracking = self._load_doc_tracking()
            
            print("Initializing Nomic embeddings...")
            os.environ["NOMIC_API_KEY"] = os.getenv("NOMIC_API_TOKEN", "")
            self.embeddings = NomicEmbeddings(
                model="nomic-embed-text-v1.5"
            )
            
            # Initialize vector store first to ensure proper cleanup
            print("Initializing Chroma vector store...")
            self.vector_store = Chroma(
                persist_directory=vector_db_path,
                embedding_function=self.embeddings,
                collection_name="reaic_docs"
            )
            
            # Get initial collection size
            collection_size = len(self.vector_store.get()['ids']) if self.vector_store.get() else 0
            
            # Clear vector store if tracking is empty
            if not self.doc_tracking and collection_size > 0:
                print("Clearing vector store due to empty tracking file...")
                # Get all existing IDs
                if self.vector_store.get() and self.vector_store.get()['ids']:
                    self.vector_store._collection.delete(
                        ids=self.vector_store.get()['ids']
                    )
                print("Vector store cleared successfully")
            
            # Verify vector store matches tracking
            collection_size = len(self.vector_store.get()['ids']) if self.vector_store.get() else 0
            print(f"Vector store initialized with {collection_size} documents")
            
            if collection_size == 0 and self.doc_tracking:
                print("Warning: Vector store is empty but tracking file has entries. Clearing tracking...")
                self.doc_tracking = {}
                self._save_doc_tracking()
            
        except Exception as e:
            print(f"Error initializing PDFEmbedder: {str(e)}")
            raise

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _load_doc_tracking(self) -> Dict:
        """Load document tracking information."""
        if os.path.exists(self.doc_tracking_path):
            with open(self.doc_tracking_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_doc_tracking(self):
        """Save document tracking information."""
        with open(self.doc_tracking_path, 'w') as f:
            json.dump(self.doc_tracking, f, indent=2)
    
    def _should_process_file(self, file_path: str) -> bool:
        """Check if a file should be processed based on its hash and last modified time."""
        file_hash = self._compute_file_hash(file_path)
        file_stat = os.stat(file_path)
        file_name = os.path.basename(file_path)
        
        if file_name not in self.doc_tracking:
            return True
            
        tracked_info = self.doc_tracking[file_name]
        return (
            tracked_info['hash'] != file_hash or
            tracked_info['last_modified'] != file_stat.st_mtime
        )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        # Remove page numbers and common headers/footers
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip page numbers and short lines
            if len(line.strip()) < 4 or line.strip().isdigit():
                continue
            cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)

    def _split_text(self, text: str, title: str = "") -> List[str]:
        """Split text into chunks using multiple strategies."""
        # First split by sections/paragraphs
        section_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " "],
            chunk_size=1500,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False
        )
        
        # Then split by sentences within sections
        sentence_splitter = CharacterTextSplitter(
            separator=".",
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False
        )
        
        # Get initial chunks
        chunks = section_splitter.split_text(text)
        final_chunks = []
        
        for chunk in chunks:
            # Add title context to longer chunks
            if len(chunk) > 1000 and title:
                chunk = f"From {title}: {chunk}"
            
            # Further split longer chunks by sentences
            if len(chunk) > 1000:
                sub_chunks = sentence_splitter.split_text(chunk)
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def process_new_pdfs(self, pdf_dir="pdf_files") -> int:
        """Process any new or modified PDFs in the specified directory."""
        processed_count = 0
        errors = []
        
        try:
            # Ensure PDF directory exists
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
            
            # Get list of PDF files
            pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
            
            if not pdf_files:
                print("No PDF files found in directory")
                return 0
            
            print(f"Found {len(pdf_files)} PDF files")
            
            # Process each PDF file
            for filename in pdf_files:
                file_path = os.path.join(pdf_dir, filename)
                
                try:
                    if not self._should_process_file(file_path):
                        print(f"Skipping {filename} - no changes detected")
                        continue
                    
                    print(f"Processing {filename}...")
                    
                    # Open and read PDF
                    doc = fitz.open(file_path)
                    text_content = ""
                    
                    # Extract text from each page
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        text_content += page.get_text()
                    
                    # Clean the extracted text
                    cleaned_text = self._clean_text(text_content)
                    
                    if not cleaned_text.strip():
                        raise ValueError("No text content extracted from PDF")
                    
                    # Split text into chunks
                    text_chunks = self._split_text(cleaned_text, title=filename)
                    
                    if not text_chunks:
                        raise ValueError("No valid text chunks generated")
                    
                    print(f"Generated {len(text_chunks)} chunks")
                    
                    # Create metadata
                    file_stat = os.stat(file_path)
                    metadata = {
                        'source': filename,
                        'hash': self._compute_file_hash(file_path),
                        'last_modified': file_stat.st_mtime,
                        'processed_date': datetime.now().isoformat(),
                        'chunk_count': len(text_chunks)
                    }
                    
                    # Generate unique IDs for chunks
                    chunk_ids = [
                        f"{filename}_{hashlib.md5(chunk.encode()).hexdigest()}"
                        for chunk in text_chunks
                    ]
                    
                    # Add to vector store
                    self.vector_store.add_texts(
                        texts=text_chunks,
                        ids=chunk_ids,
                        metadatas=[{**metadata, 'chunk_id': i} for i, _ in enumerate(text_chunks)]
                    )
                    
                    # Update tracking
                    self.doc_tracking[filename] = metadata
                    self._save_doc_tracking()
                    
                    processed_count += 1
                    print(f"Successfully processed {filename}")
                    
                except Exception as e:
                    error_msg = f"Error processing {filename}: {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)
                    
                    # Clean up any partial processing
                    if filename in self.doc_tracking:
                        del self.doc_tracking[filename]
                        self._save_doc_tracking()
                    
                finally:
                    if 'doc' in locals():
                        doc.close()
            
            if errors:
                print(f"Completed with {len(errors)} errors:")
                for error in errors:
                    print(f"  - {error}")
            
            return processed_count
            
        except Exception as e:
            print(f"Error in process_new_pdfs: {str(e)}")
            raise

    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Search for similar content in the vector store."""
        try:
            print(f"\nPerforming similarity search for: {query}")
            
            # Get results from vector store
            results = self.vector_store.similarity_search_with_score(query, k=k*2)
            
            if not results:
                print("No results found in vector store")
                return []
            
            # Convert results to our format with metadata
            processed_results = []
            for doc, score in results:
                # Convert similarity score to a 0-1 scale (lower raw score is better)
                normalized_score = 1 / (1 + score)
                
                # Get metadata with defaults
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                
                # Create result entry
                result = {
                    'content': doc.page_content,
                    'metadata': {
                        'source': metadata.get('source', 'Unknown'),
                        'title': metadata.get('title', ''),
                        'chunk': metadata.get('chunk', 0),
                        'total_chunks': metadata.get('total_chunks', 1),
                        'words': len(doc.page_content.split()),
                        'raw_similarity': score,
                        'normalized_score': normalized_score
                    }
                }
                processed_results.append(result)
            
            # Sort by normalized score (higher is better) and take top k
            processed_results.sort(key=lambda x: x['metadata']['normalized_score'], reverse=True)
            return processed_results[:k]
            
        except Exception as e:
            print(f"Error in similarity search: {str(e)}")
            return []

    def get_document_list(self) -> List[Dict]:
        """Get list of processed documents with metadata."""
        try:
            if not os.path.exists(self.doc_tracking_path):
                return []
                
            with open(self.doc_tracking_path, 'r') as f:
                tracking_data = json.load(f)
                
            documents = []
            for filename, metadata in tracking_data.items():
                doc_info = {
                    'id': filename,
                    'filename': filename,
                    'uploaded_at': metadata.get('processed_date', '')
                }
                documents.append(doc_info)
                
            return sorted(documents, key=lambda x: x['uploaded_at'], reverse=True)
            
        except Exception as e:
            print(f"Error getting document list: {str(e)}")
            return []

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its embeddings."""
        try:
            if not os.path.exists(self.doc_tracking_path):
                return False
                
            # Load tracking data
            with open(self.doc_tracking_path, 'r') as f:
                tracking_data = json.load(f)
                
            # Check if document exists
            if document_id not in tracking_data:
                return False

            # Delete the actual PDF file
            pdf_path = os.path.join('pdf_files', document_id)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                print(f"Deleted PDF file: {pdf_path}")

            # Delete from vector store
            # Get all chunk IDs for this document
            chunk_ids = [
                f"{document_id}_{hashlib.md5(str(i).encode()).hexdigest()}"
                for i in range(tracking_data[document_id].get('chunk_count', 0))
            ]
            
            if chunk_ids:
                print(f"Deleting {len(chunk_ids)} chunks from vector store...")
                self.vector_store._collection.delete(ids=chunk_ids)
                
            # Remove from tracking
            del tracking_data[document_id]
            
            # Save updated tracking
            with open(self.doc_tracking_path, 'w') as f:
                json.dump(tracking_data, f, indent=2)
                
            print(f"Successfully deleted document {document_id} and all related data")
            return True
            
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False

# Initialize the embedder
pdf_embedder = PDFEmbedder()
