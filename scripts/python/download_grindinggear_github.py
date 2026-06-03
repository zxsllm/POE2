from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "grindinggear_github"
REPOS_DIR = RAW_DIR / "repos"
METADATA_DIR = ROOT / "data" / "processed" / "metadata"

OWNER = "grindinggear"
USER_AGENT = "Mozilla/5.0 (compatible; POE2LocalResearch/1.0; +local-github-mirror-script)"
DEFAULT_REPO_ALLOWLIST = {"poe2-skilltree-export"}


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_public_repos(owner: str) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        response = requests.get(
            f"https://api.github.com/users/{owner}/repos",
            params={"per_page": 100, "page": page, "type": "public", "sort": "full_name"},
            headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
            timeout=45,
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def run_git(args: list[str], cwd: Path | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True)


def clone_repo(repo: dict[str, Any], refresh: bool = False) -> dict[str, Any]:
    repo_name = repo["name"]
    target = REPOS_DIR / repo_name
    result = {
        "name": repo_name,
        "path": str(target.relative_to(ROOT)),
        "clone_url": repo.get("clone_url", ""),
        "html_url": repo.get("html_url", ""),
        "size_kb": repo.get("size", 0),
        "default_branch": repo.get("default_branch", ""),
        "action": "skipped",
    }

    if target.exists():
        if refresh:
            run_git(["fetch", "--depth", "1", "origin"], cwd=target)
            result["action"] = "fetched"
        return result

    run_git(["clone", "--depth", "1", repo["clone_url"], str(target)])
    result["action"] = "cloned"
    return result


def compact_repo(repo: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": repo.get("name", ""),
        "full_name": repo.get("full_name", ""),
        "description": repo.get("description", ""),
        "html_url": repo.get("html_url", ""),
        "clone_url": repo.get("clone_url", ""),
        "default_branch": repo.get("default_branch", ""),
        "size_kb": repo.get("size", 0),
        "stargazers_count": repo.get("stargazers_count", 0),
        "fork": repo.get("fork", False),
        "archived": repo.get("archived", False),
        "created_at": repo.get("created_at", ""),
        "updated_at": repo.get("updated_at", ""),
        "pushed_at": repo.get("pushed_at", ""),
        "language": repo.get("language", ""),
        "topics": repo.get("topics", []),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mirror public GitHub repositories from grindinggear.")
    parser.add_argument("--refresh", action="store_true", help="Fetch existing local shallow clones.")
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Mirror every public grindinggear repository. By default only PoE2 data repositories are mirrored.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dirs()

    repos = fetch_public_repos(OWNER)
    selected_repos = repos if args.include_all else [repo for repo in repos if repo.get("name") in DEFAULT_REPO_ALLOWLIST]
    compact_repos = [compact_repo(repo) for repo in selected_repos]
    (RAW_DIR / "repos.json").write_text(
        json.dumps(compact_repos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    clone_results = [clone_repo(repo, refresh=args.refresh) for repo in selected_repos]
    total_size_kb = sum(int(repo.get("size") or 0) for repo in selected_repos)
    summary = {
        "snapshot_time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "owner": OWNER,
        "repo_count": len(selected_repos),
        "filter": "all_public_repositories" if args.include_all else "poe2_repositories_only",
        "total_github_reported_size_kb": total_size_kb,
        "repos_json": str((RAW_DIR / "repos.json").relative_to(ROOT)),
        "repos_dir": str(REPOS_DIR.relative_to(ROOT)),
        "clone_results": clone_results,
    }
    (METADATA_DIR / "grindinggear_github_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
