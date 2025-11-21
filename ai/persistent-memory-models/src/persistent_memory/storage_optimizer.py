class StorageOptimizer:
    """
    Optimize storage usage for persistent structures
    """
    
    def __init__(self, context_engine):
        self.engine = context_engine
        self.compression_ratio = 0.1  # Target 10% of original size
    
    async def optimize_storage(self):
        """
        Periodic storage optimization
        """
        # 1. Garbage collect unreferenced versions
        await self._gc_old_versions()
        
        # 2. Compress old embeddings
        await self._compress_old_embeddings()
        
        # 3. Deduplicate similar contexts
        await self._deduplicate_contexts()
        
        # 4. Merge similar semantic nodes
        await self._merge_similar_nodes()
    
    async def _compress_old_embeddings(self):
        """
        Compress embeddings older than threshold
        """
        old_embeddings = self.engine.episodic.get_old_embeddings(
            age_days=30
        )
        
        # Train compression model on old data
        compressor = await self._train_compressor(old_embeddings)
        
        # Compress and replace
        for embedding_id, embedding in old_embeddings:
            compressed = compressor.compress(embedding)
            await self.engine.episodic.replace_embedding(
                embedding_id,
                compressed,
                compression_metadata={'type': 'autoencoder', 'ratio': 0.1}
            )
    
    async def _deduplicate_contexts(self):
        """
        Find and deduplicate nearly identical contexts
        """
        # Cluster similar embeddings
        embeddings = await self.engine.episodic.get_all_embeddings()
        clusters = self._cluster_embeddings(embeddings, threshold=0.95)
        
        # For each cluster, keep best representative
        for cluster in clusters:
            if len(cluster) > 1:
                # Keep most recent or most important
                representative = max(
                    cluster, 
                    key=lambda e: e['importance'] * e['recency']
                )
                
                # Replace others with reference to representative
                for embedding in cluster:
                    if embedding != representative:
                        await self.engine.episodic.replace_with_reference(
                            embedding['id'],
                            representative['id']
                        )
