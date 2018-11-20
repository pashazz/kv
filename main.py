#!/usr/bin/env python3
from bs4 import BeautifulSoup
import pathlib
import sys
from configparser import ConfigParser

if __name__ == '__main__':
    folder = sys.argv[1]
    config = ConfigParser(inline_comment_prefixes=('#'))
    config.read('config.ini')
    api_endpoint = config['elasticsearch']['url']

    print(api_endpoint)