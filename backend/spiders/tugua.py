import asyncio
import datetime
import urllib.parse

import aiohttp
from lxml import etree

from backend.pipelines import save
from backend.pipelines.save import html_clean
from backend.spiders.base import BaseSpider
from utils.log import Logger


def get_spider(init_url: str, *args, **kwargs):
    return TuguaSpider(init_url, *args, **kwargs).run


class TuguaSpider(BaseSpider):
    """
    喷嚏图卦
    """

    def __init__(self, loop, init_url: str, headers: str = None, resource_id: int = None, default_category_id: int = None, default_tag_id: int = None):
        super().__init__(loop, init_url, headers, resource_id, default_category_id, default_tag_id)
        self.logger = Logger(__name__).get_logger()

    @asyncio.coroutine
    async def parse_article(self, article_link: str, session) -> dict:
        """
        解析文章内容
        :param article_link: 文章链接
        :param session: aiohttp Session
        :return:
        """
        article_html = await self.get_html(article_link, session)
        if article_html:
            selector = etree.HTML(article_html)

            tugua_title = selector.xpath('/html/body/table/tbody/tr/td[1]/div/table/tbody/tr[1]/td/div/span/span/a[2]/text()')[0]
            tugua_content = etree.tounicode(
                selector.xpath('/html/body/table/tbody/tr/td[1]/div/table/tbody/tr[2]/td/div[2]')[0],
                method='html'
            )
            publish_time = selector.xpath(
                '/html/body/table/tbody/tr/td[1]/div/table/tbody/tr[2]/td/table[1]/tbody/tr/td/div/span/text()'
            )[0]
            publish_time = datetime.datetime.strptime(publish_time.replace('xilei 发布于 ', ''), '%Y-%m-%d %H:%M:%S')
            clean_content = html_clean(tugua_content)

            return {
                'title': tugua_title,
                'url': article_link,
                'content': clean_content,
                'publish_time': publish_time,
                'resource_id': self.resource_id,
                'default_category_id': self.default_category_id,
                'default_tag_id': self.default_tag_id,
                'hash': self.gen_hash(clean_content.encode(errors='ignore'))
            }

    @asyncio.coroutine
    async def parse_link(self, init_url: str, session, max_count: int) -> list:
        """
        解析文章地址
        :param init_url: 入口地址
        :param session: aiohttp Session
        :param max_count: 解析数量
        :return:
        """
        init_html = await self.get_html(init_url, session)
        if init_html:
            selector = etree.HTML(init_html)
            post_nodes = selector.xpath('/html/body/table/tbody/tr/td[1]/div/div[1]/ul/li')
            relative_links = [node.xpath('./a/@href')[0] for node in post_nodes[:max_count]]
            detail_links = [urllib.parse.urljoin(base=init_url, url=link) for link in relative_links]
            return detail_links

    @asyncio.coroutine
    async def save(self, data: dict):
        """
        存储
        :return:
        """
        await save.produce(save.save_queue, data=data)

    @asyncio.coroutine
    async def run(self):
        async with aiohttp.ClientSession() as session:
            article_links = await self.parse_link(self.init_url, session, max_count=10)
            tasks = [self.parse_article(link, session) for link in article_links]
            for coro in asyncio.as_completed(tasks):
                data = await coro
                await self.save(data=data)

            # 爬取结束，更新resource中的last_refresh_time
            await self.update_resource()
