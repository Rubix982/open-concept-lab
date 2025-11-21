class PersistentContextAI:
    """
    Complete AI system with persistent multi-layer context
    """
    
    def __init__(self, llm_model):
        self.llm = llm_model
        self.context_engine = PersistentContextEngine()
        self.fact_extractor = FactExtractor(llm_model, 
                                            self.context_engine.semantic)
        
        # Background jobs
        self.archiver = ContextArchiver(self.context_engine)
        self.consolidator = KnowledgeConsolidator(self.context_engine)
    
    async def process_turn(self, user_input, session_id):
        """
        Process single conversation turn with full context awareness
        """
        start_time = time.time()
        
        # Step 1: Route query to find relevant context
        relevant_context = await self.context_engine.context_router.route_query(
            user_input,
            max_results=20
        )
        
        # Step 2: Build prompt with retrieved context
        prompt = self._build_contextualized_prompt(
            user_input,
            relevant_context
        )
        
        # Step 3: Generate response using LLM
        response = await self.llm.generate(
            prompt,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Step 4: Extract and store facts from this turn
        facts = self.fact_extractor.extract_from_turn({
            'user': user_input,
            'assistant': response,
            'id': f"{session_id}_{int(time.time())}",
            'timestamp': datetime.now()
        })
        
        # Step 5: Store turn in episodic memory
        await self.context_engine.episodic.add_conversation_turn({
            'user_input': user_input,
            'assistant_response': response,
            'timestamp': datetime.now(),
            'context_summary': relevant_context[:3],  # Top 3 contexts used
            'entities': facts['entities'],
            'topics': facts['topics']
        })
        
        # Step 6: Update working memory
        self.context_engine.working_memory.add_turn(user_input, response)
        
        # Log performance
        latency = time.time() - start_time
        self._log_performance(latency, relevant_context)
        
        return {
            'response': response,
            'context_used': relevant_context,
            'latency': latency,
            'facts_extracted': len(facts['facts'])
        }
    
    def _build_contextualized_prompt(self, user_input, relevant_context):
        """
        Build prompt with relevant context injected
        """
        # System prompt
        system = "You are a helpful AI assistant with long-term memory."
        
        # Inject relevant context
        context_section = "\n\nRelevant context from past conversations:\n"
        
        for ctx in relevant_context[:5]:  # Top 5 most relevant
            if ctx['layer'] == 'episodic':
                context_section += f"- {ctx['content']['text']['context_summary']} (from {ctx['content']['metadata']['timestamp']})\n"
            elif ctx['layer'] == 'semantic':
                context_section += f"- Related knowledge: {self._format_knowledge(ctx['content'])}\n"
        
        # Current query
        user_section = f"\n\nCurrent query: {user_input}"
        
        return system + context_section + user_section
    
    async def background_maintenance(self):
        """
        Background jobs for context maintenance
        """
        while True:
            # Archive old episodic memories (every hour)
            await self.archiver.archive_old_memories(age_threshold_days=30)
            
            # Consolidate semantic knowledge (every 6 hours)
            await self.consolidator.consolidate_facts()
            
            # Optimize indexes (every 24 hours)
            await self.context_engine.optimize_indexes()
            
            await asyncio.sleep(3600)  # 1 hour
