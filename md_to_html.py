"""Convert one UTF-8 Markdown file into a sanitized standalone HTML document."""

import argparse
from html import escape
from pathlib import Path
import sys

import nh3
from markdown_it import MarkdownIt


TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "strong", "em",
        "ul", "ol", "li", "a", "img", "blockquote", "hr", "br", "pre",
        "code", "table", "thead", "tbody", "tr", "th", "td"}
CSS = """
body { font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  line-height: 1.75; color: #20242a; max-width: 860px; margin: 40px auto;
  padding: 0 20px; overflow-wrap: anywhere; }
img { max-width: 100%; height: auto; }
table { border-collapse: collapse; display: block; overflow-x: auto; }
th, td { border: 1px solid #ccd1d8; padding: 8px 12px; }
th { background: #f2f4f7; }
pre { background: #f2f4f7; padding: 16px; overflow-x: auto; }
code { font-family: Consolas, monospace; }
pre code { white-space: pre; overflow-wrap: normal; }
blockquote { border-left: 4px solid #ccd1d8; margin-left: 0; padding-left: 16px; }
a { color: #1759ab; }
"""


def sanitize_html(fragment: str) -> str:
    """Keep only the HTML vocabulary needed by the supported Markdown."""
    return nh3.clean(
        fragment, tags=TAGS,
        attributes={"a": {"href", "title"}, "img": {"src", "alt", "title"},
                    "code": {"class"}, "ol": {"start"}},
        url_schemes={"http", "https", "mailto"},
        clean_content_tags={"script", "style"},
    )


def markdown_to_html(source: str) -> str:
    parser = MarkdownIt("commonmark", {"html": False}).enable("table")
    return sanitize_html(parser.render(source))


def build_document(body: str, title: str) -> str:
    """Wrap an already sanitized body with trusted document markup."""
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
{body}</body>
</html>
'''


def convert_file(input_path: Path, output_path: Path, overwrite: bool = False) -> Path:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")
    if input_path.resolve() == output_path.resolve() or (
        output_path.exists() and input_path.samefile(output_path)
    ):
        raise ValueError("Input and output must be different files.")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists; use --overwrite: {output_path}")
    source = input_path.read_text(encoding="utf-8-sig")
    document = build_document(markdown_to_html(source), input_path.stem)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also prevents accidental overwrite between the check and write.
    with output_path.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as target:
        target.write(document)
    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 Markdown file")
    parser.add_argument("-o", "--output", type=Path, help="Output HTML file")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = args.output if args.output is not None else args.input.with_suffix(".html")
    try:
        result = convert_file(args.input, output, args.overwrite)
    except UnicodeError:
        print("Error: Input file must be valid UTF-8.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Created: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
