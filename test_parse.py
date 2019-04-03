from parse import parser
from bs4 import BeautifulSoup

with open('log1', 'r', encoding='utf-8') as f:
    html = f.readlines()

soup = BeautifulSoup(html, 'lxml')



