#!/usr/bin/env python3
"""ipynb2md: Jupyter Notebook(.ipynb)을 Markdown(.md)으로 변환하는 도구.

외부 라이브러리 없이 표준 라이브러리만 사용합니다.

사용 예:
    python ipynb2md.py notebook.ipynb
    python ipynb2md.py notebook.ipynb -o docs/out.md
    python ipynb2md.py notebook.ipynb --no-output
    python ipynb2md.py *.ipynb -o output --images-dir output/assets
    python ipynb2md.py . -r -o output
"""

import argparse
import base64
import glob
import json
import os
import re
import sys
from pathlib import Path

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def join(src):
    """nbformat의 source/text 필드는 문자열 또는 문자열 리스트."""
    return "".join(src) if isinstance(src, list) else (src or "")


def fence_for(text):
    """내용에 포함된 백틱 연속 길이보다 긴 펜스를 반환."""
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def code_block(text, lang=""):
    text = text.rstrip("\n")
    fence = fence_for(text)
    return f"{fence}{lang}\n{text}\n{fence}"


class Converter:
    def __init__(self, nb_path, out_path, include_output=True,
                 include_images=True, images_dir=None, max_output_lines=0):
        self.nb_path = Path(nb_path)
        self.out_path = Path(out_path)
        self.include_output = include_output
        self.include_images = include_images
        self.max_output_lines = max_output_lines
        self.shared_images = bool(images_dir)
        self.images_dir = Path(images_dir) if images_dir else \
            self.out_path.parent / f"{self.out_path.stem}_files"
        self.img_count = 0

    # ---------- 출력(outputs) 처리 ----------
    def save_image(self, data, ext):
        self.img_count += 1
        self.images_dir.mkdir(parents=True, exist_ok=True)
        prefix = f"{self.out_path.stem}_" if self.shared_images else ""
        name = f"{prefix}output_{self.img_count:03d}.{ext}"
        path = self.images_dir / name
        if ext == "svg":
            path.write_text(join(data), encoding="utf-8")
        else:
            path.write_bytes(base64.b64decode(join(data)))
        rel = os.path.relpath(path, self.out_path.parent)
        return Path(rel).as_posix().replace(" ", "%20")

    def truncate(self, text):
        if self.max_output_lines and text.count("\n") > self.max_output_lines:
            lines = text.splitlines()[: self.max_output_lines]
            lines.append(f"... (총 {len(text.splitlines())}줄 중 {self.max_output_lines}줄만 표시)")
            return "\n".join(lines)
        return text

    def render_output(self, out):
        otype = out.get("output_type")
        parts = []

        if otype == "stream":
            text = ANSI_RE.sub("", join(out.get("text", "")))
            if text.strip():
                parts.append(code_block(self.truncate(text), "text"))

        elif otype in ("execute_result", "display_data"):
            data = out.get("data", {})
            if self.include_images:
                for mime, ext in (("image/png", "png"), ("image/jpeg", "jpg"),
                                  ("image/svg+xml", "svg")):
                    if mime in data:
                        rel = self.save_image(data[mime], ext)
                        parts.append(f"![output]({rel})")
                        break
            if not parts:
                if "text/markdown" in data:
                    parts.append(join(data["text/markdown"]).strip())
                elif "text/plain" in data:
                    text = ANSI_RE.sub("", join(data["text/plain"]))
                    if text.strip():
                        parts.append(code_block(self.truncate(text), "text"))

        elif otype == "error":
            tb = "\n".join(out.get("traceback", []))
            tb = ANSI_RE.sub("", tb) or f"{out.get('ename')}: {out.get('evalue')}"
            parts.append(code_block(self.truncate(tb), "text"))

        return parts

    # ---------- 셀 처리 ----------
    def convert(self):
        nb = json.loads(self.nb_path.read_text(encoding="utf-8"))
        meta = nb.get("metadata", {})
        lang = (meta.get("language_info", {}).get("name")
                or meta.get("kernelspec", {}).get("language") or "python")

        blocks = []
        for cell in nb.get("cells", []):
            ctype = cell.get("cell_type")
            src = join(cell.get("source", ""))

            if ctype == "markdown":
                if src.strip():
                    blocks.append(src.strip())

            elif ctype == "code":
                if src.strip():
                    blocks.append(code_block(src, lang))
                if self.include_output:
                    outs = []
                    for o in cell.get("outputs", []):
                        outs.extend(self.render_output(o))
                    if outs:
                        blocks.append("**출력:**\n\n" + "\n\n".join(outs))

            elif ctype == "raw":
                if src.strip():
                    blocks.append(code_block(src))

        return "\n\n".join(blocks) + "\n"

    def run(self):
        md = self.convert()
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.out_path.write_text(md, encoding="utf-8")
        return self.out_path


def expand_inputs(patterns, recursive):
    """와일드카드/폴더를 직접 펼침 (PowerShell, cmd 대응)."""
    files = []
    for pat in patterns:
        path = Path(pat)
        if path.is_dir():
            it = path.rglob("*.ipynb") if recursive else path.glob("*.ipynb")
            files.extend(sorted(it))
        elif any(c in pat for c in "*?["):
            files.extend(Path(m) for m in sorted(glob.glob(pat, recursive=True)))
        else:
            files.append(path)
    files = [f for f in files if ".ipynb_checkpoints" not in f.parts]
    seen, uniq = set(), []
    for f in files:
        key = str(f.resolve())
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


def main(argv=None):
    p = argparse.ArgumentParser(description="ipynb → Markdown 변환기")
    p.add_argument("inputs", nargs="+",
                   help="변환할 .ipynb 파일, 와일드카드(*.ipynb), 또는 폴더")
    p.add_argument("-o", "--output",
                   help="출력 .md 파일 경로(입력 1개) 또는 출력 폴더")
    p.add_argument("-r", "--recursive", action="store_true",
                   help="폴더 입력 시 하위 폴더까지 검색")
    p.add_argument("--no-output", action="store_true", help="셀 실행 결과 제외")
    p.add_argument("--no-images", action="store_true", help="이미지 출력 제외")
    p.add_argument("--images-dir", help="이미지 저장 폴더 (기본: <이름>_files)")
    p.add_argument("--max-output-lines", type=int, default=0,
                   help="텍스트 출력 최대 줄 수 (0=무제한)")
    args = p.parse_args(argv)

    files = expand_inputs(args.inputs, args.recursive)
    if not files:
        print("[오류] 변환할 .ipynb 파일을 찾지 못했습니다.", file=sys.stderr)
        return 1

    # -o 가 .md 파일명이고 입력이 1개면 파일, 그 외에는 폴더로 취급
    out_is_file = False
    out_dir = None
    if args.output:
        o = Path(args.output)
        out_is_file = (len(files) == 1 and o.suffix.lower() == ".md"
                       and not o.is_dir())
        if not out_is_file:
            out_dir = o

    status = 0
    for src in files:
        if not src.is_file():
            print(f"[오류] 파일을 찾을 수 없음: {src}", file=sys.stderr)
            status = 1
            continue
        if out_is_file:
            out = Path(args.output)
        elif out_dir:
            out = out_dir / src.with_suffix(".md").name
        else:
            out = src.with_suffix(".md")
        try:
            result = Converter(
                src, out,
                include_output=not args.no_output,
                include_images=not args.no_images,
                images_dir=args.images_dir,
                max_output_lines=args.max_output_lines,
            ).run()
            print(f"[완료] {src} → {result}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"[오류] {src}: {e}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())