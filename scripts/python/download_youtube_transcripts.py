from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

VIDEOS = {
    "1OAQs3PpI7Y": "How to Craft your Bow for Ice shot Deadeye - Crit & Non-Crit | Path of Exile 2",
    "dwMRB6RgpzA": "How to Craft a Bow for Beginners | PoE 2 0.5",
    "yQko7i73E88": "Ice Shot Deadeye Bow Craft | Path of Exile 2 0.5",
    "fFoq2VF1eJ8": "Massive Nerf To Crafting in The Updated 0.5 Patch Notes - Path of Exile 2",
    "RpE1t_-uAog": "Path of Exile 2: Runes of Aldur - Runecrafting",
    "eE8D-N7JDcY": "RuneCrafting Looks INSANE in PoE 2 | Runes of Aldur Breakdown",
    "VfVusss--0c": "These New Runecrafting Options Will Open Up So Many Build Variants | Path of Exile 2 Runes of Aldur",
}


def parse_raw_cookie_file(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8").strip()
    pairs = re.split(r"[;\n]+", raw)
    cookies: dict[str, str] = {}
    for pair in pairs:
        pair = pair.strip()
        if not pair or "=" not in pair or pair.startswith("#"):
            continue
        key, value = pair.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            cookies[key] = value
    return cookies


def write_netscape_cookie_file(raw_cookie_path: Path, output_dir: Path, domain: str) -> Path:
    cookies = parse_raw_cookie_file(raw_cookie_path)
    if not cookies:
        raise ValueError(f"No cookies parsed from {raw_cookie_path}")

    temp_path = output_dir / ".youtube_cookies.netscape.tmp"
    lines = [
        "# Netscape HTTP Cookie File",
        "# This file is generated temporarily by download_youtube_transcripts.py.",
    ]
    include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
    for key, value in cookies.items():
        secure = "TRUE" if key.startswith("__Secure-") else "FALSE"
        lines.append(f"{domain}\t{include_subdomains}\t/\t{secure}\t0\t{key}\t{value}")

    temp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Loaded {len(cookies)} cookies from raw cookie file; temporary Netscape file created.")
    return temp_path


def build_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--skip-download",
        "--write-auto-subs",
        "--write-subs",
        "--sub-langs",
        args.languages,
        "--sub-format",
        "vtt",
        "--ignore-no-formats-error",
        "--paths",
        str(args.output),
        "--ignore-errors",
        "--extractor-args",
        "youtube:player_client=web_embedded,web_safari",
    ]

    cookie_path = args.cookies
    if args.raw_cookies:
        cookie_path = write_netscape_cookie_file(args.raw_cookies, args.output, args.raw_cookie_domain)

    if cookie_path:
        command.extend(["--cookies", str(cookie_path)])
    elif args.browser:
        command.extend(["--cookies-from-browser", args.browser])

    command.extend(f"https://www.youtube.com/watch?v={video_id}" for video_id in VIDEOS)
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Download subtitles for selected PoE2 0.5 YouTube videos.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "youtube_transcripts",
        help="字幕输出目录，默认 data/youtube_transcripts",
    )
    parser.add_argument(
        "--cookies",
        type=Path,
        help="Netscape 格式 cookies.txt。不要把 cookie 写进本脚本。",
    )
    parser.add_argument(
        "--raw-cookies",
        type=Path,
        help="浏览器直接复制的原始 cookie 字符串文件，支持 'k=v; k2=v2' 或多行 k=v。",
    )
    parser.add_argument(
        "--raw-cookie-domain",
        default=".youtube.com",
        help="把原始 cookie 转成 Netscape 格式时使用的域名，默认 .youtube.com。",
    )
    parser.add_argument(
        "--browser",
        default="edge",
        help="不提供 --cookies 时，尝试读取本机浏览器 cookie，默认 edge。",
    )
    parser.add_argument(
        "--languages",
        default="en,en-orig,zh-Hans,zh-Hant",
        help='字幕语言，默认 "en,en-orig,zh-Hans,zh-Hant"。',
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    print("Target videos:")
    for video_id, title in VIDEOS.items():
        print(f"- {video_id}: {title}")

    temp_cookie_file = args.output / ".youtube_cookies.netscape.tmp"
    try:
        command = build_command(args)
        return subprocess.call(command)
    finally:
        if args.raw_cookies and temp_cookie_file.exists():
            temp_cookie_file.unlink()
            print("Temporary Netscape cookie file deleted.")


if __name__ == "__main__":
    raise SystemExit(main())
