# -*- coding:utf-8 -*-

import requests
from lxml import etree
import urllib
import json
from bs4 import BeautifulSoup
import csv
import re
import os
import sys 
reload(sys)
sys.setdefaultencoding('utf-8')

class JingDong(object):
    """抓取京东商品列表页"""
    # 初始化
    def __init__(self, goods_name, goods_num_limit):
        self.goods_name = goods_name
        self.base_url = "https://search.jd.com/Search?keyword=" + goods_name + "&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&bs=1&suggest=2.def.0.V15&page="
        self.kw = {'keyword':goods_name}
        kw = urllib.urlencode(self.kw)
        self.proxies = {"http":"http://39.106.64.132:7777"}
        self.base_ajax_url = "https://search.jd.com/s_new.php?" + kw + "&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&suggest=1.def.0.V17&page="
        self.headers = {"Accept":"*/*",
                "Accept-Encoding":"gzip, deflate, br",
                "Accept-Language":"zh-CN,zh;q=0.9",
                "Connection":"keep-alive",
                "Host":"search.jd.com",
                "Referer":"https://search.jd.com/Search?keyword=macbook%20pro&enc=utf-8&suggest=5.his.0.0&wq=&pvid=e16e93bb13ec44e39ae7b31bf4a6efe2",
                "User-Agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
                "X-Requested-With":"XMLHttpRequest"}
        self.goods_num_limit = goods_num_limit
        self.item = []

    def send_request(self, url, page_num):
        """发送请求"""
        try:
            print '[INFO]正在发送第%d页请求...'%page_num
            html = requests.get(url=url, proxies=self.proxies, headers=self.headers)
        except:
            print '[ERROR]发送请求失败!'
        return html.content

    def send_ajax_request(self, item_str, this_page_num):
        """发送ajax请求"""
        url = self.base_ajax_url + str(int(this_page_num) + 1) + "&s=27&scrolling=y&show_items=" + item_str
        try:
            print '[INFO]正在发送第%s页ajax请求...'%this_page_num
            response = requests.get(url=url, proxies=self.proxies, headers=self.headers).content
        except:
            print '[ERROR]发送ajax请求失败!'
        self.parse_ajax_page(response, this_page_num)

    def parse_page(self, html):
        """解析列表页，提取商品信息"""
#        with open('jd.html', 'w') as f:
#            f.write(html)
        parse_html = etree.HTML(html)
        node_list = parse_html.xpath('//div[@id="J_goodsList"]/ul[@class="gl-warp clearfix"]/li')
        this_page_num = parse_html.xpath("//div[@id='J_filter']//b/text()")[0]
        id_choose = parse_html.xpath('//ul[@class="gl-warp clearfix"]/@data-tpl')[0]
        print '[INFO]正在提取第%s页信息...'%this_page_num
        item_list = []
        item_li = []
        for node in node_list:
            if node.xpath('./@data-type'):
                continue
            item={}
            item['name'] = ','.join(node.xpath('.//div[@class="p-name p-name-type-2"]//em//text()'))
            item['price'] = node.xpath('.//div[@class="p-price"]//i//text()')[0]
            shop = node.xpath('.//div[@class="p-shop"]//a/@title')
            if shop != []:
                item['shop'] = shop[0]
            else:
                item['shop'] = shop
            item['comment'] = node.xpath('.//div[@class="p-commit"]//a/text()')[0]
            item['link'] = node.xpath('.//div[@class="p-img"]//a/@href')[0]
            try:
                item['img_link'] = node.xpath('.//div[@class="p-img"]/a/img/@src')[0]
            except:
                item['img_link'] = node.xpath('.//div[@class="p-img"]/a/img/@data-lazy-img')[0]
            if int(id_choose) == 1:
                goods_id = node.xpath('./@data-sku')
            elif int(id_choose) == 2:
                goods_id = node.xpath('./@data-spu')
            else:
                goods_id = node.xpath('./@data-pid')
            item_list.append(goods_id)
            self.item.append(item)
        for item in item_list:
            if item != []:
                item_li.append(item[0])
        item_str = ','.join(item_li)
        self.send_ajax_request(item_str, this_page_num)

    def parse_ajax_page(self, response, this_page_num):
        """解析ajax请求"""
        print '[INFO]正在提取第%s页ajax页的商品信息...'%this_page_num
        soup = BeautifulSoup(response, 'lxml')
        node_list = soup.find_all(class_="gl-item")
        html = etree.HTML(response)
        node_list2 = html.xpath('//li[@class="gl-item"]')
        i = 0
        for node in node_list:
            if node.get('data-type'):
                continue
            item={}
            name = node.find(class_="p-name p-name-type-2").get_text().strip()
            name = re.sub('\t|\n', '', name)
            item['name'] = name
            item['price'] = node.find(class_="p-price").find('i').get_text().strip()
            try:
                item['shop'] = node.find(class_="p-shop").find('a').get('title')
            except:
                item['shop'] = ''
            item['comment'] = node.find(class_="p-commit").find('a').get_text().strip()
            item['link'] = node.find(class_="p-img").find('a').get('href')
            try:
                item['img_link'] = node.find(class_="p-img").find('a').find('img').get('src')
            except:
                pass
            else:
                
                try:
                    item['img_link'] = node.find(class_='p-img').find('a').find('img').get('data-lazy-img')
                except:
                    pass
                else:
                    try:
                        item['img_link'] = node_list2[i].xpath('.//div[@class="p-img"]/a/img/@src')[0]
                    except:
                        pass
                    else:
                        try:
                            item['img_link'] = node_list2[i].xpath('.//div[@class="p-img"]/a/img/@data-lazy-img')[0]
                        except:
                            pass
                        else:
                            item['img_link'] = ''
            self.item.append(item)
            i += 1

    def write_page(self):
        """以json和csv格式写入文件"""
        print '正在写入文件'
        if not os.path.exists('data'):
            os.mkdir('data')
        filename = 'data/' + self.goods_name + '.json'
        j_item = json.dump(self.item, open(filename, 'w'))
        csv_file = file('data/' + self.goods_name + '.csv', 'w')
        csv_writer = csv.writer(csv_file)
        csv_title = self.item[0].keys()
        csv_body = [item.values() for item in self.item]
        csv_writer.writerow(csv_title)
        csv_writer.writerows(csv_body)
        csv_file.close()
        print '写入完成,程序结束 Bye.....'

    def start_work(self):
        """调度函数"""
        # 构建url地址
        for num in range(1, self.goods_num_limit+1):
            url = self.base_url +str(2*num-1)
            html = self.send_request(url, num)
            self.parse_page(html)
        self.write_page()

if __name__ == '__main__':
    goods_name = raw_input('请问你想抓取什么物品？')
    while True:
        try:
            goods_num_limit = int(raw_input('请问你想抓几页？'))
        except:
            print '请输入正确的想抓取的页码'
            continue
        if goods_num_limit<1:
            print '请输入正确的想抓取的页码'
        else:
            break 
    jingdong = JingDong(goods_name, goods_num_limit)
    jingdong.start_work()

