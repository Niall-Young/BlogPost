import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
from poster import render, fetch

DATA = {'url':'https://doc.niallspace.com/ai/posts/components-dev', 'title':'如何用 AI 开发\n自己的设计组件库', 'subtitle':'设计规则与代码', 'summary':'在 Figma 定好设计规则，让 AI 批量转成代码，用 Base UI 承载交互，再到 Storybook 检查调整。'}

class PosterTests(unittest.TestCase):
    def test_url_and_export(self):
        with tempfile.TemporaryDirectory() as temp:
            report = render(DATA, Path(temp))
            self.assertTrue(all(report['qr'].values()))
            self.assertEqual(set(p.name for p in Path(temp).iterdir()), {'poster.png','qr.png','copy.json','verification.json'})
            with self.assertRaisesRegex(ValueError, 'already exists'):
                render(DATA, Path(temp))

    def test_long_title_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'overflows'):
                render(dict(DATA, title='这是一个非常长的文章标题'*12), Path(temp))
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_long_url(self):
        with tempfile.TemporaryDirectory() as temp:
            report = render(dict(DATA, url='https://example.com/article?search='+'abcdef1234'*10), Path(temp))
            self.assertTrue(all(report['qr'].values()))

    def test_too_dense_url_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'too long'):
                render(dict(DATA, url='https://example.com/?q='+'abcdefghij'*60), Path(temp))

    def test_fetch_failure_is_not_content(self):
        with patch('urllib.request.urlopen', side_effect=URLError('offline')):
            with self.assertRaises(URLError):
                fetch(DATA['url'])

if __name__ == '__main__':
    unittest.main()
