import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMOS = ROOT / "demos"
EXCLUDE = {"tests", "__pycache__"}


def all_demo_names() -> list[str]:
    return sorted(d.name for d in DEMOS.iterdir() if d.is_dir() and d.name[:1].isdigit())


def classify_targets(changed: list[str], all_demos: list[str]) -> list[str]:
    if any(c.startswith("demos/_core/") for c in changed):
        return list(all_demos)
    touched = []
    for name in all_demos:
        if any(c.startswith(f"demos/{name}/") for c in changed):
            touched.append(name)
    return touched


def _changed_paths() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def _copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in EXCLUDE or item.suffix == ".pyc":
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=shutil.ignore_patterns(*EXCLUDE, "*.pyc"))
        else:
            shutil.copy2(item, target)


def _space_id(hf_user: str, demo_name: str) -> str:
    short = demo_name.split("-", 1)[1] if "-" in demo_name else demo_name
    return f"{hf_user}/agentic-{short}"


def main() -> None:
    from huggingface_hub import HfApi

    hf_user = os.environ["HF_USER"]
    token = os.environ["HF_TOKEN"]
    api = HfApi()

    targets = classify_targets(_changed_paths(), all_demo_names())
    if not targets:
        print("No demo changes to sync.")
        return

    for name in targets:
        space_id = _space_id(hf_user, name)
        print(f"Syncing {name} -> {space_id}")
        api.create_repo(
            repo_id=space_id, repo_type="space", space_sdk="gradio", exist_ok=True, token=token
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _copy_tree(DEMOS / name, tmp_path)
            _copy_tree(DEMOS / "_core", tmp_path / "_core")
            api.upload_folder(
                repo_id=space_id, repo_type="space", folder_path=str(tmp_path), token=token
            )


if __name__ == "__main__":
    main()
