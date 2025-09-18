from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorSearchService:
    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.tickets_collection = "omnidesk_tickets"
        self.kb_collection = "omnidesk_knowledge"
        
        try:
            # Initialize Qdrant client
            if settings.QDRANT_URL and settings.QDRANT_API_KEY:
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY
                )
            else:
                # Local Qdrant instance
                self.client = QdrantClient(host="localhost", port=6333)
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Ensure collections exist
            self._ensure_collections()
            logger.info("Vector search service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector search: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if vector search service is available"""
        return self.client is not None and self.embedding_model is not None
    
    def _ensure_collections(self):
        """Create collections if they don't exist"""
        if not self.client:
            return
        
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            # Create tickets collection
            if self.tickets_collection not in collection_names:
                self.client.create_collection(
                    collection_name=self.tickets_collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.tickets_collection}")
            
            # Create knowledge base collection
            if self.kb_collection not in collection_names:
                self.client.create_collection(
                    collection_name=self.kb_collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.kb_collection}")
                
        except Exception as e:
            logger.error(f"Error creating Qdrant collections: {e}")
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        if not self.embedding_model:
            return []
        
        try:
            # Clean and prepare text
            clean_text = text.strip()
            if not clean_text:
                return []
            
            embeddings = self.embedding_model.encode(clean_text)
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    async def add_ticket_vector(self, ticket_id: str, content: str, metadata: Dict) -> bool:
        """Add ticket to vector database"""
        if not self.is_available():
            return False
        
        try:
            embeddings = self.generate_embeddings(content)
            if not embeddings:
                return False
            
            point = PointStruct(
                id=ticket_id,
                vector=embeddings,
                payload={
                    "ticket_id": ticket_id,
                    "content": content[:500],  # Truncate for storage
                    **metadata
                }
            )
            
            self.client.upsert(
                collection_name=self.tickets_collection,
                points=[point]
            )
            
            logger.debug(f"Added ticket vector: {ticket_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding ticket vector: {e}")
            return False
    
    async def search_similar_tickets(self, query_text: str, limit: int = 5,
                                   exclude_ticket_id: Optional[str] = None,
                                   category_filter: Optional[str] = None) -> List[Dict]:
        """Search for similar tickets"""
        if not self.is_available():
            return []
        
        try:
            embeddings = self.generate_embeddings(query_text)
            if not embeddings:
                return []
            
            # Build filters
            must_conditions = []
            if exclude_ticket_id:
                must_conditions.append(
                    FieldCondition(
                        key="ticket_id",
                        match=MatchValue(value=exclude_ticket_id)
                    )
                )
            
            must_not_conditions = []
            if category_filter:
                must_conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category_filter)
                    )
                )
            
            query_filter = None
            if must_conditions or must_not_conditions:
                query_filter = Filter(
                    must=must_conditions if must_conditions else None,
                    must_not=must_not_conditions if must_not_conditions else None
                )
            
            # Search for similar tickets
            search_results = self.client.search(
                collection_name=self.tickets_collection,
                query_vector=embeddings,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                score_threshold=0.7  # Only return reasonably similar tickets
            )
            
            results = []
            for result in search_results:
                results.append({
                    "ticket_id": result.id,
                    "similarity_score": result.score,
                    "metadata": result.payload
                })
            
            logger.debug(f"Found {len(results)} similar tickets")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar tickets: {e}")
            return []
    
    async def search_knowledge_base(self, query_text: str, limit: int = 3,
                                  category_filter: Optional[str] = None) -> List[Dict]:
        """Search knowledge base for relevant articles"""
        if not self.is_available():
            return []
        
        try:
            embeddings = self.generate_embeddings(query_text)
            if not embeddings:
                return []
            
            # Build category filter if provided
            query_filter = None
            if category_filter:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=category_filter)
                        )
                    ]
                )
            
            search_results = self.client.search(
                collection_name=self.kb_collection,
                query_vector=embeddings,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                score_threshold=0.6
            )
            
            results = []
            for result in search_results:
                results.append({
                    "article_id": result.id,
                    "relevance_score": result.score,
                    "content": result.payload
                })
            
            logger.debug(f"Found {len(results)} relevant knowledge articles")
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    async def add_knowledge_article(self, article_id: str, title: str, content: str,
                                  category: str, tags: List[str] = None) -> bool:
        """Add knowledge article to vector database"""
        if not self.is_available():
            return False
        
        try:
            # Combine title and content for embedding
            full_content = f"{title}\n\n{content}"
            embeddings = self.generate_embeddings(full_content)
            
            if not embeddings:
                return False
            
            point = PointStruct(
                id=article_id,
                vector=embeddings,
                payload={
                    "article_id": article_id,
                    "title": title,
                    "content": content[:1000],  # Truncate for storage
                    "category": category,
                    "tags": tags or []
                }
            )
            
            self.client.upsert(
                collection_name=self.kb_collection,
                points=[point]
            )
            
            logger.debug(f"Added knowledge article: {article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding knowledge article: {e}")
            return False
    
    async def update_ticket_vector(self, ticket_id: str, content: str, metadata: Dict) -> bool:
        """Update existing ticket vector"""
        return await self.add_ticket_vector(ticket_id, content, metadata)
    
    async def delete_ticket_vector(self, ticket_id: str) -> bool:
        """Delete ticket from vector database"""
        if not self.is_available():
            return False
        
        try:
            self.client.delete(
                collection_name=self.tickets_collection,
                points_selector=[ticket_id]
            )
            logger.debug(f"Deleted ticket vector: {ticket_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting ticket vector: {e}")
            return False

# Global vector service instance
vector_service = VectorSearchService()