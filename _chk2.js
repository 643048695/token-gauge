
(function(){
'use strict';

/* ================= 基础工具 ================= */
var $  = function(s, el){ return (el||document).querySelector(s); };
var $$ = function(s, el){ return Array.prototype.slice.call((el||document).querySelectorAll(s)); };
function esc(s){
  return String(s==null?'':s).replace(/[&<>"']/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}
function deepCopy(o){ return JSON.parse(JSON.stringify(o)); }
function fmtClock(t){
  if(!t) return '--:--:--';
  var d = new Date(t*1000);
  var p = function(n){ return (n<10?'0':'')+n; };
  return p(d.getHours())+':'+p(d.getMinutes())+':'+p(d.getSeconds());
}
function fmtInterval(sec){
  if(sec==null) return '--';
  if(sec < 60) return sec+I18N.t(' 秒');
  if(sec % 60 === 0) return (sec/60)+I18N.t(' 分钟');
  return (Math.floor(sec/60))+I18N.t(' 分 ')+(sec%60)+I18N.t(' 秒');
}
function fmtReset(sec){
  if(sec==null) return '';
  if(sec <= 0) return I18N.t('即将重置');
  if(sec < 60) return sec+'s';
  if(sec < 3600) return Math.floor(sec/60)+'m '+(sec%60)+'s';
  if(sec < 86400) return Math.floor(sec/3600)+'h '+Math.floor((sec%3600)/60)+'m';
  return Math.floor(sec/86400)+'d '+Math.floor((sec%86400)/3600)+'h';
}
function toast(msg, type){
  var box = $('#toasts');
  var t = document.createElement('div');
  t.className = 'toast '+(type||'ok');
  t.textContent = msg;
  box.appendChild(t);
  setTimeout(function(){
    t.classList.add('out');
    setTimeout(function(){ if(t.parentNode) t.parentNode.removeChild(t); }, 280);
  }, 2800);
}

/* SVG 图标集 */
var ICONS = {
  warn: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M12 9v4"/><path d="M12 17v.5"/><path d="M10.3 3.8 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0z"/></svg>',
  zap: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M13 2 4 14h6l-1 8 9-12h-6z"/></svg>',
  bell: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M6 9a6 6 0 1 1 12 0c0 5 2 6 2 6H4s2-1 2-6z"/><path d="M10 20a2.2 2.2 0 0 0 4 0"/></svg>',
  tray: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><rect x="3" y="3" width="18" height="14" rx="2"/><path d="M3 18h18M9 21h6"/></svg>',
  info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M12 11v5" stroke-linecap="round"/><path d="M12 8v.5" stroke-linecap="round"/></svg>',
  gridOff: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/><path d="M6 6l12 12"/></svg>'
};

/* ================= 预置主题预览（仅用于外观页色块，实际主题以 get_theme_css 为准） ================= */
var THEMES = {
  'paper':    { name:I18N.t('纸面极简'), accent:'#537d96', accent2:'#6f9cb5', bg:'#f5efe4' },
  '8bit':     { name:I18N.t('8位像素'),  accent:'#ffd54f', accent2:'#4fc3f7', bg:'#1a237e' },
  'matrix':   { name:I18N.t('黑客帝国'), accent:'#00ff41', accent2:'#00e5a0', bg:'#000000' },
  'brutal':   { name:I18N.t('粗野主义'), accent:'#111111', accent2:'#ffeb3b', bg:'#f5f0e6' },
  'redacted': { name:I18N.t('机密档案'), accent:'#8b2c1f', accent2:'#5a4632', bg:'#e8dcc8' }
};
var STYLE_DESC = {
  'paper':I18N.t('白纸清单 · 表格化'), '8bit':I18N.t('像素方块 · 复古机台'),
  'matrix':I18N.t('矩阵绿屏 · 数字雨'), 'brutal':I18N.t('纯黑白 · 硬边框宣言'),
  'redacted':I18N.t('米色档案纸 · 红章涂黑')
};
var STYLE_PALETTES = {
  '8bit': [
    { id:'nes', name:I18N.t('红白机'), colors:['#1a237e','#ffd54f','#e53935'] },
    { id:'gameboy', name:I18N.t('掌机绿'), colors:['#0f380f','#9bbc0f','#e0e6c3'] },
    { id:'sega', name:I18N.t('世嘉红'), colors:['#1a1a1a','#e60012','#ffdd00'] }
  ],
  'matrix': [
    { id:'matrix', name:I18N.t('经典矩阵绿'), colors:['#000000','#00ff41','#00e5a0'] },
    { id:'phosphor', name:I18N.t('磷光青绿'), colors:['#020d08','#1fff9e','#00b37e'] },
    { id:'venom', name:I18N.t('毒绿'), colors:['#0a1200','#8aff2e','#ccff00'] }
  ]
};

/* schema 兜底（get_view 未携带 schema 时使用） */
var FALLBACK_SCHEMA = [
  { key:'workspace_id', label:I18N.t('工作区 ID'), type:'text',   secret:false },
  { key:'auth_cookie',  label:I18N.t('认证 Cookie'), type:'text', secret:true }
];

/* 供应商品牌徽章：provider id → logo 文件（ui/icons/ 下，真实品牌图标） */
var BRAND_ICONS = {
  'opencode-go':   'opencode.svg',
  'deepseek':      'deepseek.svg',
  'kimi':          'kimi.svg',
  'siliconflow':   'siliconflow.svg',
  'stepfun':       'stepfun.svg',
  'novita':        'novita.svg',
  'openrouter':    'openrouter.svg',
  'oneapi-relay':  'newapi.svg',
  'kimi-coding':   'kimi.svg',
  'zai-coding':    'zhipu.svg',
  'minimax-token': 'minimax.svg',
  'groq':          'groq.svg',
  'qiniu':         'qiniu.png',
  'volcengine':    'doubao.svg',
};
/* 无真实 logo 的品牌用字母徽章兜底 */
var BRAND_BADGES = {
  'detect': { c:'#6B7280', t:I18N.t('探') },
};
function brandBadgeHtml(pid){
  var f = BRAND_ICONS[pid];
  if(f){
    return '<span class="brand-badge" title="'+esc(pid)+'"><img src="icons/'+f+'" alt=""></span>';
  }
  var b = BRAND_BADGES[pid] || { c:'#6B7280', t:'?' };
  return '<span class="brand-badge" style="background:'+b.c+'" title="'+esc(pid)+'">'+b.t+'</span>';
}

/* ================= Mock 数据（示例，标注展示用） ================= */
var NOW = Math.floor(Date.now()/1000);
var MOCK = {
  ok: true,
  fetched_at: NOW,
  refresh_interval_sec: 300,
  providers: {
    'opencode-go': {
      provider:'opencode-go', ok:true, fetched_at:NOW, cookie_valid:true,
      plan_name:'Go',
      limits:[
        { id:'rolling', label:I18N.t('5h 滚动'), used_pct:34, reset_in_sec:2100 },
        { id:'weekly',  label:I18N.t('每周'),    used_pct:58, reset_in_sec:385200 },
        { id:'monthly', label:I18N.t('每月'),    used_pct:72, reset_in_sec:1450000 }
      ],
      balance:{ currency:'USD', amount:16.8 },
      meta:{
        today:{ delta_pct:4.2, delta_usd:2.5, base_label:'19:38', since_midnight:false },
        speed:{ hourly_pct:0.52, days_left:5.3, days_left_text:I18N.t('5.3 天'), source:'today' },
        monthly_limit_usd:60, used_usd:43.2
      }
    },
    'opencode-zen': {
      provider:'opencode-zen', ok:true, fetched_at:NOW-7200, cookie_valid:true, stale:true,
      plan_name:'Zen',
      limits:[ { id:'monthly', label:I18N.t('每月'), used_pct:22, reset_in_sec:152000 } ],
      balance:{ currency:'USD', amount:12.0 },
      meta:{
        speed:{ hourly_pct:0.1, days_left:21.0, days_left_text:I18N.t('21 天'), source:'monthly' },
        monthly_limit_usd:50, used_usd:11.0
      }
    },
    'anthropic': {
      provider:'anthropic', ok:false, fetched_at:NOW-9000, cookie_valid:false,
      plan_name:'Claude Pro', error:I18N.t('Cookie 失效，请更新认证信息'),
      limits:[], balance:{ currency:'USD', amount:0 },
      meta:{}
    },
    'opencode-lite': {
      provider:'opencode-lite', ok:true, fetched_at:NOW-1800, cookie_valid:true,
      plan_name:'Lite',
      limits:[ { id:'monthly', label:I18N.t('每月'), used_pct:8, reset_in_sec:864000 } ],
      balance:{ currency:'USD', amount:8.4 },
      meta:{ speed:{ hourly_pct:0.02, days_left:28.0, days_left_text:I18N.t('28 天'), source:'monthly' }, monthly_limit_usd:20, used_usd:1.6 }
    }
  },
  settings: {
    providers: {
      'opencode-go':   { enabled:true,  name:'OpenCode Go',   config:{ workspace_id:'wrk_demo_01', auth_cookie:'Fe26.2**demo' } },
      'opencode-zen':  { enabled:true,  name:'OpenCode Zen',  config:{ workspace_id:'wrk_demo_02', auth_cookie:'Fe26.2**demo' } },
      'anthropic':     { enabled:true,  name:'Anthropic',     config:{ workspace_id:'wrk_demo_03', auth_cookie:'' } },
      'opencode-lite': { enabled:false, name:'OpenCode Lite', config:{ workspace_id:'wrk_demo_04', auth_cookie:'' } }
    },
    refresh_interval_sec: 300,
    theme:{ id:'paper', variant:null },
    opacity:{ main:0.95, mini:0.92 },
    window:{ main_width:920, main_height:600, mini_width:300, mini_height:170, mini_corner:'bottom-right' },
    mini_widget_enabled:true,
    density:'compact',
    currency:'usd',
    notify:{
      method:'tray', threshold:80, urgent:95,
      events:{ threshold:true, urgent:true, cookie_fail:true, fetch_fail:true }
    },
    start_with_windows:false
  },
  theme_css: null
};

/* ================= 全局状态 ================= */
var state = {
  page: 'dashboard',
  mode: 'mock',            // mock | real
  settings: deepCopy(MOCK.settings),
  view: deepCopy(MOCK),
  themeCss: '',
  countdown: 30,
  autoRefreshSec: 30,
  refreshing: false,
  testResults: {}          // pid -> {ok, message}
};

function currentApi(){
  return (window.pywebview && window.pywebview.api) || null;
}
function call(name){
  var args = Array.prototype.slice.call(arguments, 1);
  var a = currentApi();
  return new Promise(function(resolve, reject){
    if(!a || typeof a[name] !== 'function'){
      reject(new Error(I18N.t('pywebview 接口不可用: ')+name));
      return;
    }
    Promise.resolve(a[name].apply(a, args)).then(resolve, reject);
  });
}
function isMock(){ return state.mode === 'mock'; }

/* ================= 主题与透明度 ================= */
function injectTheme(css){
  if(!css) return;
  $$('style[data-theme]').forEach(function(s){ s.parentNode && s.parentNode.removeChild(s); });
  /* 兼容裸 CSS 变量字符串与带 style 标签两种形态 */
  var html = /^\s*<style/i.test(css) ? css : '<style data-theme="t">'+css+'
/* ---- 底部统计区（全局消耗汇总） ---- */
.stats-section{margin-top:14px;display:flex;flex-direction:column;gap:10px;}
.stats-head{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;display:flex;align-items:center;gap:8px;}
.stats-head::before{content:'';width:4px;height:12px;background:var(--accent);border-radius:2px;box-shadow:0 0 8px var(--glow);}
.stats-grid{display:grid;grid-template-columns:1.35fr 1fr;gap:12px;}
@media(max-width:960px){.stats-grid{grid-template-columns:1fr;}}
.stats-card{background:var(--bg-card);border:1px solid var(--li);border-radius:12px;padding:14px 16px;min-width:0;}
.stats-card h4{margin:0 0 10px;font-size:11px;color:var(--muted);font-weight:600;display:flex;align-items:center;gap:6px;}
.stats-card h4 .u{color:var(--accent);font-weight:400;}
.stats-bar{width:100%;display:block;}
.lg-row{display:flex;align-items:center;gap:8px;font-size:11px;padding:5px 0;border-bottom:1px dashed var(--li);}
.lg-row:last-child{border-bottom:none;}
.lg-row i{width:10px;height:10px;border-radius:3px;flex:none;}
.lg-row span{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text);}
.lg-row b{font-family:Consolas,monospace;font-size:11px;color:var(--accent);font-weight:600;}
.lg-row em{font-style:normal;color:var(--muted);font-size:10px;width:38px;text-align:right;}
.stats-empty{font-size:11px;color:var(--muted);padding:8px 0;}
/* ---- 拖拽排序 ---- */
#dashGrid .pcard[draggable=true]{cursor:grab;}
#dashGrid .pcard[draggable=true]:active{cursor:grabbing;}
#dashGrid .pcard.drag-src{opacity:.35;outline:2px dashed var(--accent);outline-offset:2px;}
#dashGrid .pcard.drag-over{outline:2px solid var(--accent);outline-offset:2px;box-shadow:0 0 14px var(--glow);}
</style>';
  /* 追加到 <head> 末尾：覆盖兜底变量的同名项，未覆盖的保留兜底值 */
  document.head.insertAdjacentHTML('beforeend', html);
  state.themeCss = css;
  applyBgOpacity();
}
function applyStyleAttr(){
  var id = (state.settings && state.settings.theme && state.settings.theme.id) || 'paper';
  document.body.setAttribute('data-style', id);
}
function parseRgba(str){
  var m = String(str||'').match(/rgba?\(([^)]+)\)/);
  if(!m) return null;
  var parts = m[1].split(',').map(function(x){ return parseFloat(x.trim()); });
  if(parts.length < 3 || isNaN(parts[0])) return null;
  return { r:parts[0], g:parts[1], b:parts[2], a:parts.length>3?parts[3]:1 };
}
function applyBgOpacity(alpha){
  var op = (alpha!=null) ? alpha : (state.settings.opacity ? state.settings.opacity.main : 0.95);
  op = Math.max(0.2, Math.min(1, op));
  var bg = parseRgba(getComputedStyle(document.documentElement).getPropertyValue('--bg'));
  if(bg){
    document.documentElement.style.setProperty('--bg',
      'rgba('+Math.round(bg.r)+','+Math.round(bg.g)+','+Math.round(bg.b)+','+op+')');
  }
}

/* ================= 数据状态判定 ================= */
function statusOf(pv, cfg){
  if(!pv) return { key:'off', label:I18N.t('未抓取') };
  if(cfg && cfg.enabled === false) return { key:'off', label:'OFF' };
  if(pv.ok && !pv.stale) return { key:'live', label:'LIVE' };
  if(pv.ok && pv.stale) return { key:'stale', label:'STALE' };
  return { key:'failed', label:'FAILED' };
}
function pctClass(pct){
  var n = state.settings.notify || {};
  var th = n.urgent!=null ? n.urgent : 95;
  var no = n.threshold!=null ? n.threshold : 80;
  if(pct >= th) return 'danger';
  if(pct >= no) return 'warn';
  return 'ok';
}
function pctFillStyle(pct){
  var c = pctClass(pct);
  if(c === 'danger') return 'background:linear-gradient(90deg,#ff4d6d,#ff8f5e);box-shadow:0 0 8px rgba(255,77,109,0.55)';
  if(c === 'warn')   return 'background:linear-gradient(90deg,#ffc400,#ff8f00);box-shadow:0 0 8px rgba(255,196,0,0.5)';
  return 'background:linear-gradient(90deg,var(--accent),var(--accent2));box-shadow:0 0 8px var(--glow)';
}
function fmtBalance(p){
  var cur = state.settings.currency;
  if(cur === 'pct'){
    var m = p.meta || {};
    if(m.monthly_limit_usd && m.used_usd != null) return Math.round((m.used_usd/m.monthly_limit_usd)*100)+'%';
    var mx = maxLimit(p.limits);
    if(mx) return mx.used_pct+'%';
    return '--';
  }
  var b = p.balance;
  if(b && b.amount != null){
    return money(b.amount, b.currency);
  }
  return '--';
}
/* 金额格式化：CNY→¥ / USD→$ */
function money(v, cur){
  var n = Number(v);
  if(n == null || isNaN(n)) return '--';
  if(cur === 'CNY') return '¥'+n.toFixed(2);
  if(cur === 'USD') return '$'+n.toFixed(2);
  return (cur?cur+' ':'')+n.toFixed(2);


/* 计量单位换算：auto（原币种）/ usd / cny / tokens
   meta 可带 models（输出单价，元/百万 token 口径）供 token 换算 */
function moneyUnit(amt, cur, meta){
  if(amt == null || isNaN(Number(amt))) return money(amt, cur);
  var d = state.settings.display || {};
  var u = d.unit || 'auto';
  var fx = Number(d.fx_rate) || 7.2;
  var isCny = (cur === 'CNY' || cur === 'CN¥' || cur === '¥');
  var isUsd = (cur === 'USD' || cur === 'US$' || cur === '$');
  if(u === 'tokens'){
    var models = meta && meta.models ? meta.models : [];
    var outP = models.length ? Number(models[0].output) : 0;
    if(outP > 0){
      var cny = isUsd ? amt * fx : amt;
      return fmtTokens(cny / outP * 1000000);
    }
    return money(amt, cur);
  }
  if(u === 'usd'){
    var v = isCny ? amt / fx : amt;
    return '≈$' + v.toFixed(2);
  }
  if(u === 'cny'){
    var v2 = isUsd ? amt * fx : amt;
    return '≈¥' + v2.toFixed(2);
  }
  return money(amt, cur);
}}
function maxLimit(limits){
  if(!limits || !limits.length) return null;
  var mx = null;
  limits.forEach(function(l){ if(!mx || l.used_pct > mx.used_pct) mx = l; });
  return mx;
}
function speedText(p){
  var m = p.meta || {};
  var sp = m.speed || {};
  if(sp.days_left_text) return sp.days_left_text;
  if(sp.days_left != null) return Number(sp.days_left).toFixed(1)+I18N.t(' 天');
  return null;
}
function speedChips(p){
  var m = p.meta || {};
  var sp = m.speed || {};
  var out = [];
  // 余额型（按量）：消耗速度 + 还能撑
  if(m.kind === 'balance' || m.kind === 'relay'){
    if(sp.data_ready){
      out.push({ text:I18N.t('还能撑 ')+sp.days_left_text, main:true });
      out.push({ text:I18N.t('日均消耗 ')+(p.balance&&p.balance.currency?money(sp.daily_amount,p.balance.currency):sp.daily_text)+(sp.sample_days?I18N.t('·近')+sp.sample_days+I18N.t('日'):''), main:false });
    } else {
      out.push({ text:I18N.t('消耗速度积累中·需3天'), main:true });
    }
    return out;
  }
  // 主：科学日均（近 N 天），来源内联
  if(sp.avg_days_left_text && sp.avg_days_left_text !== '—'){
    out.push({ text:I18N.t('还能撑 ')+sp.avg_days_left_text+(sp.avg_source?'·'+sp.avg_source:''), main:true });
  } else if(sp.data_ready === false){
    out.push({ text:I18N.t('日均积累中·需3天'), main:true });
  }
  // 副：当前烧速，来源内联
  if(sp.days_left_text && sp.days_left_text !== '—'){
    var srcName = sp.source === 'today' ? I18N.t('今日') : sp.source === 'short' ? I18N.t('近1h') : sp.source === 'trend' ? I18N.t('趋势') : (sp.source || '');
    out.push({ text:I18N.t('当前 ~')+sp.days_left_text+(srcName?'·'+srcName:''), main:false });
  }
  return out;
}
function todayText(p){
  var m = p.meta || {};
  var t = m.today || {};
  if(t.delta_pct == null) return null;
  var s = I18N.t('今日 +')+Number(t.delta_pct).toFixed(1)+'%';
  if(t.today_tokens != null) s += ' · ≈'+fmtTokens(t.today_tokens)+' token';
  else if(state.settings.currency === 'usd' && t.delta_usd != null){
    s += ' (+$'+Number(t.delta_usd).toFixed(2)+')';
  }
  return s;
}

/* ================= js_api 调用封装 ================= */
var viewFetching = false;
async function fetchView(){
  if(viewFetching) return;
  viewFetching = true;
  try {
    var v = await call('get_view');
    state.view = v;
    if(v.settings) state.settings = v.settings;
    if(v.theme_css) injectTheme(v.theme_css);
    applyStyleAttr();
    state.mode = 'real';
    renderAll();
    updateHeader();
  } finally {
    viewFetching = false;
  }
}
async function refreshView(){
  try { await fetchView(); }
  catch(e){ toast(I18N.t('视图刷新失败: ')+e.message, 'err'); }
}
async function manualRefresh(){
  if(state.refreshing) return;
  state.refreshing = true;
  var btn = $('#btnRefresh');
  btn.classList.add('spinning');
  try {
    await call('refresh_now');
    toast(I18N.t('已触发后端刷新'), 'ok');
  } catch(e){
    toast(I18N.t('刷新失败: ')+e.message, 'err');
  }
  setTimeout(function(){
    state.refreshing = false;
    btn.classList.remove('spinning');
    refreshView();
  }, 1500);
}
async function save(patch, opts){
  opts = opts || {};
  try {
    var r = await call('save_settings', patch);
    if(r && r.settings) state.settings = r.settings;
    if(opts.theme || patch.theme){
      try {
        var t = await call('get_theme_css');
        if(t && t.css) injectTheme(t.css);
      } catch(e2){ toast(I18N.t('主题刷新失败'), 'warn'); }
      applyStyleAttr();
    }
    applyBgOpacity();
    toast(I18N.t('设置已保存'), 'ok');
    renderAll();
    // 立即拉一次最新视图，避免 30 秒定时器的旧数据覆盖刚保存的主题/供应商状态
    fetchView().catch(function(){});
    return true;
  } catch(e){
    toast(I18N.t('保存失败: ')+e.message, 'err');
    return false;
  }
}
/* patch 构造：顶层 key 必须传完整 dict（浅合并语义） */
function patchTop(key, value){
  var p = {}; p[key] = value; return p;
}
async function saveProvider(pid, mutate){
  var providers = deepCopy(state.settings.providers || {});
  var cur = providers[pid] || { enabled:true, name:pid, config:{} };
  providers[pid] = mutate(cur);
  return await save(patchTop('providers', providers));
}

/* ================= 渲染：仪表盘 ================= */
function renderDashboard(){
  var v = state.view || {};
  var s = state.settings || {};
  var pidList = Object.keys(s.providers || {});
  /* 模块⑤：按用户拖拽顺序排序（order.providers，未列入的排尾部） */
  var provOrder = (s.order && s.order.providers) || [];
  if(provOrder.length){
    pidList.sort(function(a, b){
      var ia = provOrder.indexOf(a), ib = provOrder.indexOf(b);
      if(ia < 0) ia = provOrder.length + pidList.indexOf(a);
      if(ib < 0) ib = provOrder.length + pidList.indexOf(b);
      return ia - ib;
    });
  }
  var disabled = isMock();
  var fetched = v.fetched_at || (v.providers ? null : null);

  /* 顶部状态行 */
  var health = { live:0, stale:0, failed:0, off:0 };
  pidList.forEach(function(pid){
    var cfg = s.providers[pid];
    var pv = v.providers ? v.providers[pid] : null;
    var st = statusOf(pv, cfg);
    health[st.key] = (health[st.key]||0)+1;
  });
  var healthHtml = '';
  pidList.forEach(function(pid){
    var cfg = s.providers[pid];
    var pv = v.providers ? v.providers[pid] : null;
    var st = statusOf(pv, cfg);
    healthHtml += '<span class="health-dot '+st.key+'" title="'+esc(cfg.name||pid)+': '+st.label+'"></span>';
  });
  var msg, msgCls = 'ok';
  if(isMock()){ msg = I18N.t('示例数据 · 未连接后端'); msgCls='warn'; }
  else if(health.failed > 0){ msg = health.failed+I18N.t(' 个供应商异常'); msgCls='err'; }
  else if(health.stale > 0){ msg = health.stale+I18N.t(' 个供应商数据过期'); msgCls='warn'; }
  else if(pidList.length === 0){ msg = I18N.t('暂无供应商'); msgCls='warn'; }
  else { msg = I18N.t('全部正常'); }

  $('#dashStatus').innerHTML =
    '<div class="status-row">'+
      I18N.t('<span class="status-item">数据时间 <span class="val">')+fmtClock(fetched)+'</span></span>'+
      I18N.t('<span class="status-item">刷新间隔 <span class="val">')+fmtInterval(v.refresh_interval_sec)+'</span></span>'+
      I18N.t('<span class="status-item">供应商 <span class="val">')+pidList.length+'</span></span>'+
      '<span class="status-item" style="gap:4px">'+healthHtml+'</span>'+
      '<span class="status-msg '+msgCls+'">'+msg+'</span>'+
      '<button class="btn sm btn-refresh-all" id="btnRefreshAll" '+(disabled?'disabled':'')+'>'+ICONS.zap+I18N.t('全部刷新</button>')+
    '</div>';

  /* 卡片 */
  var grid = $('#dashGrid');
  if(!pidList.length){
    grid.innerHTML = I18N.t('<div class="empty-box"><b>暂无供应商</b><br>请在 config.json 中配置 providers，或在「供应商」页查看配置入口。</div>');
    return;
  }
  var html = pidList.map(function(pid){
    try {
      return dashCardHtml(pid, s.providers[pid], v.providers ? v.providers[pid] : null);
    } catch(e) {
      return I18N.t('<div class="card pcard failed"><div class="card-meta"><span class="chip danger">渲染异常: ')+esc(e.message)+'</span></div></div>';
    }
  }).join('');
    var _statsHtml = '';
  try { _statsHtml = statsSectionHtml(v, s); }
  catch(_e){ _statsHtml = '<div class="stats-section"><div class="stats-empty">stats err: '+esc(String(_e && _e.message || _e))+'</div></div>'; }
  grid.innerHTML = html + _statsHtml;

  /* 卡片事件 */
  $$('#dashGrid .btn-test').forEach(function(btn){
    btn.addEventListener('click', function(){
      runTest(btn.dataset.pid);
    });
  });
  $$('#dashGrid .btn-site').forEach(function(btn){
    btn.addEventListener('click', function(){
      var api = window.pywebview && window.pywebview.api;
      if(api && api.open_url) api.open_url(btn.dataset.site);
    });
  });
  /* 模块⑤：供应商卡片拖拽排序 */
  var dragPid = null;
  $$('#dashGrid .pcard').forEach(function(card){
    card.draggable = true;
    card.addEventListener('dragstart', function(e){
      dragPid = card.dataset.pid;
      card.classList.add('drag-src');
      try { e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', dragPid); } catch(_e){}
    });
    card.addEventListener('dragend', function(){
      card.classList.remove('drag-src');
      $$('#dashGrid .pcard').forEach(function(c){ c.classList.remove('drag-over'); });
      dragPid = null;
    });
    card.addEventListener('dragover', function(e){
      e.preventDefault();
      if(dragPid && dragPid !== card.dataset.pid) card.classList.add('drag-over');
    });
    card.addEventListener('dragleave', function(){ card.classList.remove('drag-over'); });
    card.addEventListener('drop', function(e){
      e.preventDefault();
      card.classList.remove('drag-over');
      if(!dragPid || dragPid === card.dataset.pid) return;
      var from = dragPid, to = card.dataset.pid;
      var s2 = state.settings || {};
      var allPids = Object.keys(s2.providers || {});
      var order2 = ((s2.order || {}).providers || []).slice();
      var list = order2.length ? order2.filter(function(p){ return allPids.indexOf(p) >= 0; }) : allPids.slice();
      if(list.indexOf(from) < 0) list.push(from);
      var fi = list.indexOf(from);
      if(fi >= 0) list.splice(fi, 1);
      var ti = list.indexOf(to);
      if(ti < 0) ti = 0;
      list.splice(ti, 0, from);
      allPids.forEach(function(p){ if(list.indexOf(p) < 0) list.push(p); });
      save(patchTop('order', { providers: list }));
      renderAll();
    });
  });

  /* 刷新冷却：按下后 15 秒内禁点 */
  function coolDown(btn, sec){
    if(btn._cd) return;
    btn._cd = true; btn.disabled = true;
    var orig = btn.textContent, left = sec;
    btn.textContent = left+'s';
    var iv = setInterval(function(){
      left--;
      if(left <= 0){ clearInterval(iv); btn._cd = false; btn.disabled = false; btn.textContent = orig; }
      else btn.textContent = left+'s';
    }, 1000);
  }
  function doRefresh(btn, pid){
    coolDown(btn, 15);
    call(pid ? 'refresh_provider' : 'refresh_now', pid ? pid : undefined);
    setTimeout(function(){ fetchView(); }, 2500);
  }
  var btnRA = $('#btnRefreshAll');
  if(btnRA) btnRA.addEventListener('click', function(){ doRefresh(btnRA, null); });
  $$('#dashGrid .btn-refresh-one').forEach(function(btn){
    btn.addEventListener('click', function(){ doRefresh(btn, btn.dataset.pid); });
  });
}
function dashCardHtml(pid, cfg, pv){
  cfg = cfg || { enabled:true, name:pid, config:{} };
  var st = statusOf(pv, cfg);
  var off = cfg.enabled === false;
  var disabled = isMock();
  var limits = (pv && pv.limits) || [];
  var name = esc(cfg.name || pid);
  var plan = (pv && pv.plan_name) ? esc(pv.plan_name) : '';
  var note = esc(cfg.note || '');
  var cookieBad = pv && pv.cookie_valid === false;
  var errMsg = (pv && pv.error) ? esc(pv.error) : '';
  var tr = state.testResults[pid];

  var pvKind = (pv && pv.meta && pv.meta.kind) || '';
  var dm = (state.settings.diy && state.settings.diy.modules) || {};
  var dmBal = dm.balance || { bal_main:true, meta_grid:true, token_est:true, chart:true };
  var dmQuota = dm.quota || { progress:true, tokens:true, chart:true };
  var limitsHtml = '';
  if(!off && pvKind === 'balance'){
    limitsHtml = balanceCardHtml(pv, dmBal);
  } else if(off){
    limitsHtml = I18N.t('<div class="card-meta"><span class="chip neutral">已停用 · 可在供应商页启用</span></div>');
  } else if(limits.length && dmQuota.progress){
    limitsHtml = limits.map(function(l){
      return '<div class="lim">'+
        '<div class="lim-top"><span class="lbl">'+esc(I18N.t(l.label))+'</span>'+
        '<span class="pct">'+l.used_pct+'%</span></div>'+
        '<div class="bar"><div class="fill" style="width:'+Math.min(100,Math.max(0,l.used_pct))+'%;'+pctFillStyle(l.used_pct)+'"></div></div>'+
        '<div class="lim-reset">'+fmtReset(l.reset_in_sec)+I18N.t(' 后重置</div>')+
      '</div>';
    }).join('');
  } else if(pv && pv.ok === false){
    limitsHtml = I18N.t('<div class="card-meta"><span class="chip danger">抓取失败')+(errMsg?': '+errMsg:'')+'</span></div>';
  } else {
    limitsHtml = I18N.t('<div class="card-meta"><span class="chip neutral">暂无用量数据</span></div>');
  }

  var metaChips = '';
  if(!off && pvKind !== 'balance'){
    var cells = [];
    // 订阅型/中转站 token 量
    var rt = pv && pv.meta && pv.meta.remaining_tokens;
    var at = pv && pv.meta && pv.meta.available_tokens;
    var ut = pv && pv.meta && pv.meta.used_tokens;
    var estP = pv && pv.meta && pv.meta.est_price_per_mtok;
    var estLbl = pv && pv.meta && pv.meta.est_model_label;
    if(rt != null && at == null) cells.push({ k:I18N.t('剩余 token'), v: fmtTokens(rt), small:'' });
    if(at != null) cells.push({ k:I18N.t('可用 token'), v: fmtTokens(at), small: estLbl ? I18N.t('按')+estLbl+I18N.t('估') : (estP ? I18N.t('按$')+estP+I18N.t('/百万估') : I18N.t('估算')) });
    if(ut != null) cells.push({ k:I18N.t('已用 token'), v: fmtTokens(ut), small:'' });
    // 中转站型（OpenRouter/one-api）：余额按估算单价折 token
    if(pvKind === 'relay'){
      var price = parseFloat((cfg.config && cfg.config.est_price_per_mtok) || 3);
      var balAmt = pv && pv.balance && pv.balance.amount;
      if(balAmt != null) cells.push({ k:I18N.t('可用 token'), v: fmtTokens(balAmt / price * 1000000), small: I18N.t('按$')+price+I18N.t('/百万估') });
      var tc = pv && pv.meta && pv.meta.speed && pv.meta.speed.total_consumed;
      if(tc != null) cells.push({ k:I18N.t('已用 token'), v: fmtTokens(tc / price * 1000000), small:'' });
    }
    var sc = speedChips(pv);
    // 排序：今日 → 已用 → 当前烧速 → 还能撑
    var td = todayText(pv);
    if(td) cells.push({ k:I18N.t('今日'), v: td, small:'' });
    var bal = fmtBalance(pv);
    if(bal !== '--'){
      var balK = (state.settings.currency === 'pct') ? I18N.t('已用') : I18N.t('余额');
      cells.push({ k: balK, v: bal, small:'' });
    }
    if(sc.length >= 2) cells.push({ k:I18N.t('当前烧速'), v: sc[1].text, small:'' });
    if(sc.length >= 1) cells.push({ k:I18N.t('还能撑'), v: sc[0].text, small:'' });
    metaChips = '<div class="meta-grid">'+cells.map(function(c){
      return '<div class="meta-cell"><div class="meta-k">'+esc(c.k)+'</div><div class="meta-v">'+esc(c.v)+(c.small?'<span class="meta-s">'+esc(c.small)+'</span>':'')+'</div></div>';
    }).join('')+'</div>';
  }

  var trHtml = tr ? '<div class="test-result '+(tr.ok===null?'running':(tr.ok?'ok':'fail'))+'">'+(tr.ok===null?I18N.t('测试中'):(tr.ok?I18N.t('连接成功'):I18N.t('失败')))+' · '+esc(tr.message)+'</div>' : '';

  return '<div class="card pcard '+st.key+'" data-pid="'+esc(pid)+'">'+
    '<div class="pcard-head">'+
      '<span class="health-dot '+st.key+'"></span>'+
      brandBadgeHtml(pid)+
      '<span class="pcard-name">'+name+'</span>'+
      (plan ? '<span class="pcard-plan">'+plan+'</span>' : '')+
      ((pv && pv.meta && pv.meta.demo) ? I18N.t('<span class="demo-tag">演示数据</span>') : '')+
      (note ? '<span class="pcard-note" title="'+note+'">'+note+'</span>' : '')+
      '<span class="status-pill '+st.key+'"><span class="health-dot '+st.key+'"></span>'+st.label+'</span>'+
    '</div>'+
    (cookieBad ? '<div class="cookie-bar">'+ICONS.warn+I18N.t('Cookie 已失效，请到「供应商」页更新凭据</div>') : '')+
    limitsHtml+
    metaChips+
    '<div class="card-foot">'+
      I18N.t('<span class="muted">最后更新 ')+fmtClock(pv ? pv.fetched_at : null)+'</span>'+
      (pv && pv.site ? '<button class="btn-site" data-site="'+esc(pv.site)+I18N.t('" title="打开官网">官网</button>') : '')+
      '<button class="btn sm btn-refresh-one" data-pid="'+esc(pid)+'" '+(disabled?'disabled':'')+I18N.t('>刷新</button>')+
      '<button class="btn sm btn-test" data-pid="'+esc(pid)+'">'+ICONS.zap+I18N.t('测试连接</button>')+
    '</div>'+
    trHtml+
  '</div>';
}

/* 按量余额卡：余额大数字 + 状态灯/电量条 + 三格指标 + 7日柱状图 + 当前费率单价表 */
function isPeakNow(){
  var h = new Date().getHours();
  return (h >= 9 && h < 12) || (h >= 14 && h < 18);
}
function peakInfo(){
  var h = new Date().getHours();
  if(h >= 9 && h < 12) return { on:true, until:12 };
  if(h >= 14 && h < 18) return { on:true, until:18 };
  return { on:false };
}
function fmtTokens(n){
  if(n >= 100000000) return (n/100000000).toFixed(1)+I18N.t(' 亿');
  if(n >= 1000000) return (n/1000000).toFixed(1)+I18N.t(' 百万');
  if(n >= 10000) return Math.round(n/10000)+I18N.t(' 万');
  return Math.round(n)+'';
}
/* SVG 柱状图：柱顶数值 + 日期标签 + 今天高亮 + 网格线 */
function sparkChartHtml(series, opts){
  opts = opts || {};
  var fmt = opts.fmt || fmtTokens;
  var todayIdx = series.length - 1;
  var mx = Math.max.apply(null, series.concat([0.01]));
  var slot = 36, w = series.length * slot + 6, h = 92, top = 18;
  var barMax = h - 26 - 14;
  var svg = '<svg class="spark-chart" viewBox="0 0 '+w+' '+h+'" xmlns="http://www.w3.org/2000/svg">';
  for(var g = 0; g < 3; g++){
    var gy = top + (barMax - 8) * g / 2;
    svg += '<line x1="4" y1="'+gy+'" x2="'+(w-4)+'" y2="'+gy+'" class="spark-grid"/>';
  }
  series.forEach(function(v, i){
    var x = 6 + i * slot;
    var bh = Math.max(3, v / mx * (barMax - 8));
    var y = top + (barMax - 8) - bh;
    var isToday = i === todayIdx;
    var cls = (v <= 0 ? 'spark-bar dim' : 'spark-bar') + (isToday && v > 0 ? ' today' : '');
    if(v > 0){
      svg += '<text x="'+(x+13)+'" y="'+(y-4)+'" class="spark-val" text-anchor="middle">'+fmt(v)+'</text>';
    }
    svg += '<rect x="'+x+'" y="'+y+'" width="26" height="'+bh+'" rx="3" class="'+cls+'">'+
      '<title>'+fmt(v)+'</title></rect>';
    var d = new Date(Date.now() - (todayIdx - i) * 86400000);
    svg += '<text x="'+(x+13)+'" y="'+(h-4)+'" class="spark-day'+(isToday?' today':'')+'" text-anchor="middle">'+
      (d.getMonth()+1)+'-'+d.getDate()+'</text>';
  });
  svg += '</svg>';
  return svg;
}
/* ---- 底部统计区：数值版单位换算 + 柱形/扇形汇总 ---- */
var STATS_COLORS = ['#22d3ee','#a78bfa','#34d399','#fbbf24','#f472b6','#60a5fa','#fb923c','#4ade80','#e879f9','#2dd4bf'];
function unitVal(amt, cur, meta){
  if(amt == null || isNaN(Number(amt))) return null;
  var d = state.settings.display || {};
  var u = d.unit || 'auto';
  var fx = Number(d.fx_rate) || 7.2;
  var isCny = (cur === 'CNY' || cur === 'CN¥' || cur === '¥');
  var isUsd = (cur === 'USD' || cur === 'US$' || cur === '$');
  if(u === 'tokens'){
    var models = meta && meta.models ? meta.models : [];
    var outP = models.length ? Number(models[0].output) : 0;
    if(outP > 0){
      var tv = (isUsd ? amt * fx : amt) / outP * 1000000;
      return { v: tv, label: fmtTokens(tv) };
    }
  } else if(u === 'usd'){
    var v = isCny ? amt / fx : amt;
    return { v: v, label: '≈$' + (v >= 100 ? v.toFixed(0) : v.toFixed(2)) };
  } else if(u === 'cny'){
    var v2 = isUsd ? amt * fx : amt;
    return { v: v2, label: '≈¥' + (v2 >= 100 ? v2.toFixed(0) : v2.toFixed(2)) };
  }
  return { v: Number(amt), label: money(amt, cur) };
}
function fmtStatNum(n){
  if(n == null || isNaN(n)) return '—';
  if(Math.abs(n) >= 100000000) return (n/100000000).toFixed(1)+'亿';
  if(Math.abs(n) >= 1000000) return (n/1000000).toFixed(1)+'M';
  if(Math.abs(n) >= 10000) return (n/10000).toFixed(1)+'万';
  if(Math.abs(n) >= 1000) return (n/1000).toFixed(1)+'K';
  return (Math.round(n*10)/10)+'';
}
function statsSectionHtml(v, s){
  var dm = (s.diy && s.diy.modules) || {};
  var balMod = dm.balance || { chart:true };
  if(balMod.chart === false) return '';
  var d = s.display || {};
  var u = d.unit || 'auto';
  /* 收集有消耗数据的供应商 */
  var rows = [];
  Object.keys(s.providers || {}).forEach(function(pid, idx){
    var cfg = s.providers[pid];
    if(!cfg.enabled) return;
    var pv = v && v.providers ? v.providers[pid] : null;
    if(!pv || pv.ok === false) return;
    var m = pv.meta || {};
    var sp = m.speed || {};
    var kind = m.kind || '';
    var cur = (pv.balance && pv.balance.currency) || '';
    var today = null, week = null;
    if(kind === 'balance'){ today = sp.today_amount != null ? Number(sp.today_amount) : null; week = (sp.week || []).map(Number); }
    else if(kind === 'quota'){ today = m.today_tokens != null ? Number(m.today_tokens) : null; week = (m.week_tokens || []).map(Number); }
    else if(kind === 'relay'){ today = sp.today_amount != null ? Number(sp.today_amount) : null; week = (sp.week || []).map(Number); }
    if(today == null && (!week || !week.length)) return;
    rows.push({ pid: pid, name: cfg.name || pid, color: STATS_COLORS[idx % STATS_COLORS.length],
      today: today, week: week, cur: cur, meta: m });
  });
  if(!rows.length) return '<div class="stats-section"><div class="stats-empty">'+I18N.t('暂无消耗数据')+'</div></div>';

  /* ---- 堆叠柱形图（近 7 日，日期对齐到今天） ---- */
  var DAYS = 7;
  rows.forEach(function(r){
    var aligned = new Array(DAYS).fill(0);
    var wk = r.week || [];
    for(var i=0;i<wk.length;i++){ aligned[DAYS - wk.length + i] = wk[i] || 0; }
    r.aligned = aligned;
  });
  var total = [];
  for(var dd=0; dd<DAYS; dd++){
    var daySum = 0;
    rows.forEach(function(r){
      var uv = unitVal(r.aligned[dd], r.cur, r.meta);
      daySum += uv ? uv.v : 0;
    });
    total.push(daySum);
  }
  var mx = Math.max.apply(null, total.concat([0.01]));
  var bw = 54, bh = 150, wBar = DAYS*bw + 44, topBar = 14;
  var bar = '<svg class="stats-bar" viewBox="0 0 '+wBar+' '+(bh+26)+'" xmlns="http://www.w3.org/2000/svg">';
  for(var g=0; g<4; g++){
    var gy = topBar + (bh - 10) * g / 3;
    bar += '<line x1="30" y1="'+gy+'" x2="'+(wBar-10)+'" y2="'+gy+'" stroke="rgba(128,128,128,.14)"/>';
  }
  for(var d2=0; d2<DAYS; d2++){
    var dt = new Date(Date.now() - (DAYS-1-d2)*86400000);
    var lbl = (dt.getMonth()+1)+'-'+dt.getDate();
    bar += '<text x="'+(32 + d2*bw + bw/2)+'" y="'+(bh+18)+'" font-size="9" fill="rgba(128,128,128,.7)" text-anchor="middle">'+lbl+'</text>';
    var cum = 0;
    var x = 32 + d2*bw;
    rows.forEach(function(r){
      var uv = unitVal(r.aligned[d2], r.cur, r.meta);
      var val = uv ? uv.v : 0;
      if(val <= 0) return;
      var hh = Math.max(2, val / mx * (bh - 10));
      var y = topBar + (bh - 10) - cum - hh;
      bar += '<rect x="'+x+'" y="'+y+'" width="'+(bw-18)+'" height="'+hh+'" fill="'+r.color+'" rx="1.5" opacity="0.92"><title>'+esc(r.name)+': '+fmtStatNum(val)+'</title></rect>';
      cum += hh;
    });
    if(u !== 'auto' && total[d2] > 0){
      bar += '<text x="'+(32 + d2*bw + bw/2)+'" y="'+(topBar + (bh-10) - total[d2]/mx*(bh-10) - 4)+'" font-size="9" fill="var(--text)" text-anchor="middle" opacity=".85">'+fmtStatNum(total[d2])+'</text>';
    }
  }
  bar += '</svg>';

  /* ---- 环形图（今日占比） ---- */
  var pieRows = rows.filter(function(r){ return r.today != null && r.today > 0; });
  var pieHtml = '';
  if(pieRows.length){
    var pieTotal = 0;
    pieRows.forEach(function(r){ var uv = unitVal(r.today, r.cur, r.meta); pieTotal += uv ? uv.v : 0; });
    var R = 50, C = 2 * Math.PI * R;
    var pieSvg = '<svg viewBox="0 0 140 140" style="width:150px;height:150px;display:block;margin:0 auto;">';
    var offset = 0;
    pieRows.forEach(function(r){
      var uv = unitVal(r.today, r.cur, r.meta);
      var v = uv ? uv.v : 0;
      if(v <= 0 || pieTotal <= 0) return;
      var frac = v / pieTotal;
      var dash = frac * C;
      pieSvg += '<circle cx="70" cy="70" r="'+R+'" fill="none" stroke="'+r.color+'" stroke-width="17"'
        + ' stroke-dasharray="'+dash.toFixed(2)+' '+(C-dash).toFixed(2)+'"'
        + ' stroke-dashoffset="'+(-offset).toFixed(2)+'" transform="rotate(-90 70 70)"><title>'+esc(r.name)+'</title></circle>';
      offset += dash;
    });
    pieSvg += '<text x="70" y="66" text-anchor="middle" font-size="10" fill="var(--muted)">'+I18N.t('今日')+'</text>';
    pieSvg += '<text x="70" y="84" text-anchor="middle" font-size="14" font-weight="700" fill="var(--text)">'+pieRows.length+'</text>';
    pieSvg += '</svg>';
    var legend = pieRows.map(function(r){
      var uv = unitVal(r.today, r.cur, r.meta);
      var v = uv ? uv.v : 0;
      var pct = pieTotal > 0 ? Math.round(v / pieTotal * 100) : 0;
      return '<div class="lg-row"><i style="background:'+r.color+'"></i><span>'+esc(r.name)+'</span><b>'+esc(uv ? uv.label : '—')+'</b><em>'+pct+'%</em></div>';
    }).join('');
    pieHtml = '<div class="stats-card"><h4>'+I18N.t('今日消耗占比')+'</h4><div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;"><div>'+pieSvg+'</div><div style="flex:1;min-width:120px;">'+legend+'</div></div></div>';
  }

  /* ---- 汇总输出 ---- */
  var unitNote = (u === 'usd') ? I18N.t('（美元）') : (u === 'cny') ? I18N.t('（人民币）') : (u === 'tokens') ? I18N.t('（tokens）') : '';
  return '<div class="stats-section">'+
    '<div class="stats-head">'+I18N.t('全部消耗 · 统计')+unitNote+'</div>'+
    '<div class="stats-grid">'+
      '<div class="stats-card"><h4>'+I18N.t('近 7 日消耗')+'</h4>'+bar+'</div>'+
      pieHtml +
    '</div></div>';
}

function balanceCardHtml(pv, dm){
  dm = dm || { bal_main:true, meta_grid:true, token_est:true, chart:true };
  var b = pv.balance || {};
  var m = pv.meta || {};
  var sp = m.speed || {};
  var cur = b.currency || '';
  var amt = (b.amount != null && !isNaN(Number(b.amount))) ? Number(b.amount) : null;
  var pk = peakInfo();
  var hasPeak = pv.peak === true;   // 峰谷定价平台（DeepSeek 等）
  var h = '';
  if(dm.bal_main){
    if(hasPeak && pk.on){
      h += I18N.t('<div class="peak-bar">高峰时段现在跑贵一倍 · ')+pk.until+I18N.t(' 点后恢复</div>');
    }
    h += '<div class="bal-main">'+
      '<span class="bal-amount">'+(amt!=null?moneyUnit(amt,cur,m):'—')+'</span>'+
      '<span class="bal-cur">'+(cur?esc(cur):'')+I18N.t(' 可用余额</span>')+
    '</div>';
  }
  if(dm.bal_main){
    // 余额拆分：充值 + 赠金
    var parts = [];
    if(m.topped_up != null) parts.push(I18N.t('充值 ')+moneyUnit(m.topped_up,cur,m));
    if(m.granted != null) parts.push(I18N.t('赠金 ')+moneyUnit(m.granted,cur,m));
    if(parts.length) h += '<div class="bal-sub">'+parts.join(' · ')+'</div>';
    // 电量条（余额分档）+ 状态灯文字
    var barPct = 100, barCls = 'full';
    if(amt != null){
      if(amt < 0.5){ barPct = 10; barCls = 'danger'; }
      else if(amt < 2){ barPct = 30; barCls = 'low'; }
      else if(amt < 10){ barPct = 60; barCls = 'mid'; }
    }
    var availTxt = '';
    if(m.available === false) availTxt = I18N.t('<div class="bal-avail bad">余额不足 · 请充值</div>');
    else if(m.available === true) availTxt = I18N.t('<div class="bal-avail">余额充足 · 可正常调用</div>');
    h += '<div class="bal-bar"><div class="bal-fill '+barCls+'" style="width:'+barPct+'%"></div></div>'+availTxt;
  }
  // 三格指标：今日消耗 / 日均消耗 / 还能撑
  if(dm.meta_grid){
    var cells = [
      { k:I18N.t('今日消耗'), v: sp.today_amount != null ? moneyUnit(sp.today_amount, cur, m) : I18N.t('积累中'), small:'' },
      { k:I18N.t('日均消耗'), v: sp.data_ready ? moneyUnit(sp.daily_amount, cur, m) : I18N.t('积累中'), small:'' },
      { k:I18N.t('还能撑'), v: sp.data_ready ? sp.days_left_text : I18N.t('积累中'), small:'' },
    ];
    h += '<div class="meta-grid tri">'+cells.map(function(c){
      return '<div class="meta-cell"><div class="meta-k">'+esc(c.k)+'</div><div class="meta-v">'+esc(c.v)+(c.small?'<span class="meta-s">'+esc(c.small)+'</span>':'')+'</div></div>';
    }).join('')+'</div>';
  }
  // 还能调用（token 预估）：余额 ÷ 输出单价 × 百万，按当前时段费率
  var models = m.models || [];
  if(dm.token_est && models.length && amt != null){
    var mul = (hasPeak && pk.on) ? 2 : 1;
    var sinceTxt = '';
    if(sp.since_ts){
      var dd = new Date(sp.since_ts * 1000);
      sinceTxt = I18N.t('自 ') + (dd.getMonth()+1) + '-' + dd.getDate() + I18N.t(' 接入起');
    }
    h += '<div class="token-est">'+
      I18N.t('<div class="te-head"><span>还能调用 · 预估</span><span class="te-note">按输出价')+((hasPeak && pk.on)?I18N.t(' · 高峰×2'):'')+(sinceTxt?' · '+sinceTxt:'')+'</span></div>'+
      models.map(function(x){
        var outP = x.output * mul;
        var est = amt / outP * 1000000;
        return '<div class="te-row'+(pk.on?' peak':'')+'"><span>'+esc(x.name)+'</span><b>≈ '+fmtTokens(est)+' tokens</b></div>';
      }).join('')+
      (sp.today_amount != null ? I18N.t('<div class="te-row"><span>今日消耗</span><b>≈ ')+fmtTokens(sp.today_amount / (models[0].output * mul) * 1000000)+' tokens</b></div>' : '')+
      (sp.total_consumed != null ? I18N.t('<div class="te-row"><span>接入以来已用</span><b>≈ ')+fmtTokens(sp.total_consumed / (models[0].output * mul) * 1000000)+' tokens</b></div>' : '')+
    '</div>';
  }
  if(pv.ok === false){
    h = I18N.t('<div class="card-meta"><span class="chip danger">抓取失败')+(pv.error?': '+esc(pv.error):'')+'</span></div>';
  }
  if(!h){
    h = '<div class="diy-empty">'+ICONS.gridOff+'</div>';
  }
  return h;
}

/* ================= 渲染：供应商页 ================= */
var providerTypesCache = null;

async function ensureProviderTypes(){
  if(providerTypesCache) return providerTypesCache;
  try {
    var types = await call('get_provider_types');
    /* 仅成功且非空才缓存；失败/空不缓存，下次调用重试（页面加载早期 pywebview 未就绪时会失败） */
    providerTypesCache = (types && types.length) ? types : null;
    return providerTypesCache || [];
  } catch(e){ providerTypesCache = null; }
  return [];
}

/* 品牌图标 HTML（真实 logo 或字母兜底），自定义下拉 / 徽章复用 */
function brandIconHtml(pid){
  var f = BRAND_ICONS[pid];
  if(f) return '<img src="icons/'+f+'" alt="">';
  var b = BRAND_BADGES[pid] || { c:'#6B7280', t:'?' };
  return '<span class="cs-fallback" style="background:'+b.c+'">'+b.t+'</span>';
}
/* 自定义供应商下拉：列表项 = logo + 名字（原生 option 放不了图片） */
function renderTypeDropdown(types){
  var list = $('#apTypeList');
  list.innerHTML = types.map(function(t){
    return '<div class="cs-item" data-id="'+esc(t.id)+'">'+
      brandIconHtml(t.id)+
      '<span>'+esc(t.name)+(t.plan_name?'<span class="cs-plan">（'+esc(t.plan_name)+'）</span>':'')+'</span>'+
    '</div>';
  }).join('');
  var btn = $('#apTypeBtn');
  btn.onclick = function(e){
    e.stopPropagation();
    list.style.display = (list.style.display === 'none') ? 'block' : 'none';
  };
  list.onclick = function(e){
    var item = e.target && e.target.closest ? e.target.closest('.cs-item') : null;
    if(!item) return;
    selectType(item.dataset.id);
    list.style.display = 'none';
  };
  document.addEventListener('click', function(){ list.style.display = 'none'; });
  if(types.length) selectType(types[0].id);
}
/* 选中供应商类型：同步隐藏 select 并触发字段渲染 */
function selectType(tid){
  var sel = $('#apType');
  sel.value = tid;
  var t = (providerTypesCache || []).find(function(x){ return x.id === tid; });
  $('#apTypeLabel').textContent = t ? t.name : tid;
  $('#apTypeIcon').innerHTML = brandIconHtml(tid);
  if(typeof sel.onchange === 'function') sel.onchange();
}

async function openAddProvider(){
  if(isMock()){ toast(I18N.t('示例数据模式，无法添加供应商'), 'warn'); return; }
  var types = await ensureProviderTypes();
  if(!types.length){ toast(I18N.t('暂无可添加的供应商类型'), 'warn'); return; }
  var sel = $('#apType');
  sel.innerHTML = types.map(function(t){
    return '<option value="'+esc(t.id)+'">'+esc(t.name)+'</option>';
  }).join('');
  sel.onchange = function(){
    var t = types.find(function(x){ return x.id === sel.value; });
    if(t) renderApFields(t);
  };
  renderTypeDropdown(types);
  $('#apName').value = '';
  $('#addProviderPanel').style.display = 'flex';
  $('#btnAddProvider').textContent = I18N.t('收起');
}

function closeAddProvider(){
  $('#addProviderPanel').style.display = 'none';
  $('#btnAddProvider').textContent = I18N.t('＋ 添加供应商');
}

/* API 导入：模板 id → 额外需要填写的字段（来自 schema options 的 needs） */
var apiTplNeeds = {};

function renderApFields(type){
  /* API 导入：模板选择驱动条件字段（选完模板通常只需填 API Key） */
  if(type && type.id === 'api'){ renderApiAddFields(type); return; }
  var box = $('#apFields');
  var schema = (type && type.schema && type.schema.length) ? type.schema : FALLBACK_SCHEMA;
  box.innerHTML = schema.map(function(f){
    /* select 类型（如 API 导入的模板下拉） */
    if(f.type === 'select' && f.options && f.options.length){
      var opts = f.options.map(function(o){
        return '<option value="'+esc(o.value)+'">'+esc(I18N.t(o.label))+'</option>';
      }).join('');
      return '<div class="field"><label>'+esc(I18N.t(f.label))+'</label>'+
        '<select data-key="'+esc(f.key)+'">'+opts+'</select></div>';
    }
    return '<div class="field"><label>'+esc(I18N.t(f.label))+'</label>'+
      '<input type="'+(f.secret?'password':'text')+'" data-key="'+esc(f.key)+'" autocomplete="off"></div>';
  }).join('');
  /* API 导入：有 api_key 字段的类型显示唯一标识输入框（支持多实例） */
  var keyRow = $('#apKeyRow');
  if(keyRow) keyRow.style.display =
    schema.some(function(f){ return f.key === 'api_key'; }) ? 'flex' : 'none';
}

/* API 导入添加表单：模板下拉 + 按需字段（默认只需 API Key） */
function renderApiAddFields(type){
  var box = $('#apFields');
  var tplField = (type.schema || []).find(function(f){ return f.key === 'template'; });
  tplField = tplField || { label:I18N.t('查询模板'), options:[] };
  apiTplNeeds = {};
  var opts = tplField.options || [];
  opts.forEach(function(o){ apiTplNeeds[o.value] = o.needs || []; });
  var selHtml = '<div class="field"><label>'+esc(I18N.t(tplField.label))+'</label>'+
    '<select id="apTemplate">'+
      opts.map(function(o){ return '<option value="'+esc(o.value)+'">'+esc(I18N.t(o.label))+'</option>'; }).join('')+
    '</select></div>';
  box.innerHTML = selHtml + '<div id="apApiFields"></div>';
  var sel = $('#apTemplate');
  if(sel){
    sel.addEventListener('change', function(){ renderApiFieldsFor(sel.value); });
    renderApiFieldsFor(sel.value);
  }
  var keyRow = $('#apKeyRow');
  if(keyRow) keyRow.style.display = 'flex';
}

/* 按模板 needs 渲染剩余字段：api_key 恒有，base_url/user_id 按需 */
function renderApiFieldsFor(tid){
  var needs = apiTplNeeds[tid] || [];
  var html = '<div class="field"><label>API Key</label>'+
    '<input type="password" data-key="api_key" autocomplete="off" placeholder="sk-..."></div>';
  if(needs.indexOf('base_url') >= 0){
    html += '<div class="field"><label>Base URL</label>'+
      '<input type="text" data-key="base_url" placeholder="https://api.example.com"></div>';
  }
  if(needs.indexOf('user_id') >= 0){
    html += I18N.t('<div class="field"><label>User ID（one-api 中转站可选）</label>')+
      '<input type="text" data-key="user_id" placeholder="123456"></div>';
  }
  $('#apApiFields').innerHTML = html;
}

async function saveAddProvider(){
  var typeId = $('#apType').value;
  if(!typeId){ toast(I18N.t('请选择供应商类型'), 'warn'); return; }
  /* API 类（schema 含 api_key）：标识即 config 的 key，允许一个模板多个实例 */
  var typeObj = (providerTypesCache || []).find(function(t){ return t.id === typeId; });
  var isApi = !!(typeObj && (typeObj.schema || []).some(function(f){ return f.key === 'api_key'; }));
  var key = isApi ? ($('#apKey').value.trim() || typeId) : typeId;
  var providers = deepCopy(state.settings.providers || {});
  if(providers[key]){
    toast(I18N.t('该标识的供应商已存在，可直接在下方列表编辑'), 'warn');
    closeAddProvider();
    return;
  }
  var name = $('#apName').value.trim() || (isApi ? key : typeId);
  var config = {};
  $$('#apFields input[data-key], #apFields select[data-key]').forEach(function(i){ config[i.dataset.key] = i.value; });
  var entry = { enabled:true, name:name, config:config };
  if(isApi) entry.type = typeId;   /* kernel 据此实例化对应模板的 ApiProvider */
  providers[key] = entry;
  try {
    await save(patchTop('providers', providers));
    closeAddProvider();
    toast(I18N.t('已添加供应商：')+name, 'ok');
    renderAll();
  } catch(e){
    toast(I18N.t('添加失败: ')+e.message, 'err');
  }
}

async function renderProviders(){
  await ensureProviderTypes();   /* 编辑表单需要 schema（get_provider_types） */
  var s = state.settings || {};
  var pids = Object.keys(s.providers || {});
  var box = $('#providersList');
  if(!pids.length){
    box.innerHTML = I18N.t('<div class="empty-box"><b>暂无供应商</b><br>点击右上角「添加供应商」开始配置。</div>');
    return;
  }
  box.innerHTML = pids.map(function(pid){
    return providerRowHtml(pid, s.providers[pid]);
  }).join('');

  /* 事件 */
  $$('#providersList .sw-enabled').forEach(function(inp){
    inp.addEventListener('change', function(){
      var pid = inp.dataset.pid;
      saveProvider(pid, function(p){ p.enabled = inp.checked; return p; });
    });
  });
  $$('#providersList .prow-name-input').forEach(function(inp){
    inp.addEventListener('change', function(){
      var pid = inp.dataset.pid;
      var v = inp.value.trim();
      saveProvider(pid, function(p){ p.name = v || pid; return p; });
    });
  });
  $$('#providersList .btn-save-config').forEach(function(btn){
    btn.addEventListener('click', function(){
      var pid = btn.dataset.pid;
      var inputs = $$('#providersList [data-pid="'+pid+'"][data-key]');
      var config = {};
      inputs.forEach(function(i){ config[i.dataset.key] = i.value; });
      saveProvider(pid, function(p){ p.config = config; return p; });
    });
  });
  $$('#providersList .btn-test').forEach(function(btn){
    btn.addEventListener('click', function(){ runTest(btn.dataset.pid); });
  });
  $$('#providersList .btn-del-prov').forEach(function(btn){
    btn.addEventListener('click', function(){
      if(btn.dataset.arm === '1'){
        call('remove_provider', btn.dataset.pid).then(function(){
          toast(I18N.t('已删除 ')+btn.dataset.pid, 'ok');
          fetchView();
        });
      } else {
        btn.dataset.arm = '1';
        var orig = btn.textContent;
        btn.textContent = I18N.t('确认删除？');
        setTimeout(function(){ btn.dataset.arm = ''; btn.textContent = orig; }, 4000);
      }
    });
  });
  /* API 导入编辑：切换模板时联动刷新按需字段 */
  $$('#providersList .api-tpl-select').forEach(function(sel){
    sel.addEventListener('change', function(){
      var pid = sel.dataset.pid;
      var rest = $('#apiRest-'+pid);
      if(!rest) return;
      var apiT = (providerTypesCache || []).find(function(t){ return t.id === 'api'; });
      var cfg = (state.settings.providers || {})[pid] || {};
      rest.innerHTML = apiEditRestHtml(pid, cfg, apiT ? apiT.schema : [], sel.value, isMock());
    });
  });
}
function providerRowHtml(pid, cfg){
  cfg = cfg || { enabled:true, name:pid, config:{} };
  var pv = state.view && state.view.providers ? state.view.providers[pid] : null;
  var st = statusOf(pv, cfg);
  var schema = FALLBACK_SCHEMA;
  if(cfg.type){
    /* API 导入（模板类型或自定义 api）：schema 从类型缓存取（view 不带 schema） */
    var apiT = (providerTypesCache || []).find(function(t){ return t.id === cfg.type; });
    if(apiT && apiT.schema && apiT.schema.length) schema = apiT.schema;
  } else if(pv && pv.schema && pv.schema.length){
    schema = pv.schema;
  }
  var tr = state.testResults[pid];
  var disabled = isMock();

  var hasTplSelect = schema.some(function(f){ return f.type === 'select'; });
  var fields;
  if(cfg.type && hasTplSelect){
    /* 自定义 api 类型（含模板下拉）：模板切换联动按需字段 */
    fields = apiEditFieldsHtml(pid, cfg, schema, disabled);
  } else {
    fields = schema.map(function(f){
      var val = (cfg.config && cfg.config[f.key] != null) ? cfg.config[f.key] : '';
      /* select 类型（如 API 导入的模板下拉） */
      if(f.type === 'select' && f.options && f.options.length){
        var opts = f.options.map(function(o){
          return '<option value="'+esc(o.value)+'"'+(String(val)===String(o.value)?' selected':'')+'>'+esc(I18N.t(o.label))+'</option>';
        }).join('');
        return '<div class="field">'+
          '<label>'+esc(I18N.t(f.label))+'</label>'+
          '<select data-pid="'+esc(pid)+'" data-key="'+esc(f.key)+'" '+(disabled?'disabled':'')+'>'+opts+'</select>'+
        '</div>';
      }
      return '<div class="field">'+
        '<label>'+esc(I18N.t(f.label))+'</label>'+
        '<input type="'+(f.secret?'password':'text')+'" data-pid="'+esc(pid)+'" data-key="'+esc(f.key)+'" value="'+esc(val)+'" autocomplete="off" '+(disabled?'disabled':'')+'>'+
      '</div>';
    }).join('');
  }

  var statusTxt = st.label;
  var dataTxt = (pv && pv.fetched_at) ? I18N.t('抓取于 ')+fmtClock(pv.fetched_at) : I18N.t('暂无数据');
  var trHtml = tr ? '<div class="test-result '+(tr.ok?'ok':'fail')+'">'+(tr.ok?I18N.t('连接成功'):I18N.t('连接失败'))+' · '+esc(tr.message)+'</div>' : '';

  return '<div class="card prow-card '+(cfg.enabled===false?'off':'')+'">'+
    '<div class="prow-head">'+
      '<label class="switch"><input type="checkbox" class="sw-enabled" data-pid="'+esc(pid)+'" '+(cfg.enabled?'checked':'')+(disabled?' disabled':'')+'><span class="knob"></span></label>'+
      brandBadgeHtml(pid)+
      '<div>'+
        '<input class="prow-name-input" data-pid="'+esc(pid)+'" value="'+esc(cfg.name||pid)+'" '+(disabled?'disabled':'')+I18N.t(' title="编辑备注名，回车或失焦保存">')+
        '<div class="prow-id">'+esc(pid)+'</div>'+
      '</div>'+
      '<div class="prow-right">'+
        '<span class="status-pill '+st.key+'"><span class="health-dot '+st.key+'"></span>'+statusTxt+'</span>'+
        '<span class="prow-status">'+esc(dataTxt)+'</span>'+
      '</div>'+
    '</div>'+
    '<div class="schema-grid">'+fields+'</div>'+
    '<div class="prow-actions">'+
      '<button class="btn sm btn-del-prov" data-pid="'+esc(pid)+'" '+(disabled?'disabled':'')+I18N.t('>删除</button>')+
      '<button class="btn btn-test" data-pid="'+esc(pid)+'" '+(disabled?'disabled':'')+'>'+ICONS.zap+I18N.t('测试连接</button>')+
      '<button class="btn sm btn-save-config" data-pid="'+esc(pid)+'" '+(disabled?'disabled':'')+I18N.t('>保存凭据</button>')+
      '<span class="spacer"></span>'+
      I18N.t('<span class="hint">secret 字段已加密显示</span>')+
    '</div>'+
    trHtml+
  '</div>';
}
/* API 导入编辑表单：模板下拉 + API Key + 按需字段（默认只需 API Key） */
function apiNeedsOf(schema, tid){
  var tf = (schema || []).find(function(f){ return f.key === 'template'; });
  if(!tf || !tf.options) return [];
  var o = tf.options.find(function(x){ return x.value === tid; });
  return (o && o.needs) || [];
}
function apiEditFieldsHtml(pid, cfg, schema, disabled){
  var tf = (schema || []).find(function(f){ return f.key === 'template'; });
  tf = tf || { label:I18N.t('查询模板'), options:[] };
  var curTpl = (cfg.config && cfg.config.template) ||
    ((tf.options[0] && tf.options[0].value) || '');
  var selHtml = '<div class="field">'+
    '<label>'+esc(I18N.t(tf.label))+'</label>'+
    '<select class="api-tpl-select" data-pid="'+esc(pid)+'" data-key="template" '+(disabled?'disabled':'')+'>'+
      tf.options.map(function(o){
        return '<option value="'+esc(o.value)+'"'+(String(curTpl)===String(o.value)?' selected':'')+'>'+esc(I18N.t(o.label))+'</option>';
      }).join('')+
    '</select></div>';
  var keyVal = (cfg.config && cfg.config.api_key != null) ? cfg.config.api_key : '';
  var keyHtml = '<div class="field">'+
    '<label>API Key</label>'+
    '<input type="password" data-pid="'+esc(pid)+'" data-key="api_key" value="'+esc(keyVal)+'" autocomplete="off" '+(disabled?'disabled':'')+'>'+
    '</div>';
  return selHtml + keyHtml +
    '<div class="api-edit-rest" id="apiRest-'+esc(pid)+'">'+
      apiEditRestHtml(pid, cfg, schema, curTpl, disabled)+
    '</div>';
}
function apiEditRestHtml(pid, cfg, schema, tid, disabled){
  var needs = apiNeedsOf(schema, tid);
  var val = function(k){ return (cfg.config && cfg.config[k] != null) ? cfg.config[k] : ''; };
  var html = '';
  if(needs.indexOf('base_url') >= 0){
    html += '<div class="field"><label>Base URL</label>'+
      '<input type="text" data-pid="'+esc(pid)+'" data-key="base_url" value="'+esc(val('base_url'))+'" placeholder="https://api.example.com" '+(disabled?'disabled':'')+'>'+
      '</div>';
  }
  if(needs.indexOf('user_id') >= 0){
    html += I18N.t('<div class="field"><label>User ID（one-api 中转站可选）</label>')+
      '<input type="text" data-pid="'+esc(pid)+'" data-key="user_id" value="'+esc(val('user_id'))+'" placeholder="123456" '+(disabled?'disabled':'')+'>'+
      '</div>';
  }
  return html;
}

async function runTest(pid){
  try {
    await call('test_provider', pid);          // 立即返回，后端异步测试
    state.testResults[pid] = { ok:null, message:I18N.t('测试中…') };
    renderAll();
    for(var i=0; i<20; i++){                  // 轮询结果（最长 10 秒）
      await new Promise(function(r){ setTimeout(r, 500); });
      var res = await call('test_provider_result', pid);
      if(res && res.done){
        state.testResults[pid] = { ok: !!res.ok, message: res.message || '' };
        var ms = res.latency_ms != null ? res.latency_ms+' ms' : '';
        if(res.ok){
          toast(ms || I18N.t('连接成功'), 'ok');   // 成功只显示延迟
        } else {
          toast(I18N.t('连接失败')+(ms?' · '+ms:''), 'err');
        }
        break;
      }
    }
  } catch(e){
    state.testResults[pid] = { ok:false, message:e.message };
    toast(I18N.t('测试失败: ')+e.message, 'err');
  }
  renderAll();
}

/* ================= 渲染：外观页 ================= */
function renderAppearance(){
  var s = state.settings || {};
  var th = s.theme || { id:'paper', variant:null };
  var op = s.opacity || { main:0.95, mini:0.92 };
  var w = s.window || {};
  var disabled = isMock();
  var diy = s.diy || {};
  var dUnit = (s.display || {}).unit || 'auto';
  var fxRate = (s.display || {}).fx_rate || 7.2;
  var diyMini = diy.mini_provider || '';
  var diyMods = diy.modules || { balance:{bal_main:true,meta_grid:true,token_est:true,chart:true}, quota:{progress:true,tokens:true,chart:true} };
  diyMods.balance = Object.assign({bal_main:true,meta_grid:true,token_est:true,chart:true}, diyMods.balance||{});
  diyMods.quota = Object.assign({progress:true,tokens:true,chart:true}, diyMods.quota||{});
  var curTheme = THEMES[th.id] || THEMES['paper'];

  var themeCards = Object.keys(THEMES).map(function(id){
    var t = THEMES[id];
    var active = (th.id === id);
    return '<button class="theme-card'+(active?' active':'')+'" data-theme="'+id+'" '+(disabled?'disabled':'')+'>'+
      '<div class="theme-preview" style="--tp-a:'+t.accent+';--tp-b:'+t.accent2+';--tp-bg:'+t.bg+'"></div>'+
      '<div class="theme-name">'+esc(I18N.t(t.name))+(active?'<span class="tag">ACTIVE</span>':'')+'</div>'+
      '<div class="theme-desc">'+esc(I18N.t(STYLE_DESC[id]||''))+'</div>'+
    '</button>';
  }).join('');

  var palettes = STYLE_PALETTES[th.id] || [];
  var curVariant = th.variant || null;
  var paletteHtml = palettes.length ?
    '<div class="palette-row" style="margin-top:12px">'+
      I18N.t('<div style="font-size:11px;color:var(--muted);margin-bottom:6px">换色</div>')+
      '<div class="palette-grid">'+
        palettes.map(function(pal){
          var act = (curVariant === pal.id);
          return '<button class="palette-btn'+(act?' active':'')+'" data-variant="'+pal.id+'" '+(disabled?'disabled':'')+'>'+
            '<span class="palette-dots">'+pal.colors.map(function(c){ return '<i style="background:'+c+'"></i>'; }).join('')+'</span>'+
            '<span class="palette-name">'+esc(I18N.t(pal.name))+(act?I18N.t('<span class="tag">使用中</span>'):'')+'</span>'+
          '</button>';
        }).join('')+
      '</div>'+
    '</div>' : '';

  $('#appearanceBody').innerHTML =
    I18N.t('<div class="set-group"><div class="set-title">主题</div>')+
      '<div class="theme-grid">'+themeCards+'</div>'+paletteHtml+
    '</div>'+

    I18N.t('<div class="set-group"><div class="set-title">透明度</div>')+
      '<div class="card"><div class="slider-row">'+
        I18N.t('<div class="slider-top"><span>迷你窗</span><span class="v" id="opMiniV">')+Math.round(op.mini*100)+'%</span></div>'+
        '<input type="range" id="opMini" min="40" max="100" value="'+Math.round(op.mini*100)+'" '+(disabled?'disabled':'')+'>'+
      '</div></div>'+
    '</div>'+

    I18N.t('<div class="set-group"><div class="set-title">迷你窗</div>')+
      '<div class="card">'+
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">'+
          '<label class="switch"><input type="checkbox" id="miniSwitch" '+(s.mini_widget_enabled?'checked':'')+(disabled?' disabled':'')+'><span class="knob"></span></label>'+
          I18N.t('<span style="font-size:12px">启用迷你悬浮窗</span>')+
          '<span class="spacer" style="flex:1"></span>'+
          I18N.t('<span class="desc" style="font-size:11px;color:var(--muted)">右下角霓虹 HUD</span>')+
        '</div>'+
        '<div class="size-presets">'+
          '<button class="size-btn'+( (w.mini_width||300)===240 ? ' active':'')+'" data-sw="240" data-sh="140" '+(disabled?'disabled':'')+I18N.t('>小</button>')+
          '<button class="size-btn'+( (w.mini_width||300)===300 ? ' active':'')+'" data-sw="300" data-sh="170" '+(disabled?'disabled':'')+I18N.t('>中</button>')+
          '<button class="size-btn'+( (w.mini_width||300)===380 ? ' active':'')+'" data-sw="380" data-sh="210" '+(disabled?'disabled':'')+I18N.t('>大</button>')+
          I18N.t('<span style="margin-left:auto;font-size:10px;color:var(--muted)">也可在迷你窗边缘拖动微调</span>')+
        '</div>'+
        '<div class="slider-row" style="margin-top:10px">'+
          I18N.t('<div class="slider-top"><span>大小（拖动精确控制）</span><span class="v" id="miniSizeV">')+(w.mini_width||300)+'px</span></div>'+
          '<input type="range" id="miniSize" min="160" max="600" step="5" value="'+(w.mini_width||300)+'" '+(disabled?'disabled':'')+'>'+
        '</div>'+
        I18N.t('<div class="diy-row" style="margin-top:10px"><span class="diy-lbl">迷你窗显示</span>')+
          '<select id="miniProvider" '+(disabled?'disabled':'')+'>'+
            I18N.t('<option value="">自动（第一个启用）</option>')+
            Object.keys(s.providers||{}).map(function(pid){
              var cfg2 = s.providers[pid];
              var sel2 = (diyMini===(pid)) ? ' selected' : '';
              return '<option value="'+esc(pid)+'"'+sel2+'>'+esc(cfg2.name||pid)+'</option>';
            }).join('')+
          '</select>'+
        '</div>'+
      '</div>'+
    '</div>'+

    I18N.t('<div class="set-group"><div class="set-title">仪表盘显示</div>')+
      '<div class="card">'+
        I18N.t('<div class="diy-sec">余额卡（DeepSeek/Kimi 等）</div>')+
        '<div class="diy-grid">'+
        I18N.t('<div class="diy-row"><span class="diy-lbl">余额大卡</span><label class="switch"><input type="checkbox" id="diyBalMain" ')+(diyMods.balance.bal_main?'checked':'')+(disabled?' disabled':'')+'><span class="knob"></span></label></div>'+
        I18N.t('<div class="diy-row"><span class="diy-lbl">消耗指标（今日/日均/还能撑）</span><label class="switch"><input type="checkbox" id="diyBalGrid" ')+(diyMods.balance.meta_grid?'checked':'')+(disabled?' disabled':'')+'><span class="knob"></span></label></div>'+
        I18N.t('<div class="diy-row"><span class="diy-lbl">Token 预估</span><label class="switch"><input type="checkbox" id="diyBalTok" ')+(diyMods.balance.token_est?'checked':'')+(disabled?' disabled':'')+'><span class="knob"></span></label></div>'+
        I18N.t('<div class="diy-row"><span class="diy-lbl">底部统计区（柱形/扇形）</span><label class="switch"><input type="checkbox" id="diyBalChart" ')+(diyMods.balance.chart?'checked':'')+(disabled?' disabled':'')+'><span class="knob"></span></label></div>'+
        '</div>'+
        I18N.t('<div class="diy-sec">订阅卡（OpenCode Go）</div>')+
        '<div class="diy-grid">'+
        I18N.t('<div class="diy-row"><span class="diy-lbl">进度条组</span><label class="switch"><input type="checkbox" id="diyQuaProg" ')+(diyMods.quota.progress?'checked':'')+(disabled?' disabled':'')+'><span class="knob"></span></label></div>'+
        I18N.t('<div class="diy-row"><span class="diy-lbl">Token 指标</span><label class="switch"><input type="checkbox" id="diyQuaTok" ')+(diyMods.quota.tokens?'checked':'')+(disabled?' disabled':'')+'><span class="knob"></span></label></div>'+
        '</div>'+
      '</div>'+
    '</div>'+

    I18N.t('<div class="set-group"><div class="set-title">计量单位</div>')+
      '<div class="card">'+
        '<div style="font-size:11px;color:var(--muted);margin-bottom:8px">金额与消耗显示口径（卡片 + 底部统计区）</div>'+
        '<div class="opt-group">'+
          '<button class="opt-btn'+(dUnit==='auto'?' active':'')+'" data-unit="auto" '+(disabled?'disabled':'')+I18N.t('>自动（原币种）</button>')+
          '<button class="opt-btn'+(dUnit==='usd'?' active':'')+'" data-unit="usd" '+(disabled?'disabled':'')+I18N.t('>美元</button>')+
          '<button class="opt-btn'+(dUnit==='cny'?' active':'')+'" data-unit="cny" '+(disabled?'disabled':'')+I18N.t('>人民币</button>')+
          '<button class="opt-btn'+(dUnit==='tokens'?' active':'')+'" data-unit="tokens" '+(disabled?'disabled':'')+I18N.t('>Tokens</button>')+
        '</div>'+
        '<div class="slider-row" style="margin-top:10px">'+
          '<div class="slider-top"><span>汇率 1 USD = ? CNY</span><span class="v">'+fxRate+'</span></div>'+
          '<input type="number" id="fxRate" min="1" max="30" step="0.1" value="'+fxRate+'" '+(disabled?'disabled':'')+' style="width:100%">'+
        '</div>'+
      '</div>'+
    '</div>'+

    I18N.t('<div class="set-group"><div class="set-title">界面</div>')+
      '<div class="row-2col">'+
        I18N.t('<div class="card"><div style="font-size:11px;color:var(--muted);margin-bottom:8px">界面密度</div>')+
          '<div class="opt-group">'+
            '<button class="opt-btn'+(s.density==='compact'?' active':'')+'" data-density="compact" '+(disabled?'disabled':'')+I18N.t('>紧凑</button>')+
            '<button class="opt-btn'+(s.density==='comfortable'?' active':'')+'" data-density="comfortable" '+(disabled?'disabled':'')+I18N.t('>舒适</button>')+
          '</div>'+
        '</div>'+
        I18N.t('<div class="card"><div style="font-size:11px;color:var(--muted);margin-bottom:8px">货币显示</div>')+
          '<div class="opt-group">'+
            '<button class="opt-btn'+(s.currency==='usd'?' active':'')+'" data-currency="usd" '+(disabled?'disabled':'')+I18N.t('>美元</button>')+
            '<button class="opt-btn'+(s.currency==='pct'?' active':'')+'" data-currency="pct" '+(disabled?'disabled':'')+I18N.t('>百分比</button>')+
          '</div>'+
        '</div>'+
        I18N.t('<div class="card"><div style="font-size:11px;color:var(--muted);margin-bottom:8px">更新间隔</div>')+
          '<div class="opt-group">'+
            [1,2,5,10,15,30].map(function(m){
              var active = (s.refresh_interval_sec === m*60);
              return '<button class="opt-btn'+(active?' active':'')+'" data-interval="'+m+'" '+(disabled?'disabled':'')+'>'+m+I18N.t('分钟</button>');
            }).join('')+
          '</div>'+
        '</div>'+
      '</div>'+
    '</div>';

  /* 事件 */
  $$('#appearanceBody .theme-card').forEach(function(card){
    card.addEventListener('click', function(){
      if(card.disabled) return;
      var id = card.dataset.theme;
      applyTheme(id, null);   // 切换风格时配色重置为默认
    });
  });
  $$('#appearanceBody .palette-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      if(btn.disabled) return;
      var id = state.settings.theme ? state.settings.theme.id : 'paper';
      applyTheme(id, btn.dataset.variant);
    });
  });

  var opMini = $('#opMini');
  if(opMini) opMini.addEventListener('input', function(){
    $('#opMiniV').textContent = opMini.value+'%';
  });
  if(opMini) opMini.addEventListener('change', function(){
    save(patchTop('opacity', { mini: opMini.value/100 }));
  });

  var miniSwitch = $('#miniSwitch');
  if(miniSwitch) miniSwitch.addEventListener('change', function(){
    save(patchTop('mini_widget_enabled', miniSwitch.checked));
  });
  $$('#appearanceBody .size-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      if(btn.disabled) return;
      save(patchTop('window', {
        main_width:(state.settings.window||{}).main_width,
        main_height:(state.settings.window||{}).main_height,
        mini_width: parseInt(btn.dataset.sw,10),
        mini_height: parseInt(btn.dataset.sh,10),
        mini_corner:(state.settings.window||{}).mini_corner
      }));
    });
  });

  var miniSize = $('#miniSize');
  if(miniSize) miniSize.addEventListener('input', function(){
    $('#miniSizeV').textContent = miniSize.value+'px';
    var api = window.pywebview && window.pywebview.api;
    if(api && api.resize_mini_main){
      api.resize_mini_main(parseInt(miniSize.value,10));
    }
  });
  if(miniSize) miniSize.addEventListener('change', function(){
    var api = window.pywebview && window.pywebview.api;
    if(api && api.resize_mini_main){
      api.resize_mini_main(parseInt(miniSize.value,10));
    }
    save(patchTop('window', {
      main_width:(state.settings.window||{}).main_width,
      main_height:(state.settings.window||{}).main_height,
      mini_width: parseInt(miniSize.value,10),
      mini_height: (state.settings.window||{}).mini_height,
      mini_corner:(state.settings.window||{}).mini_corner
    }));
  });

  /* DIY：保存 diy 配置 */
  function saveDiy(patch){
    var d = state.settings.diy || {};
    var nd = Object.assign({}, d, patch);
    save(patchTop('diy', nd));
  }
  var miniProvider = $('#miniProvider');
  if(miniProvider) miniProvider.addEventListener('change', function(){
    saveDiy({ mini_provider: miniProvider.value });
  });
  var DIY_MAP = [
    ['diyBalMain',   'balance', 'bal_main'],
    ['diyBalGrid',   'balance', 'meta_grid'],
    ['diyBalTok',    'balance', 'token_est'],
    ['diyBalChart',  'balance', 'chart'],
    ['diyQuaProg',   'quota',   'progress'],
    ['diyQuaTok',    'quota',   'tokens'],
    ['diyQuaChart',  'quota',   'chart'],
  ];
  DIY_MAP.forEach(function(item){
    var el = $('#'+item[0]);
    if(el) el.addEventListener('change', function(){
      var mods = JSON.parse(JSON.stringify((state.settings.diy && state.settings.diy.modules) || {}));
      mods[item[1]] = mods[item[1]] || {};
      mods[item[1]][item[2]] = el.checked;
      saveDiy({ modules: mods });
    });
  });

  $$('#appearanceBody .opt-btn[data-density]').forEach(function(btn){
    btn.addEventListener('click', function(){
      if(btn.disabled) return;
      document.body.setAttribute('data-density', btn.dataset.density);
      save(patchTop('density', btn.dataset.density));
    });
  });
  /* 计量单位（display.unit）+ 汇率 */
  $$('#appearanceBody .opt-btn[data-unit]').forEach(function(btn){
    btn.addEventListener('click', function(){
      var d2 = state.settings.display || {};
      save(patchTop('display', { unit: btn.dataset.unit, fx_rate: Number(d2.fx_rate) || 7.2 }));
    });
  });
  var fxInp = $('#fxRate');
  if(fxInp) fxInp.addEventListener('change', function(){
    var d2 = state.settings.display || {};
    save(patchTop('display', { unit: d2.unit || 'auto', fx_rate: parseFloat(fxInp.value) || 7.2 }));
  });

  $$('#appearanceBody .opt-btn[data-currency]').forEach(function(btn){
    btn.addEventListener('click', function(){
      if(btn.disabled) return;
      save(patchTop('currency', btn.dataset.currency));
    });
  });
  $$('#appearanceBody .opt-btn[data-interval]').forEach(function(btn){
    btn.addEventListener('click', function(){
      if(btn.disabled) return;
      save(patchTop('refresh_interval_sec', parseInt(btn.dataset.interval,10)*60));
    });
  });
}
async function applyTheme(id, variant){
  var ok = await save(patchTop('theme', { id:id, variant:variant || null }), { theme:true });
  if(ok && variant){
    toast(I18N.t('配色已切换'), 'ok');
  }
}

