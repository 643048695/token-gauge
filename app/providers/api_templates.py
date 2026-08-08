# -*- coding: utf-8 -*-
"""API 导入预设模板定义（app/providers/api_templates.py）。

给 ApiProvider 用的"查询模板"清单。每个模板描述：

- kind:
    balance  余额型（预付费金额，主显示"剩余 XX"）
    relay    中转站型（剩余/已用/总量三项齐全，能画进度条）
    quota    订阅配额型（5h/周/月 多窗口，与 OpenCode Go 同构）
- url:       请求地址；含 {base} 时用用户填的 base_url，否则用 default_base
- default_base: url 含 {base} 时的默认 base（用户可覆盖，如国际版换域名）
- method:    请求方法（GET / POST）
- auth:      鉴权模式：bearer（Authorization: Bearer {key}，默认）/
             raw（Authorization: {key} 不加前缀，智谱专用）
- headers:   附加请求头；支持 {api_key} / {user_id} 占位
- mapping:   字段点路径（data.xxx[0].yyy），值可带 "*系数" 后缀（数值×系数）
- windows:   订阅型多窗口定义（与 mapping 二选一；见下）
- static:    静态字段（不从响应提取，如固定币种 CNY）
- unit:      单位类型：amount(金额) / tokens(token 额度) / pct(百分比)
- note:      备注（用途、待校准标记、实测要点）

mapping（余额型/中转站型）字段：
    remaining  剩余量（必填，提取不到即查询失败）
    used       已用量（可选）
    limit      总量（可选；remaining+used 都有而 limit 缺失时自动求和）
    currency   币种/单位（可选；static 优先于 mapping）
    plan_name  套餐名（可选）

windows（订阅型）每项：
    id / label          窗口标识与显示名
    pct                 直接给出已用百分比的路径（可带 "*系数"）
    used_of             用 limit/remaining 两条路径计算已用百分比
                        {"limit": 路径, "remaining": 路径} → (limit-remaining)/limit*100
    invert              布尔：接口给的是剩余百分比时置 true（used = 100 - value）
    scale100            布尔：接口给的是 0-1 小数时置 true（×100）
    reset               重置时间路径（ISO 字符串或毫秒/秒时间戳）

调研来源：2026-08-06 官方文档 + cc-switch（farion1231/cc-switch）内置模板源码
（src-tauri/src/services/balance.rs / coding_plan.rs）。
"""

