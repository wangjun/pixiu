import asyncio
import datetime

from lxml.html.clean import Cleaner

from utils.http_req import send_req
from utils.log import Logger

save_queue = asyncio.Queue(maxsize=1024)
logger = Logger(__name__).get_logger()


def html_clean(html_content):
    """
    清理HTML中的无用样式、脚本等
    :return:
    """
    cleaner = Cleaner(
        style=True,
        scripts=True,
        comments=True,
        javascript=True,
        page_structure=False,
        safe_attrs_only=True
    )
    return cleaner.clean_html(html=html_content)


async def produce(queue, data):
    """
    生产数据
    :param queue:
    :param data:
    :return:
    """
    await queue.put(data)
    logger.debug(f'写入存储队列 {data}')


async def consume(loop, queue):
    """
    消费队列数据
    :return:
    """
    from backend import executor

    while True:
        data = await queue.get()
        logger.debug(f'读取存储队列 {data}')

        post_data = {
            'title': data.get('title'),
            'url': data.get('url'),
            'content': data.get('content'),
            'pub_time': datetime.datetime.strftime(data.get('publish_time'), '%Y-%m-%dT%H:%M:%S'),
            'source': data.get('resource_id'),
            'category': data.get('default_category_id'),
            'tag': data.get('default_tag_id'),
            'hash': data.get('hash')
        }

        req = await loop.run_in_executor(
            executor,
            send_req,
            'post',
            '/api/article/',
            post_data
        )
        if req.status_code == 201:
            logger.info('存储成功')
        else:
            logger.warning(f'存储失败，状态码 {req.status_code} 响应详情 {req.text}')
