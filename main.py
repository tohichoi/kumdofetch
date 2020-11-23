# This is a sample Python script.

import json
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import logging
import os
import pickle
import urllib.request

from bs4 import BeautifulSoup
from telegram import Bot
from telegram.ext import Updater, CommandHandler

old_articles = dict()


def get_html(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def check_new_article(old_articles):
    url_gg = 'http://www.kyungkum.org/board/list.php?board=notice&page=1&md=4'

    if not os.path.exists('html_gg.pickle'):
        html_gg = get_html(url_gg)
    else:
        with open('html_gg.pickle', 'rb') as fd:
            html_gg = pickle.load(fd)

    soup = BeautifulSoup(html_gg)
    elm2 = soup.find_all('table')
    tr = elm2[11].find_all('tr')

    new_articles = dict()
    for r in tr:
        # print(r.text.strip().replace("\n", ' '))
        td = r.find_all('td')
        # td[0] : number or \n
        # td[1] : 제목
        # td[2] : 글쓴이
        # td[3] : 작성일
        # td[4] : 조회
        for d in td:
            print(d.text.strip())

        num = td[0].text.strip()
        if len(num) > 0 and num not in old_articles:
            new_articles[num] = (
                td[1].text.strip(), 'http://www.kyungkum.org/board/' + td[1].find('a').attrs['href'].strip())

    # send new articles
    # for k, v in new_articles.items():
    #     print(f'{k} : {v}')

    return new_articles


def fetch_articles(bot, chatid, old_article):
    # context.bot.send_message(chatid, "일 시작합니다~")
    new_articles = check_new_article(old_articles)

    # send new articles
    msg = ''
    for k, v in new_articles.items():
        msg += f'[{k} {v[0]}]({v[1]})\n'
    if len(msg) > 0:
        bot.send_message(chatid, msg, parse_mode='Markdown')
        old_articles.update(**new_articles)
    else:
        bot.send_message(chatid, 'No new notice', parse_mode = 'Markdown')


def job_check(context):
    logging.info(f'{context}')

    bot = context.bot
    chatid = context.job.context[1]

    fetch_articles(bot, chatid, old_articles)


# context: telegram.ext.CallbackContext
def callback_check(update, context):
    logging.info(f'{update.effective_message.text}')

    chatid = update.effective_chat.id

    fetch_articles(context.bot, chatid, old_articles)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        #    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                        format='%(asctime)s : %(funcName)s : %(message)s')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    with open('bot.json') as fd:
        cf = json.load(fd)
        bot = Bot(cf['bot_token'])

    updater = Updater(token=cf['bot_token'], use_context=True)
    dispatcher = updater.dispatcher

    job_queue = updater.job_queue
    dispatcher.add_handler(CommandHandler('check', callback_check, pass_job_queue=True))

    updater.job_queue.run_repeating(job_check, interval=3600 * 2, first=1, context=(bot, cf['bot_chatid']))

    updater.start_polling()