TEMPLATES = {
    # ============================================================ 余额型

    "deepseek": {
        "site": "https://platform.deepseek.com",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "DeepSeek",
        "kind": "balance",
        "peak": True,   # 峰谷定价（高峰 ×2）
        "url": "https://api.deepseek.com/user/balance",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "mapping": {
            "remaining": "balance_infos[0].total_balance",
            "currency": "balance_infos[0].currency",
            "available": "is_available",
            "granted": "balance_infos[0].granted_balance",
            "topped_up": "balance_infos[0].topped_up_balance",
            "used": None,
            "limit": None,
            "plan_name": None,
        },
        "static": {
            "models": [
                {"name": "deepseek-v4-flash", "input": 1, "output": 2, "cache": 0.02, "currency": "CNY", "per": "百万token"},
                {"name": "deepseek-v4-pro", "input": 3, "output": 6, "cache": 0.025, "currency": "CNY", "per": "百万token"},
            ],
        },
        "unit": "amount",
        "note": "官方余额接口；balance_infos 数组取首项（币种顺序实测确认）；单价表 2026-08 官方价，官方提示近期调价",
    },

    "kimi": {
        "site": "https://platform.moonshot.cn",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "Kimi（月之暗面）余额",
        "kind": "balance",
        "url": "https://api.moonshot.cn/v1/users/me/balance",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "mapping": {
            "remaining": "data.available_balance",
            "currency": None,
            "used": None,
            "limit": None,
            "plan_name": None,
        },
        "static": {
            "currency": "CNY",
            "models": [
                {"name": "Kimi K3", "input": 20, "output": 100, "cache": 2, "currency": "CNY", "per": "百万token"},
            ],
        },
        "unit": "amount",
        "note": "官方余额接口；附代金券 data.voucher_balance / 现金 data.cash_balance；K3 单价 2026-08 官方价",
    },

    "siliconflow": {
        "site": "https://cloud.siliconflow.cn",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "硅基流动 SiliconFlow",
        "kind": "balance",
        "url": "https://api.siliconflow.cn/v1/user/info",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "mapping": {
            "remaining": "data.balance",
            "currency": None,
            "used": None,
            "limit": None,
            "plan_name": None,
        },
        "static": {
            "currency": "CNY",
            "models": [
                {"name": "DeepSeek-V4-Flash", "input": 1, "output": 2, "cache": 0.02, "currency": "CNY", "per": "百万token"},
                {"name": "DeepSeek-V4-Pro", "input": 12, "output": 24, "cache": 1, "currency": "CNY", "per": "百万token"},
                {"name": "Qwen3.5-35B-A3B", "input": 0.4, "output": 3.2, "currency": "CNY", "per": "百万token"},
            ],
        },
        "unit": "amount",
        "note": "官方余额接口；cc-switch 取 data.totalBalance（总额），本模板取可用余额 data.balance；国际版 base 换 api.siliconflow.com；单价 2026-08 官网",
    },

    "stepfun": {
        "site": "https://platform.stepfun.com",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "StepFun（阶跃星辰）",
        "kind": "balance",
        "url": "https://api.stepfun.com/v1/accounts",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "mapping": {
            "remaining": "balance",
            "currency": None,
            "used": None,
            "limit": None,
            "plan_name": None,
        },
        "static": {
            "currency": "CNY",
            "models": [
                {"name": "step-3.5-flash", "input": 0.7, "output": 2.1, "cache": 0.14, "currency": "CNY", "per": "百万token"},
                {"name": "step-3.7-flash", "input": 1.35, "output": 8.1, "cache": 0.27, "currency": "CNY", "per": "百万token"},
            ],
        },
        "unit": "amount",
        "note": "官方余额接口；国际版 base 换 api.stepfun.ai；附 total_cash_balance/total_voucher_balance；单价 2026-08 官网",
    },

    "novita": {
        "site": "https://novita.ai",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "Novita AI",
        "kind": "balance",
        "url": "https://api.novita.ai/v3/user/balance",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "mapping": {
            "remaining": "availableBalance*0.0001",
            "currency": None,
            "used": None,
            "limit": None,
            "plan_name": None,
        },
        "static": {
            "currency": "USD",
            "models": [
                {"name": "DeepSeek V4 Flash", "input": 0.14, "output": 0.28, "currency": "USD", "per": "百万token"},
                {"name": "Llama 3.3 70B", "input": 0.135, "output": 0.40, "currency": "USD", "per": "百万token"},
                {"name": "Qwen3.5-397B", "input": 0.60, "output": 3.60, "currency": "USD", "per": "百万token"},
            ],
        },
        "unit": "amount",
        "note": "官方余额接口；金额单位为 0.0001 USD，模板已 ÷10000；单价 2026-07 聚合参考价（模型价格波动大）",
    },

    # ============================================================ 中转站型

    "openrouter": {
        "site": "https://openrouter.ai",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "OpenRouter",
        "kind": "relay",
        "infinite": True,   # 套餐可能无额度上限（limit_remaining/limit 为 null），按 0 显示
        "url": "https://openrouter.ai/api/v1/key",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "mapping": {
            "remaining": "limit_remaining",
            "used": "usage",
            "limit": "limit",
            "currency": None,
            "plan_name": None,
        },
        "static": {"currency": "USD"},
        "unit": "amount",
        "note": "key 端点；limit_remaining/limit 可能为 null（无限额度），remaining 缺失时按 0 显示",
    },

    "oneapi-relay": {
        "site": "",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "one-api / new-api 中转站",
        "kind": "relay",
        "url": "{base}/api/user/self",
        "default_base": "",
        "method": "GET",
        "auth": "bearer",
        "headers": {
            "New-Api-User": "{user_id}",
        },
        "mapping": {
            "remaining": "data.quota*0.000002",
            "used": "data.used_quota*0.000002",
            "limit": None,
            "currency": None,
            "plan_name": "data.group",
        },
        "static": {"currency": "USD"},
        "unit": "amount",
        "note": "quota/500000 换算美元；必填 base_url；新版 new-api 需 user_id，老版 one-api 可留空",
    },

    # ============================================================ 订阅配额型

    "kimi-coding": {
        "site": "https://platform.moonshot.cn",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "Kimi For Coding 订阅",
        "kind": "quota",
        "url": "https://api.kimi.com/coding/v1/usages",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "windows": [
            {"id": "five_hour", "label": "5h",
             "used_of": {"limit": "limits[0].detail.limit",
                         "remaining": "limits[0].detail.remaining"},
             "reset": "limits[0].detail.resetTime"},
            {"id": "weekly", "label": "周",
             "used_of": {"limit": "usage.limit",
                         "remaining": "usage.remaining"},
             "reset": "usage.resetTime"},
        ],
        "static": {},
        "unit": "tokens",
        "note": "Kimi For Coding 订阅（5h + 周窗口），来源 cc-switch coding_plan.rs",
    },

    "zai-coding": {
        "site": "https://open.bigmodel.cn",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "z.ai / 智谱 GLM Coding Plan",
        "kind": "quota",
        "url": "{base}/api/monitor/usage/quota/limit",
        "default_base": "https://api.z.ai",
        "method": "GET",
        "auth": "raw",
        "headers": {
            "Accept-Language": "en-US,en",
        },
        "windows": [
            {"id": "five_hour", "label": "5h",
             "pct": "data.limits[0].percentage",
             "reset": "data.limits[0].nextResetTime"},
            {"id": "weekly", "label": "周",
             "pct": "data.limits[1].percentage",
             "reset": "data.limits[1].nextResetTime"},
        ],
        "static": {},
        "unit": "tokens",
        "note": "智谱与 z.ai 共用后端；limits[] 需 type=TOKENS_LIMIT，unit 3→5h / 6→周；"
               "老套餐可能只有 1 条；percentage 语义与索引实测校准；国内 base 换 open.bigmodel.cn",
    },

    "minimax-token": {
        "site": "https://platform.minimaxi.com",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "MiniMax Token Plan",
        "kind": "quota",
        "url": "{base}/v1/api/openplatform/coding_plan/remains",
        "default_base": "https://api.minimaxi.com",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "windows": [
            {"id": "five_hour", "label": "5h",
             "pct": "data.quota_5_hour.usage_percentage",
             "scale100": True,
             "invert": True,
             "reset": "data.quota_5_hour.resets_at"},
            {"id": "weekly", "label": "7 天",
             "pct": "data.quota_7_day.usage_percentage",
             "scale100": True,
             "invert": True,
             "reset": "data.quota_7_day.resets_at"},
        ],
        "static": {},
        "unit": "tokens",
        "note": "接口给剩余百分比 → invert 反转为已用；usage_percentage 量纲（0-1/0-100）实测校准；国际版 base 换 api.minimax.io",
    },

    # ============================================================ 待确认 / 暂不支持

    "groq": {
        "site": "https://console.groq.com",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "Groq",
        "kind": "quota",
        "url": "https://api.groq.com/openai/v1/usage",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "windows": [],
        "static": {},
        "unit": "tokens",
        "note": "usage 统计 + quota；响应结构待实测校准",
    },

    "volcengine": {
        "site": "https://console.volcengine.com",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "火山引擎（豆包）",
        "kind": "quota",
        "url": "",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "windows": [],
        "static": {},
        "unit": "tokens",
        "note": "Token Plan 走火山 OpenAPI HMAC 签名（GetAFPUsage/GetCodingPlanUsage，需 AK/SK），"
               "通用模板体系暂不支持，属自定义脚本场景",
    },

    "qiniu": {
        "site": "https://ai.qiniu.com",
        "guide": "api-key",  # 凭据获取引导（前端 ❓ 弹步骤）
        "name": "七牛云 AI",
        "kind": "balance",
        "url": "",
        "method": "GET",
        "auth": "bearer",
        "headers": {},
        "mapping": {
            "remaining": None,
            "used": None,
            "limit": None,
            "currency": None,
            "plan_name": None,
        },
        "static": {},
        "unit": "amount",
        "note": "官方合作，新用户送 3M tokens；余额端点待确认",
    },
}

