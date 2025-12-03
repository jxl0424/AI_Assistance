
import subprocess
import sys

def install_rag_dependencies():
    print("Installing RAG dependencies...")
    print("1. chromadb (Vector Database)")
    print("2. pypdf (PDF Reader)")
    print("3. sentence-transformers (Embeddings)")
    print("4. docx2txt (Word Documents)")
    
    packages = [
        "chromadb", 
        "pypdf", 
        "sentence-transformers",
        "docx2txt"
    ]
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("\nSUCCESS: All RAG dependencies installed!")
        print("You can now use the Knowledge Base feature.")
    except subprocess.CalledProcessError as e:
        print(f"\nError installing packages: {e}")

if __name__ == "__main__":
    install_rag_dependencies()
    input("\nPress Enter to exit...")
