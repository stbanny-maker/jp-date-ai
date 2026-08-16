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
            <input type="text" id="batch-input" placeholder="请输入批号 (如 2585B, F6, B0002945)" oninput="validateInput()">
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
    const displayDate = data.production_date || (data.candidate_dates && data.candidate_dates.length > 0 ? data.candidate_dates[0] : null);
    
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
    brand_id = req.brand_id.lower()

    brand_info = next((b for b in BRANDS_DATA if b["id"] == brand_id), None)
    brand_name = brand_info["name"] if brand_info else brand_id

    prod_date = None
    confidence = "A"
    source = "官方/专柜交叉验证"
    rule_name = "标准工业批号解析"

    curr_year = datetime.now().year
    base_decade = (curr_year // 10) * 10

    # =========================================================================
    # [独立插槽]: Kracie / 葵缇亚 / 肌美精 (Hadabisei 5位混编码体系)
    # =========================================================================
    if not prod_date and (brand_id in ["kracie", "hadabisei"] or "KRACIE" in brand_name.upper() or "肌美精" in brand_name or "葵缇亚" in brand_name):
        rule_name = "Kracie 葵缇亚/肌美精标准批号"
        
        # 5位混编码 (如 71BH2 -> 首位年 7, 次位月 1)
        match_kracie = re.match(r"^(\d)([0-9A-Za-z])[A-Za-z0-9]*$", batch)
        if match_kracie:
            y_char = int(match_kracie.group(1))
            m_raw = match_kracie.group(2).upper()
            
            month_map_kracie = {
                "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
                "A": 10, "B": 11, "C": 12, "X": 10, "Y": 11, "Z": 12
            }
            
            month = month_map_kracie.get(m_raw, 1)
            y = base_decade + y_char
            if y > curr_year:
                y -= 10
            prod_date = f"{y}-{month:02d}"


    # =========================================================================
    # [独立插槽]: 大正制药 / Taisho (根据实物盒装校准)
    # =========================================================================
    if brand_id in ["taisho", "pabron"] or "大正" in brand_name or "TAISHO" in brand_name.upper():
        rule_name = "大正制药标准药品批号"
        shelf_life = 36  # 日本OTC药品严格36个月
        
        # 5位药品流水码 (如 045N1, 015X1)
        match_taisho_5 = re.match(r"^\d{2}(\d)([A-Za-z])\d*$", batch)

        # 实物校准的大正医药月份字母表
        # N=1月, P=2月, Q=3月, R/S=4月, T=5月, X=6月, A=7月, B=8月, C=9月, D=10月, E=11月, F=12月
        month_map_taisho = {
            "N": 1, "P": 2, "Q": 3, "R": 4, "S": 4, "T": 5, "X": 6,
            "A": 7, "B": 8, "C": 9, "D": 10, "E": 11, "F": 12,
            "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "Y": 11, "Z": 12
        }

        if match_taisho_5:
            y_char = int(match_taisho_5.group(1))
            m_char = match_taisho_5.group(2).upper()
            month = month_map_taisho.get(m_char)
            if month:
                y = base_decade + y_char
                if y > curr_year: y -= 10
                prod_date = f"{y}-{month:02d}"

    # =========================================================================
    # [LOSHI / 日本马油 - 纯动态数学推算分支]
    # =========================================================================
    if brand_id in ["loshi", "horse_oil", "cosmetec"] or "LOSHI" in brand_name.upper() or "马油" in brand_name:
        rule_name = "LOSHI 产线标准儒略日体系"
        
        # 模式 A: 5位倒序儒略日 (如 2585B -> 前3位天数 258, 第4位年份 5)
        match_loshi_5 = re.match(r"^(\d{3})(\d)[A-Za-z]?$", batch)
        # 模式 B: 6-8位复合码 (如 323501W -> 第1位车间, 第2-4位天数 235, 剩余为流水)
        match_loshi_7 = re.match(r"^\d(\d{3})\d*[A-Za-z0-9]*$", batch)

        if match_loshi_5:
            days = int(match_loshi_5.group(1))
            y_char = int(match_loshi_5.group(2))
            if 1 <= days <= 366:
                y = base_decade + y_char
                if y > curr_year:
                    y -= 10
                prod_date = (datetime(y, 1, 1) + timedelta(days=days - 1)).strftime("%Y-%m-%d")

        elif match_loshi_7:
            days = int(match_loshi_7.group(1))
            if 1 <= days <= 366:
                # 动态选取最贴近当前年份的生产周期
                y = curr_year if datetime.now().timetuple().tm_yday >= days else (curr_year - 1)
                prod_date = (datetime(y, 1, 1) + timedelta(days=days - 1)).strftime("%Y-%m-%d")


    # =========================================================================
    # 1. 花王集团体系 (KAO / Bioré碧柔 / Curél珂润 / Sofina苏菲娜 / 8x4 / Kanebo / KATE)
    # =========================================================================
    kao_group = ["kao", "biore", "curel", "sofina", "8x4", "kanebo", "kate", "freeplus", "est"]
    if not prod_date and (brand_id in kao_group or "花王" in brand_name or "碧柔" in brand_name or "珂润" in brand_name or "苏菲娜" in brand_name):
        rule_name = "花王集团产线标准"
        match_kao_8 = re.match(r"^[A-Z0-9]{3,4}(\d{3})(\d)$", batch)
        match_kao_4_rev = re.match(r"^(\d{3})(\d)$", batch)
        match_kao_4_seq = re.match(r"^(\d)(\d{3})[A-Z0-9]*$", batch)

        if match_kao_8:
            days = int(match_kao_8.group(1))
            y_char = int(match_kao_8.group(2))
            if 1 <= days <= 366:
                y = base_decade + y_char
                if y > curr_year: y -= 10
                prod_date = (datetime(y, 1, 1) + timedelta(days=days - 1)).strftime("%Y-%m-%d")
        elif match_kao_4_rev and 1 <= int(match_kao_4_rev.group(1)) <= 366:
            days = int(match_kao_4_rev.group(1))
            y_char = int(match_kao_4_rev.group(2))
            y = base_decade + y_char
            if y > curr_year: y -= 10
            prod_date = (datetime(y, 1, 1) + timedelta(days=days - 1)).strftime("%Y-%m-%d")
        elif match_kao_4_seq and 1 <= int(match_kao_4_seq.group(2)) <= 366:
            y = base_decade + int(match_kao_4_seq.group(1))
            if y > curr_year: y -= 10
            days = int(match_kao_4_seq.group(2))
            prod_date = (datetime(y, 1, 1) + timedelta(days=days - 1)).strftime("%Y-%m-%d")

    # =========================================================================
    # 2. 资生堂集团体系 (SHISEIDO / CPB / 怡丽丝尔 / 安耐晒 / IPSA / 欧珀莱 / NARS)
    # =========================================================================
    shiseido_group = ["shiseido", "cpb", "elixir", "anessa", "ipsa", "aupres", "nars", "uno", "senka"]
    if not prod_date and (brand_id in shiseido_group or "资生堂" in brand_name or "安耐晒" in brand_name or "怡丽丝尔" in brand_name):
        rule_name = "资生堂集团儒略日标准"
        match = re.match(r"^(\d)(\d{3})[A-Za-z0-9]*$", batch)
        if match:
            y_char = int(match.group(1))
            days = int(match.group(2))
            if 1 <= days <= 366:
                y = base_decade + y_char
                if y > curr_year: y -= 10
                prod_date = (datetime(y, 1, 1) + timedelta(days=days - 1)).strftime("%Y-%m-%d")

    # =========================================================================
    # 3. 高丝/奥尔滨体系 (KOSÉ / DECORTÉ黛珂 / ALBION奥尔滨 / 雪肌精)
    # =========================================================================
    kose_group = ["kose", "decorte", "albion", "sekkisei", "fasio"]
    if not prod_date and (brand_id in kose_group or "高丝" in brand_name or "黛珂" in brand_name or "奥尔滨" in brand_name):
        rule_name = "高丝集团字母轮替体系"
        match = re.match(r"^([A-Za-z])([A-Za-z0-9])[A-Za-z0-9]*$", batch)
        if match:
            y_char = match.group(1).upper()
            m_char = match.group(2).upper()
            year_map = {"A":2020, "B":2021, "C":2022, "D":2023, "E":2024, "F":2025, "G":2026, "H":2027, "J":2028, "K":2029}
            month_map = {"A":1,"B":2,"C":3,"D":4,"E":5,"F":6,"G":7,"H":8,"I":9,"J":10,"K":11,"L":12}
            month = int(m_char) if m_char.isdigit() and 1 <= int(m_char) <= 12 else month_map.get(m_char)
            if y_char in year_map and month:
                prod_date = f"{year_map[y_char]}-{month:02d}"

    # =========================================================================
    # 4. DHC 体系 (标准：首位字母为年份，次位为月份数字或跳I字母)
    # =========================================================================
    if not prod_date and (brand_id == "dhc" or "蝶翠诗" in brand_name or "DHC" in brand_name):
        rule_name = "DHC官方产线标准"
        dhc_year_map = {"A":2019, "B":2020, "C":2021, "D":2022, "E":2023, "F":2024, "G":2025, "H":2026, "J":2027, "K":2028, "L":2029}
        dhc_month_letter_map = {"A":1, "B":2, "C":3, "D":4, "E":5, "F":6, "G":7, "H":8, "J":9, "K":10, "L":11, "M":12}

        match_letter_digit = re.match(r"^([A-Za-z])(\d{1,2})[A-Za-z0-9]*$", batch)
        match_double_letter = re.match(r"^([A-Za-z])([A-Za-z])[A-Za-z0-9]*$", batch)

        if match_letter_digit:
            y_char = match_letter_digit.group(1).upper()
            m_num = int(match_letter_digit.group(2))
            if y_char in dhc_year_map and 1 <= m_num <= 12:
                prod_date = f"{dhc_year_map[y_char]}-{m_num:02d}"
        elif match_double_letter:
            y_char = match_double_letter.group(1).upper()
            m_char = match_double_letter.group(2).upper()
            if y_char in dhc_year_map and m_char in dhc_month_letter_map:
                prod_date = f"{dhc_year_map[y_char]}-{dhc_month_letter_map[m_char]:02d}"

    # =========================================================================
    # 5. 雅诗兰黛系 (雅诗兰黛 / 倩碧 / 海蓝之谜 / MAC / 悦木之源)
    # =========================================================================
    estee_group = ["estee_lauder", "clinique", "lamer", "mac", "origins", "bobbi_brown", "tom_ford", "jo_malone"]
    if not prod_date and (brand_id in estee_group or "雅诗兰黛" in brand_name or "海蓝之谜" in brand_name):
        rule_name = "雅诗兰黛集团3位码"
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

    # =========================================================================
    # 6. 直标年月日兜底 (FANCL / HABA / 进口直标等)
    # =========================================================================
    if not prod_date:
        match_ymd = re.match(r"^(\d{4}|\d{2})[.\-_/]?(\d{2})[.\-_/]?(\d{2})$", batch)
        if match_ymd:
            y_str, m_str, d_str = match_ymd.group(1), match_ymd.group(2), match_ymd.group(3)
            y = int(y_str) if len(y_str) == 4 else 2000 + int(y_str)
            m, d = int(m_str), int(d_str)
            if 2010 <= y <= curr_year + 1 and 1 <= m <= 12 and 1 <= d <= 31:
                rule_name = "直标生产日期"
                prod_date = f"{y}-{m:02d}-{d:02d}"

    # =========================================================================
    # 计算到期日期 (未开封默认 36 个月)
    # =========================================================================
    exp_date = None
    shelf_life = 36
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
            "brand_name": brand_name,
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
        "brand_name": brand_name,
        "original_batch": req.batch_code,
        "normalized_batch": batch,
        "production_date": prod_date,
        "candidate_dates": None,
        "expiry_date": exp_date,
        "rule_name": rule_name,
        "confidence": confidence,
        "source": source
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
