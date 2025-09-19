"""
Advanced Monitoring and Observability Infrastructure for OmniDesk AI
Provides comprehensive monitoring, structured logging, metrics collection,
health checks, and alerting for production deployment.
"""

import asyncio
import time
import json
import logging
import psutil
import traceback
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import threading
from functools import wraps
import os

# Prometheus metrics
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Info, Summary,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Structured logging
import structlog

# Health check utilities
import redis.asyncio as redis
import psycopg2
from sqlalchemy import text

logger = structlog.get_logger(__name__)

@dataclass
class HealthStatus:
    """Health check status information"""
    service: str
    status: str  # healthy, degraded, unhealthy
    message: str
    response_time_ms: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class MetricsSnapshot:
    """System metrics snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int
    request_rate_per_minute: float
    error_rate_percent: float
    response_time_p95: float
    gpu_utilization: Optional[float] = None
    gpu_memory_usage: Optional[float] = None

class PrometheusMetrics:
    """Prometheus metrics collection"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize Prometheus metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        # Request metrics
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        # AI processing metrics
        self.ai_processing_duration = Histogram(
            'ai_processing_duration_seconds',
            'AI processing duration in seconds',
            ['operation', 'model', 'gpu_accelerated'],
            registry=self.registry
        )
        
        self.ai_requests_total = Counter(
            'ai_requests_total',
            'Total AI requests',
            ['operation', 'model', 'status'],
            registry=self.registry
        )
        
        self.ai_confidence_score = Histogram(
            'ai_confidence_score',
            'AI confidence scores',
            ['operation', 'model'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        # System metrics
        self.system_cpu_percent = Gauge(
            'system_cpu_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_percent = Gauge(
            'system_memory_percent',
            'System memory usage percentage',
            registry=self.registry
        )
        
        self.system_disk_percent = Gauge(
            'system_disk_percent',
            'System disk usage percentage',
            registry=self.registry
        )
        
        # Database metrics
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation', 'table'],
            registry=self.registry
        )
        
        # Vector database metrics
        self.vector_search_duration = Histogram(
            'vector_search_duration_seconds',
            'Vector search duration in seconds',
            ['collection', 'similarity_threshold'],
            registry=self.registry
        )
        
        self.vector_embeddings_generated = Counter(
            'vector_embeddings_generated_total',
            'Total embeddings generated',
            ['model', 'batch_size'],
            registry=self.registry
        )
        
        # GPU metrics (if available)
        try:
            import pynvml
            pynvml.nvmlInit()
            
            self.gpu_utilization = Gauge(
                'gpu_utilization_percent',
                'GPU utilization percentage',
                ['gpu_id'],
                registry=self.registry
            )
            
            self.gpu_memory_usage = Gauge(
                'gpu_memory_usage_percent',
                'GPU memory usage percentage',
                ['gpu_id'],
                registry=self.registry
            )
            
            self.gpu_temperature = Gauge(
                'gpu_temperature_celsius',
                'GPU temperature in Celsius',
                ['gpu_id'],
                registry=self.registry
            )
            
        except ImportError:
            logger.warning("pynvml not available, GPU metrics disabled")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.request_duration.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).observe(duration)
        
        self.request_count.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()
    
    def record_ai_processing(self, operation: str, model: str, duration: float, 
                           confidence: float, gpu_accelerated: bool, status: str):
        """Record AI processing metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.ai_processing_duration.labels(
            operation=operation, model=model, gpu_accelerated=gpu_accelerated
        ).observe(duration)
        
        self.ai_requests_total.labels(
            operation=operation, model=model, status=status
        ).inc()
        
        self.ai_confidence_score.labels(
            operation=operation, model=model
        ).observe(confidence)
    
    def update_system_metrics(self):
        """Update system metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        # CPU and memory
        self.system_cpu_percent.set(psutil.cpu_percent(interval=1))
        self.system_memory_percent.set(psutil.virtual_memory().percent)
        self.system_disk_percent.set(psutil.disk_usage('/').percent)
        
        # GPU metrics (if available)
        try:
            import pynvml
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # GPU utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                self.gpu_utilization.labels(gpu_id=str(i)).set(util.gpu)
                
                # GPU memory
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                memory_percent = (mem_info.used / mem_info.total) * 100
                self.gpu_memory_usage.labels(gpu_id=str(i)).set(memory_percent)
                
                # GPU temperature
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                self.gpu_temperature.labels(gpu_id=str(i)).set(temp)
                
        except Exception as e:
            logger.warning(f"Failed to collect GPU metrics: {e}")

