#!/usr/bin/env python3
"""
Clean up unnecessary files from the project.
Removes cache files, logs, temporary files, and old data.
"""

import os
import shutil
from pathlib import Path
from typing import List

def remove_files(pattern: str, root_dir: Path, description: str) -> int:
    """Remove files matching pattern."""
    count = 0
    for file_path in root_dir.rglob(pattern):
        try:
            if file_path.is_file():
                file_path.unlink()
                count += 1
        except Exception as e:
            print(f"  Warning: Could not remove {file_path}: {e}")
    if count > 0:
        print(f"  ✅ Removed {count} {description}")
    return count

def remove_dirs(pattern: str, root_dir: Path, description: str) -> int:
    """Remove directories matching pattern."""
    count = 0
    for dir_path in root_dir.rglob(pattern):
        try:
            if dir_path.is_dir():
                shutil.rmtree(dir_path)
                count += 1
        except Exception as e:
            print(f"  Warning: Could not remove {dir_path}: {e}")
    if count > 0:
        print(f"  ✅ Removed {count} {description}")
    return count

def cleanup_project(root_dir: Path):
    """Clean up unnecessary files."""
    print("🧹 Cleaning up unnecessary files...")
    print("=" * 60)
    
    total_removed = 0
    
    # 1. Python cache files
    print("\n1. Removing Python cache files...")
    total_removed += remove_dirs("__pycache__", root_dir, "__pycache__ directories")
    total_removed += remove_files("*.pyc", root_dir, ".pyc files")
    
    # 2. System files
    print("\n2. Removing system files...")
    total_removed += remove_files(".DS_Store", root_dir, ".DS_Store files")
    
    # 3. Log files
    print("\n3. Removing log files...")
    log_files = [
        root_dir / ".cursor" / "debug.log",
        root_dir / "report" / "AntennaTwin.log",
        root_dir / "training_log.txt",
    ]
    for log_file in log_files:
        if log_file.exists():
            try:
                log_file.unlink()
                print(f"  ✅ Removed {log_file.relative_to(root_dir)}")
                total_removed += 1
            except Exception as e:
                print(f"  Warning: Could not remove {log_file}: {e}")
    
    # 4. Report build artifacts (keep .pdf and .tex)
    print("\n4. Removing LaTeX build artifacts...")
    report_dir = root_dir / "report"
    if report_dir.exists():
        build_files = ["*.aux", "*.out"]
        for pattern in build_files:
            total_removed += remove_files(pattern, report_dir, f"{pattern} files")
    
    # 5. Old model files (keep current ones in backend/models/)
    print("\n5. Removing old model files...")
    old_models_dir = root_dir / "models"
    if old_models_dir.exists():
        old_models = [
            "mock_100_samples_*.pkl",
            "real_training_v1_*.pkl"
        ]
        for pattern in old_models:
            for model_file in old_models_dir.glob(pattern):
                try:
                    model_file.unlink()
                    print(f"  ✅ Removed {model_file.name}")
                    total_removed += 1
                except Exception as e:
                    print(f"  Warning: Could not remove {model_file}: {e}")
    
    # 6. Empty cache directories
    print("\n6. Cleaning empty cache directories...")
    cache_dirs = [
        root_dir / "cache",
        root_dir / "backend" / "cache"
    ]
    for cache_dir in cache_dirs:
        if cache_dir.exists() and cache_dir.is_dir():
            try:
                # Check if empty
                if not any(cache_dir.iterdir()):
                    cache_dir.rmdir()
                    print(f"  ✅ Removed empty {cache_dir.relative_to(root_dir)}")
                    total_removed += 1
            except Exception as e:
                print(f"  Warning: Could not remove {cache_dir}: {e}")
    
    # 7. Temporary training logs in /tmp
    print("\n7. Cleaning temporary training logs...")
    import glob
    tmp_logs = glob.glob("/tmp/meep*.log")
    for tmp_log in tmp_logs:
        try:
            os.remove(tmp_log)
            print(f"  ✅ Removed {tmp_log}")
            total_removed += 1
        except Exception as e:
            print(f"  Warning: Could not remove {tmp_log}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Cleanup complete! Removed {total_removed} files/directories")
    print("\n📝 Note: Current training data and models are preserved:")
    print("   - backend/data/em_results/training_*/")
    print("   - backend/models/*.pkl")
    print("   - backend/data/simulation_log_*.txt")

if __name__ == "__main__":
    # Get project root (parent of backend)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    cleanup_project(project_root)






