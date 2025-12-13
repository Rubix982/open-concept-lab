from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer

model_name = "sentence-transformers/all-MiniLM-L6-v2"
output_dir = "./models/all-MiniLM-L6-v2-onnx"

# Export to ONNX
model = ORTModelForFeatureExtraction.from_pretrained(model_name, export=True)
tokenizer = AutoTokenizer.from_pretrained(model_name)

model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

print(f"✓ Model exported to {output_dir}")