class StructuredLogger:
    """Enhanced structured logging system"""
    
    def __init__(self, service_name: str = "omnidesk-ai"):
        self.service_name = service_name
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup structured logging configuration"""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Configure standard logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f"/app/logs/{self.service_name}.log")
            ]
        )
    
    def get_logger(self, name: str):
        """Get a structured logger instance"""
        return structlog.get_logger(name).bind(service=self.service_name)

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, HealthStatus] = {}
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.checks[name] = check_func
    
    async def check_database(self, database_url: str) -> HealthStatus:
        """Check database connectivity"""
        start_time = time.time()
        
        try:
            # Simple connection test
            import psycopg2
            conn = psycopg2.connect(database_url, connect_timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                service="database",
                status="healthy",
                message="Database connection successful",
                response_time_ms=response_time,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def check_redis(self, redis_url: str) -> HealthStatus:
        """Check Redis connectivity"""
        start_time = time.time()
        
        try:
            redis_client = redis.from_url(redis_url)
            await redis_client.ping()
            await redis_client.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                service="redis",
                status="healthy",
                message="Redis connection successful",
                response_time_ms=response_time,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service="redis",
                status="unhealthy",
                message=f"Redis connection failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def check_qdrant(self, qdrant_url: str) -> HealthStatus:
        """Check Qdrant vector database"""
        start_time = time.time()
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{qdrant_url}/collections", timeout=5.0)
                response.raise_for_status()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                service="qdrant",
                status="healthy",
                message="Qdrant vector database accessible",
                response_time_ms=response_time,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service="qdrant",
                status="unhealthy",
                message=f"Qdrant connection failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def check_ai_service(self) -> HealthStatus:
        """Check AI service availability"""
        start_time = time.time()
        
        try:
            # Import AI engine and test basic functionality
            from ai.services.ai_engine import get_ai_engine
            
            ai_engine = get_ai_engine()
            
            # Test embedding generation
            embeddings = await ai_engine.generate_embeddings(["test text"])
            
            if len(embeddings) > 0 and len(embeddings[0]) > 0:
                response_time = (time.time() - start_time) * 1000
                
                return HealthStatus(
                    service="ai_service",
                    status="healthy",
                    message="AI service operational",
                    response_time_ms=response_time,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "gpu_available": ai_engine.device.type == 'cuda',
                        "models_loaded": len(ai_engine.models)
                    }
                )
            else:
                raise Exception("AI service returned empty results")
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service="ai_service",
                status="degraded",
                message=f"AI service issues: {str(e)}",
                response_time_ms=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def run_all_checks(self, config: Dict[str, str]) -> Dict[str, HealthStatus]:
        """Run all registered health checks"""
        results = {}
        
        # Database check
        if "database_url" in config:
            results["database"] = await self.check_database(config["database_url"])
        
        # Redis check
        if "redis_url" in config:
            results["redis"] = await self.check_redis(config["redis_url"])
        
        # Qdrant check
        if "qdrant_url" in config:
            results["qdrant"] = await self.check_qdrant(config["qdrant_url"])
        
        # AI service check
        results["ai_service"] = await self.check_ai_service()
        
        # Custom checks
        for name, check_func in self.checks.items():
            try:
                results[name] = await check_func()
            except Exception as e:
                results[name] = HealthStatus(
                    service=name,
                    status="unhealthy",
                    message=f"Check failed: {str(e)}",
                    response_time_ms=0,
                    timestamp=datetime.utcnow()
                )
        
        self.last_results = results
        return results

class PerformanceMonitor:
    """Performance monitoring and alerting"""
    
    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics
        self.alert_thresholds = {
            "response_time_p95": 5.0,  # seconds
            "error_rate": 0.05,        # 5%
            "cpu_usage": 80.0,         # 80%
            "memory_usage": 85.0,      # 85%
            "disk_usage": 90.0,        # 90%
            "gpu_temperature": 80.0    # 80°C
        }
        self.alerts: List[Dict] = []
    
    def check_thresholds(self, snapshot: MetricsSnapshot) -> List[Dict]:
        """Check metrics against alert thresholds"""
        alerts = []
        
        # CPU usage alert
        if snapshot.cpu_percent > self.alert_thresholds["cpu_usage"]:
            alerts.append({
                "severity": "warning",
                "metric": "cpu_usage",
                "value": snapshot.cpu_percent,
                "threshold": self.alert_thresholds["cpu_usage"],
                "message": f"High CPU usage: {snapshot.cpu_percent:.1f}%"
            })
        
        # Memory usage alert
        if snapshot.memory_percent > self.alert_thresholds["memory_usage"]:
            alerts.append({
                "severity": "warning",
                "metric": "memory_usage",
                "value": snapshot.memory_percent,
                "threshold": self.alert_thresholds["memory_usage"],
                "message": f"High memory usage: {snapshot.memory_percent:.1f}%"
            })
        
        # Error rate alert
        if snapshot.error_rate_percent > self.alert_thresholds["error_rate"]:
            alerts.append({
                "severity": "critical",
                "metric": "error_rate",
                "value": snapshot.error_rate_percent,
                "threshold": self.alert_thresholds["error_rate"],
                "message": f"High error rate: {snapshot.error_rate_percent:.2%}"
            })
        
        return alerts

class ObservabilityManager:
    """Central observability management"""
    
    def __init__(self, service_name: str = "omnidesk-ai"):
        self.service_name = service_name
        self.metrics = PrometheusMetrics() if PROMETHEUS_AVAILABLE else None
        self.logger_manager = StructuredLogger(service_name)
        self.health_checker = HealthChecker()
        self.performance_monitor = PerformanceMonitor(self.metrics) if self.metrics else None
        
        # Background monitoring
        self._monitoring_task = None
        self._shutdown_event = asyncio.Event()
    
    def get_logger(self, name: str):
        """Get structured logger"""
        return self.logger_manager.get_logger(name)
    
    def start_monitoring(self):
        """Start background monitoring tasks"""
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        if self._monitoring_task:
            self._shutdown_event.set()
            await self._monitoring_task
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        logger = self.get_logger("monitoring")
        
        while not self._shutdown_event.is_set():
            try:
                # Update system metrics
                if self.metrics:
                    self.metrics.update_system_metrics()
                
                # Log system status
                logger.info(
                    "System metrics updated",
                    cpu_percent=psutil.cpu_percent(),
                    memory_percent=psutil.virtual_memory().percent,
                    disk_percent=psutil.disk_usage('/').percent
                )
                
                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error("Monitoring loop error", error=str(e), traceback=traceback.format_exc())
                await asyncio.sleep(5)  # Short delay before retry
    
    async def get_health_status(self, config: Dict[str, str]) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health_results = await self.health_checker.run_all_checks(config)
        
        # Calculate overall status
        statuses = [result.status for result in health_results.values()]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "checks": {name: asdict(result) for name, result in health_results.items()}
        }
    
    def get_metrics_snapshot(self) -> MetricsSnapshot:
        """Get current metrics snapshot"""
        return MetricsSnapshot(
            timestamp=datetime.utcnow(),
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage('/').percent,
            active_connections=len(psutil.net_connections()),
            request_rate_per_minute=0.0,  # Would be calculated from metrics
            error_rate_percent=0.0,       # Would be calculated from metrics
            response_time_p95=0.0,        # Would be calculated from metrics
        )

# Decorators for automatic monitoring
def monitor_performance(operation: str):
    """Decorator to automatically monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = structlog.get_logger(func.__name__)
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"{operation} completed successfully",
                    operation=operation,
                    duration_seconds=duration,
                    function=func.__name__
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    duration_seconds=duration,
                    function=func.__name__,
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = structlog.get_logger(func.__name__)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"{operation} completed successfully",
                    operation=operation,
                    duration_seconds=duration,
                    function=func.__name__
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    duration_seconds=duration,
                    function=func.__name__,
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Global observability manager
observability_manager: Optional[ObservabilityManager] = None

def get_observability_manager() -> ObservabilityManager:
    """Get global observability manager"""
    global observability_manager
    if observability_manager is None:
        observability_manager = ObservabilityManager()
        observability_manager.start_monitoring()
    return observability_manager

# Export main components
__all__ = [
    'ObservabilityManager', 'PrometheusMetrics', 'StructuredLogger',
    'HealthChecker', 'PerformanceMonitor', 'HealthStatus', 'MetricsSnapshot',
    'monitor_performance', 'get_observability_manager'
]