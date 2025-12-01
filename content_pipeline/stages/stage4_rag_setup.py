"""
Stage 4: Brand Voice RAG Setup
One-time setup to populate ChromaDB with Sendmarc brand voice examples
"""
import os
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from pathlib import Path


# Global instances
_embedding_model = None
_chroma_client = None
_collection = None


def get_embedding_model():
    """Get or create embedding model instance"""
    global _embedding_model
    if _embedding_model is None:
        print("Loading sentence transformer model...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def get_chroma_client():
    """Get or create ChromaDB client"""
    global _chroma_client
    if _chroma_client is None:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'chromadb'
        )
        os.makedirs(db_path, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=db_path)
    return _chroma_client


def get_or_create_collection():
    """Get or create the brand voice collection"""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name="sendmarc_brand_voice",
            metadata={"description": "Sendmarc blog content for brand voice consistency"}
        )
    return _collection


def chunk_content(content: str, chunk_size: int = 800) -> List[str]:
    """
    Split content into semantic chunks
    
    Args:
        content: Text content
        chunk_size: Target chunk size in words
        
    Returns:
        List of content chunks
    """
    # Split by paragraphs first
    paragraphs = content.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_words = para.split()
        para_size = len(para_words)
        
        if current_size + para_size <= chunk_size:
            current_chunk.append(para)
            current_size += para_size
        else:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return [c for c in chunks if c.strip()]


def extract_metadata_from_content(content: str, filename: str) -> Dict[str, str]:
    """
    Extract metadata from blog content
    
    Args:
        content: Blog content
        filename: Source filename
        
    Returns:
        Metadata dictionary
    """
    lines = content.split('\n')
    title = ""
    
    # Try to find title (first H1)
    for line in lines:
        if line.strip().startswith('# '):
            title = line.strip()[2:]
            break
    
    # Simple topic detection based on keywords
    content_lower = content.lower()
    topic = "general"
    
    if 'dmarc' in content_lower:
        topic = "dmarc"
    elif 'spf' in content_lower or 'dkim' in content_lower:
        topic = "email_authentication"
    elif 'phishing' in content_lower:
        topic = "phishing"
    elif 'security' in content_lower:
        topic = "email_security"
    
    # Estimate technical level
    technical_keywords = ['implementation', 'configuration', 'dns', 'record', 'policy', 'protocol']
    technical_count = sum(1 for kw in technical_keywords if kw in content_lower)
    
    if technical_count > 10:
        technical_level = "advanced"
    elif technical_count > 5:
        technical_level = "intermediate"
    else:
        technical_level = "beginner"
    
    return {
        'title': title or filename,
        'topic': topic,
        'technical_level': technical_level,
        'source_file': filename
    }


def populate_chromadb(source_dir: str) -> int:
    """
    Populate ChromaDB with Sendmarc blog content
    
    Args:
        source_dir: Directory containing Sendmarc blog markdown files
        
    Returns:
        Number of chunks added
    """
    print(f"Populating ChromaDB from {source_dir}")
    
    collection = get_or_create_collection()
    model = get_embedding_model()
    
    # Check if collection already has content
    existing_count = collection.count()
    if existing_count > 0:
        print(f"Collection already has {existing_count} chunks. Skipping population.")
        return existing_count
    
    # Find all markdown files
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Warning: Source directory {source_dir} does not exist")
        print("Creating sample brand voice entry...")
        
        # Add a sample entry for demonstration
        sample_content = """
        # Understanding DMARC: A Comprehensive Guide
        
        DMARC (Domain-based Message Authentication, Reporting, and Conformance) is an email 
        authentication protocol that builds on SPF and DKIM to prevent email spoofing and 
        phishing attacks.
        
        ## Why DMARC Matters
        
        Email remains one of the primary attack vectors for cybercriminals. Without proper 
        authentication, attackers can easily impersonate your domain, damaging your brand 
        reputation and putting your customers at risk.
        
        ## How DMARC Works
        
        DMARC works by allowing domain owners to publish policies in their DNS records that 
        specify how to handle emails that fail authentication checks. This gives you control 
        over your domain's email security posture.
        """
        
        chunks = chunk_content(sample_content)
        metadata = {
            'title': 'Sample DMARC Guide',
            'topic': 'dmarc',
            'technical_level': 'intermediate',
            'source_file': 'sample.md'
        }
        
        for i, chunk in enumerate(chunks):
            embedding = model.encode([chunk])[0].tolist()
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = i
            
            collection.add(
                ids=[f"sample_{i}"],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[chunk_metadata]
            )
        
        print(f"Added {len(chunks)} sample chunks to collection")
        return len(chunks)
    
    markdown_files = list(source_path.glob('*.md'))
    
    if not markdown_files:
        print(f"No markdown files found in {source_dir}")
        return 0
    
    total_chunks = 0
    
    for md_file in markdown_files:
        print(f"Processing {md_file.name}...")
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            metadata = extract_metadata_from_content(content, md_file.name)
            
            # Chunk content
            chunks = chunk_content(content)
            
            # Generate embeddings
            embeddings = model.encode(chunks)
            
            # Add to ChromaDB
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = i
                
                doc_id = f"{md_file.stem}_{i}"
                
                collection.add(
                    ids=[doc_id],
                    embeddings=[embedding.tolist()],
                    documents=[chunk],
                    metadatas=[chunk_metadata]
                )
            
            total_chunks += len(chunks)
            print(f"  Added {len(chunks)} chunks from {md_file.name}")
            
        except Exception as e:
            print(f"  Error processing {md_file.name}: {e}")
    
    print(f"✓ Populated ChromaDB with {total_chunks} total chunks from {len(markdown_files)} files")
    
    return total_chunks


def retrieve_brand_examples(query: str, n: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve similar brand voice examples
    
    Args:
        query: Query text (topic or content to match)
        n: Number of examples to retrieve
        
    Returns:
        List of relevant content chunks with metadata
    """
    collection = get_or_create_collection()
    model = get_embedding_model()
    
    # Check if collection has any content
    collection_count = collection.count()
    if collection_count == 0:
        print("⚠ No brand voice examples found in database. Using default examples.")
        return []
    
    # Generate query embedding
    query_embedding = model.encode([query])[0].tolist()
    
    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n, collection_count)
    )
    
    # Format results
    examples = []
    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            example = {
                'content': doc,
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results['distances'] else 0
            }
            examples.append(example)
    
    return examples


def run(source_dir: str = None) -> Dict[str, Any]:
    """
    Execute Stage 4: Brand Voice RAG Setup
    
    Args:
        source_dir: Directory containing Sendmarc blog content
        
    Returns:
        Stage output dictionary
    """
    try:
        if source_dir is None:
            source_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'data',
                'sendmarc_blogs'
            )
        
        chunk_count = populate_chromadb(source_dir)
        
        return {
            'success': True,
            'chunks_added': chunk_count,
            'source_directory': source_dir,
            'message': 'Brand voice database populated successfully'
        }
        
    except Exception as e:
        print(f"Stage 4 failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    # Allow running as standalone script
    import sys
    
    if len(sys.argv) > 1:
        source_dir = sys.argv[1]
    else:
        source_dir = None
    
    result = run(source_dir)
    print(f"\nResult: {result}")

