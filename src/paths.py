from pathlib import Path

# .../OFI/src/paths.py -> parents[1] 就是 OFI 根目录
ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
PROCESSED_TICKS_DIR = DATA_DIR / "processed" / "ticks"
