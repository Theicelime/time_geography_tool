import streamlit as st
import json
import datetime
import os
import time

# ==========================================
# 1. 基础配置与 CSS
# ==========================================
st.set_page_config(
    page_title="TimeLog Pro",
    page_icon="🕰️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
ACTIVITIES_FILE = os.path.join(DATA_DIR, "activities.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")

# iOS 风格 CSS
st.markdown("""
<style>
    .stApp { background-color: #F5F5F7; }
    header, footer, #MainMenu { visibility: hidden; }
    
    /* 卡片设计 */
    .design-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        border: 1px solid rgba(0,0,0,0.02);
    }
    
    /* 标题 */
    .card-title {
        font-size: 13px; font-weight: 700; color: #86868B;
        margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    /* 智能标签 */
    .smart-badge {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white; padding: 4px 10px; border-radius: 12px;
        font-size: 12px; font-weight: bold; display: inline-flex; align-items: center;
    }
    
    /* 按钮优化 */
    .stButton button {
        width: 100%; height: 50px !important;
        background: #007AFF !important; color: white !important;
        border-radius: 12px !important; font-weight: 600 !important; border: none !important;
    }
    
    /* 输入框样式 */
    div[data-baseweb="select"] > div, .stTextInput input, .stTimeInput input {
        background-color: #F5F5F7 !important; border: none !important;
        border-radius: 10px !important; min-height: 42px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 智能引擎 (常识库)
# ==========================================

# 这是系统的“大脑”，你可以随时扩展这个字典
KNOWLEDGE_BASE = {
    "睡觉": {"demand": "个人生理", "project": "睡眠", "activity": "睡觉", "behavior": "躺卧"},
    "午睡": {"demand": "个人生理", "project": "睡眠", "activity": "睡觉", "behavior": "躺卧"},
    "吃饭": {"demand": "个人生理", "project": "饮食", "activity": "吃饭", "behavior": "坐姿"},
    "工作": {"demand": "工作学习", "project": "职业工作", "activity": "办公", "behavior": "坐姿"},
    "开会": {"demand": "工作学习", "project": "职业工作", "activity": "会议", "behavior": "坐姿"},
    "坐地铁": {"demand": "交通出行", "project": "移动", "activity": "坐车", "behavior": "坐姿"},
    "开车": {"demand": "交通出行", "project": "移动", "activity": "开车", "behavior": "坐姿"},
    "打羽毛球": {"demand": "休闲娱乐", "project": "运动", "activity": "健身", "behavior": "跑动"},
    "刷手机": {"demand": "休闲娱乐", "project": "消遣", "activity": "刷手机", "behavior": "躺卧"},
    "洗澡": {"demand": "个人生理", "project": "健康", "activity": "洗漱", "behavior": "站立"},
}

HIERARCHY = {
    "需求": ["个人生理", "个人发展", "家庭责任", "工作学习", "休闲娱乐", "交通出行", "社交互动"],
    "企划": ["睡眠", "饮食", "健康", "职业工作", "家务", "照顾", "学习", "消遣", "运动", "移动"],
    "活动": ["睡觉", "吃饭", "洗漱", "办公", "会议", "烹饪", "清洁", "阅读", "刷手机", "游戏", "坐车", "开车", "健身", "聊天"],
    "行为": ["躺卧", "坐姿", "站立", "行走", "跑动", "操作", "交流"]
}

# ==========================================
# 3. 逻辑处理
# ==========================================

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 初始化
if 'activities' not in st.session_state:
    st.session_state.activities = load_json(ACTIVITIES_FILE, [])
if 'templates' not in st.session_state:
    st.session_state.templates = load_json(TEMPLATES_FILE, {}) # 用户自定义的模板

# --- 回调函数：当用户输入活动名后触发 ---
def on_episode_change():
    val = st.session_state.episode_input
    if not val: return

    # 1. 先查用户自定义模板 (优先级最高)
    if val in st.session_state.templates:
        t = st.session_state.templates[val]
        st.session_state.auto_demand = t.get('demand')
        st.session_state.auto_project = t.get('project')
        st.session_state.auto_activity = t.get('activity')
        st.session_state.auto_behavior = t.get('behavior')
        st.session_state.match_source = "template"
    
    # 2. 再查常识库 (智能推荐)
    elif val in KNOWLEDGE_BASE:
        kb = KNOWLEDGE_BASE[val]
        st.session_state.auto_demand = kb.get('demand')
        st.session_state.auto_project = kb.get('project')
        st.session_state.auto_activity = kb.get('activity')
        st.session_state.auto_behavior = kb.get('behavior')
        st.session_state.match_source = "smart"
    
    # 3. 没找到，默认选第一个，让用户自己改
    else:
        st.session_state.match_source = "new"
        # 不覆盖，保留用户可能已经选的值

# ==========================================
# 4. 界面渲染
# ==========================================

st.markdown("""
    <div style='text-align:center; margin-bottom:20px; padding-top:10px;'>
        <div style='font-size:20px; font-weight:800;'>TimeLog</div>
        <div style='font-size:12px; color:#888;'>智能时空记录</div>
    </div>
""", unsafe_allow_html=True)

# === 卡片 1: 活动内容 (智能分类) ===
st.markdown('<div class="design-card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">📝 活动内容 (ACTIVITY)</div>', unsafe_allow_html=True)

# 输入框：绑定回调函数
st.text_input(
    "要做什么？", 
    placeholder="输入关键词，如: 睡觉、打羽毛球...", 
    key="episode_input",
    on_change=on_episode_change # 核心：输入完按回车，自动填分类
)

# 获取匹配状态
match_source = st.session_state.get("match_source", "new")

# 根据状态显示分类选择器
if match_source == "template":
    st.markdown(f"<div style='margin-top:10px;'><span class='smart-badge'>✨ 已自动匹配模板</span></div>", unsafe_allow_html=True)
elif match_source == "smart":
    st.markdown(f"<div style='margin-top:10px;'><span class='smart-badge'>🤖 智能推荐分类</span></div>", unsafe_allow_html=True)
else:
    if st.session_state.get("episode_input"):
        st.caption("🆕 新活动：请手动选择一次，下次我就记住了")

# 分类下拉框 (为了美观，使用 2x2 布局)
# 使用 session_state 的值来定位 index
def get_index(options, key_name):
    val = st.session_state.get(key_name)
    if val and val in options:
        return options.index(val)
    return 0

c1, c2 = st.columns(2)
with c1:
    sel_demand = st.selectbox("需求", HIERARCHY["需求"], index=get_index(HIERARCHY["需求"], "auto_demand"), key="sel_demand")
    sel_activity = st.selectbox("活动", HIERARCHY["活动"], index=get_index(HIERARCHY["活动"], "auto_activity"), key="sel_activity")
with c2:
    sel_project = st.selectbox("企划", HIERARCHY["企划"], index=get_index(HIERARCHY["企划"], "auto_project"), key="sel_project")
    sel_behavior = st.selectbox("行为", HIERARCHY["行为"], index=get_index(HIERARCHY["行为"], "auto_behavior"), key="sel_behavior")

st.markdown('</div>', unsafe_allow_html=True)


# === 卡片 2: 时间与地点 (完全自由) ===
st.markdown('<div class="design-card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">⏱️ 时间 (TIME)</div>', unsafe_allow_html=True)

# 智能计算默认时间 (仅作为初始值)
if 'init_time' not in st.session_state:
    now = datetime.datetime.now()
    default_start = now.time()
    # 尝试找上一条记录
    if st.session_state.activities:
        try:
            last = st.session_state.activities[-1]
            last_end = datetime.datetime.fromisoformat(last['end_time'])
            if last_end.date() == datetime.date.today():
                default_start = last_end.time()
        except: pass
    
    st.session_state.start_val = default_start
    st.session_state.end_val = (datetime.datetime.combine(datetime.date.today(), default_start) + datetime.timedelta(hours=1)).time()
    st.session_state.init_time = True

# 这里的 step=60 是为了在某些设备上允许输入分钟
# 但在电脑上，你可以直接点开输入框，用键盘敲 "14:30"
t1, t2 = st.columns(2)
with t1:
    st.caption("开始")
    # 注意：不绑定 key，只给 value，这样不会被 Streamlit 强制重置
    inp_start = st.time_input("Start", value=st.session_state.start_val, step=60, label_visibility="collapsed")
with t2:
    st.caption("结束")
    inp_end = st.time_input("End", value=st.session_state.end_val, step=60, label_visibility="collapsed")

st.markdown('<div class="card-title" style="margin-top:15px;">📍 地点 (LOCATION)</div>', unsafe_allow_html=True)
inp_loc = st.text_input("地点", placeholder="在哪？(可选)", label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True)

# === 提交 ===
if st.button("确认记录 (Save)"):
    episode_name = st.session_state.get("episode_input")
    
    if not episode_name:
        st.toast("⚠️ 写点什么吧！", icon="🤔")
    else:
        # 1. 保存到用户模板 (如果是新词或修改了分类)
        new_template = {
            "demand": sel_demand, "project": sel_project, 
            "activity": sel_activity, "behavior": sel_behavior
        }
        st.session_state.templates[episode_name] = new_template
        save_json(TEMPLATES_FILE, st.session_state.templates)
        
        # 2. 时间计算
        today = datetime.date.today()
        dt_start = datetime.datetime.combine(today, inp_start)
        dt_end = datetime.datetime.combine(today, inp_end)
        if dt_end < dt_start: dt_end += datetime.timedelta(days=1) # 跨天
        duration = int((dt_end - dt_start).total_seconds() / 60)
        
        # 3. 保存
        record = {
            "id": int(time.time()),
            "episode": episode_name,
            "start_time": dt_start.isoformat(),
            "end_time": dt_end.isoformat(),
            "duration": duration,
            "location": inp_loc,
            **new_template, # 展开 5级分类
            "created_at": datetime.datetime.now().isoformat()
        }
        st.session_state.activities.append(record)
        st.session_state.activities.sort(key=lambda x: x['start_time'])
        save_json(ACTIVITIES_FILE, st.session_state.activities)
        
        # 4. 更新下次的默认时间
        st.session_state.start_val = dt_end.time()
        st.session_state.end_val = (dt_end + datetime.timedelta(hours=1)).time()
        
        st.toast(f"✅ 已记录: {episode_name}", icon="🎉")
        time.sleep(0.5)
        st.rerun()

# === 历史列表 ===
if st.session_state.activities:
    st.markdown('<div style="margin:20px 0 10px 0; font-size:14px; color:#888; font-weight:bold;">📅 今日记录</div>', unsafe_allow_html=True)
    
    today_str = datetime.date.today().isoformat()
    today_acts = [a for a in st.session_state.activities if a['start_time'].startswith(today_str)]
    
    for act in reversed(today_acts):
        s = datetime.datetime.fromisoformat(act['start_time']).strftime('%H:%M')
        e = datetime.datetime.fromisoformat(act['end_time']).strftime('%H:%M')
        
        st.markdown(f"""
        <div class="design-card" style="padding:15px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:800; font-size:16px; color:#1d1d1f;">{act['episode']}</div>
                    <div style="font-size:12px; color:#86868b; margin-top:4px;">
                        {s} - {e} · {act['duration']} min
                    </div>
                </div>
                <div style="text-align:right;">
                     <span style="font-size:11px; background:#F2F2F7; color:#666; padding:4px 8px; border-radius:6px;">
                        {act['demand']}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
