/* ================= i18n 双语词典（任务 A） =================
 * 方案：key 即中文原文（替换机械、zh 模式零成本）
 * lang: 'zh' | 'en'，持久化于 settings.ui.lang（settings 深合并自动保留未知键）
 * t(key)      —— 取当前语言文本；en 词典缺失时回退中文原文
 * setLang(l)  —— 切换语言（'en' 之外一律 'zh'）
 * apply(scope)—— 刷新 [data-i18n] 文本节点（保留子元素，如 svg）与 title/placeholder
 */
window.I18N = (function () {
  var EN = {
    /* ---- 单位/数字碎片 ---- */
    ' 万': ' 万',
    ' 亿': ' B',
    ' 百万': ' M',
    ' 分 ': ' min ',
    ' 分钟': ' min',
    ' 秒': ' s',
    ' 天': ' days',
    ' 日': ' d',
    ' 时': ' h',
    ' 分': ' m',
    '日': 'd',
    '天': 'd',
    '分': 'm',
    '时': 'h',
    '秒': 's',
    '分钟': 'min',
    '/天': '/day',
    '近1h': 'last 1h',
    '近3日日均': '3d avg',
    '近': 'last ',
    '5h 滚动': '5h rolling',
    '/百万估': '/M est',
    '按$': 'at $',
    '按': 'by ',
    '估': ' est',
    '估算': 'est.',
    '探': ' ',
    '·近': '·last ',
    '· 近': '· last ',
    '· 自 ': '· since ',
    '· 延迟': '· latency',
    '· 高峰×2': '· peak×2',
    '· 高峰贵一倍': '· peak double',
    ' 起算': ' base',
    ' 接入起': '',
    ' 点后恢复</div>': ' o\'clock recovery</div>',
    ' 后重置</div>': ' to reset</div>',
    ' 可用余额</span>': ' available</span>',
    ' 可用余额': ' available',
    '当前 ~': '~',
    ' 个供应商异常': ' provider(s) abnormal',
    ' 个供应商数据过期': ' provider(s) stale',
    '% 时提醒': '% alert',
    '21 天': '21 days',
    '28 天': '28 days',
    '5.3 天': '5.3 days',

    /* ---- 页面/导航 ---- */
    '仪表盘': 'Dashboard',
    '供应商': 'Providers',
    '外观': 'Appearance',
    '通知': 'Notifications',
    '关于': 'About',
    '实时用量总览': 'Live usage overview',
    '启用、凭据与连接测试': 'Enable, credentials & test',
    '主题、透明度与界面偏好': 'Theme, opacity & UI',
    '用量阈值与事件提醒': 'Thresholds & event alerts',
    '项目信息': 'About project',
    '重新查看开屏引导': 'Replay onboarding',
    '＋ 添加供应商': '+ Add provider',
    '添加供应商': 'Add provider',

    /* ---- 供应商管理 ---- */
    '类型': 'Type',
    '备注名': 'Note',
    '标识': 'ID',
    '选择供应商': 'Select provider',
    '保存并启用': 'Save & enable',
    '取消': 'Cancel',
    '保存凭据': 'Save',
    '删除': 'Delete',
    '刷新': 'Refresh',
    '全部刷新': 'Refresh all',
    '测试连接': 'Test',
    '添加失败: ': 'Add failed: ',
    '保存失败: ': 'Save failed: ',
    '刷新失败: ': 'Refresh failed: ',
    '已添加供应商：': 'Provider added: ',
    '已删除 ': 'Deleted ',
    '该标识的供应商已存在，可直接在下方列表编辑': 'Provider ID exists, edit it in the list below',
    '「标识」看起来是 API Key/Cookie——请填英文短名（如 deepseek-main），密钥填在下方 API Key 框': 'That ID looks like an API key/cookie — use a short English name (e.g. deepseek-main); put the secret in the API Key field below',
    '请选择供应商类型': 'Select a provider type',
    '工作区 ID': 'Workspace ID',
    '认证 Cookie': 'Auth Cookie',
    '查询模板': 'Query template',
    '暂无可添加的供应商类型': 'No provider types available',
    '确认删除？': 'Confirm delete?',

    /* ---- 仪表盘状态 ---- */
    '示例数据': 'Demo data',
    '示例数据 · 未连接后端': 'Demo data · backend offline',
    '示例数据模式，无法添加供应商': 'Demo mode: cannot add providers',
    '暂无供应商': 'No providers',
    '暂无数据': 'No data',
    '未抓取': 'Not fetched',
    '全部正常': 'All OK',
    '实时数据': 'Live data',
    '实时': 'Live',
    '失败': 'Failed',
    '关闭': 'Close',
    '收起': 'Collapse',
    '连接中…': 'Connecting…',
    '后端未连接，当前展示示例数据': 'Backend not connected, showing demo data',
    '已触发后端刷新': 'Backend refresh triggered',
    '隐藏失败: ': 'Hide failed: ',
    '视图刷新失败: ': 'View refresh failed: ',
    '渲染异常: ': 'Render error: ',
    'pywebview 接口不可用: ': 'pywebview API unavailable: ',

    /* ---- 卡片指标 ---- */
    '余额': 'Balance',
    '可用余额': 'Available',
    '今日': 'Today',
    '今日 ': 'Today ',
    '今日 +': 'Today +',
    '今日消耗': 'Today spent',
    '日均消耗': 'Daily avg',
    '日均消耗 ': 'Daily avg ',
    '日均 ': 'Daily avg ',
    '还能撑': 'Days left',
    '还能撑 ': 'Left ',
    '当前烧速': 'Burn rate',
    '当前速度': 'Current speed',
    '今日用量': 'Today usage',
    '剩余 token': 'Remaining tokens',
    '可用 token': 'Available tokens',
    '已用 token': 'Used tokens',
    '已用': 'Used',
    '充值 ': 'Top-up ',
    '赠金 ': 'Bonus ',
    '趋势': 'Trend',
    '3日趋势': '3d trend',
    '每月': 'Monthly',
    '每周': 'Weekly',
    '滚动': 'Rolling',
    '重置': 'Reset',
    '更新时间 --': 'Updated --',
    '更新 ': 'Updated ',
    '更新时间 ': 'Updated ',
    '更新': 'Updated',
    '月度用量 · ': 'Monthly · ',
    '积累中': 'Accumulating',
    '消耗数据积累中': 'Usage accumulating',
    '消耗速度积累中·需3天': 'Speed accumulating·needs 3d',
    '日均积累中·需3天': 'Daily avg accumulating·needs 3d',
    '即将重置': 'Resets soon',
    '抓取失败': 'Fetch failed',
    '抓取于 ': 'Fetched at ',
    '暂无用量数据': 'No usage data',
    '暂无额度数据': 'No quota data',
    '等待数据': 'Waiting for data',
    '请打开主面板配置': 'Open main panel to configure',
    '连接中断': 'Disconnected',
    '数据异常': 'Data error',
    '自 ': 'Since ',
    '每 ': 'Every ',
    '点击收起': 'Click to collapse',

    /* ---- Cookie / 凭据 ---- */
    'Cookie 失效': 'Cookie expired',
    'Cookie 失效，请更新认证信息': 'Cookie expired, update credentials',
    'Cookie 已失效，请到「供应商」页更新凭据</div>': 'Cookie expired, update it on the Providers page</div>',
    '如何获取？': 'How to get it?',
    '获取指引': 'How to get credentials',
    '凭据过期立即提醒': 'Notify on credential expiry',

    /* ---- 测试连接 ---- */
    '连接成功': 'Connected',
    '连接失败': 'Connection failed',
    '测试中': 'Testing',
    '测试中…': 'Testing…',
    '测试失败: ': 'Test failed: ',
    '测试通知已发送': 'Test notification sent',
    '发送测试通知': 'Send test notification',
    '发送失败: ': 'Send failed: ',

    /* ---- 通知 ---- */
    '用量预警': 'Usage warning',
    '用量紧急': 'Usage urgent',
    '达到阈值 ': 'Reach threshold ',
    '达到紧急线 ': 'Reach urgent line ',
    '连续抓取失败提醒': 'Notify on repeated fetch failure',
    '托盘气泡': 'Tray bubble',
    '系统通知': 'System notification',
    'winotify 弹窗': 'winotify popup',
    '静默记录': 'Silent logging',
    '零依赖，默认': 'Zero-dependency, default',

    /* ---- 主题 ---- */
    '纸面极简': 'Paper',
    '8位像素': '8-bit',
    '黑客帝国': 'Matrix',
    '粗野主义': 'Brutalist',
    '机密档案': 'Classified',
    '白纸清单 · 表格化': 'Paper list · tabular',
    '像素方块 · 复古机台': 'Pixel blocks · retro',
    '矩阵绿屏 · 数字雨': 'Matrix · digital rain',
    '纯黑白 · 硬边框宣言': 'Pure B&W · bold borders',
    '米色档案纸 · 红章涂黑': 'Beige file · red seal',
    '红白机': 'NES',
    '掌机绿': 'GameBoy Green',
    '世嘉红': 'Sega Red',
    '经典矩阵绿': 'Classic Matrix',
    '磷光青绿': 'Phosphor Teal',
    '毒绿': 'Venom Green',
    '主题刷新失败': 'Theme refresh failed',
    '配色已切换': 'Palette switched',
    '使用中': 'ACTIVE',

    /* ---- 外观页控件 ---- */
    '小': 'Small',
    '中': 'Medium',
    '大': 'Large',
    '紧凑': 'Compact',
    '舒适': 'Comfortable',
    '美元': 'USD',
    '百分比': 'Percent',
    '自动（第一个启用）': 'Auto (first enabled)',

    /* ---- 设置反馈 ---- */
    '设置已保存': 'Settings saved',
    '演示数据': 'DEMO',
    'secret 字段已加密显示': 'secret fields are encrypted',
    '最后更新 ': 'Updated ',

    /* ---- HTML 模板碎片 ---- */
    '<span class="muted">最后更新 ': '<span class="muted">Updated ',
    '<span class="tag">使用中</span>': '<span class="tag">ACTIVE</span>',
    '<span class="demo-tag">演示数据</span>': '<span class="demo-tag">DEMO</span>',
    '<span class="hint">secret 字段已加密显示</span>': '<span class="hint">secret fields are encrypted</span>',
    '<option value="">自动（第一个启用）</option>': '<option value="">Auto (first enabled)</option>',
    '<div class="spark-title">近5日每日消耗': '<div class="spark-title">Daily usage (5d)',
    '<div class="spark-title">近7日每日消耗（': '<div class="spark-title">Daily usage (7d) (',
    '<div class="peak-bar">高峰时段现在跑贵一倍 · ': '<div class="peak-bar">Peak hours cost double · ',
    '<div class="dempty">暂无额度数据</div>': '<div class="dempty">No quota data</div>',
    '" title="打开官网">官网</button>': '" title="Open site">Site</button>',
    '>中</button>': '>Medium</button>',
    '>保存凭据</button>': '>Save</button>',
    '>删除</button>': '>Delete</button>',
    '>刷新</button>': '>Refresh</button>',
    '>大</button>': '>Large</button>',
    '>小</button>': '>Small</button>',
    '>百分比</button>': '>Percent</button>',
    '>紧凑</button>': '>Compact</button>',
    '>美元</button>': '>USD</button>',
    '>舒适</button>': '>Comfortable</button>',
    '>发送测试通知</button>': '>Send test notification</button>',
    '>全部刷新</button>': '>Refresh all</button>',
    '>测试连接</button>': '>Test</button>',
    '>分钟</button>': '>min</button>',
    ' title="编辑备注名，回车或失焦保存">': ' title="Edit note, Enter or blur to save">',
    ' 后重置</div>': ' to reset</div>',

    /* ---- 迷你窗 ---- */
    '更新时间': 'Updated',
    '等待数据': 'Waiting for data',
    '点击收起': 'Click to collapse',

    /* ---- title 属性 ---- */
    '手动刷新全部供应商': 'Refresh all providers',
    '打开官网': 'Open site',
    '编辑备注名，回车或失焦保存': 'Edit note, Enter or blur to save',
    '自动刷新倒计时': 'Auto-refresh countdown',
    '隐藏到托盘': 'Hide to tray',
    '隐藏悬浮窗': 'Hide floating window',
    'Token 预估': 'Token estimate',
    '最小化': 'Minimize',
    '最大化': 'Maximize',
    '拖动排序': 'Drag to reorder',
    '当前消耗状态标签：引擎全开 / 正常巡航 / 待机 / 停烧': 'Status: full power / cruising / standby / stopped',
    '唯一标识，如 deepseek-main（API 导入多实例用）': 'Unique ID, e.g. deepseek-main (for multiple instances)',
    '如：主力订阅': 'e.g. primary plan',
    '上下拖动改高度': 'Drag vertically to resize height',
    '左右拖动改宽度': 'Drag horizontally to resize width',
    '拖动调整大小': 'Drag to resize',
    '立即刷新': 'Refresh now',

    /* ---- 托盘/其他 ---- */
    '双击托盘': 'Double-click tray',
    '打开或收起主面板；关闭按钮仅隐藏到托盘，不会退出程序': 'Open or collapse the panel; Close only hides to tray, never quits',
    '界面会亮红色告警条，及时到供应商页更新凭据': 'UI shows a red alert bar; update credentials on the Providers page',
    '进度条按阈值自动变色：越过预警线转黄，越过紧急线转红': 'Progress bars auto-color: yellow past warning, red past urgent',
    'OpenCode 用量额度监控面板。多供应商实时抓取、阈值预警、速度推算，一切数据都收在托盘里的这一块霓虹屏上。': 'OpenCode usage monitor. Multi-provider live fetching, threshold alerts, speed estimation — all packed into this neon panel in your tray.',

    /* ---- 补充：模板整段（HTML 结构保留，仅译文案） ---- */
    ' · 高峰×2': ' · peak×2',
    ' · 自 ': ' · since ',
    ' · 近': ' · last ',
    ' · 延迟': ' · latency',
    ' · 高峰贵一倍': ' · peak double',
    '全部刷新</button>': 'Refresh all</button>',
    '分钟</button>': 'min</button>',
    '发送测试通知</button>': 'Send test notification</button>',
    '测试连接</button>': 'Test</button>',
    '<div class="bal-avail bad">余额不足 · 请充值</div>': '<div class="bal-avail bad">Low balance · top up</div>',
    '<div class="bal-avail">余额充足 · 可正常调用</div>': '<div class="bal-avail">Balance OK · ready</div>',
    '<div class="card pcard failed"><div class="card-meta"><span class="chip danger">渲染异常: ': '<div class="card pcard failed"><div class="card-meta"><span class="chip danger">Render error: ',
    '<div class="card"><div style="font-size:11px;color:var(--muted);margin-bottom:8px">更新间隔</div>': '<div class="card"><div style="font-size:11px;color:var(--muted);margin-bottom:8px">Refresh interval</div>',
    '<div class="card"><div style="font-size:11px;color:var(--muted);margin-bottom:8px">界面密度</div>': '<div class="card"><div style="font-size:11px;color:var(--muted);margin-bottom:8px">Density</div>',
    '<div class="card"><div style="font-size:11px;color:var(--muted);margin-bottom:8px">货币显示</div>': '<div class="card"><div style="font-size:11px;color:var(--muted);margin-bottom:8px">Currency</div>',
    '<div class="card-meta"><span class="chip danger">抓取失败': '<div class="card-meta"><span class="chip danger">Fetch failed',
    '<div class="card-meta"><span class="chip neutral">已停用 · 可在供应商页启用</span></div>': '<div class="card-meta"><span class="chip neutral">Disabled · enable on Providers page</span></div>',
    '<div class="card-meta"><span class="chip neutral">暂无用量数据</span></div>': '<div class="card-meta"><span class="chip neutral">No usage data</span></div>',
    '<div class="diy-row" style="margin-top:10px"><span class="diy-lbl">迷你窗显示</span>': '<div class="diy-row" style="margin-top:10px"><span class="diy-lbl">Mini widget shows</span>',
    '<div class="diy-row"><span class="diy-lbl">Token 指标</span><label class="switch"><input type="checkbox" id="diyQuaTok" ': '<div class="diy-row"><span class="diy-lbl">Token metrics</span><label class="switch"><input type="checkbox" id="diyQuaTok" ',
    '<div class="diy-row"><span class="diy-lbl">Token 预估</span><label class="switch"><input type="checkbox" id="diyBalTok" ': '<div class="diy-row"><span class="diy-lbl">Token estimate</span><label class="switch"><input type="checkbox" id="diyBalTok" ',
    '<div class="diy-row"><span class="diy-lbl">余额大卡</span><label class="switch"><input type="checkbox" id="diyBalMain" ': '<div class="diy-row"><span class="diy-lbl">Balance card</span><label class="switch"><input type="checkbox" id="diyBalMain" ',
    '<div class="diy-row"><span class="diy-lbl">消耗指标（今日/日均/还能撑）</span><label class="switch"><input type="checkbox" id="diyBalGrid" ': '<div class="diy-row"><span class="diy-lbl">Spend metrics (today/avg/left)</span><label class="switch"><input type="checkbox" id="diyBalGrid" ',
    '<div class="diy-row"><span class="diy-lbl">趋势图（近5日）</span><label class="switch"><input type="checkbox" id="diyQuaChart" ': '<div class="diy-row"><span class="diy-lbl">Trend chart (5d)</span><label class="switch"><input type="checkbox" id="diyQuaChart" ',
    '<div class="diy-row"><span class="diy-lbl">趋势图（近7日）</span><label class="switch"><input type="checkbox" id="diyBalChart" ': '<div class="diy-row"><span class="diy-lbl">Trend chart (7d)</span><label class="switch"><input type="checkbox" id="diyBalChart" ',
    '<div class="diy-row"><span class="diy-lbl">进度条组</span><label class="switch"><input type="checkbox" id="diyQuaProg" ': '<div class="diy-row"><span class="diy-lbl">Progress bars</span><label class="switch"><input type="checkbox" id="diyQuaProg" ',
    '<div class="diy-sec">余额卡（DeepSeek/Kimi 等）</div>': '<div class="diy-sec">Balance card (DeepSeek/Kimi etc.)</div>',
    '<div class="diy-sec">订阅卡（OpenCode Go）</div>': '<div class="diy-sec">Subscription card (OpenCode Go)</div>',
    '<div class="empty-box"><b>暂无供应商</b><br>点击右上角「添加供应商」开始配置。</div>': '<div class="empty-box"><b>No providers</b><br>Click "Add provider" at the top-right to start.</div>',
    '<div class="empty-box"><b>暂无供应商</b><br>请在 config.json 中配置 providers，或在「供应商」页查看配置入口。</div>': '<div class="empty-box"><b>No providers</b><br>Configure providers in config.json or use the Providers page.</div>',
    '<div class="field"><label>User ID（one-api 中转站可选）</label>': '<div class="field"><label>User ID (optional for one-api relay)</label>',
    '<div class="num-row" style="flex:1"><label>紧急阈值</label>': '<div class="num-row" style="flex:1"><label>Urgent threshold</label>',
    '<div class="num-row" style="flex:1"><label>预警阈值</label>': '<div class="num-row" style="flex:1"><label>Warning threshold</label>',
    '<div class="set-group"><div class="set-title">主题</div>': '<div class="set-group"><div class="set-title">Theme</div>',
    '<div class="set-group"><div class="set-title">事件开关</div>': '<div class="set-group"><div class="set-title">Event toggles</div>',
    '<div class="set-group"><div class="set-title">仪表盘显示</div>': '<div class="set-group"><div class="set-title">Dashboard display</div>',
    '<div class="set-group"><div class="set-title">界面</div>': '<div class="set-group"><div class="set-title">UI</div>',
    '<div class="set-group"><div class="set-title">迷你窗</div>': '<div class="set-group"><div class="set-title">Mini widget</div>',
    '<div class="set-group"><div class="set-title">透明度</div>': '<div class="set-group"><div class="set-title">Opacity</div>',
    '<div class="set-group"><div class="set-title">通知方式</div><div class="method-grid">': '<div class="set-group"><div class="set-title">Notify via</div><div class="method-grid">',
    '<div class="set-group"><div class="set-title">阈值</div>': '<div class="set-group"><div class="set-title">Thresholds</div>',
    '<div class="slider-top"><span>大小（拖动精确控制）</span><span class="v" id="miniSizeV">': '<div class="slider-top"><span>Size (drag for precision)</span><span class="v" id="miniSizeV">',
    '<div class="slider-top"><span>迷你窗</span><span class="v" id="opMiniV">': '<div class="slider-top"><span>Mini widget</span><span class="v" id="opMiniV">',
    '<div class="te-head"><span>还能调用 · 预估</span><span class="te-note">按输出价': '<div class="te-head"><span>Token estimate</span><span class="te-note">at output price',
    '<div class="te-row"><span>今日消耗</span><b>≈ ': '<div class="te-row"><span>Today</span><b>≈ ',
    '<div class="te-row"><span>接入以来已用</span><b>≈ ': '<div class="te-row"><span>Used since</span><b>≈ ',
    '<div style="font-size:11px;color:var(--muted);margin-bottom:6px">换色</div>': '<div style="font-size:11px;color:var(--muted);margin-bottom:6px">Palette</div>',
    '<span class="desc" style="font-size:11px;color:var(--muted)">右下角霓虹 HUD</span>': '<span class="desc" style="font-size:11px;color:var(--muted)">Neon HUD bottom-right</span>',
    '<span class="status-item">供应商 <span class="val">': '<span class="status-item">Providers <span class="val">',
    '<span class="status-item">刷新间隔 <span class="val">': '<span class="status-item">Interval <span class="val">',
    '<span class="status-item">数据时间 <span class="val">': '<span class="status-item">Data time <span class="val">',
    '<span style="font-size:10px;color:var(--muted);margin-left:10px">会立即触发一条通知验证链路</span>': '<span style="font-size:10px;color:var(--muted);margin-left:10px">triggers a test notification</span>',
    '<span style="font-size:12px">启用迷你悬浮窗</span>': '<span style="font-size:12px">Enable mini widget</span>',
    '<span style="margin-left:auto;font-size:10px;color:var(--muted)">也可在迷你窗边缘拖动微调</span>': '<span style="margin-left:auto;font-size:10px;color:var(--muted)">or drag mini edges to fine-tune</span>',
      '暂无消耗数据': 'No usage data yet',
    '今日': 'Today',
    '今日消耗占比': "Today's Share",
    '近 7 日消耗': 'Last 7d Usage',
    '全部消耗 · 统计': 'Usage · All Providers',
    '（美元）': ' (USD)',
    '（人民币）': ' (CNY)',
    '（tokens）': ' (tokens)',
    '底部统计区（柱形/扇形）': 'Stats Section (bar/pie)',
      '自动（原币种）': 'Auto (native)',
      '自动': 'Auto',
      '自动模式：各供应商原币种之和': 'Auto: sum of native units',
    '人民币': 'CNY',
    '计量单位': 'Units',
    '金额与消耗显示口径（卡片 + 底部统计区）': 'Amount/usage display (cards + stats)',
    '汇率 1 USD = ? CNY': 'FX rate 1 USD = ? CNY',
    '超时': 'timeout',
    '加载中…': 'Loading…',
    '金额与消耗显示口径（卡片 + 底部统计区）': 'Display scale (cards + stats)',
    '接入起': 'since setup',
    '昨日': 'Yesterday',
    '⚡ 烧掉的电够': '⚡ Your power could',
    '点击切换档位（测试模式）': 'Click to cycle tiers (test mode)',
    '测试档位 · 点击返回真实': 'TEST · click to restore real',
    '📱 手机充电': '📱 Phone charges',
    '☕ 煮咖啡': '☕ Coffees brewed',
    '🍞 烤面包': '🍞 Toasts popped',
    '🚗 开车': '🚗 Driving',
    '🖥️ 服务器跑': '🖥️ Server running',
    '⚛️ 核能': '⚛️ Nuclear',
    '今日 ≈ 充 ': 'Today ≈ ',
    ' 次手机': ' phone charges',
    ' 杯咖啡': ' coffees',
    ' 次面包': ' toasts',
    ' 公里': ' km',
    ' 天': ' days',
    ' 秒': ' s',
    '今日 ≈ 煮 ': 'Today ≈ ',
    '今日 ≈ 烤 ': 'Today ≈ ',
    '今日 ≈ 开车 ': 'Today ≈ drove ',
    '今日 ≈ 服务器跑 ': 'Today ≈ server ',
    '今日 ≈ 核电站发电 ': 'Today ≈ power plant ',
    '给手机充电 ': 'charge a phone ',
    'LED 灯亮 ': 'light an LED ',
    '空调吹 ': 'run an AC ',
    ' 次': ' times',
    ' 小时': ' hours',
      '跳过引导': 'Skip guide',
    'STEP 1 · 数据源': 'STEP 1 · Data Source',
    '数据从哪来': 'Where does the data come from',
    '每个供应商的余额都存在它的 API 里，OC-GO 负责抓回来、画成屏。': "Each provider's balance lives in its own API; OC-GO fetches and renders it.",
    '供应商 API': 'Provider API',
    '余额 · 用量': 'Balance · Usage',
    '都在云端账户里': 'Stored in your cloud account',
    'OC-GO 本地抓取': 'OC-GO fetches locally',
    '定时同步': 'Scheduled sync',
    '凭据加密 · 只在本机': 'Encrypted · local only',
    '1 / 2 / 5 / 10 分钟可调': '1 / 2 / 5 / 10 min intervals',
    '仪表盘 · 迷你窗': 'Dashboard · Mini widget',
    '余额卡 · 进度条 · 统计区': 'Balance card · progress · stats',
    '超额前先提醒你': 'Get warned before overuse',
    '80% / 95% 两级阈值': '80% / 95% thresholds',
    'STEP 2 · 配置': 'STEP 2 · Setup',
    '三步接好供应商': 'Connect a provider in 3 steps',
    '在「供应商」页，从 13 种预设里挑一个。': 'Pick from 13 presets on the Providers page.',
    '添加供应商': 'Add provider',
    '选类型，余额型 / 中转站 / 订阅自动适配显示。': 'Pick a type; balance / relay / subscription auto-adapt.',
    '填 API Key': 'Enter API Key',
    '凭据加密存本机，只有你能看到。': 'Encrypted locally; only you can see it.',
    '保存即启用': 'Save to enable',
    '供应商卡片亮起，开始抓数据。': 'The card lights up and starts fetching.',
    '没有 Key？打开「演示模式」也能先看界面，再补凭据。': 'No key? Enable demo mode to preview the UI, add credentials later.',
    '＋ 添加供应商': '+ Add provider',
    '类型': 'Type',
    '演示模式': 'Demo mode',
    '保存并启用': 'Save & enable',
    'STEP 3 · 测试连接': 'STEP 3 · Test connection',
    '验证 Key 有效': 'Verify your key',
    '保存后点「测试连接」，延迟数字蹦出来就是通了。': 'After saving, hit "Test connection"; a latency number means it works.',
    '供应商 · DeepSeek': 'Provider · DeepSeek',
    '测试连接': 'Test connection',
    '点击上方按钮，模拟一次真实测试': 'Click the button above to simulate a real test',
    '失败会提示具体原因：Key 无效 / 网络不通 / 额度接口异常。': 'Failures show the reason: invalid key / network / quota API error.',
    'STEP 4 · 仪表盘': 'STEP 4 · Dashboard',
    '一眼看懂全貌': 'See everything at a glance',
    '仪表盘四件套，从上到下各司其职。': 'Four widgets, each doing its job.',
    '余额卡': 'Balance card',
    '/ 还剩 · 还能撑 12 天': '/ Remaining · ~12 days left',
    '余额型供应商的主数字，充值 / 赠金拆开看。': 'The main number; topped-up / granted split out.',
    '进度条': 'Progress bars',
    '订阅配额走到哪了，重置倒计时一起算好。': 'Subscription quota usage with reset countdown.',
    '统计区': 'Stats section',
    '近 7 日消耗柱形 + 今日占比环形。': "7-day bars + today's donut share.",
    '迷你窗': 'Mini widget',
    '桌面常驻小窗，不看仪表盘也知道用了多少。': 'Always on desktop; check usage without opening the dashboard.',
    'STEP 5 · 进阶': 'STEP 5 · Advanced',
    '对话助手也能配': 'Configure with an AI assistant',
    '不想手动填？让对话助手（agent）代劳。': "Don't want to type? Let an agent do it.",
    '对话助手': 'AI assistant',
    '在 agent 里直接说（Codex / WorkBuddy 等常用 agent）：': 'Just tell any agent (Codex, WorkBuddy, etc.):',
    '给 OC-GO 添加一个 DeepSeek 供应商': 'Add a DeepSeek provider to OC-GO',
    '它会调': 'It will run',
    '帮你配好，软件自动重载。': 'Configure it for you; the app auto-reloads.',
    '也可以在项目目录手动跑命令，': 'Or run commands manually in the project folder:',
    '表示从 stdin 读，不留在命令行里。': 'reads from stdin, keeping the key out of the command line.',
    "✓ 已添加供应商 'deepseek-main'": "✓ Provider 'deepseek-main' added",
    '&nbsp;&nbsp;运行中的软件将自动重载': '&nbsp;&nbsp;running app will auto-reload',
    '不再显示': "Don't show again",
    '跳过指引': 'Skip guide',
    '上一步': 'Back',
    '下一步 →': 'Next →',
    '开始使用 →': 'Get started →',
    'STEP 6 · 出发': 'STEP 6 · Get started',
    '完成第一次配置': 'Complete your first setup',
    '配好一个供应商，看数据活起来——这是最后一步。': 'Set up one provider and watch the data come alive — this is the last step.',
    '检查配置中…': 'Checking config…',
    '还没有配置供应商——点右下角「去配置供应商」开始。': 'No providers configured yet — click "Configure a provider →" below to start.',
    '已配置': 'Configured',
    '未配置': 'Not configured',
    '🎉 全部就绪，可以开始用了': '🎉 All set — you are ready to go',
    '已配置 ': 'Configured ',
    '还需配置 ': 'need ',
    '去配置供应商 →': 'Configure a provider →',
    '自动抓取': 'Auto refresh',
    '配好后软件按间隔自动刷新，无需手动操作': 'Data refreshes automatically on schedule — no manual work',
    '迷你窗常驻': 'Mini widget stays on top',
    '悬浮窗随时显示核心额度，一眼看清': 'Core usage visible at a glance in the floating widget',
    '超限有提醒': 'Limit alerts',
    '接近额度上限、凭据失效都会通知你': 'Get notified near limits or when credentials expire',
    '凭据会过期（软件会提示 EXPIRED / 失效），届时点卡片上的 ❓ 看获取步骤即可。': 'Credentials expire (the app will show EXPIRED) — click the ❓ on any card to see how to get a new one.',
    '成就': 'Achievements',
    '你的用量与坚持记录': 'Your usage & persistence record',
    '已解锁成就': 'Achievements unlocked',
    '全部': 'All',
    '燃烧': 'Burn',
    '燃烧引擎': 'Burn Engine',
    '太阳核心': 'Solar Core',
    '星际熔炉': 'Stellar Forge',
    '火力引擎': 'Power Engine',
    '燃烧新星': 'Ignition Nova',
    '待机': 'Idle',
    '本月燃烧 token': 'Tokens burned this month',
    '约消耗 度电': '≈ kWh of power',
    '约等于 本书': '≈ books of text',
    '连续燃烧': 'Day streak',
    '今日已烧': 'Burned today',
    '均速': 'Avg speed',
    '≈ 度电': '≈ kWh',
    '≈ 书本': '≈ books',
    '引擎全开': 'Full throttle',
    '正常巡航': 'Cruising',
    '待机': 'Idle',
    '停烧': 'Stopped',

    '行业基准：普通开发者月烧 ': 'Benchmark: avg dev burns ',
    '已达成中位数 ': 'You have reached ',
    ' · 再烧 ': ' of the median · burn ',
    ' token 即可追平普通开发者': ' more tokens to match the avg dev',
    ' · 已超过普通开发者！': ' · above the average dev!',

    '坚持': 'Stick',
    '配置': 'Setup',
    '探索': 'Explore',
    '解锁于 ': 'Unlocked on ',
    '成就已解锁': 'Achievement unlocked',
    '今日燃烧 ': 'Burned today ',
    ' token': ' tokens',
    ' 度电': ' kWh',
    ' 本书': ' book(s)',
    '均速 ': 'avg ',
    ' token/s': ' tok/s',
    '静默待命': 'Idle',
    '正在最大马力燃烧': 'Burning at full power',
    '引擎全开': 'Engine full open',
    '高速巡航': 'Cruising',
    '怠速运转': 'Idling',
    '⚡ 快速配置一个 API': '⚡ Quick-setup an API',
    '保存配置 ✓': 'Save ✓',
    '请先填写 API Key': 'Please enter the API Key first',
    '测试中…': 'Testing…',
    '后端未连接（示例模式），无法测试': 'Backend not connected (demo mode) — cannot test',
    '测试失败': 'Test failed',
    '连接失败': 'Connection failed',
    '✓ 已保存「': '✓ Saved "',
    '」，数据开始抓取': '" — data fetching starts',
    '保存失败：后端未连接（示例模式）': 'Save failed: backend not connected (demo mode)',
    '还没有配置供应商，在下方快速配置一个': 'No provider configured — set one up below',
    '选择类型 → 填 Key → 测试连接 → 保存，一分钟搞定。': 'Pick a type → paste the key → Test → Save. Done in a minute.',
    '配置一个供应商 →': 'Configure a provider →',
    '开始你的第一次配置 →': 'Start your first setup →',
    '暂不配置，直接进入 →': 'Skip for now, enter the app →',
    '⚡ 开始你的第一次配置': '⚡ Start your first setup',
    '🎉 已成功配置 ': '🎉 Configured ',
    ' 个供应商，可以开始用了': ' provider(s) — you are ready!',
  };

  var lang = 'zh';

  function t(key) {
    if (lang !== 'zh' && Object.prototype.hasOwnProperty.call(EN, key)) {
      return EN[key];
    }
    return key;
  }

  function setLang(l) {
    lang = (l === 'en') ? 'en' : 'zh';
    try { document.documentElement.lang = lang; } catch (e) {}
  }

  function getLang() { return lang; }

  function apply(scope) {
    scope = scope || document;
    scope.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
      var node = null, cur;
      while ((cur = walker.nextNode())) {
        if (cur.nodeValue && cur.nodeValue.trim()) { node = cur; break; }
      }
      if (node) { node.nodeValue = t(key); }
      else { el.textContent = t(key); }
    });
    scope.querySelectorAll('[data-i18n-title]').forEach(function (el) {
      el.title = t(el.getAttribute('data-i18n-title'));
    });
    scope.querySelectorAll('[data-i18n-ph]').forEach(function (el) {
      el.placeholder = t(el.getAttribute('data-i18n-ph'));
    });
  }

  return { t: t, setLang: setLang, getLang: getLang, apply: apply };
})();

