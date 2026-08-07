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
