"""
GPU-Accelerated Vector Search Engine for OmniDesk AI
Provides advanced semantic search capabilities with optimized vector operations,
intelligent indexing, and production-ready scaling features.
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import asynccontextmanager

# Qdrant imports
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, 
    MatchValue, Range, GeoBoundingBox, PayloadSchemaInfo,
    CreateCollection, OptimizersConfigDiff, HnswConfigDiff,
    SearchRequest, PointIdsList, UpdateCollection
)

# Sentence transformers
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel

logger = logging.getLogger(__name__)

@dataclass
class VectorSearchConfig:
    """Configuration for vector search engine"""
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    max_batch_size: int = 64
    cache_size: int = 10000
    search_timeout: float = 30.0
    enable_gpu: bool = True
    enable_quantization: bool = True

@dataclass
class VectorSearchResult:
    """Structured vector search result"""
    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None

@dataclass
class IndexStats:
    """Vector index statistics"""
    total_points: int
    collections: List[str]
    memory_usage_mb: float
    avg_search_time_ms: float
    cache_hit_rate: float
    gpu_utilization: float

class GPUAcceleratedVectorEngine:
    """
    Production-ready vector search engine with GPU acceleration,
    intelligent caching, and advanced semantic search capabilities
    """
    
    def __init__(self, config: VectorSearchConfig):
        self.config = config
        self.device = self._setup_device()
        self.client = None
        self.async_client = None
        self.embedding_model = None
        self.tokenizer = None
        
        # Collections
        self.collections = {
            'tickets': 'omnidesk_tickets_v2',
            'knowledge': 'omnidesk_knowledge_v2',
            'responses': 'omnidesk_responses_v2',
            'users': 'omnidesk_users_v2'
        }
        
        # Performance tracking
        self.stats = IndexStats(
            total_points=0,
            collections=[],
            memory_usage_mb=0.0,
            avg_search_time_ms=0.0,
            cache_hit_rate=0.0,
            gpu_utilization=0.0
        )
        
        # Thread safety
        self._lock = asyncio.Lock()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Caching
        self._embedding_cache = {}
        self._search_cache = {}
        
        logger.info(f"Vector Engine initialized with device: {self.device}")
        
    def _setup_device(self) -> torch.device:
        """Setup optimal device for vector operations"""
        if self.config.enable_gpu and torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"GPU enabled: {torch.cuda.get_device_name()}")
            
            # Enable optimizations
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.enabled = True
            
        else:
            device = torch.device("cpu")
            logger.info("Using CPU for vector operations")
            
        return device
    
    async def initialize(self):
        """Initialize the vector engine asynchronously"""
        try:
            # Initialize clients
            await self._initialize_clients()
            
            # Load embedding model
            await self._load_embedding_model()
            
            # Setup collections
            await self._setup_collections()
            
            # Load existing stats
            await self._update_stats()
            
            logger.info("Vector Engine initialization complete")
            
        except Exception as e:
            logger.error(f"Vector Engine initialization failed: {e}")
            raise
    
    async def _initialize_clients(self):
        """Initialize Qdrant clients"""
        try:
            if self.config.qdrant_api_key:
                self.client = QdrantClient(
                    url=self.config.qdrant_url,
                    api_key=self.config.qdrant_api_key,
                    timeout=self.config.search_timeout
                )
                self.async_client = AsyncQdrantClient(
                    url=self.config.qdrant_url,
                    api_key=self.config.qdrant_api_key,
                    timeout=self.config.search_timeout
                )
            else:
                self.client = QdrantClient(
                    host="localhost", 
                    port=6333,
                    timeout=self.config.search_timeout
                )
                self.async_client = AsyncQdrantClient(
                    host="localhost",
                    port=6333,
                    timeout=self.config.search_timeout
                )
            
            # Test connection
            await self.async_client.get_collections()
            logger.info("Qdrant connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant clients: {e}")
            raise
    
    async def _load_embedding_model(self):
        """Load embedding model with GPU optimization"""
        try:
            # Load model
            self.embedding_model = SentenceTransformer(self.config.embedding_model)
            
            # Move to GPU if available
            if self.device.type == 'cuda':
                self.embedding_model = self.embedding_model.to(self.device)
                
                # Enable half precision for memory efficiency
                if self.config.enable_quantization:
                    self.embedding_model.half()
            
            # Load tokenizer for advanced processing
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.embedding_model.replace('sentence-transformers/', '')
            )
            
            logger.info(f"Embedding model loaded: {self.config.embedding_model}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    async def _setup_collections(self):
        """Setup optimized Qdrant collections"""
        try:
            existing_collections = await self.async_client.get_collections()
            existing_names = {col.name for col in existing_collections.collections}
            
            for purpose, collection_name in self.collections.items():
                if collection_name not in existing_names:
                    await self._create_optimized_collection(collection_name, purpose)
                else:
                    await self._optimize_existing_collection(collection_name)
            
            self.stats.collections = list(self.collections.values())
            logger.info(f"Collections setup complete: {self.stats.collections}")
            
        except Exception as e:
            logger.error(f"Collection setup failed: {e}")
            raise
    
    async def _create_optimized_collection(self, collection_name: str, purpose: str):
        """Create optimized collection with proper configuration"""
        # Optimize HNSW parameters based on use case
        hnsw_config = HnswConfigDiff(
            m=48,  # Higher connectivity for better recall
            ef_construct=200,  # Better indexing quality
            full_scan_threshold=20000,  # Switch to full scan for small datasets
            max_indexing_threads=4  # Parallel indexing
        )
        
        # Optimize for memory vs speed trade-off
        optimizers_config = OptimizersConfigDiff(
            deleted_threshold=0.2,
            vacuum_min_vector_number=1000,
            default_segment_number=4,  # Parallel processing
            max_segment_size=200000,  # Memory management
            memmap_threshold=100000,  # Use memory mapping for large segments
            indexing_threshold=50000,  # Start indexing threshold
            flush_interval_sec=30,  # Batch writes
            max_optimization_threads=2  # Background optimization
        )
        
        await self.async_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=self.config.embedding_dim,
                distance=Distance.COSINE,
                hnsw_config=hnsw_config
            ),
            optimizers_config=optimizers_config,
            shard_number=1,  # Can be increased for scaling
            replication_factor=1  # For production, use 2+
        )
        
        logger.info(f"Created optimized collection: {collection_name}")
    
    async def _optimize_existing_collection(self, collection_name: str):
        """Optimize existing collection parameters"""
        try:
            # Update collection with optimized parameters
            await self.async_client.update_collection(
                collection_name=collection_name,
                optimizer_config=OptimizersConfigDiff(
                    indexing_threshold=50000,
                    flush_interval_sec=30
                )
            )
            
            logger.debug(f"Optimized existing collection: {collection_name}")
            
        except Exception as e:
            logger.warning(f"Could not optimize collection {collection_name}: {e}")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    async def generate_embeddings_batch(self, 
                                      texts: List[str], 
                                      batch_size: Optional[int] = None) -> List[np.ndarray]:
        """
        Generate embeddings with GPU acceleration and intelligent batching
        
        Args:
            texts: List of texts to embed
            batch_size: Override default batch size
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        batch_size = batch_size or self.config.max_batch_size
        start_time = time.time()
        
        try:
            embeddings = []
            cache_hits = 0
            
            # Check cache first
            uncached_texts = []
            uncached_indices = []
            
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    embeddings.append(self._embedding_cache[cache_key])
                    cache_hits += 1
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
                    embeddings.append(None)  # Placeholder
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = await self._generate_embeddings_gpu(uncached_texts, batch_size)
                
                # Cache and insert results
                for idx, embedding in zip(uncached_indices, new_embeddings):
                    cache_key = self._get_cache_key(texts[idx])
                    self._embedding_cache[cache_key] = embedding
                    embeddings[idx] = embedding
                    
                    # Limit cache size
                    if len(self._embedding_cache) > self.config.cache_size:
                        # Remove oldest entries (simple FIFO)
                        oldest_key = next(iter(self._embedding_cache))
                        del self._embedding_cache[oldest_key]
            
            processing_time = time.time() - start_time
            
            # Update cache hit rate
            total_requests = len(texts)
            self.stats.cache_hit_rate = (
                (self.stats.cache_hit_rate * 0.9) + 
                (cache_hits / total_requests * 0.1)
            ) if total_requests > 0 else self.stats.cache_hit_rate
            
            logger.debug(f"Generated {len(embeddings)} embeddings in {processing_time:.3f}s "
                        f"(cache hits: {cache_hits}/{total_requests})")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            return [np.array([]) for _ in texts]
    
    async def _generate_embeddings_gpu(self, texts: List[str], batch_size: int) -> List[np.ndarray]:
        """Generate embeddings using GPU acceleration"""
        try:
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                with torch.no_grad():
                    # Encode batch
                    if self.device.type == 'cuda':
                        batch_embeddings = self.embedding_model.encode(
                            batch,
                            convert_to_tensor=True,
                            device=self.device,
                            show_progress_bar=False,
                            batch_size=min(len(batch), 32)  # GPU memory management
                        )
                        
                        # Convert to CPU numpy arrays
                        if isinstance(batch_embeddings, torch.Tensor):
                            batch_embeddings = batch_embeddings.cpu().numpy()
                            
                    else:
                        batch_embeddings = self.embedding_model.encode(
                            batch,
                            show_progress_bar=False,
                            batch_size=len(batch)
                        )
                    
                    all_embeddings.extend(batch_embeddings)
                    
                    # Clear GPU cache periodically
                    if self.device.type == 'cuda' and i % (batch_size * 4) == 0:
                        torch.cuda.empty_cache()
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"GPU embedding generation failed: {e}")
            raise
    
    async def add_vectors_batch(self, 
                              collection_purpose: str,
                              vectors_data: List[Dict[str, Any]]) -> bool:
        """
        Add multiple vectors to collection with optimized batching
        
        Args:
            collection_purpose: Purpose key ('tickets', 'knowledge', etc.)
            vectors_data: List of dicts with 'id', 'text', 'metadata'
            
        Returns:
            Success status
        """
        if not vectors_data or collection_purpose not in self.collections:
            return False
        
        try:
            collection_name = self.collections[collection_purpose]
            
            # Extract texts and generate embeddings
            texts = [item['text'] for item in vectors_data]
            embeddings = await self.generate_embeddings_batch(texts)
            
            if len(embeddings) != len(vectors_data):
                logger.error("Embedding generation mismatch")
                return False
            
            # Create points for batch upsert
            points = []
            for i, (item, embedding) in enumerate(zip(vectors_data, embeddings)):
                if len(embedding) == 0:
                    continue
                    
                point = PointStruct(
                    id=item['id'],
                    vector=embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
                    payload={
                        'text': item['text'][:2000],  # Truncate for storage
                        'created_at': datetime.utcnow().isoformat(),
                        'collection_purpose': collection_purpose,
                        **(item.get('metadata', {}))
                    }
                )
                points.append(point)
            
            if not points:
                logger.warning("No valid points to add")
                return False
            
            # Batch upsert with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await self.async_client.upsert(
                        collection_name=collection_name,
                        points=points,
                        wait=True  # Ensure consistency
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            # Update stats
            self.stats.total_points += len(points)
            
            logger.info(f"Added {len(points)} vectors to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Batch vector addition failed: {e}")
            return False
    
    async def search_similar_advanced(self,
                                    query_text: str,
                                    collection_purpose: str,
                                    limit: int = 10,
                                    filters: Optional[Dict[str, Any]] = None,
                                    min_score: float = 0.7,
                                    include_vectors: bool = False) -> List[VectorSearchResult]:
        """
        Advanced semantic search with filtering and optimization
        
        Args:
            query_text: Search query
            collection_purpose: Collection to search in
            limit: Maximum results
            filters: Optional filters (category, date_range, etc.)
            min_score: Minimum similarity score
            include_vectors: Include vector data in results
            
        Returns:
            List of search results
        """
        start_time = time.time()
        
        try:
            if collection_purpose not in self.collections:
                logger.error(f"Unknown collection purpose: {collection_purpose}")
                return []
            
            collection_name = self.collections[collection_purpose]
            
            # Generate query embedding
            query_embeddings = await self.generate_embeddings_batch([query_text])
            if not query_embeddings or len(query_embeddings[0]) == 0:
                logger.error("Failed to generate query embedding")
                return []
            
            query_vector = query_embeddings[0].tolist() if isinstance(query_embeddings[0], np.ndarray) else query_embeddings[0]
            
            # Build filters
            search_filter = self._build_search_filter(filters) if filters else None
            
            # Perform search
            search_results = await self.async_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=min_score,
                with_payload=True,
                with_vectors=include_vectors
            )
            
            # Convert to structured results
            results = []
            for result in search_results:
                search_result = VectorSearchResult(
                    id=str(result.id),
                    score=float(result.score),
                    payload=result.payload or {},
                    vector=result.vector if include_vectors else None
                )
                results.append(search_result)
            
            search_time = (time.time() - start_time) * 1000
            self._update_search_stats(search_time)
            
            logger.debug(f"Found {len(results)} results in {search_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            return []
    
    def _build_search_filter(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """Build Qdrant filter from search parameters"""
        conditions = []
        
        try:
            # Category filter
            if 'category' in filters:
                conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=filters['category'])
                    )
                )
            
            # Date range filter
            if 'date_from' in filters or 'date_to' in filters:
                date_range = {}
                if 'date_from' in filters:
                    date_range['gte'] = filters['date_from']
                if 'date_to' in filters:
                    date_range['lte'] = filters['date_to']
                
                conditions.append(
                    FieldCondition(
                        key="created_at",
                        range=Range(**date_range)
                    )
                )
            
            # User/department filter
            if 'user_id' in filters:
                conditions.append(
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=filters['user_id'])
                    )
                )
            
            # Status filter
            if 'status' in filters:
                conditions.append(
                    FieldCondition(
                        key="status",
                        match=MatchValue(value=filters['status'])
                    )
                )
            
            # Exclude specific IDs
            if 'exclude_ids' in filters:
                for exclude_id in filters['exclude_ids']:
                    conditions.append(
                        FieldCondition(
                            key="id",
                            match=MatchValue(value=exclude_id)
                        )
                    )
            
            return Filter(must=conditions) if conditions else None
            
        except Exception as e:
            logger.error(f"Filter building failed: {e}")
            return None
    
    def _update_search_stats(self, search_time_ms: float):
        """Update search performance statistics"""
        # Exponential moving average
        alpha = 0.1
        self.stats.avg_search_time_ms = (
            (1 - alpha) * self.stats.avg_search_time_ms + 
            alpha * search_time_ms
        )
    
    async def _update_stats(self):
        """Update comprehensive statistics"""
        try:
            total_points = 0
            memory_usage = 0.0
            
            for collection_name in self.collections.values():
                try:
                    info = await self.async_client.get_collection(collection_name)
                    total_points += info.points_count or 0
                    
                    # Estimate memory usage (rough calculation)
                    if info.points_count:
                        memory_usage += (info.points_count * self.config.embedding_dim * 4) / (1024 * 1024)  # MB
                        
                except Exception as e:
                    logger.warning(f"Could not get stats for {collection_name}: {e}")
            
            self.stats.total_points = total_points
            self.stats.memory_usage_mb = memory_usage
            
            # GPU utilization
            if self.device.type == 'cuda':
                self.stats.gpu_utilization = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() * 100
            
        except Exception as e:
            logger.error(f"Stats update failed: {e}")
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        await self._update_stats()
        
        return {
            'stats': asdict(self.stats),
            'config': {
                'embedding_model': self.config.embedding_model,
                'embedding_dim': self.config.embedding_dim,
                'device': str(self.device),
                'gpu_available': torch.cuda.is_available(),
                'collections': self.collections
            },
            'cache_info': {
                'embedding_cache_size': len(self._embedding_cache),
                'embedding_cache_max': self.config.cache_size,
                'cache_hit_rate': f"{self.stats.cache_hit_rate:.2%}"
            }
        }
    
    async def optimize_index(self, collection_purpose: str) -> bool:
        """Optimize collection index for better performance"""
        try:
            collection_name = self.collections[collection_purpose]
            
            # Trigger index optimization
            await self.async_client.update_collection(
                collection_name=collection_name,
                optimizer_config=OptimizersConfigDiff(
                    indexing_threshold=0  # Force immediate indexing
                )
            )
            
            logger.info(f"Index optimization triggered for {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Index optimization failed: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.executor:
                self.executor.shutdown(wait=True)
            
            if self.async_client:
                await self.async_client.close()
            
            # Clear caches
            self._embedding_cache.clear()
            self._search_cache.clear()
            
            # Clear GPU memory
            if self.device.type == 'cuda':
                torch.cuda.empty_cache()
            
            logger.info("Vector Engine cleanup complete")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Global instance
vector_engine = None

async def get_vector_engine(config: Optional[VectorSearchConfig] = None) -> GPUAcceleratedVectorEngine:
    """Get singleton vector engine instance"""
    global vector_engine
    if vector_engine is None:
        config = config or VectorSearchConfig()
        vector_engine = GPUAcceleratedVectorEngine(config)
        await vector_engine.initialize()
    return vector_engine