class HierarchicalSummarizer:
    """
    Create multi-level summaries of long contexts
    Enable fast coarse-grained search before fine-grained retrieval
    """
    
    def __init__(self, llm):
        self.llm = llm
        
        # Persistent summary tree
        self.summary_tree = PersistentTree()
    
    async def summarize_conversation(self, conversation_turns):
        """
        Build hierarchical summary tree
        
        Level 0: Individual turns
        Level 1: Segment summaries (10 turns)
        Level 2: Topic summaries (100 turns)
        Level 3: Session summaries (entire conversation)
        """
        # Level 0: Store raw turns
        turn_nodes = []
        for turn in conversation_turns:
            node = self.summary_tree.add_leaf({
                'type': 'turn',
                'content': turn,
                'embedding': self.embed(turn)
            })
            turn_nodes.append(node)
        
        # Level 1: Summarize segments
        segment_nodes = []
        for i in range(0, len(turn_nodes), 10):
            segment_turns = turn_nodes[i:i+10]
            summary = await self.llm.summarize(
                [n.content for n in segment_turns],
                max_length=200
            )
            
            node = self.summary_tree.add_internal({
                'type': 'segment',
                'summary': summary,
                'embedding': self.embed(summary),
                'children': segment_turns
            })
            segment_nodes.append(node)
        
        # Level 2: Summarize topics
        topic_nodes = []
        for i in range(0, len(segment_nodes), 10):
            topic_segments = segment_nodes[i:i+10]
            summary = await self.llm.summarize(
                [n.summary for n in topic_segments],
                max_length=500
            )
            
            node = self.summary_tree.add_internal({
                'type': 'topic',
                'summary': summary,
                'embedding': self.embed(summary),
                'children': topic_segments
            })
            topic_nodes.append(node)
        
        # Level 3: Session summary
        session_summary = await self.llm.summarize(
            [n.summary for n in topic_nodes],
            max_length=1000
        )
        
        root = self.summary_tree.set_root({
            'type': 'session',
            'summary': session_summary,
            'embedding': self.embed(session_summary),
            'children': topic_nodes
        })
        
        return root
    
    async def hierarchical_search(self, query, max_turns=20):
        """
        Search hierarchically: coarse to fine
        """
        query_embedding = self.embed(query)
        
        # Level 3: Find relevant session summaries
        relevant_sessions = self.summary_tree.search_level(
            query_embedding, 
            level=3, 
            k=5
        )
        
        # Level 2: Find relevant topics within sessions
        relevant_topics = []
        for session in relevant_sessions:
            topics = session.search_children(query_embedding, k=3)
            relevant_topics.extend(topics)
        
        # Level 1: Find relevant segments within topics
        relevant_segments = []
        for topic in relevant_topics:
            segments = topic.search_children(query_embedding, k=2)
            relevant_segments.extend(segments)
        
        # Level 0: Get actual turns
        relevant_turns = []
        for segment in relevant_segments:
            turns = segment.children  # All turns in segment
            relevant_turns.extend(turns)
        
        # Rank and return top turns
        ranked = sorted(
            relevant_turns, 
            key=lambda t: cosine_similarity(t.embedding, query_embedding),
            reverse=True
        )
        
        return ranked[:max_turns]
