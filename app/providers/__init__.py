"""供应商插件包。

导出：
- Provider 抽象基类
- OpenCodeGoProvider 具体实现
- PROVIDERS 注册表（id → 类），供 kernel 按 config.providers 的 key 实例化：
      cls = PROVIDERS.get(provider_id)
      provider = cls(config["config"])
"""
from .base import Provider
from .opencode_go import OpenCodeGoProvider
from .api_provider import ApiProvider, DetectProvider, TEMPLATE_PROVIDERS

# 模板即类型：供应商清单优先（DeepSeek / Kimi / … / 探测模式），
# 再是 opencode-go 与自定义入口（api，兼容旧配置）
PROVIDERS: dict = {
    **TEMPLATE_PROVIDERS,
    DetectProvider.id: DetectProvider,
    OpenCodeGoProvider.id: OpenCodeGoProvider,
    ApiProvider.id: ApiProvider,
}

__all__ = ["Provider", "OpenCodeGoProvider", "ApiProvider",
           "DetectProvider", "TEMPLATE_PROVIDERS", "PROVIDERS"]
