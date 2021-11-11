# This is a sample Python script.

import json
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import logging
import os
import pickle
import urllib.request
from urllib.parse import urlencode, quote_plus

from bs4 import BeautifulSoup
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from telegram.utils.helpers import escape_markdown

old_articles = {}
urls = {
    'center_notice': ['http://www.kumdo.org/notice/', 'http://www.kumdo.org/notice/', 13],
    'center_lesson': ['http://www.kumdo.org/deahan_kumdo/d-kumdo6.php', 'http://www.kumdo.org/deahan_kumdo/', 16],
    'center_news': ['http://www.kumdo.org/news/', 'http://www.kumdo.org/news/', 13],
    'gg_notice': ['http://www.kyungkum.org/board/list.php?board=notice&page=1&md=4', 'http://www.kyungkum.org/board/',
                  11],
}


def get_html(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def check_new_article(o_articles, preloaded_htmls=None):

    htmls = preloaded_htmls if preloaded_htmls else dict()

    # for k, u in urls.items():
    #     htmls[k] = get_html(u[0])
    new_articles = dict()

    for board_name, url in urls.items():
        if board_name not in htmls:
            htmls[board_name] = get_html(url[0])

        # htmls[board_name] = get_html(url[0])

        soup = BeautifulSoup(htmls[board_name])
        elms = soup.find_all('table')

        # for i, e in enumerate(elms):
        #     ...:     print(f'=============== {i} =============\n{e.text.strip()}')
        tr = elms[url[2]].find_all('tr')
        for r in tr:
            # print(r.text.strip().replace("\n", ' '))
            td = r.find_all('td')
            # td[0] : number or \n
            # td[1] : 제목
            # td[2] : 글쓴이
            # td[3] : 작성일
            # td[4] : 조회
            # for d in td:
            #     print(d.text.strip())

            num = td[0].text.strip()
            board_key = board_name + num
            if len(num) > 0 and num.isnumeric() and board_key not in o_articles:
                new_articles[board_key] = (
                    td[1].text.strip(), urls[board_name][1] + td[1].find('a').attrs['href'].strip())

    return new_articles


def get_title(board_key):
    if 'center_notice' in board_key:
        return '[중앙:공지]'
    elif 'center_news' in board_key:
        return '[중앙:뉴스]'
    elif 'center_lesson' in board_key:
        return '[중앙:강습회]'
    elif 'gg_notice' in board_key:
        return '[경기:공지]'
    else:
        return ''


def make_message(articles):
    # msg = f'**{title}**\n'
    msgs = []
    m = ''
    table = str.maketrans('<>', '[]')
    for k, v in articles.items():
        # s = f'* \\[{k} {v[0]}\\]\\({v[1]}\\)\n'
        s = f'{get_title(k)} <a href="{v[1]}">{v[0].translate(table)}</a>\n'
        if len(m) + len(s) > 4096:
            msgs.append(m)
            m = s
        else:
            m += s

    if len(m) > 0:
        msgs.append(m)

    return msgs


def fetch_articles(tbot, chatid, o_article, notify_empty_event=False):

    new_articles_sl = check_new_article(o_article)
    msgs = make_message(new_articles_sl)
    if len(msgs) > 0:
        for msg in msgs:
            tbot.send_message(chatid, msg, parse_mode='HTML')
    else:
        if notify_empty_event:
            tbot.send_message(chatid, "No new message", parse_mode='HTML')

    if len(new_articles_sl) > 0:
        o_article.update(**new_articles_sl)
        with open('old_articles.pickle', 'wb+') as fd:
            pickle.dump(o_article, fd)


def job_check(context):
    logging.info(f'{context}')

    tbot = context.bot
    chatid = context.job.context

    fetch_articles(tbot, chatid, old_articles)


# context: telegram.ext.CallbackContext
def callback_check(update, context):
    logging.info(f'{update.effective_message.text}')

    chatid = update.effective_chat.id

    fetch_articles(context.bot, chatid, old_articles, notify_empty_event=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        #    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                        format='%(asctime)s : %(funcName)s : %(message)s')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    with open('bot.json') as fd:
        cf = json.load(fd)
        Bot(cf['bot_token'])

    if os.path.exists('old_articles.pickle'):
        with open('old_articles.pickle', 'rb') as fd:
            old_articles = pickle.load(fd)

    updater = Updater(token=cf['bot_token'], use_context=True)
    dispatcher = updater.dispatcher

    job_queue = updater.job_queue
    dispatcher.add_handler(CommandHandler('check', callback_check, pass_job_queue=True))

    updater.job_queue.run_repeating(job_check, interval=3600 * 2, first=1, context=cf['bot_chatid'])

    updater.start_polling()
