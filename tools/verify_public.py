from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
FORBIDDEN = ("苑", "佰宁", "D:\\Nikon", "D:/Nikon")


def main() -> None:
    if not (PUBLIC / "index.html").exists():
        raise SystemExit("缺少 public/index.html，请先运行 npm run build")

    html_files = list(PUBLIC.rglob("*.html"))
    if not html_files:
        raise SystemExit("没有生成 HTML")

    for path in PUBLIC.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".js", ".css", ".json", ".xml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in FORBIDDEN:
            if token in text:
                raise SystemExit(f"隐私检查失败: {token!r} 出现在 {path}")

    manifest = json.loads((ROOT / "source" / "_data" / "photo-manifest.json").read_text(encoding="utf-8"))
    explore_data = json.loads((PUBLIC / "explore" / "albums.json").read_text(encoding="utf-8"))
    expected_routes = [PUBLIC / "album" / album["id"] / "index.html" for album in manifest["albums"]]
    missing = [str(path) for path in expected_routes if not path.exists()]
    if missing:
        raise SystemExit("缺少相册页面:\n" + "\n".join(missing))

    public_images = list((PUBLIC / "images" / "albums").glob("*/*.jpg"))
    expected_images = sum(album["photos"] for album in manifest["albums"])
    if len(public_images) != expected_images:
        raise SystemExit(f"公开大图数量异常: expected={expected_images} actual={len(public_images)}")

    explore_files = [
        PUBLIC / "explore" / "index.html",
        PUBLIC / "explore" / "explore.css",
        PUBLIC / "explore" / "explore.js",
        PUBLIC / "explore" / "character.svg",
        PUBLIC / "_routes.json",
    ]
    missing_explore = [str(path) for path in explore_files if not path.exists()]
    if missing_explore:
        raise SystemExit("探索页面文件缺失:\n" + "\n".join(missing_explore))
    if len(explore_data) != len(manifest["albums"]):
        raise SystemExit("探索地图相册数量与照片清单不一致")
    if sum(album["photos"] for album in explore_data) != expected_images:
        raise SystemExit("探索地图照片数量与照片清单不一致")

    print(f"ok html={len(html_files)} albums={len(expected_routes)} photos={expected_images} explore=ready")


if __name__ == "__main__":
    main()
