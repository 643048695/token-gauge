"""Provider 抽象基类 + 标准化数据模型（INTERFACES.md §2）。

所有具体供应商（如 OpenCode Go）必须继承本类并实现 fetch / verify。
标准化结果结构见 INTERFACES.md §2，任何 provider 的 fetch() 返回值都必须满足：

{
  "provider": "opencode-go",     # 唯一标识
  "ok": true,                    # 本次抓取是否成功
  "fetched_at": 1785930000,      # 抓取时间戳 int(time.time())
  "cookie_valid": true,          # 凭据是否有效（ok:false 时也必须给出）
  "plan_name": "Go",             # 套餐名
  "limits": [...],               # 额度数组（失败可为 []）
  "balance": {"currency": "USD", "amount": 0.0},
  "meta": {...}                  # provider 特有增值信息（没有则为 {}）
}

ok:false 时仍返回完整结构，含 error 字符串；limits 可为空数组。
"""
from abc import ABC, abstractmethod


class Provider(ABC):
    # ---- 类属性：子类必须覆盖 ----
    id: str = ""            # 唯一标识，如 "opencode-go"
    name: str = ""          # 显示名
    schema: list = []       # 配置字段定义，如
                            # [{"key":"workspace_id","label":"工作区 ID","type":"text","secret":False}, ...]
    plan_name: str = ""     # 套餐名，如 "Go"

    def __init__(self, config: dict):
        """config 为该 provider 的配置 dict（来自 config.json 的 providers.<id>.config）。"""
        self.config = config or {}

    @abstractmethod
    def fetch(self) -> dict:
        """抓取一次用量数据，返回标准化结果 dict（见模块 docstring / INTERFACES.md §2）。"""

    @abstractmethod
    def verify(self) -> dict:
        """测试连接：{"ok": bool, "message": str, "detail": dict}。"""
