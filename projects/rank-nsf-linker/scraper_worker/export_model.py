#!/usr/bin/env python3
"""
ONNX Model Export Script
Exports sentence-transformers model to ONNX format for production use.
"""

import sys
import os
from pathlib import Path
from typing import Optional


def validate_environment() -> bool:
    """Validate required dependencies are available."""
    try:
        import optimum.onnxruntime
        import transformers

        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}", file=sys.stderr)
        return False


def validate_existing_model(output_path: Path) -> bool:
    """
    Check if valid model already exists.

    Returns:
        True if valid model exists, False otherwise
    """
    required_files = ["model.onnx", "tokenizer_config.json", "config.json"]

    if not output_path.exists():
        return False

    missing = [f for f in required_files if not (output_path / f).exists()]

    if missing:
        print(f"→ Incomplete model found, missing: {missing}")
        return False

    # Check file sizes (model.onnx should be substantial)
    model_file = output_path / "model.onnx"
    if model_file.stat().st_size < 1024 * 1024:  # Less than 1MB
        print(f"→ model.onnx too small, likely corrupted")
        return False

    return True


def export_model(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    output_dir: str = "./models/all-MiniLM-L6-v2-onnx",
) -> int:
    """
    Download/export model only if not already present.

    Returns:
        0 on success, 1 on failure
    """
    from optimum.onnxruntime import ORTModelForFeatureExtraction
    from transformers import AutoTokenizer

    output_path = Path(output_dir)

    try:
        # Check if valid model already exists
        if validate_existing_model(output_path):
            model_size = (output_path / "model.onnx").stat().st_size / (1024 * 1024)
            print(f"✓ Valid model already exists at {output_path.absolute()}")
            print(f"  Size: {model_size:.2f} MB")
            print(f"  Skipping download/export")
            return 0

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"→ Output directory: {output_path.absolute()}")

        # Try to load pre-converted ONNX model first
        print(f"→ Downloading model: {model_name}")
        try:
            model = ORTModelForFeatureExtraction.from_pretrained(
                model_name, export=False  # Try pre-converted first
            )
            print("✓ Using pre-converted ONNX model")
        except Exception as e:
            print(f"→ Pre-converted model not available, exporting from PyTorch")
            model = ORTModelForFeatureExtraction.from_pretrained(
                model_name, export=True
            )
            print("✓ Model exported to ONNX")

        print("→ Loading tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Save both
        print("→ Saving model")
        model.save_pretrained(str(output_path))

        print("→ Saving tokenizer")
        tokenizer.save_pretrained(str(output_path))

        # Final validation
        if not validate_existing_model(output_path):
            print(f"✗ Model validation failed after export", file=sys.stderr)
            return 1

        # Print file sizes
        model_size = (output_path / "model.onnx").stat().st_size / (1024 * 1024)
        print(f"✓ Model exported successfully")
        print(f"  Location: {output_path.absolute()}")
        print(f"  Size: {model_size:.2f} MB")

        return 0

    except Exception as e:
        print(f"✗ Export failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point."""
    if not validate_environment():
        print("✗ Environment validation failed", file=sys.stderr)
        return 1

    # Support environment variable overrides (Docker-friendly)
    model_name = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    output_dir = os.getenv("MODEL_OUTPUT_DIR", "./models/all-MiniLM-L6-v2-onnx")

    print("=== ONNX Model Export ===")
    print(f"Model: {model_name}")
    print(f"Output: {output_dir}")
    print()

    return export_model(model_name, output_dir)


if __name__ == "__main__":
    sys.exit(main())