/* ===== 凭据获取引导（GUIDES）：后端只传 guide id，文案全部前端维护，双语完整 ===== */
window.GUIDES = {
  'opencode-cookie': {
    zh: {
      title: '获取 OpenCode Go 登录凭据',
      steps: [
        { t: '用浏览器打开 opencode.ai，登录你的账号（Cookie 只能从登录后的页面拿）' },
        { t: '按键盘 F12 打开开发者工具（或页面空白处右键 → 检查）', svg: 'f12cookie' },
        { t: '顶部切到「Application（应用）」标签 → 左侧 Storage → Cookies → 点开 opencode.ai' },
        { t: '找到名为 auth 的 Cookie，双击 Value 列，全选复制整串值（形如 Fe26.2* 开头）' },
        { t: '回到本软件 → 供应商页 → 粘贴到「认证 Cookie」输入框 → 保存 → 点「测试连接」' }
      ],
      tips: [
        'Cookie 会过期（通常几周），软件提示 EXPIRED 时按同样步骤重新复制一次即可',
        '工作区 ID：登录后地址栏是 opencode.ai/workspace/<wrk_xxx>/go，复制中间 wrk_ 开头的那段',
        'Cookie 是本软件唯一需要的凭据，加密保存在本机，不会上传任何第三方'
      ]
    },
    en: {
      title: 'Get OpenCode Go credentials',
      steps: [
        { t: 'Open opencode.ai in a browser and sign in (the cookie only exists after login)' },
        { t: 'Press F12 to open DevTools (or right-click the page → Inspect)', svg: 'f12cookie' },
        { t: 'Switch to the Application tab → Storage → Cookies → expand opencode.ai' },
        { t: 'Find the cookie named auth, double-click the Value column and copy the whole string (starts with Fe26.2*)' },
        { t: 'Back in this app: Providers page → paste it into the Auth Cookie field → Save → Test' }
      ],
      tips: [
        'The cookie expires (usually after a few weeks); when the app shows EXPIRED, repeat the same steps',
        'Workspace ID: the address bar shows opencode.ai/workspace/<wrk_xxx>/go after login — copy the wrk_ part',
        'The cookie is the only credential this app needs; it is encrypted locally and never sent anywhere'
      ]
    }
  },
  'api-key': {
    zh: {
      title: '获取 API Key',
      steps: [
        { t: '打开该供应商官网并登录（卡片上的「官网」按钮会直接带你过去）' },
        { t: '进入「API Keys / 密钥管理」页面（一般在左侧菜单或个人中心）' },
        { t: '点击「创建 / 新建 API Key」，复制生成的长串（通常 sk- 开头）' },
        { t: '回到本软件 → 粘贴到 API Key 输入框 → 保存 → 点「测试连接」' }
      ],
      tips: [
        '密钥通常只在创建时完整显示一次，丢了就重新建一个，旧的最好同时删除',
        '本软件把密钥加密保存在本机，不会上传任何第三方'
      ]
    },
    en: {
      title: 'Get an API Key',
      steps: [
        { t: 'Open the provider website and sign in (the "Site" button on the card takes you there)' },
        { t: 'Go to the "API Keys" page (usually in the left menu or account section)' },
        { t: 'Click "Create / New API Key" and copy the generated string (usually starts with sk-)' },
        { t: 'Back in this app: paste it into the API Key field → Save → Test' }
      ],
      tips: [
        'Keys are usually shown in full only once at creation; if lost, create a new one and delete the old',
        'This app encrypts keys locally and never sends them anywhere'
      ]
    }
  }
};

