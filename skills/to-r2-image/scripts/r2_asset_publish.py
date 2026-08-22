#!/usr/bin/env python3
"""Publish local image assets to Cloudflare R2 and rewrite Markdown URLs."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zlib
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONFIG = {
    "bucket": "laifuyou-assets",
    "domain": "assets.laifuyou.com",
    "public_base_url": "https://assets.laifuyou.com",
    "zone_id": "caf7791839a1c0ef2115d1b9e73234a8",
    "cache_control": "public, max-age=31536000, immutable",
    "max_width": 2000,
    "webp_quality": 84,
    "manifest": ".r2-assets/manifest.json",
}

MANIFEST_VERSION = 1
INLINE_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\n]+)\)")
REF_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
REF_DEF_RE = re.compile(r"(?m)^([ \t]*\[([^\]]+)\]:[ \t]*)(\S+)(.*)$")
HTML_IMG_RE = re.compile(r"<img\b[^>]*\bsrc=(['\"])(.*?)\1[^>]*>", re.IGNORECASE)
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


@dataclass
class ImageInfo:
    kind: str
    mime: str
    width: int | None
    height: int | None


@dataclass
class OptimizedAsset:
    source_path: Path
    output_path: Path
    optimized_sha256: str
    content_type: str
    width: int | None
    height: int | None
    bytes_before: int
    bytes_after: int
    tool: str
    copied: bool = False


@dataclass
class MarkdownRef:
    kind: str
    alt: str
    original_url: str
    full_span: tuple[int, int]
    replacement_template: str | None = None
    def_id: str | None = None


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_slug(value: str, fallback: str = "asset") -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or fallback


def rel_to_cwd(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_json(path: Path, fallback: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return dict(fallback)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON: {path}: {exc}") from exc


def load_config(config_path: str | None = None) -> dict:
    config = dict(DEFAULT_CONFIG)
    path = Path(config_path or ".r2-assets/config.json")
    if path.exists():
        loaded = load_json(path, {})
        config.update({k: v for k, v in loaded.items() if v is not None})
    env_map = {
        "R2_ASSET_BUCKET": "bucket",
        "R2_ASSET_DOMAIN": "domain",
        "R2_ASSET_PUBLIC_BASE_URL": "public_base_url",
        "R2_ASSET_ZONE_ID": "zone_id",
        "R2_ASSET_CACHE_CONTROL": "cache_control",
    }
    for env, key in env_map.items():
        if os.environ.get(env):
            config[key] = os.environ[env]
    return config


def manifest_path(config: dict, override: str | None = None) -> Path:
    return Path(override or config["manifest"]).expanduser()


def empty_manifest() -> dict:
    return {"version": MANIFEST_VERSION, "project": safe_slug(Path.cwd().name, "project"), "updated_at": now_iso(), "usages": []}


def normalize_manifest(data: dict) -> dict:
    data.setdefault("version", MANIFEST_VERSION)
    data.setdefault("project", safe_slug(Path.cwd().name, "project"))
    data.setdefault("updated_at", now_iso())
    data.setdefault("usages", [])
    if not isinstance(data["usages"], list):
        data["usages"] = []
    assets = data.pop("assets", {})
    if isinstance(assets, dict):
        data["usages"] = [normalize_usage(usage, assets) for usage in data["usages"]]
    return data


def normalize_usage(usage: dict, assets: dict | None = None) -> dict:
    assets = assets or {}
    sha = usage.get("optimized_sha256") or usage.get("asset_sha256")
    asset = assets.get(sha, {}) if sha else {}
    normalized = {
        "source": usage.get("source", ""),
        "role": usage.get("role", "article-image"),
        "alt": usage.get("alt", ""),
        "url": usage.get("url") or asset.get("url", ""),
        "key": usage.get("key") or asset.get("key", ""),
        "optimized_sha256": sha or "",
        "content_type": usage.get("content_type") or asset.get("content_type", ""),
        "width": usage.get("width", asset.get("width")),
        "height": usage.get("height", asset.get("height")),
        "bytes_before": usage.get("bytes_before", asset.get("bytes_before")),
        "bytes_after": usage.get("bytes_after", asset.get("bytes_after")),
        "tool": usage.get("tool") or asset.get("tool", ""),
        "uploaded_at": usage.get("uploaded_at") or asset.get("created_at") or usage.get("updated_at") or now_iso(),
    }
    original_ref = usage.get("original_ref") or usage.get("image_ref")
    if original_ref:
        normalized["original_ref"] = original_ref
    return {key: value for key, value in normalized.items() if value not in ("", None)}


def load_manifest(path: Path) -> dict:
    return normalize_manifest(load_json(path, empty_manifest()))


def resolve_wrangler() -> list[str] | None:
    env = os.environ.get("R2_ASSET_WRANGLER", "").strip()
    candidates: list[list[str]] = []
    if env:
        candidates.append(env.split())
    if shutil.which("wrangler"):
        candidates.append([shutil.which("wrangler") or "wrangler"])
    if shutil.which("npx"):
        candidates.append(["npx", "--no-install", "wrangler"])
    for candidate in candidates:
        proc = subprocess.run(candidate + ["--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode == 0:
            return candidate
    return None


def run_cmd(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"command failed: {' '.join(cmd)}")
    return proc


def wrangler_cmd(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    wrangler = resolve_wrangler()
    if not wrangler:
        raise RuntimeError("Wrangler not found. Install it or set R2_ASSET_WRANGLER.")
    return run_cmd(wrangler + args, check=check)


def sniff_image(path: Path) -> ImageInfo:
    data = path.read_bytes()
    head = data[:64]
    if head.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return ImageInfo("png", "image/png", width, height)
    if head.startswith(b"\xff\xd8"):
        width, height = sniff_jpeg_size(data)
        return ImageInfo("jpeg", "image/jpeg", width, height)
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        width, height = struct.unpack("<HH", data[6:10])
        return ImageInfo("gif", "image/gif", width, height)
    if head.startswith(b"RIFF") and data[8:12] == b"WEBP":
        width, height = sniff_webp_size(data)
        return ImageInfo("webp", "image/webp", width, height)
    stripped = data[:512].lstrip()
    if stripped.startswith(b"<svg") or b"<svg" in stripped[:128]:
        width, height = sniff_svg_size(data)
        return ImageInfo("svg", "image/svg+xml", width, height)
    raise RuntimeError(f"Unsupported image type: {path}")


def sniff_jpeg_size(data: bytes) -> tuple[int | None, int | None]:
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if i + 2 > len(data):
            break
        length = struct.unpack(">H", data[i:i + 2])[0]
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if i + 7 <= len(data):
                height = struct.unpack(">H", data[i + 3:i + 5])[0]
                width = struct.unpack(">H", data[i + 5:i + 7])[0]
                return width, height
        i += length
    return None, None


def sniff_webp_size(data: bytes) -> tuple[int | None, int | None]:
    if len(data) < 30:
        return None, None
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if chunk == b"VP8 " and len(data) >= 30:
        width = struct.unpack("<H", data[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", data[28:30])[0] & 0x3FFF
        return width, height
    if chunk == b"VP8L" and len(data) >= 25:
        b0, b1, b2, b3 = data[21], data[22], data[23], data[24]
        width = 1 + (((b1 & 0x3F) << 8) | b0)
        height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
        return width, height
    return None, None


def sniff_svg_size(data: bytes) -> tuple[int | None, int | None]:
    text = data[:4096].decode("utf-8", "ignore")
    width = parse_svg_length(re.search(r'\bwidth=["\']([^"\']+)["\']', text))
    height = parse_svg_length(re.search(r'\bheight=["\']([^"\']+)["\']', text))
    if width and height:
        return width, height
    viewbox = re.search(r'\bviewBox=["\']([^"\']+)["\']', text)
    if viewbox:
        nums = re.findall(r"-?\d+(?:\.\d+)?", viewbox.group(1))
        if len(nums) == 4:
            return int(float(nums[2])), int(float(nums[3]))
    return width, height


def parse_svg_length(match: re.Match[str] | None) -> int | None:
    if not match:
        return None
    num = re.match(r"\s*(\d+(?:\.\d+)?)", match.group(1))
    return int(float(num.group(1))) if num else None


def choose_output_path(source: Path, out_dir: Path, info: ImageInfo, output_format: str | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = output_format or ("webp" if info.kind in {"png", "jpeg", "webp"} else info.kind)
    return out_dir / f"{source.stem}.{fmt}"


def optimize_image(source: Path, out_dir: Path, *, quality: int, max_width: int, output_format: str | None = None) -> OptimizedAsset:
    source = source.resolve()
    info = sniff_image(source)
    before = source.stat().st_size
    output = choose_output_path(source, out_dir, info, output_format)
    tool = "copy"
    copied = True

    if info.kind in {"svg", "gif"}:
        shutil.copy2(source, output)
    elif shutil.which("cwebp"):
        args = ["cwebp", "-quiet", "-q", str(quality), "-m", "6", "-mt", "-metadata", "none"]
        if info.kind == "png" and has_png_alpha(source):
            args = ["cwebp", "-quiet", "-lossless", "-z", "6", "-metadata", "none"]
        if info.width and info.width > max_width:
            args.extend(["-resize", str(max_width), "0"])
        args.extend([str(source), "-o", str(output)])
        run_cmd(args)
        tool = "cwebp"
        copied = False
    elif info.kind == "jpeg" and shutil.which("jpegtran"):
        output = out_dir / f"{source.stem}.jpg"
        proc = subprocess.run(["jpegtran", "-copy", "none", "-optimize", "-progressive", str(source)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode:
            raise RuntimeError(proc.stderr.decode("utf-8", "ignore"))
        output.write_bytes(proc.stdout)
        tool = "jpegtran"
        copied = False
    else:
        output = out_dir / source.name
        shutil.copy2(source, output)

    final_info = sniff_image(output)
    return OptimizedAsset(
        source_path=source,
        output_path=output,
        optimized_sha256=sha256_file(output),
        content_type=final_info.mime,
        width=final_info.width,
        height=final_info.height,
        bytes_before=before,
        bytes_after=output.stat().st_size,
        tool=tool,
        copied=copied,
    )


def has_png_alpha(path: Path) -> bool:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    color_type = data[25] if len(data) > 25 else 0
    if color_type in {4, 6}:
        return True
    return b"tRNS" in data


def build_fence_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    in_fence = False
    start = 0
    pos = 0
    fence_re = re.compile(r"^[ \t]*(```|~~~)")
    for line in text.splitlines(keepends=True):
        if fence_re.match(line):
            if not in_fence:
                start = pos
                in_fence = True
            else:
                ranges.append((start, pos + len(line)))
                in_fence = False
        pos += len(line)
    if in_fence:
        ranges.append((start, len(text)))
    return ranges


def in_ranges(index: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in ranges)


def normalize_ref_id(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def split_markdown_dest(value: str) -> tuple[str, str]:
    raw = value.strip()
    if raw.startswith("<") and ">" in raw:
        idx = raw.index(">")
        return raw[1:idx], raw[idx + 1:].strip()
    match = re.match(r"(\S+)(.*)", raw, re.DOTALL)
    if not match:
        return raw, ""
    return match.group(1), match.group(2).strip()


def is_remote_or_special(url: str) -> bool:
    value = url.strip()
    parsed = urllib.parse.urlsplit(value)
    return bool(parsed.scheme in {"http", "https", "data", "mailto"}) or value.startswith("#")


def local_path_from_url(markdown_path: Path, url: str) -> Path:
    parsed = urllib.parse.urlsplit(url.strip("<>"))
    local = urllib.parse.unquote(parsed.path)
    return (markdown_path.parent / local).resolve()


def parse_markdown_refs(markdown_path: Path, text: str) -> list[MarkdownRef]:
    fences = build_fence_ranges(text)
    refs: list[MarkdownRef] = []
    definitions: dict[str, re.Match[str]] = {}

    for match in REF_DEF_RE.finditer(text):
        if not in_ranges(match.start(), fences):
            definitions[normalize_ref_id(match.group(2))] = match

    for match in INLINE_IMAGE_RE.finditer(text):
        if in_ranges(match.start(), fences):
            continue
        url, title = split_markdown_dest(match.group(2))
        replacement = f"![{match.group(1)}]({{url}}{(' ' + title) if title else ''})"
        refs.append(MarkdownRef("inline", match.group(1), url, match.span(), replacement))

    used_defs: set[str] = set()
    for match in REF_IMAGE_RE.finditer(text):
        if in_ranges(match.start(), fences):
            continue
        ref_id = normalize_ref_id(match.group(2) or match.group(1))
        if ref_id in definitions and ref_id not in used_defs:
            used_defs.add(ref_id)
            def_match = definitions[ref_id]
            replacement = f"{def_match.group(1)}{{url}}{def_match.group(4)}"
            refs.append(MarkdownRef("reference", match.group(1), def_match.group(3), def_match.span(), replacement, ref_id))

    for match in HTML_IMG_RE.finditer(text):
        if in_ranges(match.start(), fences):
            continue
        tag = match.group(0)
        quote = match.group(1)
        url = match.group(2)
        src_re = re.search(r"\bsrc=" + re.escape(quote) + re.escape(url) + re.escape(quote), tag, re.IGNORECASE)
        if not src_re:
            continue
        replacement = tag[:src_re.start()] + f"src={quote}" + "{url}" + quote + tag[src_re.end():]
        alt_match = re.search(r"\balt=(['\"])(.*?)\1", tag, re.IGNORECASE)
        alt = alt_match.group(2) if alt_match else ""
        refs.append(MarkdownRef("html", alt, url, match.span(), replacement))

    refs.sort(key=lambda item: item.full_span[0])
    return refs


def frontmatter_value(text: str, key: str) -> str | None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if line.strip().startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


def default_prefix(markdown_path: Path, text: str) -> str:
    parts = markdown_path.as_posix().split("/")
    stem_slug = safe_slug(markdown_path.stem, hashlib.sha256(markdown_path.stem.encode()).hexdigest()[:8])
    if "blog" in parts:
        idx = parts.index("blog")
        if idx + 1 < len(parts) and re.fullmatch(r"\d{4}", parts[idx + 1]):
            return f"posts/blog/{parts[idx + 1]}/{stem_slug}"
    if "wechat" in parts:
        year = None
        date = frontmatter_value(text, "date")
        if date and re.match(r"\d{4}", date):
            year = date[:4]
        if not year:
            year = str(dt.datetime.fromtimestamp(markdown_path.stat().st_mtime).year if markdown_path.exists() else dt.datetime.now().year)
        return f"posts/wechat/{year}/{stem_slug}"
    project = safe_slug(Path.cwd().name, "project")
    return f"assets/{project}/{stem_slug}"


def build_key(prefix: str, source: Path, optimized: OptimizedAsset) -> str:
    ext = optimized.output_path.suffix.lstrip(".") or optimized.content_type.split("/")[-1]
    stem = safe_slug(source.stem, optimized.optimized_sha256[:8])
    return f"{prefix.strip('/')}/{stem}.{optimized.optimized_sha256[:12]}.{ext}"


def public_url(base: str, key: str) -> str:
    return base.rstrip("/") + "/" + "/".join(urllib.parse.quote(part) for part in key.split("/"))


def asset_entry(config: dict, optimized: OptimizedAsset, key: str, url: str) -> dict:
    return {
        "optimized_sha256": optimized.optimized_sha256,
        "key": key,
        "url": url,
        "content_type": optimized.content_type,
        "width": optimized.width,
        "height": optimized.height,
        "bytes_before": optimized.bytes_before,
        "bytes_after": optimized.bytes_after,
        "created_at": now_iso(),
        "tool": optimized.tool,
        "cache_control": config["cache_control"],
    }


def usage_entry(markdown: Path, ref: MarkdownRef, optimized: OptimizedAsset, entry: dict) -> dict:
    usage = {
        "source": rel_to_cwd(markdown),
        "role": "article-image",
        "alt": ref.alt,
        "url": entry["url"],
        "key": entry["key"],
        "optimized_sha256": optimized.optimized_sha256,
        "content_type": optimized.content_type,
        "width": optimized.width,
        "height": optimized.height,
        "bytes_before": optimized.bytes_before,
        "bytes_after": optimized.bytes_after,
        "tool": optimized.tool,
        "uploaded_at": entry.get("created_at") or now_iso(),
    }
    if ref.original_url:
        usage["original_ref"] = ref.original_url
    return usage


def find_usage_by_hash(manifest: dict, optimized_sha256: str) -> dict | None:
    for usage in manifest["usages"]:
        if usage.get("optimized_sha256") == optimized_sha256 and usage.get("url") and usage.get("key"):
            return usage
    return None


def upload_asset(config: dict, optimized: OptimizedAsset, key: str) -> None:
    wrangler_cmd([
        "r2", "object", "put", f"{config['bucket']}/{key}",
        "--file", str(optimized.output_path),
        "--content-type", optimized.content_type,
        "--cache-control", config["cache_control"],
        "--remote",
        "--force",
    ])


def delete_object(config: dict, key: str) -> subprocess.CompletedProcess[str]:
    return wrangler_cmd(["r2", "object", "delete", f"{config['bucket']}/{key}", "--remote", "--force"], check=False)


def object_exists(config: dict, key: str) -> bool:
    with tempfile.TemporaryDirectory(prefix="r2-asset-get-") as tmp:
        target = Path(tmp) / "object"
        proc = wrangler_cmd(["r2", "object", "get", f"{config['bucket']}/{key}", "--file", str(target), "--remote"], check=False)
        return proc.returncode == 0


def apply_replacements(text: str, replacements: list[tuple[tuple[int, int], str]]) -> str:
    for (start, end), value in sorted(replacements, key=lambda item: item[0][0], reverse=True):
        text = text[:start] + value + text[end:]
    return text


def cmd_init(args: argparse.Namespace) -> int:
    config_path = Path(args.config or ".r2-assets/config.json")
    manifest = Path(args.manifest or DEFAULT_CONFIG["manifest"])
    if config_path.exists() and not args.force:
        print(f"exists: {config_path}")
    else:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(config_path, DEFAULT_CONFIG)
        print(f"wrote: {config_path}")
    if manifest.exists() and not args.force:
        print(f"exists: {manifest}")
    else:
        atomic_write_json(manifest, empty_manifest())
        print(f"wrote: {manifest}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "wrangler": None,
        "whoami": None,
        "bucket": config["bucket"],
        "bucket_exists": None,
        "domain": config["domain"],
        "domain_connected": None,
        "tools": {},
    }
    wrangler = resolve_wrangler()
    if wrangler:
        report["wrangler"] = " ".join(wrangler)
        report["wrangler_version"] = wrangler_cmd(["--version"], check=False).stdout.strip()
        whoami = wrangler_cmd(["whoami"], check=False)
        report["whoami_ok"] = whoami.returncode == 0
        report["whoami"] = (whoami.stdout or whoami.stderr).strip()
        info = wrangler_cmd(["r2", "bucket", "info", config["bucket"], "--json"], check=False)
        report["bucket_exists"] = info.returncode == 0
        domains = wrangler_cmd(["r2", "bucket", "domain", "list", config["bucket"]], check=False)
        report["domain_connected"] = domains.returncode == 0 and config["domain"] in domains.stdout
    for tool in ("cwebp", "jpegtran", "sips"):
        report["tools"][tool] = shutil.which(tool)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"python: {report['python']}")
        print(f"wrangler: {report['wrangler'] or 'missing'}")
        print(f"whoami_ok: {report.get('whoami_ok', False)}")
        print(f"bucket: {config['bucket']} exists={report['bucket_exists']}")
        print(f"domain: {config['domain']} connected={report['domain_connected']}")
        for tool, path in report["tools"].items():
            print(f"{tool}: {path or 'missing'}")
    return 0 if report["wrangler"] else 1


def cmd_setup(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    bucket = args.bucket or config["bucket"]
    domain = args.domain or config["domain"]
    zone_id = args.zone_id or config["zone_id"]
    if args.dry_run:
        print(f"would ensure bucket: {bucket}")
        print(f"would connect domain: {domain} zone={zone_id}")
        return 0

    info = wrangler_cmd(["r2", "bucket", "info", bucket, "--json"], check=False)
    if info.returncode:
        print(f"creating bucket: {bucket}")
        wrangler_cmd(["r2", "bucket", "create", bucket])
    else:
        print(f"bucket exists: {bucket}")

    domains = wrangler_cmd(["r2", "bucket", "domain", "list", bucket], check=False)
    if domains.returncode == 0 and domain in domains.stdout:
        print(f"domain connected: {domain}")
    else:
        print(f"connecting domain: {domain}")
        wrangler_cmd([
            "r2", "bucket", "domain", "add", bucket,
            "--domain", domain,
            "--zone-id", zone_id,
            "--min-tls", "1.2",
            "--force",
        ])
    return 0


def cmd_optimize(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    out_dir = Path(args.out_dir or tempfile.mkdtemp(prefix="r2-asset-opt-"))
    for item in args.inputs:
        optimized = optimize_image(Path(item), out_dir, quality=args.quality or int(config["webp_quality"]), max_width=args.max_width or int(config["max_width"]))
        print(json.dumps({
            "source": str(optimized.source_path),
            "output": str(optimized.output_path),
            "content_type": optimized.content_type,
            "bytes_before": optimized.bytes_before,
            "bytes_after": optimized.bytes_after,
            "optimized_sha256": optimized.optimized_sha256,
            "tool": optimized.tool,
        }, ensure_ascii=False))
    return 0


def publish_markdown(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    markdown = Path(args.markdown)
    text = markdown.read_text(encoding="utf-8")
    prefix = args.prefix or default_prefix(markdown, text)
    refs = parse_markdown_refs(markdown, text)
    project_manifest_path = manifest_path(config, args.manifest)
    project_manifest = load_manifest(project_manifest_path)
    out_dir = Path(args.out_dir or tempfile.mkdtemp(prefix="r2-asset-publish-"))
    replacements: list[tuple[tuple[int, int], str]] = []
    local_cache: dict[Path, tuple[OptimizedAsset, dict]] = {}
    skipped: list[dict] = []
    changed = 0

    for ref in refs:
        if is_remote_or_special(ref.original_url):
            continue
        path = local_path_from_url(markdown, ref.original_url)
        if not path.exists():
            skipped.append({"ref": ref.original_url, "reason": "missing file"})
            continue
        if path not in local_cache:
            optimized = optimize_image(path, out_dir, quality=args.quality or int(config["webp_quality"]), max_width=args.max_width or int(config["max_width"]))
            existing = find_usage_by_hash(project_manifest, optimized.optimized_sha256)
            if existing:
                entry = {"key": existing["key"], "url": existing["url"], "created_at": existing.get("uploaded_at")}
            else:
                key = build_key(prefix, path, optimized)
                url = public_url(config["public_base_url"], key)
                entry = asset_entry(config, optimized, key, url)
                if args.write:
                    upload_asset(config, optimized, key)
            local_cache[path] = (optimized, entry)
        optimized, entry = local_cache[path]
        project_manifest["usages"].append(usage_entry(markdown, ref, optimized, entry))
        if ref.replacement_template:
            replacements.append((ref.full_span, ref.replacement_template.format(url=entry["url"])))
            changed += 1

    if args.write:
        if replacements:
            markdown.write_text(apply_replacements(text, replacements), encoding="utf-8")
        project_manifest["updated_at"] = now_iso()
        atomic_write_json(project_manifest_path, project_manifest)
        print(f"published={changed} skipped={len(skipped)} markdown={markdown}")
    else:
        print(f"dry-run publishable={changed} skipped={len(skipped)} markdown={markdown}")
        for _, entry in local_cache.values():
            print(f"  {entry['url']}")
    for item in skipped:
        print(f"skipped: {item['ref']} ({item['reason']})")
    return 1 if skipped and args.strict else 0


def collect_markdown_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for value in paths:
        path = Path(value)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        elif path.suffix == ".md":
            files.append(path)
    return files


def is_publish_true(text: str) -> bool:
    value = frontmatter_value(text, "publish")
    return str(value).lower() == "true"


def cmd_check(args: argparse.Namespace) -> int:
    failures: list[str] = []
    for md in collect_markdown_files(args.paths):
        text = md.read_text(encoding="utf-8")
        if args.published_only and not is_publish_true(text):
            continue
        for ref in parse_markdown_refs(md, text):
            if is_remote_or_special(ref.original_url):
                continue
            failures.append(f"{md}:{ref.original_url}")
    if failures:
        print("local image references found:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("no local image references found")
    return 0


def cmd_catalog(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    data = load_manifest(manifest_path(config, args.manifest))
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    if args.html:
        rows = []
        for usage in data["usages"]:
            url = usage.get("url", "")
            rows.append(
                "<tr>"
                f"<td><img src=\"{html.escape(url)}\" loading=\"lazy\"></td>"
                f"<td><a href=\"{html.escape(url)}\">{html.escape(url)}</a></td>"
                f"<td>{html.escape(str(usage.get('source') or ''))}</td>"
                f"<td>{html.escape(str(usage.get('width') or ''))}x{html.escape(str(usage.get('height') or ''))}</td>"
                f"<td>{html.escape(str(usage.get('bytes_after') or ''))}</td>"
                f"<td>{html.escape(str(usage.get('optimized_sha256') or '')[:12])}</td>"
                "</tr>"
            )
        html_doc = """<!doctype html>
