#!/usr/bin/env python3
from bs4 import BeautifulSoup, Tag,NavigableString
import pathlib
import sys
from configparser import ConfigParser
from elasticsearch_dsl import connections, Document, InnerDoc, Nested, Long, Text, Object, Keyword, Date, MetaField
from elasticsearch.helpers import bulk
from collections import namedtuple
from urllib.parse import urlparse
from datetime  import datetime

MESSAGES_PATH = 'messages/'
MESSAGES_INDEX_FILE = 'index-messages.html'

LanguageSettings = namedtuple('LanguageSettings', ['encoding', 'datefmt', 'locale', 'you'])
language_table = {
    'ru': LanguageSettings(encoding='cp1251', datefmt='%d %b %Y в %H:%M:%S', locale='ru_RU.UTF-8', you='Вы')
}

def insert(doc: Document):
    return doc.to_dict(include_meta=True)


class Author(InnerDoc):
    id = Keyword(required=True)
    name = Text(required=True, fields={'keyword': Keyword()})




class Conversation(Document):
    id = Long(required=True)
    name = Text(required=True, fields={'keyword': Keyword()})



class Message(Document):
    author = Object(Author, required=True)
    text = Text(required=True)
    time = Date(required=True)
    last_edit = Date()
    conversation = Object(Conversation, required=True)

    class Index:
        name = 'messages'


def read_messages(conversation, path: pathlib.Path, lang: LanguageSettings):
        with open(path, 'r', encoding=lang.encoding) as file:
            contents = file.read()
        dialog = BeautifulSoup(contents, 'html.parser')
        msgs = []
        for writing in dialog.find_all('div', {'class': 'message'}):
            id: str = None
            name: str = None
            text: str = ""
            msgtime: datetime = None
            edited: datetime = None
            for elem in writing.children:

                if not isinstance(elem, Tag) or elem.name != 'div':
                    continue
                if 'class' in elem.attrs and 'message__header' in elem.attrs['class']:
                    if elem.a:
                        link = elem.a  # profile link
                        id = urlparse(link['href']).path[1:]
                        name = link.text
                        date_s = elem.contents[1].strip(', ')
                        author = Author(id=id, name=name)
                    else:
                        date_s = elem.contents[0].replace(lang.you, '').strip(', ')
                        author = Author(id='id0', name=lang.you)

                    msgtime = datetime.strptime(date_s, lang.datefmt)

                    if elem.span:
                        edited = datetime.strptime(elem.span['title'], lang.datefmt)




                else:
                    # Replace all <br> s with \n
                    for child in elem.children:
                        if isinstance(child, NavigableString):
                            text += child.strip()
                        elif isinstance(child, Tag) and child.name == 'br':
                            text += '\n'

            print(f"Add message: {author} at {msgtime}")
            msg = Message(author=author, text=text, time=msgtime, last_edit=edited, conversation=conversation)
            msgs.append(msg)

        bulk(connections.get_connection(), (insert(msg) for msg in msgs))





def setup():
    " Create an IndexTemplate and save it into elasticsearch. "
    connections.create_connection()
    Message.init()


if __name__ == '__main__':
    setup()
    if not len(sys.argv) > 1:
        exit()



    folder = pathlib.Path(sys.argv[1])
    config = ConfigParser(inline_comment_prefixes=('#'))
    config.read('config.ini')
    language = config['settings']['lang']

    lang = language_table.get(language) or LanguageSettings(encoding='utf-8', datefmt='%d %b %Y at %H:%M:%S', locale=None)
    import locale
    locale.setlocale(locale.LC_TIME, lang.locale)

    with open(folder.joinpath(MESSAGES_PATH, MESSAGES_INDEX_FILE), 'r', encoding=lang.encoding) as file:
        contents = file.read()

    msg_index = BeautifulSoup(contents, 'html.parser')
    conversations = []
    for peer in msg_index.find_all('div', {'class': 'message-peer--id'}):
        link = peer.a
        href = link['href']
        id = int(href.split('/')[0])
        name = link.text
        conversation = Conversation(id=id, name=name)
        read_messages(conversation, folder.joinpath(MESSAGES_PATH, href), lang)



