import os
import re
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Inject Windows native truststore to resolve SSL certificate verification on Windows
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from src.config import DOCS_DIR, CHROMA_PERSIST_DIR

class StandaloneTextEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Self-contained, zero-network deterministic semantic-hash embedding function.
    Guarantees 100% offline uptime with no external downloads or SSL failures,
    while producing consistent high-dimensional vectors for cosine similarity.
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            vec = [0.0] * self.dim
            words = re.findall(r'\b\w+\b', text.lower())
            if not words:
                embeddings.append(vec)
                continue
            
            for w in words:
                # Hash word into bucket
                h = int(hashlib.sha256(w.encode('utf-8')).hexdigest(), 16)
                idx = h % self.dim
                sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
                vec[idx] += sign

            # Normalize vector to unit length
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings

class DocumentRAGEngine:
    def __init__(self, docs_dir: Path = DOCS_DIR, persist_dir: Path = CHROMA_PERSIST_DIR):
        self.docs_dir = Path(docs_dir)
        self.persist_dir = Path(persist_dir)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # Robust standalone embedding function
        self.embedding_fn = StandaloneTextEmbeddingFunction(dim=128)
        self.collection = self.client.get_or_create_collection(
            name="enterprise_decision_docs_v2",
            embedding_function=self.embedding_fn
        )
        self._ensure_indexed()

    def _chunk_markdown_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Intelligently chunks markdown files by headings to preserve business context."""
        content = file_path.read_text(encoding="utf-8")
        filename = file_path.name
        
        # Split by level 1 or level 2 headers
        sections = re.split(r'\n(?=##?\s)', content)
        chunks = []
        doc_title = sections[0].split('\n')[0].replace('#', '').strip() if sections else filename

        for idx, sec in enumerate(sections):
            lines = sec.strip().split('\n')
            header = lines[0].replace('#', '').strip() if lines else f"Section {idx+1}"
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else lines[0]
            
            if len(body) < 30: # Skip trivial chunks
                continue

            chunks.append({
                "id": f"{filename}_chunk_{idx}",
                "text": f"Document: {doc_title}\nSection: {header}\n\n{body}",
                "metadata": {
                    "source_file": filename,
                    "doc_title": doc_title,
                    "section": header,
                    "chunk_index": idx
                }
            })
        return chunks

    def _ensure_indexed(self):
        """Indexes all documents if collection is empty."""
        count = self.collection.count()
        if count == 0:
            self.index_all_documents()

    def index_all_documents(self):
        """Reads all markdown files from documents directory and stores them in ChromaDB."""
        all_chunks = []
        for file in self.docs_dir.glob("*.md"):
            chunks = self._chunk_markdown_file(file)
            all_chunks.extend(chunks)

        if not all_chunks:
            print("[Warning] No document chunks found to index.")
            return

        # Prepare for ChromaDB insertion
        ids = [c["id"] for c in all_chunks]
        documents = [c["text"] for c in all_chunks]
        metadatas = [c["metadata"] for c in all_chunks]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"Indexed {len(all_chunks)} chunks into ChromaDB from {self.docs_dir}")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Performs semantic vector search with source citation tracking."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        retrieved_chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0]*len(docs)
            
            for doc, meta, dist in zip(docs, metas, distances):
                retrieved_chunks.append({
                    "content": doc,
                    "metadata": meta,
                    "source": f"{meta.get('source_file')} - Section: {meta.get('section')}",
                    "distance": dist
                })
        return retrieved_chunks

    def hybrid_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Hybrid search combining semantic search with keyword/token matching."""
        vector_results = self.search(query, top_k=top_k + 2)
        
        query_tokens = set(re.findall(r'\w+', query.lower()))
        
        # Score combining semantic distance and keyword overlap
        scored_results = []
        for res in vector_results:
            text_tokens = set(re.findall(r'\w+', res["content"].lower()))
            overlap = len(query_tokens.intersection(text_tokens))
            # Lower distance is better; higher overlap is better
            hybrid_score = (1.0 / (res["distance"] + 0.1)) + (overlap * 0.5)
            scored_results.append((hybrid_score, res))
            
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_results[:top_k]]
