import re, json, sys
from bs4 import BeautifulSoup
from model import weibo

class parser(object):
    
    @staticmethod
    def parse_mainpage(response):
        html = response.text
        soup = BeautifulSoup(html, 'lxml')        
        uid_config = soup.find('script', attrs={'type': "text/javascript"}, text=re.compile(r'\$CONFIG'))
        page_id = re.search('(page_id).+?(\d+)', uid_config.text).group(2)
        domain_id = re.search('(domain).+?(\d+)', uid_config.text).group(2)
        if page_id != None and domain_id != None:
            is_success = True
        else:
            is_success = False
        return {'success': is_success, 'data': {'page_id': page_id, 'domain_id': domain_id}, 'text': html}

    @staticmethod
    def parse_weibo_page(response):
        is_success = False
        html = response.text
        soup = BeautifulSoup(html, 'lxml')
        div = soup.find("script", text=re.compile(r'"ns":"pl.content.homeFeed.index","domid":"Pl_Official_MyProfileFeed__22"'))
        if not div:
            print("unsuccess in weibo page")
            return {'success': is_success, 'text': html, 'has_next' : False, 'error': 'no weibo card div in weibo page'}
        return parser.parse_weibo(div.text)

    @staticmethod
    def parse_weibo_ajax(response):
        is_success = False
        text = response.text
        try:
            res_json = json.loads(text)
            html = res_json['data']
        except:
            print("unsuccess in weibo ajax")
            return {'success': is_success, 'text': text, 'has_next' : False, 'error': 'no json data in weibo ajax'}
        return parser.parse_weibo(html)

    @staticmethod
    def parse_weibo(html):
        html = parser.clear_html_in_script(html)
        soup = BeautifulSoup(html, 'lxml')
        has_next = soup.find("a", {'class': 'page next S_txt1 S_line1'})
        #divs = soup.find_all("div", {'class': 'WB_cardwrap WB_feed_type S_bg2 WB_feed_vipcover WB_feed_like'})
        divs = soup.find_all("div", {'class': re.compile(r'WB_cardwrap.*'), 'mid': re.compile(r'\d+')})
        wbs = []
        rejected = []
        is_success = False
        for div in divs:
            is_success = True
            wb = weibo()
            try:
                # get date
                detail = div.find("div", {'class': 'WB_detail'})
                date_div = detail.find("div", {'class': 'WB_from S_txt2'})
                wb.date = date_div.a.attrs['date']
                # get message
                text_div = div.find("div", {'class': 'WB_text W_f14'})
                wb.message = re.sub(r'\s+', '', text_div.text)
                # get handle
                feed_div = div.find("div", {'class': re.compile(r'WB_feed_handle.*')})
                handle_div = feed_div.find("div", {'class': re.compile(r'WB_handle.*')})
                li = handle_div.find_all("li")
                wb.shares = parser.get_num(li[1].text)
                wb.comments = parser.get_num(li[2].text)
                wb.likes = parser.get_num(li[3].text)
            except:
                rejected.append({'error': sys.exc_info()[0], 'html': str(div)})
            else:
                wbs.append(wb)
        if not is_success:
            print("unsuccess in parse weibo")
        return {'success': is_success, 'wbs': wbs, 'rejected': rejected, 'has_next': has_next, 'text': html, 'error' : 'Cannot find divs'}

    @staticmethod
    def get_num(str):
        if str:
            str = re.sub(r'\D+', '\t', str)
            str = re.sub(r'\D+', '\t', str)
            str = re.sub(r'^\t+', '', str)
            str = re.sub(r'\t+$', '', str)
        return str
    
    @staticmethod
    def clear_html_in_script(html):
        if html:
            html = re.sub(r'\\r', '\r', html)    
            html = re.sub(r'\\n', '\n', html)
            html = re.sub(r'\\t', '\t', html)    
            html = re.sub(r'\\/', '/', html)
            html = re.sub(r'\\"', '"', html)
        return html
