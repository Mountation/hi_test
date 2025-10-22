"""配置加载：支持 YAML 文件 + 环境变量覆盖。

优先级：默认值 < YAML(config.yaml) < 环境变量(HI_ 前缀)
"""

import os
import yaml
from functools import lru_cache
from typing import Optional
from pydantic import BaseModel


class Settings(BaseModel):
	agent_base_url: str = "http://agent-runtime-aicustomerservice-test.xyftest.hisense.com/v1/"
	agent_api_key: str = "app-l2u7WHOfPjpdqWx87LYOBFPE"
	# 可单独配置评分服务地址与 key（若不配置，回退至 agent_base_url/agent_api_key）
	scoring_base_url: Optional[str] = None
	scoring_api_key: Optional[str] = None
	# 网络/外部服务调用相关配置
	# 单次 requests 超时时间（秒） - 用于 requests 库的 timeout 参数
	external_request_timeout_seconds: int = 30
	# 外部调用（整个异步工作流）最大等待时间（秒），用于 asyncio.wait_for
	external_call_timeout_seconds: int = 60
	# requests 重试次数
	external_max_retries: int = 2
	default_user_phone: str = "11111111111"
	default_hotline_phone: str = "43001"

	@classmethod
	def load(cls):
		data = {}
		yaml_path = os.getenv("HI_CONFIG_PATH") or os.path.join(os.path.dirname(__file__), "config.yaml")
		if os.path.exists(yaml_path):
			try:
				with open(yaml_path, 'r', encoding='utf-8') as f:
					file_data = yaml.safe_load(f) or {}
				if isinstance(file_data, dict):
					data.update(file_data)
			except Exception as e:
				print(f"读取配置文件失败: {e}")
		# 环境变量覆盖
		mapping = {
			'HI_AGENT_BASE_URL': 'agent_base_url',
			'HI_AGENT_API_KEY': 'agent_api_key',
			'HI_SCORING_BASE_URL': 'scoring_base_url',
			'HI_SCORING_API_KEY': 'scoring_api_key',
			'HI_DEFAULT_USER_PHONE': 'default_user_phone',
			'HI_DEFAULT_HOTLINE_PHONE': 'default_hotline_phone',
		}
		for env_key, field in mapping.items():
			if env_key in os.environ:
				data[field] = os.environ[env_key]
		return cls(**data)


@lru_cache()
def get_settings() -> Settings:
	return Settings.load()


settings = get_settings()
