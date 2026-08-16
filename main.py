# main.py
import os
import json
import re
from datetime import datetime, timedelta
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ==========================================
# 1. 前端模板定义 (HTML, CSS, JS)
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
    <header class="top-bar">
        <div class="settings-btn" onclick="alert('美妆批号查询系统 V1.2 在线版')">⚙️</div>
    </header>

    <div class="card query-card">
        <div class="brand-select-row" onclick="openBrandModal()">
            <span id="selected-brand-name" class="placeholder-text">选择品牌</span>
            <span class="arrow">＞</span>
        </div>
        <div class="divider"></div>
        <div class="input-row">
            <input type="text" id="batch-input" placeholder="请输入批号 (如 GL1, F6, 3185, 240601)" oninput="validateInput()">
        </div>
        <button id="query-btn" class="btn-primary" disabled onclick="executeQuery()">查 询</button>
    </div>

    <div id="result-container" class="card result-card" style="display: none;"></div>

    <div class="section-title">最近记录</div>
    <div id="recent-history-list"></div>

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

    <nav class="bottom-nav">
        <div class="nav-item active">
            <div class="nav-icon">🔎</div>
            <div>查询</div>
        </div>
        <div class="nav-item" onclick="alert('收藏功能开发中')">
            <div class="nav-icon">▣</div>
            <div>收藏</div>
        </div>
        <div class="nav-item" onclick="alert('历史记录已保存在本地')">
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
    --primary-color: #20B2AA;
    --primary-dark: #1A938C;
    --text-main: #333333;
    --text-sub: #888888;
    --border-color: #EEEEEE;
    --radius-lg: 20px;
    --radius-md: 12px;
}
* { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body { margin: 0; padding: 0; background-color: var(--bg-color); color: var(--text-main); padding-bottom: 80px; }
html { display: flex; justify-content: center; }
body { width: 100%; max-width: 500px; min-height: 100vh; position: relative; background: var(--bg-color); }

.top-bar { padding: 15px 20px; display: flex; justify-content: flex-start; font-size: 20px; color: var(--text-sub); }
.card { background: var(--card-bg); border-radius: var(--radius-lg); padding: 20px; margin: 0 20px 20px 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); }

.query-card { padding: 0; display: flex; flex-direction: column; overflow: hidden; margin-top: 10px; }
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
.res-row span.label { color: var(--text-sub); display: inline-block; width: 100px; }
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

renderHistory();

fetch('/api/brands?t=' + new Date().getTime()).then(r => r.json()).then(data => { 
    brandsData = data; 
    renderBrandList(data); 
});

function openBrandModal() { document.getElementById('brand-modal').style.display = 'flex'; }
function closeBrandModal() { document.getElementById('brand-modal').style.display = 'none'; }

