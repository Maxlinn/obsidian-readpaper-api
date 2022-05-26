import argparse
import os.path
import re
from functools import lru_cache
from typing import Tuple, Dict
from datetime import datetime
import yaml

import crawler
import stored

class ReadpaperMarkdownManager(object):
    def __init__(self):
        self._crawler = crawler.ReadPaperCrawler()
        self._paper2desc = {}

    def manage_single_markdown_file(self, fname: str):
        if os.path.exists(fname):
            with open(fname, 'r', encoding='utf-8') as f:
                fm, content = self._separate_frontmatter_with_content(f.read())
        else:
            fm, content = dict(), str()

        # 找到论文
        if 'aliases' in fm:
            name: str = fm['aliases']
        else:
            name: str = os.path.splitext(os.path.basename(fname))[0]

        if name not in self._paper2desc:
            self._fetch_all_papers()

        # 找出含有该名字片段的第一篇论文
        def find_name_inside():
            for k in self._paper2desc.keys():
                if name.lower() in k.lower(): return k
            return ''

        name_found = find_name_inside()
        if not name_found:
            raise Exception(f"Not found paper name like {name}.")
        name = name_found

        fm_update = self._parse_paper_desc(self._paper2desc[name])
        # 更新aliases
        fm_update['aliases'] = name
        # tag需要手动merge，因为可能有一些本地的tag
        if 'tags' in fm:
            fm_update['tags'] = list(set(fm_update['tags']) | set(fm['tags']))
        fm.update(fm_update)

        with open(fname, 'w', encoding='utf-8') as f:
            to_write = self._merge_frontmatter_with_content(fm, content)
            f.write(to_write)

    def _parse_paper_desc(self, j:dict):
        url = f'https://readpaper.com/pdf-annotate/note?pdfId={j["pdfId"]}'
        authors = j.get('authors', [])[:3]
        tags = [
            el['classifyName'] for el in
            j.get('classifyInfos', [])
        ]
        published_on = j.get('conference', '') or j.get('journal', '')

        published_ts :int = j.get('publishDate', 0)
        published_ts :datetime = datetime.fromtimestamp(published_ts // 1000)
        published_ts :str = published_ts.strftime('%Y年%m月%d日')

        d = {
            'readpaper': url,
            'authors': authors,
            'tags': tags,
            'published_on': published_on,
            'published_datetime': published_ts
        }
        return d

    def _separate_frontmatter_with_content(self, content: str) -> Tuple[Dict, str]:
        pat = r'^---\n(.*?)---'
        match = re.search(pat, content, re.S)
        if match:
            ridx = match.span()[1]
            return yaml.safe_load(match.group().strip('-\n')), content[ridx:].lstrip()
        else:
            return dict(), content

    def _merge_frontmatter_with_content(self, fm:dict, content:str)->str:
        fm = yaml.safe_dump(fm, indent=4, allow_unicode=True)
        return f'---\n{fm}---\n' + content

    # 程序的一次运行中，不重复请求
    @lru_cache(1)
    def _fetch_all_papers(self):
        l = self._crawler.request_all_papers()
        self._paper2desc = {el['docName']: el for el in l}

    def _get_note_desc(self, pdfId: str):
        return self._crawler.request_note_desc(pdfId)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--md', type=str, help='Location of the markdown file want to inject readpaper info to.')
    args = parser.parse_args()

    m = ReadpaperMarkdownManager()
    m.manage_single_markdown_file(args.md)