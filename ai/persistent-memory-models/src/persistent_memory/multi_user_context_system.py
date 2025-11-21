class MultiUserContextSystem:
    """
    Manage persistent context for multiple users with shared knowledge
    """
    
    def __init__(self):
        # Per-user private context
        self.user_contexts = {}  # user_id -> PersistentContextEngine
        
        # Shared knowledge base (all users)
        self.shared_semantic = PersistentKnowledgeGraph()
        self.shared_episodic = PersistentVectorStore()
        
        # Access control
        self.acl = AccessControlLayer()
    
    def get_or_create_user_context(self, user_id):
        """
        Get user's personal context engine
        """
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = PersistentContextEngine()
            
            # Link to shared knowledge
            self.user_contexts[user_id].semantic.add_view(
                self.shared_semantic,
                filter_fn=lambda fact: self.acl.can_access(user_id, fact)
            )
        
        return self.user_contexts[user_id]
    
    async def process_user_turn(self, user_id, user_input):
        """
        Process turn with both private and shared context
        """
        user_context = self.get_or_create_user_context(user_id)
        
        # Query both private and shared contexts
        private_results = await user_context.route_query(user_input)
        shared_results = await self.query_shared_context(user_input, user_id)
        
        # Merge and rank
        all_results = self._merge_private_and_shared(
            private_results, 
            shared_results
        )
        
        # Generate response
        response = await self.llm.generate(
            self._build_prompt(user_input, all_results)
        )
        
        # Store in user's private context
        await user_context.episodic.add_conversation_turn(...)
        
        # Optionally contribute to shared knowledge
        if self._is_generalizable(response):
            await self.shared_semantic.add_fact(
                self._extract_general_fact(response)
            )
        
        return response
    
    async def query_shared_context(self, query, user_id):
        """
        Query shared knowledge with access control
        """
        results = await self.shared_semantic.query(query)
        
        # Filter by access permissions
        filtered = [
            r for r in results 
            if self.acl.can_access(user_id, r)
        ]
        
        return filtered
