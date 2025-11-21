class TransformerContext:
    """
    Manages current context window.
    Simplified for MVP.
    """
    
    def __init__(self, max_tokens=4096):
        self.max_tokens = max_tokens
        self.current_tokens = []
        self.history = []
    
    def add_turn(self, user_input, system_prompt_additions=None):
        """
        Add new turn to context
        """
        self.history.append({"role": "user", "content": user_input})
        return "Response placeholder"
    
    def get_current_context(self):
        return self.history[-5:] # Return last 5 turns
