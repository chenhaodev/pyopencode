from pathlib import Path


def detect_project_type(root: str = ".") -> dict:
    root_path = Path(root)
    markers = {
        "python": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"],
        "node": ["package.json"],
        "go": ["go.mod"],
        "rust": ["Cargo.toml"],
        "java": ["pom.xml", "build.gradle"],
        "ruby": ["Gemfile"],
        "php": ["composer.json"],
    }

    detected = []
    for lang, files in markers.items():
        if any((root_path / f).exists() for f in files):
            detected.append(lang)

    git_root = _find_git_root(root_path)

    return {
        "languages": detected,
        "primary": detected[0] if detected else "unknown",
        "git_root": str(git_root) if git_root else None,
        "root": str(root_path.resolve()),
    }


def _find_git_root(path: Path) -> Path | None:
    current = path.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None
