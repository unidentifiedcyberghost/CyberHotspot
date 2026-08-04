import os
import shutil
import subprocess
from typing import List, Optional


class CommandError(RuntimeError):
    pass


def which(command: str) -> Optional[str]:
    return shutil.which(command)


def run(command: List[str], check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            command,
            check=check,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=os.environ.copy(),
        )
    except FileNotFoundError as exc:
        raise CommandError(f"Required command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise CommandError(f"{' '.join(command)} failed: {detail}") from exc