/* ================= 渲染：通知页 ================= */
function renderNotify(){
  var s = state.settings || {};
  var n = s.notify || { method:'tray', threshold:80, urgent:95, events:{ threshold:true, urgent:true, cookie_fail:true, fetch_fail:true } };
  var ev = n.events || {};
  var disabled = isMock();

  var methods = [
    { id:'tray', name:I18N.t('托盘气泡'), desc:I18N.t('零依赖，默认'), icon:'tray' },
    { id:'system', name:I18N.t('系统通知'), desc:I18N.t('winotify 弹窗'), icon:'bell' },
    { id:'off', name:I18N.t('关闭'), desc:I18N.t('静默记录'), icon:'info' }
  ];
  var methodHtml = methods.map(function(m){
    return '<button class="method-card'+(n.method===m.id?' active':'')+'" data-method="'+m.id+'" '+(disabled?'disabled':'')+'>'+
      ICONS[m.icon]+
      '<div class="m-name">'+m.name+'</div>'+
      '<div class="m-desc">'+m.desc+'</div>'+
    '</button>';
  }).join('');

  var evs = [
    { id:'threshold',  name:I18N.t('用量预警'),        desc:I18N.t('达到阈值 ')+n.threshold+I18N.t('% 时提醒') },
    { id:'urgent',     name:I18N.t('用量紧急'),        desc:I18N.t('达到紧急线 ')+n.urgent+I18N.t('% 时提醒') },
    { id:'cookie_fail',name:I18N.t('Cookie 失效'),     desc:I18N.t('凭据过期立即提醒') },
    { id:'fetch_fail', name:I18N.t('抓取失败'),        desc:I18N.t('连续抓取失败提醒') }
  ];
  var evHtml = evs.map(function(e){
    return '<div class="ev-row">'+
      '<div><div class="ev-name">'+e.name+'</div><div class="ev-desc">'+e.desc+'</div></div>'+
      '<label class="switch"><input type="checkbox" class="sw-ev" data-ev="'+e.id+'" '+(ev[e.id]?'checked':'')+(disabled?' disabled':'')+'><span class="knob"></span></label>'+
    '</div>';
  }).join('');

  $('#notifyBody').innerHTML =
    I18N.t('<div class="set-group"><div class="set-title">通知方式</div><div class="method-grid">')+methodHtml+'</div></div>'+
    I18N.t('<div class="set-group"><div class="set-title">阈值</div>')+
      '<div class="card"><div class="threshold-row">'+
        I18N.t('<div class="num-row" style="flex:1"><label>预警阈值</label>')+
          '<input type="number" id="thNorm" min="1" max="100" value="'+(n.threshold!=null?n.threshold:80)+'" '+(disabled?'disabled':'')+'><span class="unit">%</span></div>'+
        I18N.t('<div class="num-row" style="flex:1"><label>紧急阈值</label>')+
          '<input type="number" id="thUrgent" min="1" max="100" value="'+(n.urgent!=null?n.urgent:95)+'" '+(disabled?'disabled':'')+'><span class="unit">%</span></div>'+
      '</div></div>'+
    '</div>'+
    I18N.t('<div class="set-group"><div class="set-title">事件开关</div>')+evHtml+'</div>'+
    '<div class="set-group" style="margin-bottom:0">'+
      '<button class="btn" id="btnTestNotify" '+(disabled?'disabled':'')+'>'+ICONS.bell+I18N.t('发送测试通知</button>')+
      I18N.t('<span style="font-size:10px;color:var(--muted);margin-left:10px">会立即触发一条通知验证链路</span>')+
    '</div>';

  $$('#notifyBody .method-card').forEach(function(card){
    card.addEventListener('click', function(){
      if(card.disabled) return;
      save(patchTop('notify', Object.assign({}, state.settings.notify, { method: card.dataset.method })));
    });
  });
  $$('#notifyBody .sw-ev').forEach(function(inp){
    inp.addEventListener('change', function(){
      var evs2 = Object.assign({}, (state.settings.notify||{}).events, {});
      evs2[inp.dataset.ev] = inp.checked;
      save(patchTop('notify', Object.assign({}, state.settings.notify, { events: evs2 })));
    });
  });
  var thN = $('#thNorm'), thU = $('#thUrgent');
  function saveThresholds(){
    var n2 = Object.assign({}, state.settings.notify, {});
    n2.threshold = parseInt(thN.value,10)||0;
    n2.urgent = parseInt(thU.value,10)||0;
    save(patchTop('notify', n2));
  }
  if(thN) thN.addEventListener('change', saveThresholds);
  if(thU) thU.addEventListener('change', saveThresholds);
  var btnTest = $('#btnTestNotify');
  if(btnTest) btnTest.addEventListener('click', async function(){
    try {
      await call('notify_test');
      toast(I18N.t('测试通知已发送'), 'ok');
    } catch(e){
      toast(I18N.t('发送失败: ')+e.message, 'err');
    }
  });
}

