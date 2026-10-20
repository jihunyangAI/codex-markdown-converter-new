import contextlib
from html.parser import HTMLParser
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import md_to_html as app


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.text = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)


class RenderingTests(unittest.TestCase):
    def test_basic_structure_and_korean(self):
        parsed = Elements(app.markdown_to_html('# 안녕하세요\n\n**중요** *강조*\n\n- 항목\n\n1. 순서\n\n> 인용\n\n---'))
        tags = [tag for tag, _ in parsed.elements]
        for tag in ('h1', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote', 'hr'):
            self.assertIn(tag, tags)
        self.assertIn('안녕하세요', ''.join(parsed.text))

    def test_table_and_code(self):
        source = '| 항목 | 설명 |\n| --- | --- |\n| 입력 | 마크다운 |\n\n```python\nprint("<안녕하세요>")\n```'
        parsed = Elements(app.markdown_to_html(source))
        for tag in ('table', 'thead', 'tbody', 'th', 'td', 'pre'):
            self.assertIn(tag, [name for name, _ in parsed.elements])
        self.assertIn(('code', {'class': 'language-python'}), parsed.elements)
        self.assertIn('print("<안녕하세요>")\n', parsed.text)

    def test_relative_links_and_images(self):
        parsed = Elements(app.markdown_to_html('[안내](docs/guide.html)\n\n![사진](images/photo.png)'))
        self.assertTrue(any(tag == 'a' and attrs.get('href') == 'docs/guide.html' for tag, attrs in parsed.elements))
        self.assertIn(('img', {'src': 'images/photo.png', 'alt': '사진'}), parsed.elements)

    def test_raw_html_is_inert_and_unsafe_markdown_link_has_no_href(self):
        parsed = Elements(app.markdown_to_html('<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>\n\n[클릭](javascript:alert(1))'))
        self.assertFalse(any(tag in ('script', 'img') for tag, _ in parsed.elements))
        self.assertIn('클릭', ''.join(parsed.text))
        self.assertFalse(any('href' in attrs for _, attrs in parsed.elements))

    def test_sanitizer_removes_dangerous_html_and_schemes(self):
        parsed = Elements(app.sanitize_html('<script>bad()</script><img src="javascript:alert(1)" onerror="x()"><a href="java&#x73;cript:alert(1)">클릭</a><a href="https://example.com">safe</a>'))
        self.assertNotIn('bad()', ''.join(parsed.text))
        for tag, attrs in parsed.elements:
            self.assertNotEqual(tag, 'script')
            self.assertNotIn('onerror', attrs)
            self.assertFalse(any(value.lower().startswith('javascript:') for value in attrs.values()))
        self.assertTrue(any(attrs.get('href') == 'https://example.com' for _, attrs in parsed.elements))

    def test_document_title_is_escaped(self):
        result = app.build_document('', '</title><script>bad()</script>')
        parsed = Elements(result)
        self.assertNotIn('script', [tag for tag, _ in parsed.elements])
        self.assertIn('<!DOCTYPE html>', result)
        self.assertIn(('html', {'lang': 'ko'}), parsed.elements)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / '한글.md'
        self.source.write_text('# 안녕하세요', encoding='utf-8')

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            code = app.main(list(map(str, args)))
        return code, out.getvalue(), err.getvalue()

    def test_default_output_and_overwrite(self):
        code, out, _ = self.run_cli(self.source)
        self.assertEqual(code, 0)
        self.assertIn('Created:', out)
        target = self.source.with_suffix('.html')
        self.assertIn('<title>한글</title>', target.read_text(encoding='utf-8'))
        original = target.read_bytes()
        self.source.write_text('changed', encoding='utf-8')
        self.assertNotEqual(self.run_cli(self.source)[0], 0)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual(self.run_cli(self.source, '--overwrite')[0], 0)
        self.assertIn('changed', target.read_text(encoding='utf-8'))

    def test_empty_input_and_nested_output(self):
        self.source.write_text('', encoding='utf-8')
        target = self.root / 'new' / 'nested' / 'empty.html'
        self.assertEqual(self.run_cli(self.source, '-o', target)[0], 0)
        self.assertIn('<body>\n</body>', target.read_text(encoding='utf-8'))

    def test_invalid_paths_and_same_file(self):
        for source in (self.root / 'missing.md', self.root):
            code, _, error = self.run_cli(source)
            self.assertNotEqual(code, 0)
            self.assertIn('Error:', error)
        self.assertNotEqual(self.run_cli(self.source, '-o', self.source, '--overwrite')[0], 0)
        self.assertEqual(self.source.read_text(encoding='utf-8'), '# 안녕하세요')

    def test_invalid_utf8(self):
        self.source.write_bytes(b'\xff\xfe\x80')
        code, _, error = self.run_cli(self.source)
        self.assertNotEqual(code, 0)
        self.assertIn('UTF-8', error)
        self.assertFalse(self.source.with_suffix('.html').exists())

    def test_permission_errors_reported(self):
        with patch.object(Path, 'read_text', side_effect=PermissionError('read denied')):
            code, _, error = self.run_cli(self.source)
        self.assertEqual(code, 1)
        self.assertIn('read denied', error)
        original_open = Path.open

        def deny_write(path, mode='r', *args, **kwargs):
            if mode in ('w', 'x'):
                raise PermissionError('write denied')
            return original_open(path, mode, *args, **kwargs)

        with patch.object(Path, 'open', deny_write):
            code, _, error = self.run_cli(self.source)
        self.assertEqual(code, 1)
        self.assertIn('write denied', error)


if __name__ == '__main__':
    unittest.main()
