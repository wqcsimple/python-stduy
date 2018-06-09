# coding:utf-8
import urllib

import scrapy
import zlib
from  bs4 import BeautifulSoup
import os

import sys

DEFAULT_HEADERS = [
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
    },
    {
        'User-Agent': 'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)'
    }
]


class Comics(scrapy.Spider):
    name = "comics"

    def start_requests(self):
        self.log("encode: " + sys.getdefaultencoding())
        urls = ['http://www.xeall.com/shenshi']
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        content = response.body

        if not content:
            self.log('parse body error.')
            return

        soup = BeautifulSoup(content, 'html5lib')
        listcon_tag = soup.find('ul', class_='listcon')
        if len(listcon_tag) < 1:
            self.log('extract comics list error')
            return

        com_a_list = listcon_tag.find_all('a', attrs={'href': True})
        if len(com_a_list) < 1:
            self.log('can not find <a> that contain href attr')
            return

        comics_url_list = []
        href_prefix = "http://www.xeall.com"

        for tag_a in com_a_list:
            url = href_prefix + tag_a['href']
            comics_url_list.append(url)


        # 处理当前页每部漫画
        # for url in comics_url_list:
            # yield scrapy.Request(url=url, callback=self.comic_parse)

        for i in range(1):
            yield scrapy.Request(url=comics_url_list[i], callback=self.comic_parse)

        # # 只爬取当前一页
        # return


        # 漫画列表下方的选页栏
        # page_tag = soup.find('ul', class_='pagelist')
        # if len(page_tag) < 1:
        #     self.log('extract page list error')
        #     return
        #
        # # 获取下一页的url
        # page_a_list = page_tag.find_all('a', attrs={'href': True})
        # if len(page_a_list) < 2:
        #     self.log('extract page tag a error.')
        #     return
        #
        # # 根据select控件来判断当前是否为最后一页
        # select_tag = soup.find('select', attrs={'name': 'sldd'})
        # option_list = select_tag.find_all('option')
        #
        # # 最后一个option标签，若有 selected 属性，则说明为最后一页
        # last_option = option_list[-1]
        # current_option = select_tag.find('option', attrs={'selected': True})
        #
        # is_last = (last_option.string == current_option.string)
        # if not is_last:
        #     # 最后一个为“末页”，倒数第二个为“下一页”
        #     next_page = 'http://www.xeall.com/shenshi/' + page_a_list[-2]['href']
        #     if next_page is not None:
        #         print('\n------ parse next page --------')
        #         print(next_page)
        #         yield scrapy.Request(next_page, callback=self.parse)
        #         pass
        # else:
        #     print('========= Last page ==========')

    def comic_parse(self, response):
        content = response.body
        if not content:
            self.log("parse comics body error.")
            return

        # 注意BeautifulSoup的解析器参数，不能指定为'html.parser'，因为有些网页可能为 lxml
        soup = BeautifulSoup(content, 'html5lib')

        page_list_tag = soup.find("ul", class_='pagelist')

        current_li = page_list_tag.find('li', class_='thisclass')
        page_num = current_li.a.string

        li_tag = soup.find("li", id="imgshow")
        img_tag = li_tag.find('img')

        img_url = img_tag['src']  # 漫画封面图
        # title = img_tag['alt']  # 漫画标题
        title = "whis"  # 漫画标题

        # 将图片保存到本地
        self.save_img(page_num, title, img_url)


        a_tag_list = page_list_tag.find_all('a')
        next_page = a_tag_list[-1]['href']
        if next_page == '#':
            self.log("parse comics: " + title + ' finished')
        else:
            next_page = 'http://www.xeall.com/shenshi/' + next_page
            yield scrapy.Request(url=next_page, callback=self.comic_parse)

    def save_img(self, page_num, title, img_url):
        # 将图片保存到本地
        self.log('save pic: ' + img_url)

        # 保存漫画的文件夹
        document = os.getcwd() + "/bak/"

        # 每部漫画的文件名以标题命名
        comics_path = document + title
        comics_path_exists = os.path.exists(comics_path)
        if not comics_path_exists:
            self.log("create document: " + title)
            os.makedirs(comics_path)

        # 每张图片以页数命名
        pic_name = comics_path + '/' + page_num + ".jpg"

        # 检查图片是否已经下载到本地，若存在则不再重新下载
        pic_name_exists = os.path.exists(pic_name)
        if pic_name_exists:
            self.log("pic exists: " + pic_name)
            return

        try:
            request = urllib.request.Request(img_url, headers=DEFAULT_HEADERS[1])
            response = urllib.request.urlopen(request, timeout=30)

            data = response.read()

            # 若返回数据为压缩数据需要先进行解压
            if response.info().get('Content-Encoding') == 'gzip':
                data = zlib.decompress(data, 16 + zlib.MAX_WBITS)

            # 图片保存到本地
            fp = open(pic_name, 'wb')
            fp.write(data)
            fp.close()

            self.log("save image finished: " + pic_name)

        except Exception as e:
            self.log('save image error.')
            self.log(e)
