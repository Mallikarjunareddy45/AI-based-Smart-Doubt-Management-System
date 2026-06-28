from typing import List
import numpy as np
import logging

logger = logging.getLogger("uvicorn.error")

# Global placeholder for the Transformer model
_model = None

def get_embedding_model():
    """Lazy load sentence transformers model to conserve memory on worker startup."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Initializing SentenceTransformer 'all-MiniLM-L6-v2'...")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}. Falling back to mock embeddings.")
            _model = "fallback"
    return _model

def generate_embedding(text: str) -> List[float]:
    """Encode input question text into a 384-dimensional float vector."""
    model = get_embedding_model()
    if model == "fallback" or model is None:
        # Graceful development fallback: Generate a deterministic mock vector based on string hash
        import hashlib
        hash_val = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        vector = np.random.randn(384)
        norm = np.linalg.norm(vector)
        vector = vector / norm if norm > 0 else vector
        return vector.tolist()
        
    try:
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Embedding generation error: {e}. Returning mock vector.")
        return [0.0] * 384
