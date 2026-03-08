# -*- coding: utf-8 -*-
"""
Server酱3 发送提醒服务

职责：
1. 通过 Server酱3 API 发送 Server酱3 消息
"""
import logging
import re
from datetime import datetime
from typing import Optional

import requests

from src.config import Config


logger = logging.getLogger(__name__)


class Serverchan3Sender:

    def __init__(self, config: Config):
        """
        初始化 Server酱3 配置

        Args:
            config: 配置对象
        """
        self._serverchan3_sendkey = getattr(config, 'serverchan3_sendkey', None)

    def send_to_serverchan3(self, content: str, title: Optional[str] = None) -> bool:
        """
        推送消息到 Server酱3

        Server酱3 API 格式：
        POST https://sctapi.ftqq.com/{sendkey}.send
        或
        POST https://{num}.push.ft07.com/send/{sendkey}.send
        {
            "title": "消息标题",
            "desp": "消息内容",
            "options": {}
        }

        Server酱3 特点：
        - 国内推送服务，支持多家国产系统推送通道，可无后台推送
        - 简单易用的 API 接口

        Args:
            content: 消息内容（Markdown 格式）
            title: 消息标题（可选）

        Returns:
            是否发送成功
        """
        if not self._serverchan3_sendkey:
            logger.warning("Server酱3 SendKey 未配置，跳过推送")
            return False

        if title is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
            title = f"📈 股票分析报告 - {date_str}"

        try:
            sendkeys = [k.strip() for k in str(self._serverchan3_sendkey).split(',') if k.strip()]
            if not sendkeys:
                logger.warning("Server酱3 SendKey 为空，跳过推送")
                return False

            params = {
                'title': title,
                'desp': content,
                'options': {}
            }
            headers = {
                'Content-Type': 'application/json;charset=utf-8'
            }

            any_success = False
            for sendkey in sendkeys:
                url = self._build_url(sendkey)
                if not url:
                    logger.error(f"Invalid sendkey format: {sendkey}")
                    continue

                response = requests.post(url, json=params, headers=headers, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Server酱3 消息发送成功, sendkey={sendkey}: {result}")
                    any_success = True
                else:
                    logger.error(f"Server酱3 请求失败, sendkey={sendkey}: HTTP {response.status_code}")
                    logger.error(f"响应内容: {response.text}")

            return any_success

        except Exception as e:
            logger.error(f"发送 Server酱3 消息失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False

    @staticmethod
    def _build_url(sendkey: str) -> Optional[str]:
        if sendkey.startswith('sctp'):
            match = re.match(r'sctp(\d+)t', sendkey)
            if not match:
                return None
            num = match.group(1)
            return f"https://{num}.push.ft07.com/send/{sendkey}.send"

        return f"https://sctapi.ftqq.com/{sendkey}.send"
