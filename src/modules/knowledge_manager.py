
import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict
import glob
from src.core.logger_config import get_logger

logger = get_logger(__name__)

class KnowledgeManager:
    def __init__(self, kb_path="knowledge_base", collection_name="jarvis_knowledge"):
        self.kb_path = kb_path
        self.collection_name = collection_name
        
        # Initialize ChromaDB
        # PersistentClient saves data to disk so we don't re-index every time
        self.client = chromadb.PersistentClient(path="db_storage")
        
        # Use a default embedding model (all-MiniLM-L6-v2 is fast and good)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn
        )
        
        # Ensure knowledge base directory exists
        if not os.path.exists(self.kb_path):
            os.makedirs(self.kb_path)

    def ingest_documents(self):
        """Read files from knowledge_base and add to vector db"""
        logger.info("Scanning knowledge base...")
        
        # Supported extensions
        files = []
        for ext in ["*.txt", "*.md", "*.pdf"]:
            files.extend(glob.glob(os.path.join(self.kb_path, ext)))
            
        if not files:
            logger.info("No documents found in knowledge_base/")
            return 0
            
        count = 0
        for file_path in files:
            try:
                content = self._read_file(file_path)
                if content:
                    # Simple chunking (can be improved)
                    # We use the filename as ID for simplicity in this basic version
                    # In a real app, we'd chunk large files and use unique IDs per chunk
                    filename = os.path.basename(file_path)
                    
                    # Check if already exists (simple check)
                    existing = self.collection.get(ids=[filename])
                    if existing['ids']:
                        # Update existing
                        self.collection.update(
                            ids=[filename],
                            documents=[content],
                            metadatas=[{"source": filename}]
                        )
                    else:
                        # Add new
                        self.collection.add(
                            ids=[filename],
                            documents=[content],
                            metadatas=[{"source": filename}]
                        )
                    count += 1
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                
        logger.info(f"Ingested {count} documents into Knowledge Base")
        return count

    def _read_file(self, file_path):
        """Read content based on file type"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif ext == '.pdf':
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                logger.error("pypdf not installed. Cannot read PDF.")
                return None
        return None

    def query(self, query_text, n_results=2):
        """Search the knowledge base"""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Format results
        # results['documents'] is a list of lists (one list per query)
        if not results['documents'] or not results['documents'][0]:
            return []
            
        formatted_results = []
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            formatted_results.append({
                "content": doc,
                "source": metadata.get("source", "unknown")
            })
            
        return formatted_results
