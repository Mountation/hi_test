import requests
import json
from typing import Optional, Dict, Any, Iterable
import asyncio
from functools import partial

try:
    from config.settings import settings  # 若存在外部配置
except Exception:
    class _Fallback:
        agent_api_key = ''
        agent_base_url = 'http://agent-runtime-aicustomerservice-test.xyftest.hisense.com/v1/'
        default_user_phone = '11111111111'
        default_hotline_phone = '43001'
    settings = _Fallback()

from utils.log import get_logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = get_logger("AIClient")


class AIClient:
    """AI 客户端：统一流式事件处理，消除业务函数间重复的 payload 构造"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_user_phone: Optional[str] = None,
        default_hotline_phone: Optional[str] = None,
    ):
        self.api_key = api_key or getattr(settings, 'agent_api_key', '')
        self.base_url = (base_url or getattr(
            settings, 'agent_base_url',
            'http://agent-runtime-aicustomerservice-test.xyftest.hisense.com/v1/'
        )).rstrip('/') + '/'
        self.default_user_phone = default_user_phone or getattr(settings, 'default_user_phone', '11111111111')
        self.default_hotline_phone = default_hotline_phone or getattr(settings, 'default_hotline_phone', '43001')
        # prepare requests session with retries
        self.timeout = getattr(settings, 'external_request_timeout_seconds', 30)
        max_retries = getattr(settings, 'external_max_retries', 2)
        self.session = requests.Session()
        retries = Retry(total=max_retries, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        logger.info(f"AIClient initialized base_url={self.base_url} api_key={'***' if self.api_key else ''} timeout={self.timeout}")

    # ==================== 公共基础能力 ====================
    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.api_key}",
        }

    def _post_stream(self, endpoint: str, payload: Dict[str, Any]) -> Iterable[str]:
        url = self.base_url + endpoint
        try:
            logger.debug(f"POST streaming to {url} payload keys={list(payload.keys())}")
            resp = self.session.post(
                url,
                json=payload,
                headers=self._headers(),
                stream=True,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True, chunk_size=2048):
                if not line:
                    continue
                yield line[6:].strip() if line.startswith('data: ') else line.strip()
        except requests.RequestException as e:
            logger.error(f"_post_stream request failed for {url}: {e}")
            # propagate a clearer exception while preserving type
            raise RuntimeError(f"API请求失败: {e}") from e

    def _parse_json_stream(self, raw_lines: Iterable[str]) -> Iterable[Dict[str, Any]]:
        for line in raw_lines:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue

    def _build_payload(self, query: str, user_phone: str, hotline_phone: str) -> Dict[str, Any]:
        return {
            "inputs": {"user_phone": user_phone, "hotline_phone": hotline_phone},
            "query": query,
            "response_mode": "streaming",
            "conversation_id": "",
            "user": user_phone,
        }

    def _chat_events(
        self,
        query: str,
        user_phone: Optional[str] = None,
        hotline_phone: Optional[str] = None
    ) -> Iterable[Dict[str, Any]]:
        up = user_phone or self.default_user_phone
        hp = hotline_phone or self.default_hotline_phone
        payload = self._build_payload(query, up, hp)
        logger.debug(f"_chat_events payload prepared for user={up} hotline={hp}")
        return self._parse_json_stream(self._post_stream("chat-messages", payload))

    # ==================== 业务方法 ====================
    def get_agent_info(self) -> Dict[str, Any]:
        url = self.base_url + "info"
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()['name']
            logger.info(f"get_agent_info returned data keys={list(data.keys()) if isinstance(data, dict) else 'unknown'}")
            return data
        except requests.RequestException as e:
            logger.error(f"get_agent_info failed: {e}")
            raise RuntimeError(f"API请求失败: {e}") from e

    def get_answer(self, query: str) -> Optional[str]:
        logger.info(f"get_answer called query={query}")
        for evt in self._chat_events(query):
            logger.debug(f"stream event: {evt.get('event')}")
            if evt.get('event') == 'workflow_finished':
                answer = evt.get('data', {}).get('outputs', {}).get('answer')
                logger.info(f"get_answer finished: answer_len={len(answer) if answer else 0}")
                return answer
        logger.info("get_answer: no workflow_finished event found")
        return None

    async def aget_answer(self, query: str) -> Optional[str]:
        """异步获取答案"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self.get_answer, query))

    def get_intent(self, query: str) -> Optional[str]:
        logger.info(f"get_intent called query={query}")
        for evt in self._chat_events(query):
            logger.debug(f"stream event: {evt.get('event')}")
            if evt.get('event') == 'node_finished':
                data = evt.get('data', {})
                if data.get('title') == '意图识别':
                    intent = data.get('outputs', {}).get('text')
                    logger.info(f"get_intent found: intent={intent}")
                    return intent
        logger.info("get_intent: no intent found")
        return None

    async def aget_intent(self, query: str) -> Optional[str]:
        """异步获取意图"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self.get_intent, query))

    def is_Kdb(self, query: str) -> int:
        logger.info(f"is_Kdb called query={query}")
        for evt in self._chat_events(query):
            logger.debug(f"stream event: {evt.get('event')}")
            if evt.get('event') == 'node_finished':
                title = evt.get('data', {}).get('title', '')
                logger.debug(f"node_finished title={title}")
                if '知识库' in title:
                    logger.info("is_Kdb: matched knowledge base node")
                    return 1
        logger.info("is_Kdb: no knowledge base match")
        return 0

    async def ais_Kdb(self, query: str) -> int:
        """异步判断是否命中知识库"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self.is_Kdb, query))

    def chat(
        self,
        query: str,
        user_phone: Optional[str] = None,
        hotline_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        for evt in self._chat_events(query, user_phone=user_phone, hotline_phone=hotline_phone):
            if evt.get('event') == 'workflow_finished':
                return evt
        return {}