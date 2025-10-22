import requests
import json
import re
from typing import Optional
from utils.log import get_logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.settings import settings

try:
    from config.settings import settings
except Exception:
    class _Fallback:
        agent_base_url = ''
        agent_api_key = ''
    settings = _Fallback()

logger = get_logger("scoring")


class AIEval:
    def __init__(self):
        # Prepare a session with retries to avoid transient network issues
        self.base_url = (getattr(settings, 'scoring_base_url', None) or '')
        self.api_key = (getattr(settings, 'scoring_api_key', None) or '')
        self.timeout = getattr(settings, 'external_request_timeout_seconds', 30)
        max_retries = getattr(settings, 'external_max_retries', 2)
        self.session = requests.Session()
        retries = Retry(total=max_retries, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def eval_ai(self, output: str, reference: Optional[str]):
        """调用远程评分服务，返回 thought 文本（blocking sync）。
        使用 session + 重试 + timeout，流式读取直到找到 agent_thought 事件或超时。
        返回字符串或 None。"""
        url = self.base_url or ''
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }
        logger.info(f"AIEval.eval_ai using url={url} api_key_set={'yes' if self.api_key else 'no'} timeout={self.timeout}")
        payload = {
            "inputs": {"output": output, "reference_output": reference or ""},
            "query": "给出得分",
            "response_mode": "streaming",
            "conversation_id": "",
            "user": "AI service",
        }
        if not url:
            logger.error("AIEval.eval_ai: no scoring url configured")
            return None
        try:
            logger.debug(f"AIEval.eval_ai posting to {url} output_len={len(output) if output else 0}")
            response = self.session.post(url, json=payload, headers=headers, stream=True, timeout=self.timeout)
            response.raise_for_status()
            final_result = None
            for line in response.iter_lines(decode_unicode=True, chunk_size=2048):
                if not line:
                    continue
                try:
                    json_str = line[6:].strip() if line.startswith('data: ') else line
                    data = json.loads(json_str)
                except Exception:
                    logger.debug(f"AIEval.eval_ai: failed to parse stream chunk: {line}")
                    continue
                logger.debug(f"AIEval.eval_ai stream event={data.get('event')}")
                if data.get('event') == 'agent_thought' and data.get('thought'):
                    final_result = data
                    logger.info("AIEval.eval_ai received agent_thought")
                    break
            if final_result:
                thought = final_result.get('thought')
                logger.info(f"AIEval.eval_ai returning thought_len={len(thought) if thought else 0}")
                return thought
            logger.info("AIEval.eval_ai finished without agent_thought")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"AIEval.eval_ai request exception: {e}")
            return None


def parse_score(thought: Optional[str]) -> int:
    """从思考文本中提取第一个 0-10 整数作为分数"""
    logger.debug(f"parse_score input_len={len(thought) if thought else 0}")
    if not thought:
        logger.info("parse_score: empty thought")
        return 0
    m = re.search(r"(\d{1,3})", thought)
    if not m:
        logger.info("parse_score: no numeric match")
        return 0
    val = int(m.group(1))
    score = max(0, min(100, val))
    logger.info(f"parse_score extracted score={score}")
    return score


def score_answer(answer: Optional[str], expected: Optional[str]) -> int:
    """基于远程评测服务获取分数，失败或无整数则返回0

    注意：新的评分请求仅发送模型输出（answer）与参考答案（expected），不再需要原始 user_input。
    """
    logger.info(f"score_answer called answer_len={len(answer) if answer else 0}")
    thought = AIEval().eval_ai(answer or '', expected)
    if thought is None:
        logger.info("score_answer: no thought returned, returning 0")
        return 0
    score = parse_score(thought)
    logger.info(f"score_answer result score={score}")
    return score
