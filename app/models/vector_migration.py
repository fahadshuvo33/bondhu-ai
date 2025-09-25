from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from app.models._base import BaseModelWithIntID


class VectorMigrationConfig(BaseModelWithIntID):
    """Configuration for vector database migration"""

    __tablename__ = "vector_migration_config"

    # Target vector DB
    vector_db_type = Column(String)  # pinecone, weaviate, qdrant, milvus
    connection_string = Column(Text)  # Encrypted

    # Migration settings
    # Migration settings
    batch_size = Column(Integer, default=100)
    parallel_workers = Column(Integer, default=4)

    # Indexing strategy
    index_name = Column(String)
    dimension = Column(Integer, default=1536)
    metric = Column(String, default="cosine")  # cosine, euclidean, dot_product

    # Namespace/Collection strategy
    namespace_strategy = Column(String)  # by_user, by_subject, by_date, global

    # Sync strategy
    sync_mode = Column(String)  # real_time, batch, hybrid
    sync_interval_minutes = Column(Integer, default=60)

    # Feature flags
    keep_pg_vectors = Column(Boolean, default=True)  # Keep vectors in PG for fallback
    use_hybrid_search = Column(Boolean, default=True)  # Combine PG and vector DB

    # Status
    is_active = Column(Boolean, default=False)
    migration_started_at = Column(DateTime(timezone=True), nullable=True)
    migration_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Stats
    total_documents_migrated = Column(Integer, default=0)
    total_chunks_migrated = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
