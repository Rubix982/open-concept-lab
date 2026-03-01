from persistent_memory.core.persistent_context_engine import (
    PersistentContextEngine,
    PersistentKnowledgeGraph,
    PersistentVectorStore,
)


class AccessControlLayer:
    """Placeholder for access control."""

    def check_permission(self, user_id, resource):
        """Check if user has permission (placeholder)."""
        return True


class MultiUserContextSystem:
    """
    Manage separate context for each user
    """

    def __init__(self):
        # Per-user contexts
        self.user_contexts = {}  # user_id -> PersistentContextEngine

        # Shared knowledge base (all users)
        self.shared_semantic = PersistentKnowledgeGraph()
        self.shared_episodic = PersistentVectorStore()

        # Access control
        self.acl = AccessControlLayer()

    def get_or_create_user_context(self, user_id):
        """
        Get or create context for a specific user
        """
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = PersistentContextEngine()

            # Link to shared knowledge
            self.user_contexts[user_id].semantic = self.shared_semantic

        return self.user_contexts[user_id]

    def get_user_context(self, user_id):
        """Get user context (alias for compatibility)."""
        return self.get_or_create_user_context(user_id)

    async def query_with_context(self, user_id, query):
        """
        Query with user-specific context
        """
        if not self.acl.check_permission(user_id, "query"):
            raise PermissionError(f"User {user_id} not authorized")

        context = self.get_or_create_user_context(user_id)
        return await context.query(query)

    async def process_user_turn(self, user_id, user_input):
        """
        Process turn with both private and shared context
        """
        user_context = self.get_or_create_user_context(user_id)

        # Query both private and shared contexts
        private_results = await user_context.route_query(user_input)
        shared_results = await self.query_shared_context(user_input, user_id)

        # Merge and rank
        all_results = self._merge_private_and_shared(private_results, shared_results)

        # Generate response
        response = await self.llm.generate(self._build_prompt(user_input, all_results))

        # Store in user's private context
        await user_context.episodic.add_conversation_turn(...)

        # Optionally contribute to shared knowledge
        if self._is_generalizable(response):
            await self.shared_semantic.add_fact(self._extract_general_fact(response))

        return response

    async def query_shared_context(self, query, user_id):
        """
        Query shared knowledge with access control
        """
        results = await self.shared_semantic.query(query)

        # Filter by access permissions
        filtered = [r for r in results if self.acl.can_access(user_id, r)]

        return filtered
