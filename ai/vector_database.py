from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import os
import uuid
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class QdrantVectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "ticket_embeddings"
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
    
    def add_ticket_embedding(self, ticket_id: str, text: str, metadata: Dict[str, Any]):
        """Add ticket embedding to vector store"""
        try:
            # Generate embedding
            embedding = list(self.model.encode(text))
            
            # Create point
            # Use ticket_id as the point id to make updates easier
            point = PointStruct(
                id=ticket_id,
                vector=embedding,
                payload={
                    "ticket_id": ticket_id,
                    "text": text,
                    **(metadata or {})
                }
            )

            # Insert or update point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Added embedding for ticket: {ticket_id}")
            
        except Exception as e:
            logger.error(f"Error adding ticket embedding: {e}")
    
    def find_similar_tickets(self, query_text: str, limit: int = 5) -> List[Dict]:
        """Find similar tickets based on query text"""
        try:
            # Generate query embedding
            query_embedding = list(self.model.encode(query_text))

            # Search similar vectors
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=0.0  # return results, we'll filter by score if needed
            )
            
            # Format results
            similar_tickets = []
            for result in search_result:
                payload = getattr(result, 'payload', result.get('payload') if isinstance(result, dict) else {})
                score = getattr(result, 'score', result.get('score') if isinstance(result, dict) else None)
                similar_tickets.append({
                    "ticket_id": payload.get("ticket_id"),
                    "text": payload.get("text"),
                    "similarity_score": score,
                    "metadata": {k: v for k, v in payload.items() 
                               if k not in ["ticket_id", "text"]}
                })
            
            return similar_tickets
            
        except Exception as e:
            logger.error(f"Error finding similar tickets: {e}")
            return []
    
    def update_ticket_embedding(self, ticket_id: str, text: str, metadata: Dict[str, Any]):
        """Update existing ticket embedding"""
        try:
            # Since we store point id as ticket_id, upsert will overwrite existing point
            self.add_ticket_embedding(ticket_id, text, metadata)
            
        except Exception as e:
            logger.error(f"Error updating ticket embedding: {e}")

# Global instance
vector_store = QdrantVectorStore()