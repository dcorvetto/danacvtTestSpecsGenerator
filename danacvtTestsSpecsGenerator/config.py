from pathlib import Path
import os

# Default output paths
DEFAULT_OUT_DIR = Path("outputs")
DEFAULT_OUT_DIR.mkdir(exist_ok=True)

# Supported file types
SUPPORTED_DOCS = [".txt", ".md", ".docx", ".pdf"]
SUPPORTED_IMAGES = [".png", ".jpg", ".jpeg"]

# OpenAI key (read from env var if available)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")