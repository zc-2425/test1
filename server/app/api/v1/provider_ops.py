"""提供商运维接口：真实连通性测试。

和「模型厂商详情页」的「测试连接」按钮对应。
真的发一次 HTTP 请求到厂商的 /models，用延迟和状态码说话，
并把结果写回提供商行的 status —— 列表页的状态徽章因此会跟着变。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app import models
from app.db import get_session
from app.services.llm import resolve_config
from app.services.llm.openai_compatible import probe
from app.services.llm.registry import env_var_for, resolve_provider_slug

router = APIRouter(prefix="/providers", tags=["模型厂商"])


@router.post("/{provider_id}/test")
async def test_provider(
    provider_id: str, session: Session = Depends(get_session)
) -> dict:
    provider = session.get(models.ModelProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"提供商不存在: {provider_id}")

    slug = resolve_provider_slug(provider.slug)
    if slug is None:
        return {
            "ok": False,
            "latencyMs": 0,
            "message": f"「{provider.name}」暂不支持真实连通性测试",
            "supported": False,
        }

    config = resolve_config(provider.slug)
    if config is None or not config.ready:
        env_var = env_var_for(provider.slug)
        return {
            "ok": False,
            "latencyMs": 0,
            "message": f"未配置 API Key，把 Key 写入 server/.env 的 {env_var or '对应变量'} 后再试",
            "needsKey": True,
            "envVar": env_var,
            "supported": True,
        }

    ok, latency_ms, message = await probe(config)

    # 状态回写：列表页与详情页的徽章都读同一个字段
    provider.status = "已连接" if ok else "错误"
    if ok:
        provider.enabled = True
    session.add(provider)
    session.commit()

    return {
        "ok": ok,
        "latencyMs": latency_ms,
        "message": message or ("连接成功" if ok else "连接失败"),
        "supported": True,
        "model": config.model,
    }
