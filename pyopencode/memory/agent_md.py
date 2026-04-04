from pathlib import Path

MEMORY_FILENAME = "AGENT.md"


def load_memory(project_root: str = ".") -> str:
    memory_path = Path(project_root) / MEMORY_FILENAME
    if memory_path.exists():
        return memory_path.read_text(encoding="utf-8")
    return ""


def save_memory(content: str, project_root: str = "."):
    memory_path = Path(project_root) / MEMORY_FILENAME
    memory_path.write_text(content, encoding="utf-8")


def append_memory(entry: str, project_root: str = "."):
    current = load_memory(project_root)
    if entry not in current:
        save_memory(current.rstrip() + "\n\n" + entry + "\n", project_root)
