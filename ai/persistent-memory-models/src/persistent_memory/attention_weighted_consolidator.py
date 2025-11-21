class AttentionWeightedConsolidator:
    """
    Consolidate memories based on attention patterns
    Important memories (high attention) preserved longer
    """
    
    def __init__(self, transformer_model):
        self.model = transformer_model
        self.importance_scores = {}
    
    def track_attention(self, conversation_turn_id, attention_weights):
        """
        Track which parts of context received high attention
        """
        # Average attention across layers and heads
        avg_attention = attention_weights.mean(dim=(0, 1))
        
        # Update importance scores
        if conversation_turn_id not in self.importance_scores:
            self.importance_scores[conversation_turn_id] = []
        
        self.importance_scores[conversation_turn_id].append(avg_attention)
    
    def consolidate_memories(self, episodic_memory, threshold_days=7):
        """
        Consolidate low-attention memories, preserve high-attention ones
        """
        old_memories = episodic_memory.get_old_memories(threshold_days)
        
        for memory in old_memories:
            # Compute aggregate importance
            importance = np.mean(
                self.importance_scores.get(memory['id'], [0.5])
            )
            
            if importance < 0.3:  # Low importance
                # Compress aggressively or archive
                episodic_memory.archive(memory, compression='high')
            elif importance < 0.7:  # Medium importance
                # Summarize and store summary
                summary = self._summarize(memory)
                episodic_memory.replace_with_summary(memory['id'], summary)
            else:  # High importance
                # Keep full detail, just move to long-term storage
                episodic_memory.move_to_long_term(memory)
