from pathlib import Path
import shutil


def mkdir(dir):
    pdir = Path(dir)
    if not pdir.exists():
        pdir.mkdir(parents=True)
    return pdir


def remake(dir):
    pdir = Path(dir)
    if pdir.exists():
        shutil.rmtree(pdir)
    return pdir