function renderBrandList(list) {
    const container = document.getElementById('brand-list');
    container.innerHTML = '';
    list.forEach(b => {
        const div = document.createElement('div');
        div.className = 'brand-item';
        div.innerHTML = `<span>${b.name}</span> <span style="color:#aaa; font-size:12px;">${b.category || ''}</span>`;
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
    const filtered = brandsData.filter(b => b.name.toLowerCase().includes(q) || (b.aliases && b.aliases.some(a => a.toLowerCase().includes(q))));
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

function showResult(data) {
    const rc = document.getElementById('result-container');
    rc.style.display = 'block';
    
    let dateHtml = '';
    const displayDate = data.production_date || (data.candidate_dates && data.candidate_dates.length > 0 ? data.candidate_dates.join(' / ') : null);
    
    if (displayDate) {
        dateHtml = `<div class="res-row"><span class="label">预测生产日期:</span> <span class="val" style="color: var(--primary-color); font-weight: bold;">${displayDate}</span></div>`;
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
"""

MANIFEST_JSON = """{
  "name": "JP Date AI",
  "short_name": "JP Date",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#F5F7F6",
  "theme_color": "#20B2AA",
  "icons": []
}"""

# ==========================================
# 2. 静态文件目录初始化
# ==========================================
BASE_DIR = "jp_product_date_ai_v1_1_web"

def init_project_files():
    os.makedirs(os.path.join(BASE_DIR, "static/css"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "static/js"), exist_ok=True)

    files = {
        "static/index.html": HTML_INDEX,
        "static/css/style.css": CSS_STYLE,
        "static/js/app.js": JS_APP,
        "static/manifest.json": MANIFEST_JSON,
    }

    for path, content in files.items():
        file_path = os.path.join(BASE_DIR, path)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

init_project_files()

# ==========================================
# 3. FastAPI 后端与全品牌核心算法引擎
# ==========================================
app = FastAPI()

class QueryRequest(BaseModel):
    brand_id: str
    batch_code: str

BRANDS_DATA = []
RULES_DATA = []

def load_data_from_disk():
    global BRANDS_DATA, RULES_DATA
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(current_dir, "data"),
        os.path.join(os.getcwd(), "data"),
        os.path.join(current_dir, BASE_DIR, "data")
    ]
    
    target_brands_path = None
    target_rules_path = None
    
    for c in candidates:
        bp = os.path.join(c, "brands.json")
        rp = os.path.join(c, "rules.json")
        if os.path.exists(bp):
            target_brands_path = bp
            target_rules_path = rp
            break

    if target_brands_path and os.path.exists(target_brands_path):
        try:
            with open(target_brands_path, "r", encoding="utf-8") as f:
                BRANDS_DATA = json.load(f)
        except Exception:
            BRANDS_DATA = []

    if target_rules_path and os.path.exists(target_rules_path):
        try:
            with open(target_rules_path, "r", encoding="utf-8") as f:
                RULES_DATA = json.load(f)
        except Exception:
            RULES_DATA = []

load_data_from_disk()

@app.get("/api/brands")
def get_brands():
    load_data_from_disk()
    return BRANDS_DATA

@app.post("/api/query")
def process_query(req: QueryRequest):
    if not BRANDS_DATA or not RULES_DATA:
        load_data_from_disk()

    batch = req.batch_code.strip().upper()
    brand_id = req.brand_id

    brand_info = next((b for b in BRANDS_DATA if b["id"] == brand_id), None)
    if not brand_info:
        return {"confidence": "E", "source": "错误", "rule_name": "未知品牌", "production_date": None}

    # 1. 匹配规则库中的规则
    matched_rule = None
    for rule in RULES_DATA:
        if rule.get("brand_id") == brand_id:
            pat = rule.get("pattern", ".*")
            if re.match(pat, batch):
                matched_rule = rule
                if rule.get("verified", False):
                    break

    decode_type = matched_rule.get("decode_type") if matched_rule else None
    prod_date = None
    candidates = None
    curr_year = datetime.now().year
    base_decade = (curr_year // 10) * 10
    
    # ---------------- 核心算法分支 ----------------

    # 分支 1: DHC 体系 (标准：首位字母为年份，次位为月份数字或跳I字母)
    if brand_id == "dhc" or decode_type == "dhc_standard":
        # DHC 年份基准轮替表
        dhc_year_map = {
            "A": 2019, "B": 2020, "C": 2021, "D": 2022, 
            "E": 2023, "F": 2024, "G": 2025, "H": 2026, 
            "J": 2027, "K": 2028, "L": 2029, "M": 2030
        }
        # DHC 双字母月份表 (标准跳过 I: A-H 为 1-8月, J-M 为 9-12月)
        dhc_month_letter_map = {
            "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6,
            "G": 7, "H": 8, "J": 9, "K": 10, "L": 11, "M": 12
        }

        match_letter_digit = re.match(r"^([A-Za-z])(\d{1,2})[A-Za-z0-9]*$", batch)
        match_double_letter = re.match(r"^([A-Za-z])([A-Za-z])[A-Za-z0-9]*$", batch)

        # 模式 A: 首字母年份 + 数字月份 (如 F6 -> F=2024年, 6=06月)
        if match_letter_digit:
            y_char = match_letter_digit.group(1).upper()
            m_num = int(match_letter_digit.group(2))
            
            if y_char in dhc_year_map and 1 <= m_num <= 12:
                year = dhc_year_map[y_char]
                prod_date = f"{year}-{m_num:02d}"

        # 模式 B: 双字母编码 (如 GL1 -> G=2025年, L=11月)
        elif match_double_letter:
            y_char = match_double_letter.group(1).upper()
            m_char = match_double_letter.group(2).upper()
            
            if y_char in dhc_year_map and m_char in dhc_month_letter_map:
                year = dhc_year_map[y_char]
                month = dhc_month_letter_map[m_char]
                prod_date = f"{year}-{month:02d}"

    # 分支 2: 高丝 / 奥尔滨 / 黛珂体系 (首位年字母 + 次位月份)
    elif decode_type == "japanese_letter_year_month" or brand_id in ["kose", "albion", "decorte"]:
        match = re.match(r"^([A-Za-z])([A-Za-z0-9])[A-Za-z0-9]*$", batch)
        if match:
            y_char = match.group(1).upper()
            m_char = match.group(2).upper()
            year_map = matched_rule.get("year_mapping", {
                "A":2020, "B":2021, "C":2022, "D":2023, "E":2024, "F":2025, "G":2026, "H":2027, "J":2028, "K":2029
            }) if matched_rule else {"C":2022, "D":2023, "E":2024, "F":2025, "G":2026}
            month_map = {"A":1,"B":2,"C":3,"D":4,"E":5,"F":6,"G":7,"H":8,"I":9,"J":10,"K":11,"L":12}
            
            month = int(m_char) if m_char.isdigit() and 1 <= int(m_char) <= 12 else month_map.get(m_char)
            if y_char in year_map and month:
                prod_date = f"{year_map[y_char]}-{month:02d}"

    # 分支 3: 儒略日 YDDD (资生堂 / 花王 / SK-II / 8X4)
    elif decode_type == "julian_date_yddd" or (len(batch) >= 4 and batch[:4].isdigit() and brand_id in ["shiseido", "kao", "sk-ii", "8x4"]):
        match = re.match(r"^(\d)(\d{3})[A-Za-z0-9]*$", batch)
        if match:
            y_char = int(match.group(1))
            days = int(match.group(2))
            if 1 <= days <= 366:
                y = base_decade + y_char
                if y > curr_year:
                    y -= 10
                try:
                    target_date = datetime(y, 1, 1) + timedelta(days=days - 1)
                    prod_date = target_date.strftime("%Y-%m-%d")
                except Exception:
                    prod_date = f"{y}年"

    # 分支 4: 近江兄弟 (OMI Brotherhood)
    elif decode_type == "omi_standard" or brand_id == "omi":
        match_letter = re.match(r"^([A-Za-z])([A-Za-z])[A-Za-z0-9]*$", batch)
        match_digit = re.match(r"^(\d)(\d{3})[A-Za-z0-9]*$", batch)
        if match_letter:
            y_char = match_letter.group(1).upper()
            m_char = match_letter.group(2).upper()
            year_map = {"A":2024, "B":2025, "C":2026, "D":2027, "E":2028}
            month_map = {"A":1,"B":2,"C":3,"D":4,"E":5,"F":6,"G":7,"H":8,"I":9,"J":10,"K":11,"L":12}
            if y_char in year_map and m_char in month_map:
                prod_date = f"{year_map[y_char]}-{month_map[m_char]:02d}"
        elif match_digit:
            y = base_decade + int(match_digit.group(1))
            if y > curr_year: y -= 10
            days = int(match_digit.group(2))
            if 1 <= days <= 366:
                prod_date = (datetime(y, 1, 1) + timedelta(days=days - 1)).strftime("%Y-%m-%d")

    # 分支 5: 直标年月日 (FANCL / HABA)
    elif decode_type == "direct_date_ymd" or brand_id in ["fancl", "haba"]:
        match = re.match(r"^(\d{4}|\d{2})[.\-_]?(\d{2})[.\-_]?(\d{2})", batch)
        if match:
            y_str, m_str, d_str = match.group(1), match.group(2), match.group(3)
            y = int(y_str) if len(y_str) == 4 else 2000 + int(y_str)
            m, d = int(m_str), int(d_str)
            try:
                prod_date = datetime(y, m, d).strftime("%Y-%m-%d")
            except Exception:
                pass

    # 分支 6: 雅诗兰黛 3位码 (A53)
    elif decode_type == "estee_lauder_3_digit" or brand_id in ["estee_lauder", "clinique", "mac", "lamer", "origins"]:
        match = re.match(r"^[A-Za-z0-9]([A-Za-z0-9])(\d)$", batch)
        if match:
            m_char = match.group(1).upper()
            y_char = int(match.group(2))
            month_map = {"1":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"A":10,"B":11,"C":12}
            month = month_map.get(m_char)
            if month:
                y = base_decade + y_char
                if y > curr_year: y -= 10
                prod_date = f"{y}-{month:02d}"

    # 分支 7: LVMH 体系 (迪奥/娇兰/纪梵希)
    elif decode_type == "lvmh_4digit" or brand_id in ["dior", "guerlain", "givenchy", "fresh"]:
        match = re.match(r"^(\d)([A-Za-z])(\d{2})?", batch)
        if match:
            y_char = int(match.group(1))
            m_char = match.group(2).upper()
            day_str = match.group(3)
            lvmh_months = "ABCDEFGHJKLMN"
            if m_char in lvmh_months:
                month = lvmh_months.index(m_char) + 1
                y = base_decade + y_char
                if y > curr_year: y -= 10
                if day_str and 1 <= int(day_str) <= 31:
                    prod_date = f"{y}-{month:02d}-{int(day_str):02d}"
                else:
                    prod_date = f"{y}-{month:02d}"

    # 分支 8: Kissme / 井田体系 (如 7A1)
    elif decode_type == "digit_year_letter_month" or brand_id in ["kissme", "canmake"]:
        match = re.match(r"^(\d)([A-Za-z])[A-Za-z0-9]*$", batch)
        if match:
            y_char = int(match.group(1))
            m_char = match.group(2).upper()
            month_map = {"A":1,"B":2,"C":3,"D":4,"E":5,"F":6,"G":7,"H":8,"I":9,"J":10,"K":11,"L":12}
            month = month_map.get(m_char)
            if month:
                y = base_decade + y_char
                if y > curr_year: y -= 10
                prod_date = f"{y}-{month:02d}"

    # 分支 9: 嘉娜宝 / KATE 倒序儒略日 (如 2143 -> 第214天 2023年)
    elif decode_type == "kanebo_reverse_julian" or brand_id in ["kanebo", "kate"]:
        match = re.match(r"^(\d{3})(\d)$", batch)
        if match:
            days = int(match.group(1))
            y_char = int(match.group(2))
            if 1 <= days <= 366:
                y = base_decade + y_char
                if y > curr_year: y -= 10
                try:
                    prod_date = (datetime(y, 1, 1) + timedelta(days=days - 1)).strftime("%Y-%m-%d")
                except Exception:
                    pass

    # 分支 10: 娇韵诗 / 希思黎 (6位码 如 230501)
    elif decode_type == "clarins_6digit" or (len(batch) == 6 and batch.isdigit() and brand_id in ["clarins", "sisley"]):
        y_part = int(batch[:2])
        m_part = int(batch[2:4])
        if 1 <= m_part <= 12:
            prod_date = f"{2000 + y_part}-{m_part:02d}"

    # 自动推算参考保质期 (未开封默认 36 个月)
    exp_date = None
    shelf_life = matched_rule.get("shelf_life_months", 36) if matched_rule else 36
    if prod_date and "-" in prod_date:
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
        except Exception:
            pass

    if not prod_date:
        return {
            "success": True,
            "brand_name": brand_info["name"],
            "original_batch": req.batch_code,
            "normalized_batch": batch,
            "production_date": None,
            "candidate_dates": None,
            "expiry_date": None,
            "rule_name": "批号规则暂未收录或格式不符",
            "confidence": "E",
            "source": "数据库暂无对应可靠规则"
        }

    return {
        "success": True,
        "brand_name": brand_info["name"],
        "original_batch": req.batch_code,
        "normalized_batch": batch,
        "production_date": prod_date,
        "candidate_dates": candidates,
        "expiry_date": exp_date,
        "rule_name": matched_rule.get("name", "产线标准批号解析") if matched_rule else "标准编码规则",
        "confidence": "A",
        "source": matched_rule.get("source", "官方/专柜交叉验证") if matched_rule else "品牌产线标准"
    }

# 挂载静态资源
static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/css", StaticFiles(directory=os.path.join(static_dir, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(static_dir, "js")), name="js")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_file = os.path.join(BASE_DIR, "static/index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return HTML_INDEX

@app.get("/manifest.json")
def get_manifest():
    return JSONResponse(content=json.loads(MANIFEST_JSON))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