# 模板 id 顺序（决定前端下拉列表 / get_provider_types 的展示顺序）
TEMPLATE_ORDER = [
    "deepseek", "kimi", "siliconflow", "stepfun", "novita",
    "openrouter", "oneapi-relay",
    "kimi-coding", "zai-coding", "minimax-token",
    "groq", "volcengine", "qiniu",
]

# 探测模式（只给 base_url + api_key）：候选路径按序尝试，命中即停
PROBE_PATHS = [
    "user/balance",          # DeepSeek 式（最大公约数）
    "users/me/balance",      # Moonshot 式
    "user/info",             # SiliconFlow 式
    "api/user/self",         # one-api / new-api 式
    "api/usage/balance",     # 部分中转站
    "v1/accounts",           # StepFun 式
    "key",                   # OpenRouter 式
    "usage",                 # Groq 式
]

# 命中判定用的余额类字段名白名单（响应 JSON 中出现任一即视为命中）
BALANCE_FIELD_KEYS = (
    "balance", "total_balance", "available_balance", "quota",
    "remain_quota", "remaining", "limit_remaining", "usage",
    "amount", "credits", "used_quota",
)


def list_templates() -> list:
    """返回模板清单（id / 名称 / 类型 / 是否就绪 / 需额外填写字段），供 UI / 测试使用。"""
    out = []
    for tid in TEMPLATE_ORDER:
        t = TEMPLATES.get(tid, {})
        mapping_ready = bool(t.get("mapping", {}).get("remaining"))
        windows_ready = bool(t.get("windows"))
        out.append({
            "id": tid,
            "name": t.get("name", tid),
            "kind": t.get("kind", "balance"),
            "unit": t.get("unit", "amount"),
            "needs": template_field_needs(tid),
            "ready": bool(t.get("url")) and (mapping_ready or windows_ready),
        })
    return out


def template_field_needs(template_id: str) -> list:
    """返回该模板需要用户额外填写的字段（如 ["base_url", "user_id"]）。

    规则：模板 url 含 {base} 且无 default_base → 需要 base_url；
    headers 用了 {user_id} 占位 → 需要 user_id（可选）。
    其余模板只需要 API Key。
    """
    t = TEMPLATES.get(template_id)
    if not t:
        return ["base_url"]
    needs = []
    url = t.get("url") or ""
    if "{base}" in url and not (t.get("default_base") or ""):
        needs.append("base_url")
    headers = t.get("headers") or {}
    if any("{user_id}" in v for v in headers.values()):
        needs.append("user_id")
    return needs
