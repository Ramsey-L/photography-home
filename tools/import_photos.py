from __future__ import annotations

import hashlib
import html
import json
import os
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps


SOURCE_ROOT = Path(os.environ.get("PHOTO_SOURCE", r"D:\Nikon z30\zfc"))
SITE_ROOT = Path(__file__).resolve().parents[1]
IMAGE_ROOT = SITE_ROOT / "source" / "images" / "albums"
POST_ROOT = SITE_ROOT / "source" / "_posts"
ABOUT_PATH = SITE_ROOT / "source" / "about" / "index.md"
MANIFEST_PATH = SITE_ROOT / "source" / "_data" / "photo-manifest.json"
EXPLORE_DATA_PATH = SITE_ROOT / "source" / "explore" / "albums.json"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_DISPLAY_WIDTH = 2200
MAX_THUMB_WIDTH = 960
DISPLAY_QUALITY = 88
THUMB_QUALITY = 82
EXCLUDED_WORDS = ("苑", "佰宁")
EXCLUDED_PHOTO_TITLES = {
    "我在乍浦路",
    "镜中的我们",
    "滨江的我",
    "我在静安寺",
}
ROLL_DATE_OVERRIDES = {
    "20260703": "2026.07.02–07.04",
}
ROLL_PLACE_OVERRIDES = {
    "20260721": "嘉定第二日",
}


def natural_sort_key(path: Path) -> tuple[object, ...]:
    return tuple(
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", path.name)
    )


def clean_title(path: Path) -> str:
    title = re.sub(r"^\d{6}\s*", "", path.stem)
    title = re.sub(r"^\d+\s*", "", title)
    return title.strip() or path.stem


def album_id(name: str) -> str:
    match = re.match(r"(\d{8})", name)
    if not match:
        raise ValueError(f"相册目录缺少 8 位日期前缀: {name}")
    return match.group(1)


def album_place(name: str) -> str:
    ident = album_id(name)
    if ident in ROLL_PLACE_OVERRIDES:
        return ROLL_PLACE_OVERRIDES[ident]
    return re.sub(r"^\d{8}", "", name).strip() or name


def display_date(ident: str) -> str:
    if ident in ROLL_DATE_OVERRIDES:
        return ROLL_DATE_OVERRIDES[ident]
    return f"{ident[:4]}.{ident[4:6]}.{ident[6:8]}"


def yaml_text(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def keep_photo(path: Path, album_name: str) -> bool:
    title = clean_title(path)
    if title in EXCLUDED_PHOTO_TITLES:
        return False
    content = f"{title}{album_name}{path.name}"
    return not any(word in content for word in EXCLUDED_WORDS)


def rational_text(value: object) -> str:
    try:
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            if value.denominator == 1:
                return str(value.numerator)
            return f"{value.numerator}/{value.denominator}"
        return str(value)
    except Exception:
        return ""


def aperture_text(value: object) -> str:
    try:
        return f"f/{float(value):.1f}".replace(".0", "")
    except Exception:
        return ""


def focal_text(value: object) -> str:
    try:
        return f"{float(value):.0f}mm"
    except Exception:
        return ""


def exif_summary(image: Image.Image, path: Path) -> dict[str, str]:
    exif = image.getexif()
    exif_ifd = exif.get_ifd(34665)
    exposure = rational_text(exif_ifd.get(33434) or "")
    if exposure:
        exposure += "s"
    raw_date = exif_ifd.get(36867) or exif.get(306)
    taken = str(raw_date or "").replace("\x00", "").strip()
    if taken:
        taken = taken.replace(":", ".", 2)
    else:
        taken = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y.%m.%d %H:%M")
    return {
        "camera": str(exif.get(272) or "Nikon Z fc").replace("\x00", "").strip(),
        "date": taken,
        "iso": str(exif_ifd.get(34855) or "").strip(),
        "aperture": aperture_text(exif_ifd.get(33437) or exif_ifd.get(37378) or ""),
        "shutter": exposure,
        "focal": focal_text(exif_ifd.get(37386) or ""),
    }


def image_key(path: Path) -> str:
    relative = path.relative_to(SOURCE_ROOT).as_posix().encode("utf-8")
    return hashlib.sha1(relative).hexdigest()[:12]


def save_variant(source: Path, target: Path, max_width: int, quality: int) -> tuple[int, int]:
    if target.exists() and target.stat().st_mtime_ns >= source.stat().st_mtime_ns:
        with Image.open(target) as current:
            return current.width, current.height
    with Image.open(source) as raw:
        image = ImageOps.exif_transpose(raw).convert("RGB")
        if image.width > max_width:
            height = round(image.height * max_width / image.width)
            image = image.resize((max_width, height), Image.Resampling.LANCZOS)
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, "JPEG", quality=quality, optimize=True, progressive=True)
        os.utime(target, ns=(source.stat().st_atime_ns, source.stat().st_mtime_ns))
        return image.width, image.height


