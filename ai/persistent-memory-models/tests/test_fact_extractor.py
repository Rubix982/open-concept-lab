"""Tests for FactExtractor."""
import pytest
from persistent_memory.fact_extractor import FactExtractor, MockFactExtractor, ExtractionResult

class TestMockFactExtractor:
    """Test the mock fact extractor."""
    
    @pytest.mark.asyncio
    async def test_extract_from_chunk(self, sample_text):
        """Test basic extraction."""
        extractor = MockFactExtractor()
        result = await extractor.extract_from_chunk(sample_text)
        
        assert isinstance(result, ExtractionResult)
        assert len(result.facts) > 0
        assert len(result.entities) > 0
        assert result.summary != ""
    
    @pytest.mark.asyncio
    async def test_extraction_structure(self, sample_text):
        """Test that extraction returns proper structure."""
        extractor = MockFactExtractor()
        result = await extractor.extract_from_chunk(sample_text)
        
        for fact in result.facts:
            assert hasattr(fact, 'subject')
            assert hasattr(fact, 'predicate')
            assert hasattr(fact, 'object')
            assert hasattr(fact, 'confidence')
            assert 0 <= fact.confidence <= 1

@pytest.mark.integration
class TestFactExtractorIntegration:
    """Integration tests requiring LLM."""
    
    @pytest.mark.asyncio
    async def test_real_extraction(self, sample_text):
        """Test with real LLM (requires API key)."""
        import os
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("LLM_BACKEND") == "ollama":
            pytest.skip("No LLM backend configured")
        
        extractor = FactExtractor()
        result = await extractor.extract_from_chunk(sample_text)
        
        assert isinstance(result, ExtractionResult)