/* ================= 渲染：关于（静态，无需渲染） ================= */

/* ================= 顶栏 & 倒计时 ================= */
var RING_C = 2*Math.PI*11;
function updateCountdownUI(){
  var fg = $('#ringFg');
  if(!fg) return;
  var remain = state.countdown/state.autoRefreshSec;
  fg.style.strokeDasharray = RING_C;
  fg.style.strokeDashoffset = RING_C*(1-remain);
  $('#ringText').textContent = state.countdown;
}
function updateHeader(){
  var s = state.settings || {};
  var v = state.view || {};
  var t = v.fetched_at;
  var parts = [];
  if(isMock()) parts.push(I18N.t('示例数据'));
  else parts.push(I18N.t('实时'));
  if(t) parts.push(fmtClock(t));
  parts.push(I18N.t('每 ')+fmtInterval(v.refresh_interval_sec||s.refresh_interval_sec));
  $('#tbStatus').textContent = parts.join(' · ');

  var badge = $('#dataBadge');
  if(badge){
    if(isMock()){ badge.textContent = I18N.t('示例数据'); badge.className = 'badge'; }
    else { badge.textContent = I18N.t('实时数据'); badge.className = 'badge real'; }
  }
  if(s.density) document.body.setAttribute('data-density', s.density);
}