def photo_html(photo: dict[str, object]) -> str:
    orientation = "is-tall" if photo["height"] > photo["width"] else "is-wide"
    title = html.escape(str(photo["title"]))
    details = " · ".join(
        value
        for value in (
            str(photo["aperture"]),
            str(photo["shutter"]),
            f"ISO {photo['iso']}" if photo["iso"] else "",
            str(photo["focal"]),
        )
        if value
    )
    caption = html.escape(f"{title} · {details}" if details else title)
    return (
        f'<a class="photo-item {orientation}" href="{photo["src"]}" '
        f'data-fancybox="album" data-caption="{caption}">\n'
        f'  <img src="{photo["thumb"]}" alt="{title}" loading="lazy" '
        f'width="{photo["thumb_width"]}" height="{photo["thumb_height"]}">\n'
        f'  <span class="photo-caption">{caption}</span>\n'
        "</a>"
    )


def make_post(album: dict[str, object]) -> str:
    photos = album["photos"]
    cover = photos[0]
    date_value = f"{album['id'][:4]}-{album['id'][4:6]}-{album['id'][6:8]} 12:00:00"
    lines = [
        "---",
        f"title: {yaml_text(str(album['place']))}",
        f"date: {date_value}",
        "categories:",
        "  - 摄影",
        "tags:",
        f"  - {yaml_text(str(album['place']))}",
        "  - Nikon Z fc",
        f"description: {yaml_text(str(album['place']) + '摄影记录')}",
        f"photo_count: {len(photos)}",
        "comments: false",
        "generated_by: photo-import",
        "---",
        "",
        '<div class="photo-log-cover">',
        f'  <img src="{cover["src"]}" alt="{html.escape(str(album["place"]))}" width="{cover["width"]}" height="{cover["height"]}">',
        "</div>",
        '<p class="photo-log-deck">',
        f'  <strong>{html.escape(str(album["place"]))}</strong>',
        f'  <span>{album["display_date"]} · {len(photos)} 张照片</span>',
        "</p>",
        "",
        "<!-- more -->",
        "",
        f'<p class="photo-log-intro">{html.escape(str(album["place"]))}，{album["display_date"]}。用 Nikon Z fc 留下的 {len(photos)} 个片段。</p>',
        "",
        '<div class="photo-grid">',
    ]
    lines.extend(photo_html(photo) for photo in photos[1:])
    lines.extend(["</div>", ""])
    return "\n".join(lines)


def make_about(cover: dict[str, object] | None) -> str:
    portrait = ""
    if cover:
        portrait = (
            '<figure class="about-portrait">\n'
            f'  <img src="{cover["src"]}" alt="关于我的照片" width="{cover["width"]}" height="{cover["height"]}">\n'
            "</figure>"
        )
    return f'''---
title: 关于我
date: 2025-05-14 12:00:00
comments: false
---

<div class="about-profile">
  <div class="about-copy">
    <p>欢迎浏览本主页。我是 zncu，一名普通的上海大学生。</p>
    <p>我经常会去想寻找自己，思考所处的这个环境是从何而来，我在这里扮演了一个什么角色，为何会产生某种情感。</p>
    <p>因此在生活中，当看到某些画面，有时我会产生触动。它们或永恒，或转瞬即逝。我想，如果我把它拍下来，在以后再次浏览时，或许会想起当时的心情。</p>
    <p>所以，我制作了本网站，通过我用尼康拍摄的照片，向你分享那些我曾看到过的风景。</p>
  </div>
  {portrait}
</div>
'''


