# JP_PRODUCT_DATE_AI_V1.1.py
import os
import json
import re
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ==========================================
# 1. 项目文件内容定义 (HTML, CSS, JS, JSON)
# ==========================================

HTML_INDEX = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>JP Product Date AI</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <!-- 顶部状态栏 -->
    <header class="top-bar">
        <div class="settings-btn" onclick="alert('设置页面开发中...')">⚙️</div>
    </header>

    <!-- 试用状态卡片 -->
    <div class="card trial-card" onclick="alert('V1.1当前为免费试用版，功能完全开放！')">
        <div class="trial-left">⏱ <span id="trial-text">试用查询可用 (剩余<span id="trial-count">20</span>次)</span></div>
        <div class="trial-right">解锁无限查询 ＞</div>
    </div>

    <!-- 核心查询卡片 -->
    <div class="card query-card">
        <div class="brand-select-row" onclick="openBrandModal()">
            <span id="selected-brand-name" class="placeholder-text">选择品牌</span>
            <span class="arrow">＞</span>
        </div>
        <div class="divider"></div>
        <div class="input-row">
            <input type="text" id="batch-input" placeholder="请输入批号 (如 F6, 240601)" oninput="validateInput()">
        </div>
        <button id="query-btn" class="btn-primary" disabled onclick="executeQuery()">查 询</button>
    </div>

    <!-- 结果区域 (默认隐藏) -->
    <div id="result-container" class="card result-card" style="display: none;">
        <!-- 结果动态填充 -->
    </div>

    <!-- 最近记录 -->
    <div class="section-title">最近记录</div>
    <div id="recent-history-list"></div>

    <!-- 品牌选择弹窗 -->
    <div id="brand-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <input type="text" id="brand-search" placeholder="搜索品牌 (中文/英文/日文)" oninput="filterBrands()">
                <span class="close-btn" onclick="closeBrandModal()">取消</span>
            </div>
            <div class="brand-categories">
                <span class="cat-chip active" onclick="setCategory('全部')">全部</span>
                <span class="cat-chip" onclick="setCategory('化妆品')">化妆品</span>
                <span class="cat-chip" onclick="setCategory('日用品')">日用品</span>
                <span class="cat-chip" onclick="setCategory('食品')">食品</span>
                <span class="cat-chip" onclick="setCategory('药品')">药品</span>
            </div>
            <div id="brand-list" class="brand-list"></div>
        </div>
    </div>

    <!-- 底部导航 -->
    <nav class="bottom-nav">
        <div class="nav-item active">
            <div class="nav-icon">🔎</div>
            <div>查询</div>
        </div>
        <div class="nav-item" onclick="alert('收藏功能将在 V1.2 上线')">
            <div class="nav-icon">▣</div>
            <div>收藏</div>
        </div>
        <div class="nav-item" onclick="alert('完整历史页面将在 V1.2 上线，当前请看首页最近记录')">
            <div class="nav-icon">◷</div>
            <div>历史</div>
        </div>
    </nav>

    <script src="/js/app.js"></script>
</body>
</html>
"""

CSS_STYLE = """
:root {
    --bg-color: #F5F7F6;
    --card-bg: #FFFFFF;
    --primary-color: #20B2AA; /* 青绿色 */
    --primary-dark: #1A938C;
    --text-main: #333333;
    --text-sub: #888888;
    --border-color: #EEEEEE;
    --radius-lg: 20px;
    --radius-md: 12px;
}
* { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, sans-serif; }
body { margin: 0; padding: 0; background-color: var(--bg-color); color: var(--text-main); padding-bottom: 80px; }
/* Mobile First Layout */
html { display: flex; justify-content: center; }
body { width: 100%; max-width: 500px; min-height: 100vh; position: relative; background: var(--bg-color); }

.top-bar { padding: 15px 20px; display: flex; justify-content: flex-start; font-size: 20px; color: var(--text-sub); }
.card { background: var(--card-bg); border-radius: var(--radius-lg); padding: 20px; margin: 0 20px 20px 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); }

