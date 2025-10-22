from fastapi import APIRouter, Body, HTTPException
from typing import Optional
import os
import yaml
try:
    from config.settings import settings
except Exception:
    # 回退：若无 settings 则使用默认
    class _Fallback:
        agent_api_key = ''
        agent_base_url = 'http://agent-runtime-aicustomerservice-test.xyftest.hisense.com/v1/'
        default_user_phone = '11111111111'
        default_hotline_phone = '43001'
    settings = _Fallback()

router = APIRouter(prefix="/api/v1/config", tags=["config"])


@router.get("/test", summary="查询当前测试配置")
def get_test_config():
    """返回当前测试配置: url、api_key、hotline、userphone"""
    return {
        "url": getattr(settings, 'agent_base_url', ''),
        "api_key": getattr(settings, 'agent_api_key', ''),
        "scoring_url": getattr(settings, 'scoring_base_url', '') or getattr(settings, 'agent_base_url', ''),
        "scoring_api_key": getattr(settings, 'scoring_api_key', '') or getattr(settings, 'agent_api_key', ''),
        "hotline": getattr(settings, 'default_hotline_phone', ''),
        "userphone": getattr(settings, 'default_user_phone', ''),
    }


@router.patch("/test", summary="修改当前测试配置")
def update_test_config(
    url: Optional[str] = Body(None, embed=True),
    api_key: Optional[str] = Body(None, embed=True),
    scoring_url: Optional[str] = Body(None, embed=True),
    scoring_api_key: Optional[str] = Body(None, embed=True),
    hotline: Optional[str] = Body(None, embed=True),
    userphone: Optional[str] = Body(None, embed=True),
):
    """更新测试配置并写入 YAML 文件。仅更新传入的字段。"""
    # 找到配置文件路径
    yaml_path = os.getenv("HI_CONFIG_PATH") or os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.yaml")
    # 读取现有数据
    data = {}
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                file_data = yaml.safe_load(f) or {}
            if isinstance(file_data, dict):
                data.update(file_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取配置文件失败: {e}")

    # 应用更新
    if url is not None:
        data['agent_base_url'] = url
    if api_key is not None:
        data['agent_api_key'] = api_key
    if scoring_url is not None:
        data['scoring_base_url'] = scoring_url
    if scoring_api_key is not None:
        data['scoring_api_key'] = scoring_api_key
    if hotline is not None:
        data['default_hotline_phone'] = hotline
    if userphone is not None:
        data['default_user_phone'] = userphone

    # 写入文件
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入配置文件失败: {e}")

    # 重新加载 settings（由于使用了 lru_cache，需要手动刷新）
    try:
        from config.settings import get_settings
        # 清除缓存并重载
        get_settings.cache_clear()  # type: ignore
        global settings
        settings = get_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载设置失败: {e}")

    return {
        "url": getattr(settings, 'agent_base_url', ''),
        "api_key": getattr(settings, 'agent_api_key', ''),
        "scoring_url": getattr(settings, 'scoring_base_url', '') or getattr(settings, 'agent_base_url', ''),
        "scoring_api_key": getattr(settings, 'scoring_api_key', '') or getattr(settings, 'agent_api_key', ''),
        "hotline": getattr(settings, 'default_hotline_phone', ''),
        "userphone": getattr(settings, 'default_user_phone', ''),
        "updated": True,
        "path": yaml_path,
    }