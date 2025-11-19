import streamlit as st
import json
import datetime
import os
import time

# ==========================================
# 1. 核心配置与 CSS 设计系统
# ==========================================
st.set_page_config(
    page_title="TimeLog",
    page_icon="🕰️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 📂 数据路径
DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
ACTIVITIES_FILE = os.path.join(DATA_DIR, "activities.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")

# 🎨 iOS 设计语言 CSS
st.markdown("""
<style>
    /* 1. 全局背景：高级灰 */
    .stApp { background-color: #F5F5F7; }
    header, footer { visibility: hidden; }
    
    /* 2. 隐藏 Streamlit 默认丑陋的元素 */
    #MainMenu { visibility: hidden; }
    .stDeployButton { visibility: hidden; }
    
    /* 3. 卡片容器设计 - 核心 */
    .design-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03); /* 极柔和的阴影 */
        border: 1px solid rgba(0,0,0,0.02);
    }
    
    /* 4. 标题排版 */
    .card-title {
        font-size: 14px;
        font-weight: 600;
        color: #86868B; /* 苹果灰 */
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* 5. 状态标签 */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    .badge-new { background: #FFE5E5; color: #FF3B30; } /* 红 */
    .badge-exist { background: #E4FBF0; color: #34C759; } /* 绿 */
    
    /* 6. 输入框优化 - 去除边框，融入背景 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #F5F5F7 !important;
        border: none !important;
        border-radius: 10px !important;
        height: 42px;
    }
    
    /* 7. 按钮 - 悬浮感 */
    .stButton button {
        width: 100%;
        height: 52px !important;
        background: linear-gradient(135deg, #007AFF 0%, #005ECB 100%) !important;
        border: none !important;
        border-radius: 14px !important;
        font-size: 17px !important;
        font-weight: 600 !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.25);
        transition: transform 0.1s;
    }
    .stButton button:active { transform: scale(0.98); }

    /* 8. 历史列表条目 */
    .history-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #F0F0F0;
    }
    .history-row:last-child { border-bottom: none; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 数据逻辑层
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

# 初始化数据
if 'activities' not in st.session_state:
    st.session_state.activities = load_json(ACTIVITIES_FILE, [])
if 'templates' not in st.session_state:
    st.session_state.templates = load_json(TEMPLATES_FILE, {})

# --- 智能时间计算 ---
# 逻辑：默认开始时间 = 上一条记录的结束时间
# 这个值只作为 Input 的 value 传入，不绑定 key，允许用户随意修改
def get_default_times():
    now = datetime.datetime.now()
    if st.session_state.activities:
        last_record = st.session_state.activities[-1]
        try:
            last_end = datetime.datetime.fromisoformat(last_record['end_time'])
            # 如果上一条记录在24小时内，则接续；否则用当前时间
            if (now - last_end).total_seconds() < 86400:
                return last_end.time(), (last_end + datetime.timedelta(minutes=60)).time()
        except:
            pass
    return now.time(), (now + datetime.timedelta(minutes=60)).time()

default_start, default_end = get_default_times()

# 五级分类默认选项
HIERARCHY = {
    "需求": ["个人生理", "个人发展", "家庭责任", "工作学习", "休闲娱乐", "交通出行"],
    "企划": ["睡眠", "饮食", "健康", "职业工作", "家务", "照顾", "学习", "消遣", "运动"],
    "活动": ["睡觉", "吃饭", "洗漱", "办公", "会议", "烹饪", "清洁", "阅读", "刷手机", "游戏", "坐车"],
    "行为": ["躺卧", "坐姿", "站立", "行走", "操作", "交流"]
}

# ==========================================
# 3. 页面主体 (UI渲染)
# ==========================================

# 标题区
st.markdown("""
    <div style='margin: 10px 0 20px 0; text-align:center;'>
        <div style='font-size:24px; font-weight:800; color:#1D1D1F;'>TimeLog</div>
        <div style='font-size:13px; color:#86868B;'>时空行为轨迹记录</div>
    </div>
""", unsafe_allow_html=True)

# === 核心卡片：新建记录 ===
# 用 HTML div 模拟卡片容器的开始
st.markdown('<div class="design-card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">✨ 新建记录 (New Entry)</div>', unsafe_allow_html=True)

# 1. 核心输入：做什么？
episode_input = st.text_input("准备做什么？", placeholder="输入活动名称，如: 打羽毛球", label_visibility="collapsed")

# 2. 动态逻辑：判断是否为老活动
is_new = False
template_data = {}

if episode_input:
    if episode_input in st.session_state.templates:
        # === 情境 A: 老活动 (模板) ===
        t = st.session_state.templates[episode_input]
        template_data = t
        st.markdown(f"""
            <div style='margin-bottom: 15px; display:flex; align-items:center; justify-content:space-between; background:#F5F5F7; padding:10px; border-radius:10px;'>
                <div>
                    <span class="status-badge badge-exist">已识别模板</span>
                    <span style='margin-left:8px; font-size:13px; font-weight:600; color:#333;'>{episode_input}</span>
                </div>
                <div style='font-size:12px; color:#666;'>
                    {t['demand']} > {t['activity']}
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # === 情境 B: 新活动 (需补全) ===
        is_new = True
        st.markdown(f"""
            <div style='margin-bottom: 15px;'>
                <span class="status-badge badge-new">新活动</span>
                <span style='font-size:13px; color:#666; margin-left:5px;'>请完善分类，下次自动记住</span>
            </div>
        """, unsafe_allow_html=True)
        
        # 只有新活动才显示这 4 个下拉框
        c1, c2 = st.columns(2)
        with c1:
            demand = st.selectbox("需求", HIERARCHY["需求"], key="new_demand")
            activity = st.selectbox("活动", HIERARCHY["活动"], key="new_activity")
        with c2:
            project = st.selectbox("企划", HIERARCHY["企划"], key="new_project")
            behavior = st.selectbox("行为", HIERARCHY["行为"], key="new_behavior")
        
        template_data = {
            "demand": demand, "project": project, 
            "activity": activity, "behavior": behavior
        }

st.markdown('<hr style="border:none; height:1px; background:#F0F0F0; margin:15px 0;">', unsafe_allow_html=True)

# 3. 时间与地点 (每次都要确认，与模板无关)
col_t1, col_t2 = st.columns(2)
with col_t1:
    st.caption("开始时间")
    # value 设为动态计算的 default_start，但没有 key，允许修改
    inp_start = st.time_input("Start", value=default_start, step=60, label_visibility="collapsed")
with col_t2:
    st.caption("结束时间")
    inp_end = st.time_input("End", value=default_end, step=60, label_visibility="collapsed")

inp_loc = st.text_input("地点", placeholder="📍 地点 (如: 体育馆)", label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True) # 结束卡片

# === 底部按钮 ===
if st.button("确认记录 (Save)"):
    if not episode_input:
        st.toast("⚠️ 请输入活动名称", icon="🤔")
    else:
        # 1. 保存模板 (如果是新的)
        if is_new:
            st.session_state.templates[episode_input] = template_data
            save_json(TEMPLATES_FILE, st.session_state.templates)
        
        # 2. 计算时间
        today = datetime.date.today()
        dt_start = datetime.datetime.combine(today, inp_start)
        dt_end = datetime.datetime.combine(today, inp_end)
        
        # 跨天逻辑
        if dt_end < dt_start:
            dt_end += datetime.timedelta(days=1)
        
        duration = int((dt_end - dt_start).total_seconds() / 60)
        
        # 3. 保存记录
        new_record = {
            "id": int(time.time()),
            "episode": episode_input,
            "start_time": dt_start.isoformat(),
            "end_time": dt_end.isoformat(),
            "duration": duration,
            "location": inp_loc,
            # 展开保存完整的五级分类
            "demand": template_data.get("demand"),
            "project": template_data.get("project"),
            "activity": template_data.get("activity"),
            "behavior": template_data.get("behavior"),
            "created_at": datetime.datetime.now().isoformat()
        }
        
        st.session_state.activities.append(new_record)
        st.session_state.activities.sort(key=lambda x: x['start_time'])
        save_json(ACTIVITIES_FILE, st.session_state.activities)
        
        st.toast(f"✅ 已记录: {episode_input}", icon="🎉")
        time.sleep(0.5)
        st.rerun()

# === 历史记录卡片 ===
if st.session_state.activities:
    st.markdown('<div class="design-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📅 今日时间轴 (Today)</div>', unsafe_allow_html=True)
    
    # 获取今日数据
    today_str = datetime.date.today().isoformat()
    today_acts = [a for a in st.session_state.activities if a['start_time'].startswith(today_str)]
    
    if not today_acts:
        st.info("今天还没有记录，开始新的一天吧！")
    else:
        # 倒序显示
        for act in reversed(today_acts):
            s = datetime.datetime.fromisoformat(act['start_time']).strftime('%H:%M')
            e = datetime.datetime.fromisoformat(act['end_time']).strftime('%H:%M')
            
            st.markdown(f"""
            <div class="history-row">
                <div style="display:flex; flex-direction:column;">
                    <span style="font-size:15px; font-weight:700; color:#1D1D1F;">{act['episode']}</span>
                    <span style="font-size:12px; color:#86868B; margin-top:2px;">
                        {s} - {e} · {act['duration']} min
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:12px; background:#F0F0F0; color:#666; padding:3px 8px; border-radius:6px;">
                        {act.get('location', '')}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 删除逻辑 (为了美观，用 Streamlit 原生按钮放下面，或者用 col)
            # 这里为了保持卡片纯洁，不放删除按钮，如需删除请在电脑端管理
    
    st.markdown('</div>', unsafe_allow_html=True)
