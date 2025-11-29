"""Fact extraction from text using LLMs."""

import json
import logging
import os
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, validator

from persistent_memory.metrics import fact_extraction_total, llm_call_duration, track_duration

logger = logging.getLogger(__name__)


class Fact(BaseModel):
    """A structured fact extracted from text."""

    subject: str = Field(description="The subject entity")
    predicate: str = Field(description="The relationship or action")
    object: str = Field(description="The object entity or value")
    confidence: float = Field(description="Confidence score between 0 and 1", ge=0.0, le=1.0)
    source_text: str | None = Field(default=None, description="Original text snippet")

    @validator("subject", "predicate", "object")
    def not_empty(self, cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class ExtractionResult(BaseModel):
    """Result of fact extraction."""

    facts: list[Fact] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    summary: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class FactExtractor:
    """
    Extracts structured facts (Entity-Relation-Entity) from text using an LLM.

    Supports both OpenAI and Ollama backends with intelligent prompt engineering.
    """

    def __init__(self, llm=None, knowledge_graph=None, model: str = "gpt-3.5-turbo"):
        self.llm_client = llm
        self.knowledge_graph = knowledge_graph
        self.backend = os.getenv("LLM_BACKEND", "openai")

        if self.backend == "ollama":
            ollama_host = os.getenv("OLLAMA_HOST", "http://llm-service:11434/v1")
            self.client = AsyncOpenAI(
                base_url=ollama_host,
                api_key="ollama",  # Required but unused
            )
            self.model = os.getenv("OLLAMA_MODEL", "mistral")
            logger.info(f"Initialized FactExtractor with Ollama: {self.model}")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # If no API key and no LLM client provided, warn but don't crash yet
                if not self.llm_client:
                    logger.warning("OPENAI_API_KEY not set and no LLM client provided")

            self.client = AsyncOpenAI(api_key=api_key) if api_key else None
            self.model = model
            logger.info(f"Initialized FactExtractor with OpenAI: {self.model}")

    async def extract_from_text(self, text: str) -> ExtractionResult:
        """Alias for extract_from_chunk."""
        return await self.extract_from_chunk(text)

    @track_duration(llm_call_duration)
    async def extract_from_chunk(self, text_chunk: str) -> ExtractionResult:
        """
        Extracts facts, entities, and a brief summary from a text chunk.

        Args:
            text_chunk: The text to analyze

        Returns:
            ExtractionResult containing facts, entities, and summary
        """
        if not text_chunk or len(text_chunk.strip()) < 10:
            logger.warning("Text chunk too short for extraction")
            return ExtractionResult(summary="Text too short")

        system_prompt = """You are an expert knowledge engineer. Extract structured information from text.

Your task:
1. Identify key entities (People, Places, Organizations, Concepts)
2. Extract relationships in (Subject, Predicate, Object) format
3. Provide a brief summary

Guidelines:
- Be precise and factual
- Use canonical entity names (e.g., "Elizabeth Bennet" not "she")
- Predicates should be clear verbs or relationships
- Confidence: 1.0 = certain, 0.5 = probable, 0.0 = guess
- Extract 3-10 facts per chunk

Return valid JSON matching this schema:
{
  "facts": [{"subject": "X", "predicate": "Y", "object": "Z", "confidence": 0.9}],
  "entities": ["Entity1", "Entity2"],
  "summary": "Brief summary"
}"""

        user_prompt = f"""Text to analyze:

{text_chunk}

Extract structured knowledge as JSON:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for factual extraction
                max_tokens=1000,
            )

            content = response.choices[0].message.content

            # Try to parse JSON from response
            try:
                # Handle markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                data = json.loads(content.strip())
                result = ExtractionResult(**data)

                # Add source text to facts
                for fact in result.facts:
                    fact.source_text = text_chunk[:100]

                fact_extraction_total.labels(status="success").inc()
                logger.info(f"Extracted {len(result.facts)} facts from chunk")
                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}\nContent: {content}")
                fact_extraction_total.labels(status="parse_error").inc()
                return ExtractionResult(
                    summary="Failed to parse extraction results",
                    metadata={"error": str(e), "raw_content": content[:200]},
                )

        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            fact_extraction_total.labels(status="error").inc()
            return ExtractionResult(summary="Extraction failed", metadata={"error": str(e)})


class MockFactExtractor(FactExtractor):
    """Mock extractor for testing without API calls."""

    async def extract_from_chunk(self, text_chunk: str) -> ExtractionResult:
        """Return mock facts for testing."""
        logger.info("Using MockFactExtractor")
        return ExtractionResult(
            facts=[
                Fact(
                    subject="Alice",
                    predicate="knows",
                    object="Bob",
                    confidence=0.9,
                    source_text=text_chunk[:50],
                ),
                Fact(
                    subject="Bob",
                    predicate="lives_in",
                    object="Paris",
                    confidence=0.8,
                    source_text=text_chunk[:50],
                ),
            ],
            entities=["Alice", "Bob", "Paris"],
            summary="Mock summary of the text.",
            metadata={"mock": True},
        )