def remove_stale_files(expected_images: set[Path], expected_posts: set[Path]) -> None:
    if IMAGE_ROOT.exists():
        for path in IMAGE_ROOT.rglob("*.jpg"):
            if path not in expected_images:
                path.unlink()
    if POST_ROOT.exists():
        for path in POST_ROOT.glob("*.md"):
            if path not in expected_posts and "generated_by: photo-import" in path.read_text(encoding="utf-8"):
                path.unlink()


def main() -> None:
    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"照片目录不存在: {SOURCE_ROOT}")

    IMAGE_ROOT.mkdir(parents=True, exist_ok=True)
    POST_ROOT.mkdir(parents=True, exist_ok=True)
    ABOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPLORE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    albums: list[dict[str, object]] = []
    excluded: list[str] = []
    expected_images: set[Path] = set()
    expected_posts: set[Path] = set()
    about_cover: dict[str, object] | None = None

    for folder in sorted(path for path in SOURCE_ROOT.iterdir() if path.is_dir()):
        ident = album_id(folder.name)
        place = album_place(folder.name)
        album_photos: list[dict[str, object]] = []
        files = sorted(
            (path for path in folder.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS),
            key=natural_sort_key,
        )
        for source in files:
            if not keep_photo(source, folder.name):
                excluded.append(str(source.relative_to(SOURCE_ROOT)))
                continue
            key = image_key(source)
            target = IMAGE_ROOT / ident / f"{key}.jpg"
            thumb = IMAGE_ROOT / ident / "thumbs" / f"{key}.jpg"
            width, height = save_variant(source, target, MAX_DISPLAY_WIDTH, DISPLAY_QUALITY)
            thumb_width, thumb_height = save_variant(source, thumb, MAX_THUMB_WIDTH, THUMB_QUALITY)
            expected_images.update((target, thumb))
            with Image.open(source) as raw:
                meta = exif_summary(raw, source)
            photo = {
                "title": clean_title(source),
                "src": f"/images/albums/{ident}/{key}.jpg",
                "thumb": f"/images/albums/{ident}/thumbs/{key}.jpg",
                "width": width,
                "height": height,
                "thumb_width": thumb_width,
                "thumb_height": thumb_height,
                **meta,
            }
            album_photos.append(photo)
            if ident == "20260516" and photo["title"] == "我":
                about_cover = photo
        if album_photos:
            album = {
                "id": ident,
                "folder": folder.name,
                "place": place,
                "display_date": display_date(ident),
                "photos": album_photos,
            }
            albums.append(album)
            post_path = POST_ROOT / f"{ident}.md"
            post_path.write_text(make_post(album), encoding="utf-8")
            expected_posts.add(post_path)

    remove_stale_files(expected_images, expected_posts)
    ABOUT_PATH.write_text(make_about(about_cover), encoding="utf-8")

    avatar_source = about_cover
    if avatar_source:
        source_path = SITE_ROOT / "source" / avatar_source["thumb"].lstrip("/")
        avatar_path = SITE_ROOT / "source" / "images" / "avatar.jpg"
        avatar_path.write_bytes(source_path.read_bytes())

    manifest = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "source": "D:/Nikon z30/zfc",
        "albums": [
            {
                "id": album["id"],
                "folder": album["folder"],
                "title": album["place"],
                "photos": len(album["photos"]),
            }
            for album in albums
        ],
        "excluded": excluded,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    explore_data = [
        {
            "id": album["id"],
            "title": album["place"],
            "date": album["display_date"],
            "photos": len(album["photos"]),
            "route": f"/album/{album['id']}/",
            "cover": album["photos"][0]["thumb"],
        }
        for album in sorted(albums, key=lambda item: str(item["id"]), reverse=True)
    ]
    EXPLORE_DATA_PATH.write_text(
        json.dumps(explore_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"albums={len(albums)} public_photos={sum(len(album['photos']) for album in albums)} excluded={len(excluded)}")
    for album in albums:
        print(f"{album['id']} {album['place']}: {len(album['photos'])}")


if __name__ == "__main__":
    main()
