#!/usr/bin/env python3
from bs4 import BeautifulSoup
import pathlib
import sys
from configparser import ConfigParser
from elasticsearch_dsl import connections, Document, InnerDoc, Nested, Long, Text, Object, Keyword, Date
from collections import namedtuple

MESSAGES_PATH = 'messages/'
MESSAGES_INDEX_FILE = 'index-messages.html'

LanguageSettings = namedtuple('LanguageSettings', ['encoding', 'datefmt', 'locale'])
language_table = {
    'ru': LanguageSettings(encoding='cp1251', datefmt='%d %b %Y в %H:%M:%S', locale='ru_RU.UTF-8')
}

class Author(InnerDoc):
    id = Keyword(required=True)
    name = Text(required=True, fields={'keyword': Keyword()})


class Message(InnerDoc):
    author = Object(Author, required=True)
    text = Text(required=True)
    time = Date(required=True)

class Conversation(Document):
    id = Long(required=True)
    name = Text(required=True, fields={'keyword': Keyword()})
    messages = Nested(Message)

    class Index:
        name = 'conversations'

    def add_message(self, author, text, time, commit = True):
        msg = Message(author=author, text=text, time=time)
        self.messages.append(msg)
        if commit:
            msg.save()

        return msg


    def read_messages(self, path : pathlib.Path, lang: LanguageSettings):
        with open(path, 'r', encoding=lang.encoding) as file:
            contents = file.read()







if __name__ == '__main__':
    folder = pathlib.Path(sys.argv[1])
    config = ConfigParser(inline_comment_prefixes=('#'))
    config.read('config.ini')
    connections.create_connection()
    language = config['settings']['lang']

    lang = language_table.get(language) or LanguageSettings(encoding='utf-8', datefmt='%d %b %Y at %H:%M:%S', locale=None)
    import locale
    locale.setlocale(locale.LC_TIME, lang.locale)

    with open(folder.joinpath(MESSAGES_PATH, MESSAGES_INDEX_FILE), 'r', encoding=lang.encoding) as file:
        contents = file.read()

    msg_index = BeautifulSoup(contents, 'html.parser')
    for peer in msg_index.find_all('div', {'class': 'message-peer--id'}):
        link = peer.a
        href = link['href']
        id = int(href.split('/')[0])
        name = link.text
        conversation = Conversation(id=id, name=name)
        conversation.read_messages(folder.joinpath(MESSAGES_PATH, href), lang)
        conversation.save()

