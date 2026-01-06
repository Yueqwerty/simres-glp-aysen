"""Script para iniciar el servidor backend."""
import os
import sys

from pathlib import Path

# Configurar PYTHONPATH y cambiar al directorio raíz
root_dir = Path(__file__).parent.parent
os.chdir(str(root_dir))
sys.path.insert(0, str(root_dir))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(root_dir / "backend" / "app"), str(root_dir / "src")]
    )
