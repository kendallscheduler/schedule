import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    print(f"Running: {command}")
    subprocess.check_call(command, shell=True, cwd=cwd)

def main():
    ROOT_DIR = Path(__file__).parent.resolve()
    FRONTEND_DIR = ROOT_DIR / "webapp" / "frontend"
    BACKEND_DIR = ROOT_DIR / "webapp" / "backend"
    STATIC_DIR = BACKEND_DIR / "static"
    DIST_DIR = ROOT_DIR / "dist"
    BUILD_DIR = ROOT_DIR / "build"

    # 1. Clean previous builds
    if STATIC_DIR.exists():
        shutil.rmtree(STATIC_DIR)
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    # 2. Build Frontend
    print("\n📦 Building Frontend...")
    # Ensure dependencies installed
    if not (FRONTEND_DIR / "node_modules").exists():
        run_command("npm install", cwd=FRONTEND_DIR)
    
    # Run build (next build -> out)
    run_command("npm run build", cwd=FRONTEND_DIR)

    # 3. Copy Frontend artifacts to Backend
    print("\n🚚 Moving Frontend artifacts...")
    FRONTEND_OUT = FRONTEND_DIR / "out"
    if not FRONTEND_OUT.exists():
        print("❌ Frontend build failed: 'out' directory not found.")
        sys.exit(1)
    
    shutil.copytree(FRONTEND_OUT, STATIC_DIR)
    print(f"✅ Copied frontend to {STATIC_DIR}")

    # 4. Install PyInstaller
    print("\n🛠 Installing PyInstaller...")
    run_command(f"{sys.executable} -m pip install pyinstaller", cwd=BACKEND_DIR)

    # 5. Run PyInstaller
    print("\n🚀 Packaging Application...")
    
    # We need to construct the PyInstaller command
    # --add-data format: source:dest (on Mac/Linux) or source;dest (Windows)
    sep = ":" if os.name == 'posix' else ";"
    
    # Hidden imports that OR-Tools/Pandas/Uvicorn often need
    hidden_imports = [
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.workers",
        "--hidden-import=sqlalchemy.sql.default_comparator",
        "--hidden-import=ortools",
        "--hidden-import=pandas",
    ]
    
    cmd = [
        # Call pyinstaller module instead of command just in case
        f"{sys.executable}", "-m", "PyInstaller",
        "--name=KendallScheduler",
        "--onedir",  # Folder output (easier to debug than --onefile)
        "--windowed", # No terminal window
        "--clean",
        "--noconfirm",
        f"--add-data=static{sep}static", # Include the static folder
        # Include schedule.db as a template
        f"--add-data=schedule.db{sep}.", 
    ] + hidden_imports + [
        "run.py"
    ]
    
    # Execute PyInstaller from backend dir so paths resolve
    # But output needs to go to ROOT/dist
    
    full_cmd = " ".join(cmd)
    # We run inside backend dir, so distpath needs to point out
    run_command(f"{full_cmd} --distpath ../../dist --workpath ../../build", cwd=BACKEND_DIR)

    print("\n✨ Build Complete!")
    print(f"👉 Application is at: {DIST_DIR / 'KendallScheduler.app'}")
    print("   You may need to manually copy 'schedule.db' to ~/Documents/KendallScheduler/ if specific data is needed.")

if __name__ == "__main__":
    main()