<meta charset="utf-8">
<title>R2 Image Catalog</title>
<style>
body{font-family:system-ui,sans-serif;margin:24px;background:#f7f7f4;color:#1b1b18}
table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px;vertical-align:top}
img{max-width:180px;max-height:120px;object-fit:contain;background:white}
a{word-break:break-all}
</style>
<h1>R2 Image Catalog</h1>
<table><thead><tr><th>Image</th><th>URL</th><th>Source</th><th>Size</th><th>Bytes</th><th>Hash</th></tr></thead><tbody>
""" + "\n".join(rows) + "</tbody></table>\n"
        Path(args.html).write_text(html_doc, encoding="utf-8")
        print(f"wrote: {args.html}")
    return 0


def cmd_find(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    data = load_manifest(manifest_path(config, args.manifest))
    term = args.term.lower()
    found = 0
    for usage in data["usages"]:
        blob = json.dumps(usage, ensure_ascii=False).lower()
        if term in blob:
            print(json.dumps(usage, ensure_ascii=False))
            found += 1
    return 0 if found else 1


def verify_url(url: str, expected_content_type: str | None = None, expected_cache: str | None = None, wait_seconds: int = 0) -> dict:
    deadline = time.time() + wait_seconds
    last_error = ""
    while True:
        try:
            req = urllib.request.Request(url, method="GET", headers={"User-Agent": "to-r2-image/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                headers = dict(resp.headers.items())
                result = {
                    "status": resp.status,
                    "content_type": headers.get("Content-Type", ""),
                    "cache_control": headers.get("Cache-Control", ""),
                    "bytes": len(data),
                }
                if expected_content_type and expected_content_type not in result["content_type"]:
                    raise RuntimeError(f"content-type mismatch: {result['content_type']}")
                if expected_cache and "max-age=31536000" not in result["cache_control"]:
                    raise RuntimeError(f"cache-control mismatch: {result['cache_control']}")
                if result["bytes"] <= 0:
                    raise RuntimeError("empty response")
                return result
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            if time.time() >= deadline:
                raise RuntimeError(last_error) from exc
            time.sleep(5)


def create_test_png(path: Path) -> None:
    width, height = 2, 2
    raw_rows = [
        b"\x00" + bytes([255, 0, 0, 255, 0, 160, 0, 255]),
        b"\x00" + bytes([0, 0, 255, 255, 255, 255, 255, 255]),
    ]

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    data = zlib.compress(b"".join(raw_rows))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", data) + chunk(b"IEND", b""))


def cmd_smoke(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    with tempfile.TemporaryDirectory(prefix="r2-asset-smoke-") as tmp:
        tmpdir = Path(tmp)
        source = tmpdir / "smoke.png"
        create_test_png(source)
        optimized = optimize_image(source, tmpdir, quality=int(config["webp_quality"]), max_width=int(config["max_width"]))
        key = f"_smoke/to-r2-image-{int(time.time())}.{optimized.output_path.suffix.lstrip('.')}"
        upload_asset(config, optimized, key)
        url = public_url(config["public_base_url"], key)
        print(f"uploaded: {url}")
        try:
            result = verify_url(url, optimized.content_type, config["cache_control"], args.wait_seconds)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        finally:
            deleted = delete_object(config, key)
            if deleted.returncode:
                eprint(deleted.stderr.strip() or deleted.stdout.strip())
            print(f"deleted: {key}")
            if object_exists(config, key):
                raise RuntimeError(f"smoke object still exists after delete: {key}")
            print("delete_verified: r2 object missing")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    result = verify_url(args.url, args.content_type, args.cache_control, args.wait_seconds)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def self_check() -> None:
    with tempfile.TemporaryDirectory(prefix="r2-asset-self-") as tmp:
        root = Path(tmp)
        img = root / "image.png"
        create_test_png(img)
        gif = root / "anim.gif"
        gif.write_bytes(
            b"GIF89a\x01\x00\x01\x00\x80\x01\x00\xff\xff\xff\x00\x00\x00"
            b",\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        )
        svg = root / "vector.svg"
        svg.write_text('<svg width="10" height="12" xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")
        jpg = root / "photo.jpg"
        if shutil.which("sips"):
            run_cmd(["sips", "-s", "format", "jpeg", str(img), "--out", str(jpg)])
        md = root / "post.md"
        md.write_text(
            "![inline](image.png)\n"
            "![remote](https://example.com/a.png)\n"
            "![ref][one]\n\n"
            "[one]: vector.svg\n\n"
            "```md\n![skip](image.png)\n```\n"
            "<img src=\"anim.gif\" alt=\"html\">\n",
            encoding="utf-8",
        )
        assert sniff_image(img).kind == "png"
        assert sniff_image(svg).kind == "svg"
        assert sniff_image(gif).kind == "gif"
        if jpg.exists():
            assert sniff_image(jpg).kind == "jpeg"
        refs = parse_markdown_refs(md, md.read_text(encoding="utf-8"))
        assert len(refs) == 4
        local = [r for r in refs if not is_remote_or_special(r.original_url)]
        assert len(local) == 3
        rewritten = apply_replacements(
            md.read_text(encoding="utf-8"),
            [(ref.full_span, ref.replacement_template.format(url=f"https://assets.example/{idx}.webp")) for idx, ref in enumerate(local) if ref.replacement_template],
        )
        assert rewritten.count("https://assets.example/") == 3
        assert "![skip](image.png)" in rewritten
        optimized = optimize_image(img, root / "out", quality=84, max_width=2000)
        assert optimized.output_path.exists()
        manifest = normalize_manifest({"usages": []})
        manifest["usages"].append(usage_entry(md, local[0], optimized, asset_entry(DEFAULT_CONFIG, optimized, "x.webp", "https://assets.example/x.webp")))
        assert manifest["usages"][0]["optimized_sha256"] == optimized.optimized_sha256
        migrated = normalize_manifest({
            "assets": {optimized.optimized_sha256: asset_entry(DEFAULT_CONFIG, optimized, "x.webp", "https://assets.example/x.webp")},
            "usages": [{"source": "old.md", "image_ref": "image.png", "alt": "old", "asset_sha256": optimized.optimized_sha256}],
        })
        assert "assets" not in migrated
        assert migrated["usages"][0]["original_ref"] == "image.png"
        manifest_file = root / "manifest.json"
        atomic_write_json(manifest_file, manifest)
        catalog_file = root / "catalog.html"
        cmd_catalog(argparse.Namespace(config=None, manifest=str(manifest_file), html=str(catalog_file), json=False))
        assert catalog_file.exists()


def cmd_self_check(args: argparse.Namespace) -> int:
    self_check()
    print("self-check passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Path to .r2-assets/config.json")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--config")
    p.add_argument("--manifest")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("doctor")
    p.add_argument("--config")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("setup")
    p.add_argument("--config")
    p.add_argument("--bucket")
    p.add_argument("--domain")
    p.add_argument("--zone-id")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("optimize")
    p.add_argument("inputs", nargs="+")
    p.add_argument("--config")
    p.add_argument("--out-dir")
    p.add_argument("--quality", type=int)
    p.add_argument("--max-width", type=int)
    p.set_defaults(func=cmd_optimize)

    p = sub.add_parser("publish")
    p.add_argument("markdown")
    p.add_argument("--config")
    p.add_argument("--manifest")
    p.add_argument("--prefix")
    p.add_argument("--out-dir")
    p.add_argument("--quality", type=int)
    p.add_argument("--max-width", type=int)
    p.add_argument("--write", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=publish_markdown)

    p = sub.add_parser("check")
    p.add_argument("paths", nargs="+")
    p.add_argument("--published-only", action="store_true")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("catalog")
    p.add_argument("--config")
    p.add_argument("--manifest")
    p.add_argument("--html")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_catalog)

    p = sub.add_parser("find")
    p.add_argument("term")
    p.add_argument("--config")
    p.add_argument("--manifest")
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("verify")
    p.add_argument("url")
    p.add_argument("--content-type")
    p.add_argument("--cache-control")
    p.add_argument("--wait-seconds", type=int, default=0)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("smoke")
    p.add_argument("--config")
    p.add_argument("--wait-seconds", type=int, default=180)
    p.set_defaults(func=cmd_smoke)

    p = sub.add_parser("self-check")
    p.set_defaults(func=cmd_self_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001
        eprint(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