/* ================= 页面切换 ================= */
function renderCurrent(){
  if(state.page === 'dashboard') renderDashboard();
  else if(state.page === 'providers') renderProviders();
  else if(state.page === 'appearance') renderAppearance();
  else if(state.page === 'notify') renderNotify();
}
function renderAll(){
  try {
    renderDashboard();
    renderProviders();
    renderAppearance();
    renderNotify();
    updateHeader();
  } catch(e){
    toast(I18N.t('渲染异常: ')+e.message, 'err');
  }
}

/* 语言切换：国旗按钮 + 持久化 ui.lang */
function bindLangSwitch(){
  var btns = $$('#langSwitch .lang-btn');
  btns.forEach(function(btn){
    if(btn.dataset.lang === I18N.getLang()) btn.classList.add('active');
    btn.addEventListener('click', function(){
      var l = btn.dataset.lang;
      if(l === I18N.getLang()) return;
      I18N.setLang(l);
      btns.forEach(function(b){ b.classList.toggle('active', b.dataset.lang === l); });
      state.settings.ui = state.settings.ui || {};
      state.settings.ui.lang = l;
      /* 立即生效（不依赖保存成功）；保存失败也不阻断切换 */
      renderAll();
      I18N.apply();
      save(patchTop('ui', state.settings.ui)).catch(function(){});
    });
  });
}

