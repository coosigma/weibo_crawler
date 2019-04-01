import sys, os, time, re, json, pickle

from login import WeiboLogin
from parse import parser

class WeiboSpider(object):
    conf = {}
    IOHandle = {}
    uids = set()
    uid = None
    sleep_time = (600)
    def __init__(self, downloader):
        self.downloader = downloader
        handle = self.IOHandle
        try:
            with open('settings.json', 'r') as f:
                conf = json.load(f)
            if not (conf['uids'] or conf['log'] or conf['output_path']):
                print('Please check configs in settings.json')
            else:
                if conf['output_path'][-1] != '/':
                    conf['output_path'] += '/'
        except:
            print('Please check the config file "settings.json"')
            print("sys err info:", sys.exc_info()[0])
            sys.exit()
        else:
            handle['uid'] = WeiboSpider.open_file(conf['uids'], 'r')
            log = handle['log'] = WeiboSpider.open_file(conf['log'], 'w', 1)
            print('Read uids...')
            self.read_uids()
            log.write("uids:"+"\n")
            [log.write(i + "\n") for i in self.uids]
            self.conf = conf


    @staticmethod
    def open_file(path, mode, buffering=1, encoding='utf-8'):
        try:
            if 'w' in mode:
                fh = open(path, mode, buffering=buffering, encoding=encoding)
            else:
                fh = open(path, mode)
            return fh
        except IOError:
            print('cannot open', path)
            print("sys err info:", sys.exc_info()[0])
            sys.exit(2)

    def read_uids(self):
        fh = self.IOHandle['uid']
        with fh as f:
            #self.uids.update([re.match(r'(\w+)\t(\d+)', i).expand(r'\2') for i in f.readlines()])
            self.uids.update([re.search(r'(\d+)', i).expand(r'\1') for i in f.readlines()])

    def make_output_handles(self):
        uid = self.uid
        path = self.conf['output_path'] + uid + '/'
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            self.IOHandle['output_json'].close
            self.IOHandle['output_rejected'].close
        except:
            pass
        self.IOHandle['output_json'] = self.open_file(path + 'weibo.json', 'w', )
        self.IOHandle['output_rejected'] = self.open_file(path+'rejected.txt', 'w')

    def crawl(self, base_url, paras, parser, writer=None):
        dl = self.downloader
        url = base_url % paras
        try:
            response = dl.session.get(url)
        except:
            print('cannot download url:[%s]' % url)
            print("sys err info:", sys.exc_info()[0])
            print("start to sleep for %s" % self.sleep_time)
            time.sleep(self.sleep_time)
            print("Woke up, crawl again...")
            return self.crawl(base_url, paras, parser, writer)
        else:
            res = parser(response)
            if writer:
                writer(res, url)
            return res
    
    def write_to_json(self, res, url):
        if res['success']:
            for wb in res['wbs']:
                wb.write_to_file(self.IOHandle['output_json'])
            for rj in res['rejected']:
                rejected_text = "rejected url: %s\nreason: %s\nhtml:%s\n" % (url, rj['error'], rj['html'])
                self.IOHandle['output_rejected'].write(rejected_text)
        else:
            error_text = "uid: %s cannot get data at url: %s\n%s" % (self.uid, url, res['text'])
            self.IOHandle['output_rejected'].write(error_text)

if __name__ == '__main__':
    base_url = "https://www.weibo.com/u/%s?is_all=1"
    wb_url = "https://www.weibo.com/p/%s/home?pids=Pl_Official_MyProfileFeed__22&is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page=%s#feedtop"
    ajax_url = "https://www.weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=%s&is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page=%s&pagebar=%s&pl_name=Pl_Official_MyProfileFeed__22&id=%s&pre_page=%s"
    # url = ajax_url % (domain_id, page, page_bar, page_id)
    sleep_time = 0.1

    # S1: Get cookie
    print('Get logined cookie...')
    username = 'dummy'
    password = 'dummy'
    dl = WeiboLogin(username=username, password=password)
    with open('login.cookie', 'rb') as f:
        dl.session.cookies.update(pickle.load(f))
   
    # S2: Create spider
    print('Initialized the Spider...')
    spider = WeiboSpider(dl)
    log = spider.IOHandle['log']

    # S3: Treat uids
    for uid in spider.uids:
        print("start to treat uid:", uid)
        log.write("start to treat uid: %s\n"%uid)
        spider.uid = uid
        # 3.0
        spider.make_output_handles()
        # 3.1 get main page
        paras = (uid)
        config_res = spider.crawl(base_url, paras, parser.parse_mainpage)
        if config_res['success'] == True:
            page_id = config_res['data']['page_id']
            domain_id = config_res['data']['domain_id']
        else:
            print("Cannot cat page id and domain id, main page problem.")
            sys.exit(1)
        log.write('Got the main page, the page id is %s\n' % page_id)
        log.write('And the domain id is %s\n' % domain_id)
        # s4.2 get weibo page
        page = 1
        while True:
            print("Try to treat page %s" % page)
            paras = (page_id, page)
            print("treat top page")
            wb_res = spider.crawl(wb_url, paras, parser.parse_weibo_page, spider.write_to_json)
            time.sleep(sleep_time)
            page_bar = 0
            paras = (domain_id, page, page_bar, page_id, page)
            print("treat 1st ajax")
            aj1_res = spider.crawl(ajax_url, paras, parser.parse_weibo_ajax, spider.write_to_json)
            time.sleep(sleep_time)
            page_bar = 1
            paras = (domain_id, page, page_bar, page_id, page)
            print("treat 2nd ajax")
            aj2_res = spider.crawl(ajax_url, paras, parser.parse_weibo_ajax, spider.write_to_json)
            log.write("page %s is done\n" % page)
            time.sleep(sleep_time)
            if aj2_res['has_next']:
                page += 1
                if page > 30:
                    t = spider.sleep_time
                    print("pages over 30, start to sleep for %s''\n"%t)
                    time.sleep(t)
                    print("Woke up, continue crawl...")
            else:
                log.write("%s is the final page\n" % page)
                break