/* F12 开发者工具取 Cookie 示意图（绿色霓虹线框风，跟随主题 accent 变量） */
window.GUIDE_SVGS = {
  f12cookie:
    '<svg viewBox="0 0 480 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DevTools guide">' +
    '<rect x="8" y="8" width="464" height="284" rx="10" fill="none" stroke="var(--border)" stroke-width="2"/>' +
    '<rect x="20" y="20" width="440" height="24" rx="6" fill="var(--panel)" stroke="var(--line)" stroke-width="1"/>' +
    '<circle cx="34" cy="32" r="4" fill="var(--danger)"/><circle cx="48" cy="32" r="4" fill="var(--warn)"/><circle cx="62" cy="32" r="4" fill="var(--accent)"/>' +
    '<rect x="80" y="26" width="260" height="12" rx="6" fill="var(--card-hi)" stroke="var(--line)" stroke-width="1"/>' +
    '<text x="92" y="35" font-size="9" fill="var(--muted)" font-family="Consolas,monospace">https://opencode.ai/workspace/...</text>' +
    '<rect x="20" y="54" width="440" height="120" rx="4" fill="var(--card)" stroke="var(--line)" stroke-width="1"/>' +
    '<rect x="32" y="66" width="180" height="10" rx="5" fill="var(--line)" opacity="0.5"/>' +
    '<rect x="32" y="84" width="120" height="10" rx="5" fill="var(--line)" opacity="0.3"/>' +
    '<rect x="32" y="102" width="300" height="10" rx="5" fill="var(--line)" opacity="0.3"/>' +
    '<rect x="32" y="120" width="260" height="10" rx="5" fill="var(--line)" opacity="0.3"/>' +
    '<text x="32" y="152" font-size="10" fill="var(--muted)" font-family="Consolas,monospace">press F12 → DevTools opens at the bottom</text>' +
    '<rect x="20" y="184" width="440" height="96" rx="4" fill="var(--panel)" stroke="var(--accent)" stroke-width="1.5"/>' +
    '<rect x="24" y="188" width="120" height="20" rx="4" fill="var(--card-hi)"/>' +
    '<text x="32" y="202" font-size="10" fill="var(--accent)" font-family="Consolas,monospace">Application</text>' +
    '<rect x="150" y="188" width="80" height="20" rx="4" fill="transparent"/>' +
    '<text x="158" y="202" font-size="10" fill="var(--muted)" font-family="Consolas,monospace">Elements</text>' +
    '<rect x="236" y="188" width="90" height="20" rx="4" fill="transparent"/>' +
    '<text x="244" y="202" font-size="10" fill="var(--muted)" font-family="Consolas,monospace">Console</text>' +
    '<line x1="24" y1="214" x2="456" y2="214" stroke="var(--line)" stroke-width="1"/>' +
    '<rect x="24" y="220" width="130" height="56" rx="4" fill="var(--card)" stroke="var(--line)" stroke-width="1"/>' +
    '<text x="32" y="236" font-size="9" fill="var(--muted)" font-family="Consolas,monospace">▶ Cookies</text>' +
    '<text x="36" y="252" font-size="9" fill="var(--accent)" font-family="Consolas,monospace">▼ opencode.ai</text>' +
    '<rect x="162" y="220" width="294" height="56" rx="4" fill="var(--card)" stroke="var(--line)" stroke-width="1"/>' +
    '<text x="170" y="236" font-size="9" fill="var(--muted)" font-family="Consolas,monospace">Name</text>' +
    '<text x="300" y="236" font-size="9" fill="var(--muted)" font-family="Consolas,monospace">Value</text>' +
    '<rect x="170" y="242" width="278" height="20" rx="3" fill="rgba(0,255,156,0.12)" stroke="var(--accent)" stroke-width="1.5"/>' +
    '<text x="178" y="256" font-size="10" fill="var(--accent)" font-family="Consolas,monospace" font-weight="bold">auth</text>' +
    '<text x="300" y="256" font-size="9" fill="var(--warn)" font-family="Consolas,monospace">Fe26.2*…………（整串复制）</text>' +
    '<text x="178" y="272" font-size="8" fill="var(--muted)" font-family="Consolas,monospace">← 双击 Value 全选复制这一行</text>' +
    '</svg>'
};