/* ================= 初始化 ================= */
async function init(){
  /* 语言初始化（首次渲染前生效） */
  I18N.setLang((state.settings.ui || {}).lang);
  /* 初始布局 + mock 渲染 */
  document.body.setAttribute('data-density', state.settings.density || 'compact');
  applyStyleAttr();
  applyBgOpacity();
  updateCountdownUI();
  renderAll();
  I18N.apply();

  /* 导航 */
  $$('#nav .nav-item').forEach(function(btn){
    btn.addEventListener('click', function(){
      $$('#nav .nav-item').forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      state.page = btn.dataset.page;
      $$('.page').forEach(function(p){
        p.classList.toggle('active', p.id === 'page-'+state.page);
      });
      renderCurrent();
    });
  });

  /* 语言切换 */
  bindLangSwitch();

  /* 手动刷新 */
  $('#btnRefresh').addEventListener('click', manualRefresh);

  /* 关闭 = 隐藏到托盘 */
  $('#btnClose').addEventListener('click', async function(){
    try {
      await call('hide_window');
    } catch(e){
      toast(I18N.t('隐藏失败: ')+e.message, 'err');
    }
  });

  /* 关于页：重看开屏引导 */
  $('#btnReplayGuide').addEventListener('click', function(){
    call('replay_guide').then(function(res){
      if(res && res.url){ location.href = res.url; }
      else { location.href = 'index.html?guide=1'; }
    }).catch(function(){ location.href = 'index.html?guide=1'; });
  });

  /* 添加供应商 */
  $('#btnAddProvider').addEventListener('click', function(){
    if($('#addProviderPanel').style.display === 'none'){
      openAddProvider();
    } else {
      closeAddProvider();
    }
  });
  $('#apSave').addEventListener('click', saveAddProvider);
  $('#apCancel').addEventListener('click', closeAddProvider);

  /* 连接后端 */
  try {
    await fetchView();
  } catch(e){
    toast(I18N.t('后端未连接，当前展示示例数据'), 'warn');
    state.mode = 'mock';
    renderAll();
  }

  /* pywebview API 注入晚于 DOMContentLoaded：就绪后再拉一次真实数据 */
  window.addEventListener('pywebviewready', function(){
    fetchView().catch(function(){});
  });

  /* 30 秒自动刷新 */
  setInterval(function(){
    state.countdown--;
    if(state.countdown <= 0){
      state.countdown = state.autoRefreshSec;
      refreshView();
    }
    updateCountdownUI();
  }, 1000);
}

document.addEventListener('DOMContentLoaded', init);

  /* 测试接口：暴露渲染函数与状态（evaluate_js 可测，不参与业务） */
  window.__app = {
    state: state,
    renderAll: renderAll,
    renderDashboard: renderDashboard,
    renderAppearance: renderAppearance,
    dashCardHtml: dashCardHtml,
    balanceCardHtml: balanceCardHtml,
    todayText: todayText,
    speedChips: speedChips,
    fmtTokens: fmtTokens,
    isPeakNow: isPeakNow,
    fetchView: fetchView,
  };
})();
