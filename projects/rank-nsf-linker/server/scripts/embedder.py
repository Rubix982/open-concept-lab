import sys
import json
from sentence_transformers import SentenceTransformer
import os
import logging

# Configure logging to stderr so it doesn't pollute stdout (vectors)
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("embedder")

def main():
    # Verify Cache Location
    hf_home = os.getenv("HF_HOME")
    logger.info(f"HF_HOME set to: {hf_home}")
    
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    logger.info(f"Loading model: {model_name}")
    
    try:
        model = SentenceTransformer(model_name)
        logger.info("Model loaded successfully. Ready for input.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Dimensionality
    dim = model.get_sentence_embedding_dimension()
    logger.info(f"Vector dimension: {dim}")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            data = json.loads(line)
            text = data.get("text", "")
            
            if not text.strip():
                # Return zero vector or empty
                print(json.dumps([0.0] * dim))
                sys.stdout.flush()
                continue

            # Embed
            embedding = model.encode(text)
            
            # Output as JSON list
            print(json.dumps(embedding.tolist()))
            sys.stdout.flush()

        except json.JSONDecodeError:
            logger.error("Invalid JSON input")
            print(json.dumps([]))
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error processing line: {e}")
            print(json.dumps([])) # Empty on error
            sys.stdout.flush()

if __name__ == "__main__":
    main()
