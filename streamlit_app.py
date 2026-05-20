"""Streamlit app entry point for cloud deployment."""

import sys
from pathlib import Path

# Add src/ to Python path so imports work correctly in Streamlit Cloud
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from restaurant_rec.presentation.streamlit_app import main

if __name__ == "__main__":
    main()