.trial-card { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; cursor: pointer; }
.trial-left { font-weight: 600; font-size: 14px; }
.trial-right { font-size: 13px; color: var(--primary-color); font-weight: 600; }

.query-card { padding: 0; display: flex; flex-direction: column; overflow: hidden; }
.brand-select-row { padding: 20px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; font-size: 16px; font-weight: 500; }
.placeholder-text { color: var(--text-sub); }
.brand-selected-text { color: var(--text-main); font-weight: bold; }
.arrow { color: #CCCCCC; }
.divider { height: 1px; background: var(--border-color); margin: 0 20px; }
.input-row { padding: 20px; }
.input-row input { width: 100%; border: none; font-size: 16px; outline: none; }
.input-row input::placeholder { color: #CCCCCC; }
.btn-primary { background: var(--primary-color); color: white; border: none; padding: 16px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; }
.btn-primary:disabled { background: #E0E0E0; color: #AAAAAA; cursor: not-allowed; }

.section-title { margin: 10px 20px; font-size: 14px; color: var(--text-sub); font-weight: bold; }
.history-item { display: flex; flex-direction: column; background: var(--card-bg); border-radius: var(--radius-md); padding: 15px 20px; margin: 0 20px 10px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.history-top { display: flex; justify-content: space-between; margin-bottom: 8px; font-weight: bold; }
.history-bottom { font-size: 13px; color: var(--text-sub); line-height: 1.5; }

.result-card { border-left: 4px solid var(--primary-color); }
.res-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; }
.res-row { margin-bottom: 8px; font-size: 15px; }
.res-row span.label { color: var(--text-sub); display: inline-block; width: 80px; }
.res-row span.val { font-weight: 500; }
.confidence-high { color: var(--primary-color); }
.confidence-warn { color: #F59E0B; }
.confidence-err { color: #EF4444; }

.modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); z-index: 100; justify-content: center; align-items: flex-end; }
.modal-content { background: var(--bg-color); width: 100%; max-width: 500px; height: 85vh; border-radius: 20px 20px 0 0; display: flex; flex-direction: column; }
.modal-header { padding: 15px 20px; display: flex; gap: 10px; background: white; border-radius: 20px 20px 0 0; align-items: center; }
.modal-header input { flex: 1; padding: 10px 15px; border-radius: 20px; border: 1px solid var(--border-color); outline: none; background: #F9F9F9; }
.close-btn { color: var(--primary-color); font-weight: bold; cursor: pointer; }
.brand-categories { display: flex; gap: 10px; padding: 10px 20px; overflow-x: auto; background: white; border-bottom: 1px solid var(--border-color); }
.cat-chip { padding: 5px 12px; border-radius: 15px; font-size: 13px; background: #F0F0F0; color: var(--text-sub); white-space: nowrap; cursor: pointer; }
.cat-chip.active { background: var(--primary-color); color: white; }
.brand-list { flex: 1; overflow-y: auto; padding: 10px 20px; }
.brand-item { padding: 15px 0; border-bottom: 1px solid var(--border-color); font-size: 15px; cursor: pointer; display: flex; justify-content: space-between; }

.bottom-nav { position: fixed; bottom: 0; width: 100%; max-width: 500px; height: 65px; background: white; display: flex; justify-content: space-around; align-items: center; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); }
.nav-item { display: flex; flex-direction: column; align-items: center; font-size: 11px; color: #AAAAAA; cursor: pointer; }
.nav-item.active { color: var(--primary-color); }
.nav-icon { font-size: 22px; margin-bottom: 2px; }
"""

JS_APP = """
let currentBrand = null;
let brandsData = [];
let historyData = JSON.parse(localStorage.getItem('jp_query_history') || '[]');
// 1. 初始化试用次数（如果为0或者在调试阶段，点击试用卡片可以直接重置为999次）
let trialCount = parseInt(localStorage.getItem('jp_trial_count') || '999');
document.getElementById('trial-count').innerText = trialCount;

// 点击顶部试用卡片即可一键重置调试次数
document.querySelector('.trial-card').onclick = function() {
    trialCount = 999;
    localStorage.setItem('jp_trial_count', trialCount);
    document.getElementById('trial-count').innerText = trialCount;
    alert('已重置调试查询次数为 999 次！');
};

renderHistory();

// 获取品牌数据
fetch('/api/brands').then(r => r.json()).then(data => { brandsData = data; renderBrandList(data); });

function openBrandModal() { document.getElementById('brand-modal').style.display = 'flex'; }
function closeBrandModal() { document.getElementById('brand-modal').style.display = 'none'; }

function renderBrandList(list) {
    const container = document.getElementById('brand-list');
    container.innerHTML = '';
    list.forEach(b => {
        const div = document.createElement('div');
        div.className = 'brand-item';
        div.innerHTML = `<span>${b.name}</span> <span style="color:#aaa; font-size:12px;">${b.category}</span>`;
        div.onclick = () => selectBrand(b);
        container.appendChild(div);
    });
}

function selectBrand(brand) {
    currentBrand = brand;
    const label = document.getElementById('selected-brand-name');
    label.innerText = brand.name;
    label.className = 'brand-selected-text';
    validateInput();
    closeBrandModal();
}

function filterBrands() {
    const q = document.getElementById('brand-search').value.toLowerCase();
    const filtered = brandsData.filter(b => b.name.toLowerCase().includes(q) || b.aliases.some(a => a.toLowerCase().includes(q)));
    renderBrandList(filtered);
}

function setCategory(cat) {
    document.querySelectorAll('.cat-chip').forEach(el => el.classList.remove('active'));
    event.target.classList.add('active');
    if (cat === '全部') { renderBrandList(brandsData); } 
    else { renderBrandList(brandsData.filter(b => b.category === cat)); }
}

function validateInput() {
    const batch = document.getElementById('batch-input').value.trim();
    document.getElementById('query-btn').disabled = !(currentBrand && batch.length > 0);
}

async function executeQuery() {
    if (trialCount <= 0) { alert('试用次数已用完，请解锁无限查询！'); return; }
    
    const batchInput = document.getElementById('batch-input').value.trim();
    const btn = document.getElementById('query-btn');
    btn.innerText = "正在解析批号...";
    btn.disabled = true;

    try {
        const res = await fetch('/api/query', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ brand_id: currentBrand.id, batch_code: batchInput })
        });
        const data = await res.json();
        
        trialCount--;
        localStorage.setItem('jp_trial_count', trialCount);
        document.getElementById('trial-count').innerText = trialCount;
        
        saveHistory(data);
        showResult(data);
        renderHistory();
        
    } catch (err) {
        alert("网络或服务错误");
    } finally {
        btn.innerText = "查 询";
        btn.disabled = false;
    }
}

// 2. 优化结果展示卡片：更名为“预测生产日期”，隐藏规则行，展示最新日期与到期日期
function showResult(data) {
    const rc = document.getElementById('result-container');
    rc.style.display = 'block';
    
    let dateHtml = '';
    // 优先显示生产日期或最新的预测生产日期
    const displayDate = data.production_date || (data.candidate_dates && data.candidate_dates.length > 0 ? data.candidate_dates[0] : null);
    
    if (displayDate) {
        dateHtml = `<div class="res-row"><span class="label">预测生产日期:</span> <span class="val" style="color: #20B2AA; font-weight: bold;">${displayDate}</span></div>`;
    } else {
        dateHtml = `<div class="res-row"><span class="label">生产日期:</span> <span class="val confidence-err">无法可靠确定</span></div>`;
    }

    let expHtml = data.expiry_date ? `<div class="res-row"><span class="label">参考到期:</span> <span class="val">${data.expiry_date}</span></div>` : '';
    let confColor = data.confidence === 'E' ? 'confidence-err' : (data.confidence === 'A' || data.confidence === 'S' ? 'confidence-high' : 'confidence-warn');
    
    rc.innerHTML = `
        <div class="res-title">查询结果</div>
        <div class="res-row"><span class="label">品牌:</span> <span class="val">${data.brand_name}</span></div>
        <div class="res-row"><span class="label">批号:</span> <span class="val">${data.normalized_batch}</span></div>
        ${dateHtml}
        ${expHtml}
        <div class="res-row"><span class="label">可信度:</span> <span class="val ${confColor}">级别 ${data.confidence} (${data.source})</span></div>
    `;
}

function saveHistory(data) {
    historyData.unshift({
        brand_name: data.brand_name,
        batch: data.original_batch,
        date: data.candidate_dates ? data.candidate_dates.join(' / ') : (data.production_date || '无法确定'),
        time: new Date().toISOString().substring(0, 10)
    });
    if (historyData.length > 10) historyData.pop();
    localStorage.setItem('jp_query_history', JSON.stringify(historyData));
}

function renderHistory() {
    const hl = document.getElementById('recent-history-list');
    hl.innerHTML = '';
    if (historyData.length === 0) {
        hl.innerHTML = '<div style="text-align:center; color:#aaa; font-size:13px; margin-top:20px;">暂无查询记录</div>';
        return;
    }
    historyData.forEach(item => {
        hl.innerHTML += `
            <div class="history-item">
                <div class="history-top"><span>${item.batch}</span> <span>${item.brand_name}</span></div>
                <div class="history-bottom">生产：${item.date}</div>
            </div>
        `;
    });
}

// 注册PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js'); });
}
"""

JSON_BRANDS = """[
    {"id": "dhc", "name": "DHC 蝶翠诗", "category": "化妆品", "aliases": ["dhc", "蝶翠诗"]},
    {"id": "shiseido", "name": "SHISEIDO / 资生堂", "category": "化妆品", "aliases": ["shiseido", "资生堂", "資生堂"]},
    {"id": "kose", "name": "KOSÉ / 高丝", "category": "化妆品", "aliases": ["kose", "高丝", "コーセー"]},
    {"id": "kao", "name": "KAO / 花王", "category": "日用品", "aliases": ["kao", "花王"]},
    {"id": "meiji", "name": "明治 Meiji", "category": "食品", "aliases": ["meiji", "明治"]}
]"""

JSON_RULES = """[
    {
        "brand_id": "dhc",
        "name": "字母月份 + 年份末位",
        "pattern": "^([A-Za-z])(\\\\d)[A-Za-z0-9]*$",
        "decode_type": "letter_month_digit_year",
        "month_letters": "ABCDEFGHJKLMNPQRSTUVWXY",
        "shelf_life_months": 36,
        "confidence": "A",
        "verified": true,
        "source": "历史经验推测，多方验证"
    },
    {
        "brand_id": "shiseido",
        "name": "多体系规则，暂未验证",
        "pattern": ".*",
        "decode_type": "unverified",
        "shelf_life_months": 36,
        "confidence": "E",
        "verified": false,
        "source": "系统暂未收录该品牌可靠批号规则"
    }
]"""

MANIFEST_JSON = """{
  "name": "JP Date AI",
  "short_name": "JP Date",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#F5F7F6",
  "theme_color": "#20B2AA",
  "icons": []
}"""

SW_JS = """
self.addEventListener('install', (e) => { e.waitUntil(caches.open('jp-date-v1').then((c) => c.addAll(['/', '/css/style.css', '/js/app.js']))); });
self.addEventListener('fetch', (e) => { e.respondWith(caches.match(e.request).then((res) => res || fetch(e.request))); });
"""

# ==========================================
# 2. 自动生成目录结构函数
# ==========================================
def setup_project():
    base_dir = "jp_product_date_ai_v1_1_web"
    os.makedirs(os.path.join(base_dir, "static/css"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "static/js"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)

    files = {
        "static/index.html": HTML_INDEX,
        "static/css/style.css": CSS_STYLE,
        "static/js/app.js": JS_APP,
        "static/manifest.json": MANIFEST_JSON,
        "static/sw.js": SW_JS,
        "data/brands.json": JSON_BRANDS,
        "data/rules.json": JSON_RULES
    }

    for path, content in files.items():
        file_path = os.path.join(base_dir, path)
        # ⚠️ 确保加上这句：如果已经存在且是 data 目录下的 json，不覆盖！
        if os.path.exists(file_path) and "data" in path:
            continue
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    return base_dir

# ==========================================
# 3. FastAPI 后端与规则引擎引擎
# ==========================================
app = FastAPI()

class QueryRequest(BaseModel):
    brand_id: str
    batch_code: str

# 内存缓存数据
BRANDS_DATA = []
RULES_DATA = []

@app.on_event("startup")
def load_data():
    global BRANDS_DATA, RULES_DATA
    base_dir = "jp_product_date_ai_v1_1_web"
    with open(os.path.join(base_dir, "data/brands.json"), "r", encoding="utf-8") as f:
        BRANDS_DATA = json.load(f)
    with open(os.path.join(base_dir, "data/rules.json"), "r", encoding="utf-8") as f:
        RULES_DATA = json.load(f)

@app.get("/api/brands")
def get_brands():
    return BRANDS_DATA

@app.post("/api/query")
def process_query(req: QueryRequest):
    batch = req.batch_code.strip().upper()
    brand_id = req.brand_id

    brand_info = next((b for b in BRANDS_DATA if b["id"] == brand_id), None)
    if not brand_info:
        return {"confidence": "E", "source": "错误", "rule_name": "未知品牌", "production_date": None}

    # 寻找匹配规则 (优先选择已验证 verified=True)
    matched_rule = None
    for rule in RULES_DATA:
        if rule["brand_id"] == brand_id and re.match(rule["pattern"], batch):
            if rule.get("verified", False):
                matched_rule = rule
                break
            elif matched_rule is None:
                matched_rule = rule

    # 绝对禁止AI瞎猜：未收录或未验证
    if not matched_rule or matched_rule.get("decode_type") == "unverified" or not matched_rule.get("verified", False):
        return {
            "success": True,
            "brand_name": brand_info["name"],
            "original_batch": req.batch_code,
            "normalized_batch": batch,
            "production_date": None,
            "candidate_dates": None,
            "expiry_date": None,
            "rule_name": "暂未收录该批号可靠规则" if not matched_rule else matched_rule["name"],
            "confidence": "E",
            "source": matched_rule["source"] if matched_rule else "数据库暂无对应规则，无法可靠确定生产日期"
        }

    decode_type = matched_rule["decode_type"]
    prod_date = None
    candidates = None  # 👈 补充初始化，避免未定义报错
    curr_year = datetime.now().year
    base_decade = (curr_year // 10) * 10
    from datetime import timedelta

    # 1. DHC 字母月份 + 年份末位 (如 F6)
    if decode_type == "letter_month_digit_year":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            m_char = match.group(1).upper()
            y_char = int(match.group(2))
            month_letters = matched_rule.get("month_letters", "ABCDEFGHJKLMNPQRSTUVWXY")
            if m_char in month_letters:
                month = month_letters.index(m_char) + 1
                y = base_decade + y_char
                if y > curr_year + 1:
                    y -= 10
                prod_date = f"{y}-{month:02d}"

    # 2. 高丝/奥尔滨/黛珂系 (修正最新轮替表：C=2022, D=2023, E=2024, F=2025, G=2026, H=2027...)
    elif decode_type == "japanese_letter_year_month":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            y_char = match.group(1).upper()
            m_char = match.group(2).upper()
            year_map = matched_rule.get("year_mapping", {})
            month_map = matched_rule.get("month_mapping", {})
            
            month = None
            if m_char.isdigit() and 1 <= int(m_char) <= 12:
                month = int(m_char)
            elif m_char in month_map:
                month = month_map[m_char]
                
            if y_char in year_map and month:
                year = year_map[y_char]
                prod_date = f"{year}-{month:02d}"

    # 3. 近江兄弟 (OMI Brotherhood) - 支持 CFF10J (首位年字母+次位月字母) 及 4位数字儒略日
    elif decode_type == "omi_standard":
        # 匹配模式 A: 纯字母开头 (如 CFF10J -> C=2026, F=6月)
        match_letter = re.match(r"^([A-Za-z])([A-Za-z])[A-Za-z0-9]*$", batch)
        # 匹配模式 B: 数字开头 (如 6185 -> 2026年第185天)
        match_digit = re.match(r"^(\d)(\d{3})[A-Za-z0-9]*$", batch)

        if match_letter:
            y_char = match_letter.group(1).upper()
            m_char = match_letter.group(2).upper()
            year_map = matched_rule.get("year_mapping", {})
            month_map = matched_rule.get("month_mapping", {})
            if y_char in year_map and m_char in month_map:
                year = year_map[y_char]
                month = month_map[m_char]
                prod_date = f"{year}-{month:02d}"

        elif match_digit:
            y_char = int(match_digit.group(1))
            days = int(match_digit.group(2))
            if 1 <= days <= 366:
                y = base_decade + y_char
                if y > curr_year + 1:
                    y -= 10
                try:
                    d = datetime(y, 1, 1) + timedelta(days=days - 1)
                    prod_date = d.strftime("%Y-%m-%d")
                except:
                    pass

    # 4. FANCL / HABA / 直标年月日
    elif decode_type == "direct_date_ymd":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            raw_str = "".join(match.groups())
            if len(raw_str) == 8:
                y, m, d = int(raw_str[0:4]), int(raw_str[4:6]), int(raw_str[6:8])
            elif len(raw_str) == 6:
                y, m, d = 2000 + int(raw_str[0:2]), int(raw_str[2:4]), int(raw_str[4:6])
            try:
                dt = datetime(y, m, d)
                prod_date = dt.strftime("%Y-%m-%d")
            except:
                pass

    # 5. 雅诗兰黛 3位码 (如 A53)
    elif decode_type == "estee_lauder_3_digit":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            m_char = match.group(2).upper()
            y_char = int(match.group(3))
            month_map = matched_rule.get("month_mapping", {"A":10, "B":11, "C":12})
            month = int(m_char) if m_char.isdigit() else month_map.get(m_char)
            if month:
                y = base_decade + y_char
                if y > curr_year + 1:
                    y -= 10
                prod_date = f"{y}-{month:02d}"

    # 6. Kracie / 肌美精 混编码 (如 71BH2)
    elif decode_type == "kracie_mix_code":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            y_char = int(match.group(1))
            y = base_decade + y_char
            if y > curr_year + 1:
                y -= 10
            prod_date = f"{y}年"

    # 7. Kissme / 井田体系 (如 7A1)
    elif decode_type == "digit_year_letter_month":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            y_char = int(match.group(1))
            m_char = match.group(2).upper()
            month_map = matched_rule.get("month_mapping", {"A":1,"B":2,"C":3,"D":4,"E":5,"F":6,"G":7,"H":8,"I":9,"J":10,"K":11,"L":12})
            month = month_map.get(m_char)
            if month:
                y = base_decade + y_char
                if y > curr_year + 1:
                    y -= 10
                prod_date = f"{y}-{month:02d}"

    # 8. Rosette / 露姬婷 多产线体系 (支持 FB18A 字母年+字母月+日期，以及 6A12 数字年体系)
    elif decode_type == "rosette_standard":
        match_letter = re.match(r"^([A-Za-z])([A-Za-z])(\d{1,2})[A-Za-z0-9]*$", batch)
        match_digit = re.match(r"^(\d)([A-Za-z0-9])[A-Za-z0-9]*$", batch)
        
        year_map = matched_rule.get("year_mapping", {})
        month_map = matched_rule.get("month_mapping", {})

        if match_letter:
            y_char = match_letter.group(1).upper()
            m_char = match_letter.group(2).upper()
            day_str = match_letter.group(3)
            
            if y_char in year_map and m_char in month_map:
                year = year_map[y_char]
                month = month_map[m_char]
                day = int(day_str)
                if 1 <= day <= 31:
                    prod_date = f"{year}-{month:02d}-{day:02d}"
                else:
                    prod_date = f"{year}-{month:02d}"

        elif match_digit:
            y_char = int(match_digit.group(1))
            m_char = match_digit.group(2).upper()
            y = base_decade + y_char
            if y > curr_year + 1:
                y -= 10
            month = int(m_char) if m_char.isdigit() else month_map.get(m_char)
            if month:
                prod_date = f"{y}-{month:02d}"

    # 9. LVMH 体系 (Christian Dior 迪奥等: 4位码 如 3A01 -> 2023年1月01日)
    elif decode_type == "lvmh_4digit":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            y_char = int(match.group(1))
            m_char = match.group(2).upper()
            day_str = match.group(3)
            # LVMH 月份表: A-M (跳过I) 对应 1-12月
            lvmh_months = "ABCDEFGHJKLMN"
            if m_char in lvmh_months:
                month = lvmh_months.index(m_char) + 1
                y = base_decade + y_char
                if y > curr_year + 1:
                    y -= 10
                if day_str and 1 <= int(day_str) <= 31:
                    prod_date = f"{y}-{month:02d}-{int(day_str):02d}"
                else:
                    prod_date = f"{y}-{month:02d}"

    # 10. Chanel (香奈儿) 4位基准月递增码 (如 8101)
    elif decode_type == "chanel_4digit":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            code_num = int(match.group(1))
            # Chanel 以 2010年1月=1301 为基准递增计算
            months_diff = code_num - 1301
            base_dt = datetime(2010, 1, 1)
            target_year = 2010 + (months_diff // 12)
            target_month = (months_diff % 12) + 1
            if 2015 <= target_year <= curr_year + 2 and 1 <= target_month <= 12:
                prod_date = f"{target_year}-{target_month:02d}"

    # LVMH 体系 (Guerlain 娇兰, Givenchy 纪梵希, Make Up For Ever, Benefit, Fresh 等)
    elif decode_type == "lvmh_4digit":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            y_char = int(match.group(1))
            m_char = match.group(2).upper()
            day_str = match.group(3) if len(match.groups()) >= 3 else None
            lvmh_months = "ABCDEFGHJKLMN"
            if m_char in lvmh_months:
                month = lvmh_months.index(m_char) + 1
                y = base_decade + y_char
                if y > curr_year + 1:
                    y -= 10
                if day_str and day_str.isdigit() and 1 <= int(day_str) <= 31:
                    prod_date = f"{y}-{month:02d}-{int(day_str):02d}"
                else:
                    prod_date = f"{y}-{month:02d}"

    # Clarins 娇韵诗 / Sisley 希思黎 (6位前两位年码 如 230501)
    elif decode_type == "clarins_6digit":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            y_part = int(match.group(1))
            m_part = int(match.group(2))
            if 1 <= m_part <= 12:
                y = 2000 + y_part if y_part < 100 else y_part
                prod_date = f"{y}-{m_part:02d}"

    # 3. YDDD 儒略日体系 (8X4、花王、资生堂、SK-II等，如 3185 -> 2023年第185天)
    elif decode_type == "julian_date_yddd":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            y_char = int(match.group(1))
            days = int(match.group(2))
            if 1 <= days <= 366:
                # 寻找最接近当前年份的合理年份
                y = base_decade + y_char
                if y > curr_year:  # 如果算出来大于当前年份，取上一个10年周期
                    y -= 10
                try:
                    target_date = datetime(y, 1, 1) + timedelta(days=days - 1)
                    prod_date = target_date.strftime("%Y-%m-%d")
                except Exception as e:
                    prod_date = f"{y}年"

    # 皮尔法伯体系 (Pierre Fabre: A-Derma, 雅漾等，如 AV123 -> 第3位数字年 3=2023, 第4-5位月 12月)
    elif decode_type == "pierre_fabre_standard":
        match = re.match(r"^[A-Za-z]{2}(\d)(\d{2})[A-Za-z0-9]*$", batch)
        if match:
            y_char = int(match.group(1))
            m_part = int(match.group(2))
            if 1 <= m_part <= 12:
                y = base_decade + y_char
                if y > curr_year:
                    y -= 10
                prod_date = f"{y}-{m_part:02d}"

    # 富士胶片体系 (Astalift 艾诗缇: 6位码 如 230601 或 YDDD)
    elif decode_type == "astalift_fujifilm":
        if re.match(r"^\d{6}$", batch):
            y_part = int(batch[:2])
            m_part = int(batch[2:4])
            if 1 <= m_part <= 12:
                y = 2000 + y_part if y_part < 100 else y_part
                prod_date = f"{y}-{m_part:02d}"
        else:
            match = re.match(r"^(\d)(\d{3})[A-Za-z0-9]*$", batch)
            if match:
                y_char = int(match.group(1))
                days = int(match.group(2))
                if 1 <= days <= 366:
                    y = base_decade + y_char
                    if y > curr_year:
                        y -= 10
                    try:
                        d = datetime(y, 1, 1) + timedelta(days=days - 1)
                        prod_date = d.strftime("%Y-%m-%d")
                    except:
                        pass

    # 9. 嘉娜宝 / KATE 倒序儒略日 (如 2143)
    elif decode_type == "kanebo_reverse_julian":
        match = re.match(matched_rule["pattern"], batch)
        if match:
            days = int(match.group(1))
            y_char = int(match.group(2))
            if 1 <= days <= 366:
                y = base_decade + y_char
                if y > curr_year + 1:
                    y -= 10
                try:
                    d = datetime(y, 1, 1) + timedelta(days=days - 1)
                    prod_date = d.strftime("%Y-%m-%d")
                except:
                    pass

    # 自动计算参考到期日期 (未开封默认 + shelf_life_months，通常为36个月)
    exp_date = None
    shelf_life = matched_rule.get("shelf_life_months", 36)
    if prod_date and shelf_life and "-" in prod_date:
        try:
            parts = prod_date.split("-")
            py = int(parts[0])
            pm = int(parts[1])
            ey = py + (pm + shelf_life - 1) // 12
            em = (pm + shelf_life - 1) % 12 + 1
            if len(parts) == 3:
                exp_date = f"{ey}-{em:02d}-{parts[2]}"
            else:
                exp_date = f"{ey}-{em:02d}"
        except:
            pass

    return {
        "success": True,
        "brand_name": brand_info["name"],
        "original_batch": req.batch_code,
        "normalized_batch": batch,
        "production_date": prod_date,
        "candidate_dates": candidates,
        "expiry_date": exp_date,
        "rule_name": matched_rule["name"],
        "confidence": matched_rule["confidence"],
        "source": matched_rule["source"]
    }

# 动态挂载生成的静态文件
@app.get("/")
def serve_index():
    with open("jp_product_date_ai_v1_1_web/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    # 1. 自动生成前端与数据文件
    base_dir = setup_project()
    print(f"✅ 项目文件已生成至目录: {os.path.abspath(base_dir)}")
    
    # 挂载静态资源（供浏览器读取CSS/JS等）
    app.mount("/", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

    # 2. 启动服务
    print("🚀 正在启动服务，请在浏览器访问: http://127.0.0.1:8000")
    print("📱 手机访问：确保手机与电脑在同一Wi-Fi，访问 http://<你的电脑局域网IP>:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)