#!/usr/bin/env python3
"""
Interactive Chatbot - Talk to the Enhanced LLM

A simple CLI chatbot powered by the Enhanced LLM.
This demonstrates a REAL working chatbot with persistent memory.

Usage:
    python chatbot.py

Commands:
    /teach <text>  - Teach the bot new information
    /stats         - Show bot statistics
    /clear         - Clear conversation history
    /quit          - Exit
"""

import sys

sys.path.insert(0, "src")

import asyncio
from persistent_memory.enhanced_llm import EnhancedLLM


class InteractiveChatbot:
    """Interactive CLI chatbot."""

    def __init__(self):
        self.bot = None
        self.session_id = f"interactive_{int(asyncio.get_event_loop().time())}"

    async def initialize(self):
        """Initialize the bot."""
        print("\n🤖 Initializing Enhanced LLM Chatbot...")
        print("   (This may take a moment...)\n")

        try:
            self.bot = EnhancedLLM(
                model="mistral",
                enable_cache=True,
                enable_attention=True,
                enable_quality_monitoring=True,
            )
            print("✅ Bot ready!\n")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            print("\n💡 Make sure Ollama is running:")
            print("   brew services start ollama")
            print("   ollama pull mistral")
            return False

    async def handle_command(self, user_input: str) -> bool:
        """Handle special commands. Returns True if it was a command."""
        if not user_input.startswith("/"):
            return False

        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()

        if command == "/quit" or command == "/exit":
            print("\n👋 Goodbye!")
            return True

        elif command == "/clear":
            self.bot.clear_conversation()
            print("✅ Conversation cleared!\n")
            return True

        elif command == "/stats":
            stats = self.bot.get_stats()
            print("\n📊 Bot Statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
            print()
            return True

        elif command == "/teach":
            if len(parts) < 2:
                print("Usage: /teach <text to teach>")
                return True

            text = parts[1]
            print(f"\n📖 Teaching bot...")
            await self.bot.teach(text, source="user")
            print("✅ Learned!\n")
            return True

        elif command == "/help":
            self.show_help()
            return True

        else:
            print(f"Unknown command: {command}")
            print("Type /help for available commands\n")
            return True

    def show_help(self):
        """Show help message."""
        print("\n📚 Available Commands:")
        print("   /teach <text>  - Teach the bot new information")
        print("   /stats         - Show bot statistics")
        print("   /clear         - Clear conversation history")
        print("   /help          - Show this help")
        print("   /quit          - Exit chatbot")
        print()

    async def chat_loop(self):
        """Main chat loop."""
        print("=" * 60)
        print("Enhanced LLM Chatbot - Interactive Mode")
        print("=" * 60)
        print("\n💡 This bot has persistent memory and learns from conversations!")
        print("   Type /help for commands, /quit to exit\n")

        while True:
            try:
                # Get user input
                user_input = input("👤 You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if await self.handle_command(user_input):
                    if user_input.startswith("/quit") or user_input.startswith("/exit"):
                        break
                    continue

                # Chat with bot
                print("🤖 Bot: ", end="", flush=True)

                result = await self.bot.chat(
                    user_input, session_id=self.session_id, return_metadata=True
                )

                print(result["response"])

                # Show metadata (optional)
                if result.get("cached"):
                    print("   ⚡ (from cache)")
                else:
                    print(f"   ⏱️  {result['latency']:.2f}s | 📚 {result['contexts_used']} contexts")

                print()

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

    async def run(self):
        """Run the chatbot."""
        if await self.initialize():
            await self.chat_loop()


async def main():
    """Main entry point."""
    chatbot = InteractiveChatbot()
    await chatbot.run()


if __name__ == "__main__":
    asyncio.run(main())
