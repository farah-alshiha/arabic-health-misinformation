from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import Callable, Optional


PIPELINE_MODULES = [
    "collector",
    "build_dataset",
    "add_ocr_to_dataset",
    "add_labels_to_dataset",
    "download_images",
]


def _run_as_module(module_name: str) -> None:
    cmd = [sys.executable, "-m", f"src.{module_name}"]
    print(f"\n===== RUNNING: {' '.join(cmd)} =====")
    subprocess.run(cmd, check=True)


def _try_import_and_run_main(module_name: str) -> bool:
    try:
        mod = __import__(f"src.{module_name}", fromlist=["main"])
    except Exception as e:
        print(f"[WARN] Could not import src.{module_name}: {e}")
        return False

    main_fn: Optional[Callable[[], None]] = getattr(mod, "main", None)
    if callable(main_fn):
        print(f"\n===== RUNNING: src.{module_name}.main() =====")
        main_fn()
        return True

    return False


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)

    print("=== Pipeline runner ===")
    print("Repo root:", repo_root)
    print("Python:", sys.executable)

    src_dir = repo_root / "src"
    if not src_dir.exists():
        raise RuntimeError(f"Could not find src/ directory at: {src_dir}")

    for name in PIPELINE_MODULES:
        ran = _try_import_and_run_main(name)
        if not ran:
            _run_as_module(name)

    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()