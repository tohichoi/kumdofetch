import pickle
import unittest
from pprint import pprint

from main import get_html, urls, check_new_article, old_articles, make_message


class MyTestCase(unittest.TestCase):
    @unittest.skip
    def test_save_html(self):
        htmls = dict()
        for board_name, url in urls.items():
            htmls[board_name] = get_html(url[0])
        with open('htmls.pickle', 'wb+') as fd:
            pickle.dump(htmls, fd)

    def test_parse(self):
        with open('htmls.pickle', 'rb') as fd:
            htmls = pickle.load(fd)

        new_articles = check_new_article(old_articles, htmls)
        msgs = make_message(new_articles)
        pprint(msgs)

if __name__ == '__main__':
    unittest.main()
