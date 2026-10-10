#!/usr/bin/env python3
"""OpenMontage Global Video Generator for Any Project.

Usage:
    python generate_project_video.py [--project-path PATH] [--title TITLE] [--theme THEME]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

OPENMONTAGE_DIR = Path(__file__).resolve().parent
COMPOSER_DIR = OPENMONTAGE_DIR / "remotion-composer"
PROPS_DIR = COMPOSER_DIR / "public" / "demo-props"
ASSETS_DIR = COMPOSER_DIR / "public" / "assets"
RENDERS_DIR = OPENMONTAGE_DIR / "projects" / "demos" / "renders"


def sanitize_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in name.lower()).strip("-")


def detect_project_info(project_path: Path) -> dict:
    name = project_path.name
    title = name.replace("-", " ").replace("_", " ").title()
    subtitle = "Next-Generation Intelligent Application"
    features = []
    
    # 1. Inspect package.json
    pkg_file = project_path / "package.json"
    if pkg_file.exists():
        try:
            with pkg_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                name = data.get("name", name)
                title = name.replace("-", " ").replace("_", " ").title()
                desc = data.get("description")
                if desc:
                    subtitle = desc
        except Exception:
            pass

    # 2. Inspect README.md
    readme_file = project_path / "README.md"
    if readme_file.exists():
        try:
            content = readme_file.read_text(encoding="utf-8", errors="ignore")
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            for line in lines[:10]:
                if line.startswith("# "):
                    title = line.replace("# ", "").strip()
                elif not line.startswith("#") and not line.startswith("!") and len(line) > 10:
                    if subtitle == "Next-Generation Intelligent Application":
                        subtitle = line[:80].strip()
        except Exception:
            pass

    # 3. Find screenshots or images in public/
    image_asset = None
    for search_dir in [project_path / "public", project_path / "assets", project_path]:
        if search_dir.exists():
            for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                matches = list(search_dir.glob(f"*{ext}"))
                if matches:
                    image_asset = matches[0]
                    break
        if image_asset:
            break

    return {
        "slug": sanitize_name(name),
        "title": title,
        "subtitle": subtitle,
        "image_asset": image_asset,
    }


def ensure_audio(slug: str) -> str:
    audio_rel = f"assets/{slug}-ambient.mp3"
    audio_full = COMPOSER_DIR / "public" / audio_rel
    audio_full.parent.mkdir(parents=True, exist_ok=True)
    
    if not audio_full.exists():
        # Check if global ambient exists
        default_ambient = ASSETS_DIR / "ambient-music.mp3"
        if default_ambient.exists():
            shutil.copy(default_ambient, audio_full)
        else:
            # Generate synth audio with ffmpeg
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anoisesrc=d=22:c=pink:r=44100:a=0.03",
                "-f", "lavfi", "-i", "sine=f=220:d=22",
                "-f", "lavfi", "-i", "sine=f=277.18:d=22",
                "-f", "lavfi", "-i", "sine=f=329.63:d=22",
                "-filter_complex",
                "[1:a]volume=0.08[a1];[2:a]volume=0.06[a2];[3:a]volume=0.05[a3];[0:a][a1][a2][a3]amix=inputs=4:duration=first,afade=t=in:ss=0:d=1.5,afade=t=out:st=20:d=2",
                "-c:a", "mp3", str(audio_full)
            ]
            subprocess.run(cmd, capture_output=True)
    return audio_rel


def build_storyboard(info: dict, theme: str = "flat-motion-graphics") -> dict:
    slug = info["slug"]
    title = info["title"]
    subtitle = info["subtitle"]
    
    copied_img_rel = None
    if info.get("image_asset") and info["image_asset"].exists():
        dest = ASSETS_DIR / f"{slug}-hero{info['image_asset'].suffix}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy(info["image_asset"], dest)
            copied_img_rel = f"assets/{dest.name}"
        except Exception:
            pass

    audio_rel = ensure_audio(slug)

    hero_cut = {
        "id": f"{slug}-hero",
        "source": "",
        "type": "hero_title",
        "in_seconds": 0,
        "out_seconds": 4.0,
        "text": title,
        "subtitle": subtitle,
        "accentColor": "#F59E0B"
    }
    if copied_img_rel:
        hero_cut["backgroundImage"] = copied_img_rel
        hero_cut["backgroundOverlay"] = 0.70

    cuts = [
        hero_cut,
        {
            "id": f"{slug}-stat",
            "source": "",
            "type": "stat_card",
            "in_seconds": 4.0,
            "out_seconds": 8.0,
            "stat": "10x Faster",
            "subtitle": "Streamlined Architecture & High-Performance Core",
            "accentColor": "#10B981",
            "backgroundColor": "#0F172A"
        },
        {
            "id": f"{slug}-chart",
            "source": "",
            "type": "bar_chart",
            "in_seconds": 8.0,
            "out_seconds": 13.0,
            "title": "Performance & Efficiency Benchmark",
            "chartData": [
                {"label": "Standard Setup", "value": 14},
                {"label": "Optimized", "value": 8},
                {"label": f"{title}", "value": 2}
            ],
            "chartColors": ["#FB7185", "#FBBF24", "#34D399"],
            "showGrid": True,
            "showValues": True,
            "backgroundColor": "#0F172A"
        },
        {
            "id": f"{slug}-comparison",
            "source": "",
            "type": "comparison",
            "in_seconds": 13.0,
            "out_seconds": 17.5,
            "title": "Core Architecture & Capabilities",
            "leftLabel": "Modern Frontend & POS",
            "leftValue": "Sub-Second Interactive UI with Offline Resilience",
            "rightLabel": "Scalable Backend & Cloud",
            "rightValue": "Realtime Sync, Secure RBAC & Telemetry Streams",
            "backgroundColor": "#0F172A",
            "cardBackgroundColor": "#1E293B"
        },
        {
            "id": f"{slug}-cta",
            "source": "",
            "type": "text_card",
            "in_seconds": 17.5,
            "out_seconds": 22.0,
            "text": f"Built with {title}",
            "subtitle": "Ready for Production · Fast, Robust & Scalable",
            "color": "#F8FAFC",
            "backgroundColor": "#0F172A"
        }
    ]

    overlays = [
        {
            "type": "section_title",
            "in_seconds": 8.2,
            "out_seconds": 11.2,
            "text": "Efficiency Unleashed",
            "subtitle": "Instant Realtime Performance",
            "accentColor": "#34D399"
        },
        {
            "type": "stat_reveal",
            "in_seconds": 13.5,
            "out_seconds": 17.0,
            "text": "Production Ready",
            "subtitle": "100% Tested Architecture",
            "accentColor": "#60A5FA",
            "position": "bottom-right"
        }
    ]

    return {
        "theme": theme,
        "cuts": cuts,
        "overlays": overlays,
        "captions": [],
        "audio": {
            "music": {
                "src": audio_rel,
                "volume": 0.35,
                "fadeInSeconds": 1.5,
                "fadeOutSeconds": 2.0,
                "loop": True
            }
        }
    }


def main():
    parser = argparse.ArgumentParser(description="OpenMontage Global Video Generator")
    parser.add_argument("--project-path", default=".", help="Target project root directory")
    parser.add_argument("--title", help="Custom video title")
    parser.add_argument("--subtitle", help="Custom subtitle / tagline")
    parser.add_argument("--theme", default="flat-motion-graphics", help="Theme (flat-motion-graphics, clean-professional, minimalist-diagram)")
    parser.add_argument("--output", help="Optional custom output path for mp4")
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    info = detect_project_info(project_path)
    if args.title:
        info["title"] = args.title
    if args.subtitle:
        info["subtitle"] = args.subtitle

    slug = info["slug"]
    props_path = PROPS_DIR / f"{slug}.json"
    PROPS_DIR.mkdir(parents=True, exist_ok=True)

    storyboard = build_storyboard(info, theme=args.theme)
    with props_path.open("w", encoding="utf-8") as f:
        json.dump(storyboard, f, indent=2)

    print(f"==> Generated OpenMontage storyboard: {props_path}")
    print(f"==> Title: {info['title']}")
    print(f"==> Subtitle: {info['subtitle']}")
    print(f"==> Rendering video with Remotion engine...")

    render_script = OPENMONTAGE_DIR / "render_demo.py"
    python_exe = OPENMONTAGE_DIR / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = Path(sys.executable)

    res = subprocess.run([str(python_exe), str(render_script), slug], cwd=str(OPENMONTAGE_DIR))
    if res.returncode != 0:
        print(f"Error: Render exited with code {res.returncode}")
        sys.exit(res.returncode)

    rendered_file = RENDERS_DIR / f"{slug}.mp4"
    if not rendered_file.exists():
        print(f"Error: Rendered file not found at {rendered_file}")
        sys.exit(1)

    # Copy to project output
    dest_file = Path(args.output).resolve() if args.output else project_path / f"{slug}-openmontage.mp4"
    shutil.copy(rendered_file, dest_file)
    size_mb = dest_file.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 60)
    print("SUCCESS: OpenMontage Video Generated!")
    print(f"Video File: {dest_file} ({size_mb:.1f} MB)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
