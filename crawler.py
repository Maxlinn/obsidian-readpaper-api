from typing import Callable
import requests
import requests.utils
from stored import COOKIES, HEADERS, TEST_NOTE_ID


def API(url: str):
    # - API is a decorator factory, it returns a decorator object
    # - a decorator object receives a function as param
    #   - it manipulates the call `function()` to `decorator()()` in python runtime
    #   - notice, it has double `()`, means should call `decorator()` to get a real function
    #   - so a good practice is to return a `wrapper` inside `decorator` definition
    # - the `wrapper` receives the params of `function(params)` call
    def decorator(api_caller: Callable):
        def wrapper(*args, **kwargs):
            kwargs['url'] = url
            return api_caller(*args, **kwargs)

        return wrapper

    return decorator


class ReadPaperCrawler(object):

    def __init__(self):
        self.session: requests.Session = requests.session()
        self.load_session()

    def load_session(self):
        requests.utils.add_dict_to_cookiejar(self.session.cookies, COOKIES)
        self.session.headers = HEADERS

    @API('https://readpaper.com/api/microService-app-aiKnowledge/client/doc/getDocListByFolderId')
    def request_all_papers(self, url):
        payload = {"folderId": "0", "sortType": 0, "orgId": "535992339879038976", "appId": "aiKnowledge"}
        r = self.session.post(url, json=payload)
        return r.json()['data']

    @API('https://readpaper.com/api/microService-app-aiKnowledge/userDoc/getUserAllClassifyList')
    def request_all_tags(self, url):
        payload = {"orgId": "535992339879038976", "appId": "aiKnowledge"}
        r = self.session.post(url, json=payload)
        return r.json()['data']

    @API('https://readpaper.com/api/microService-app-aiKnowledge/paperNote/getOwnerPaperNoteBaseInfo')
    def request_note_desc(self, pdfId: str, url):
        '''note_id和下载链接'''
        payload = {"pdfId": pdfId, "orgId": "535992339879038976", "appId": "aiKnowledge", "paperId": "", "noteId": ""}
        r = self.session.post(url, json=payload)
        return r.json()['data']

    @API('https://readpaper.com/api/microService-app-aiKnowledge/paperNote/getPaperNoteBaseInfoById')
    def request_note_desc_by_note_id(self, noteId: str, url):
        '''一般用不到，因为和request_note_desc的返回值是一样的，而且人家不需要noteId'''
        payload = {"noteId": noteId, "orgId": "535992339879038976", "appId": "aiKnowledge", "paperId": "", "pdfId": ""}
        r = self.session.post(url, json=payload)
        return r.json()['data']

    @API('https://readpaper.com/api/microService-app-aiKnowledge/pdfMark/v2/web/getByNote')
    def request_notes(self, noteId: str, url):
        params = {'noteId': noteId}
        # 这很重要
        # https://blog.csdn.net/ITCwg/article/details/112805584
        # 1、Content-Length 如果存在并且有效的话，则必须和消息内容的传输长度完全一致。
        # （经过测试，如果过短则会截断，过长则会导致超时。）
        if 'Content-Length' in self.session.headers:
            del self.session.headers['Content-Length']
        r = self.session.get(url, params=params)
        return r.json()


if __name__ == '__main__':
    obj = ReadPaperCrawler()
    j = obj.request_all_papers()
    from pprint import pprint
    pprint(j)
