import streamlit as st
import json
import datetime
import os
import time
import pandas as pd
import plotly.express as px
import random

# ==========================================
# 1. 赛博霓虹配置 (Cyberpunk Config)
# ==========================================
st.set_page_config(
    page_title="Chronos",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
ACTIVITIES_FILE = os.path.join(DATA_DIR, "activities.json")

# --- 炫酷 CSS 注入 ---
st.markdown("""
<style>
    /* 全局深色背景 */
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
    }
    
    /* 隐藏杂项 */
    header, footer, #MainMenu { visibility: hidden; }
    
    /* 霓虹卡片容器 */
    .neon-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        border-left: 5px solid #8b5cf6; /* 紫色光条 */
    }
    
    /* 标题样式 */
    .card-title {
        font-size: 14px; font-weight: 800; color: #a5b4fc;
        letter-spacing: 1px; text-transform: uppercase; margin-bottom: 15px;
        display: flex; align-items: center; gap: 8px;
    }
    
    /* 输入组件美化 */
    .stSelectbox div[data-baseweb="select"] > div, 
    .stTextInput input, 
    .stTimeInput input {
        background-color: #334155 !important;
        color: white !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }
    
    /* 提交按钮：渐变流光 */
    .stButton button {
        width: 100%;
        background: linear-gradient(45deg, #6366f1, #8b5cf6, #ec4899);
        border: none !important;
        color: white !important;
        font-weight: 800 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        font-size: 18px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 10px 20px rgba(139, 92, 246, 0.3);
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 25px rgba(139, 92, 246, 0.5);
    }
    
    /* 历史记录条目 */
    .history-item {
        background: #1e293b;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 3px solid #10b981;
        display: flex; justify-content: space-between; align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 数据核心 (Data Core)
# ==========================================

def load_data():
    if os.path.exists(ACTIVITIES_FILE):
        try:
            with open(ACTIVITIES_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return []

def save_data(data):
    with open(ACTIVITIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if 'activities' not in st.session_state:
    st.session_state.activities = load_data()

# --- 智能提取历史选项 ---
def get_history_options(field_name):
    """从历史记录中提取去重的选项，按使用频率排序"""
    if not st.session_state.activities: return []
    vals = [a.get(field_name, "") for a in st.session_state.activities if a.get(field_name)]
    # 统计频率
    counts = {}
    for v in vals: counts[v] = counts.get(v, 0) + 1
    # 按频率倒序
    sorted_vals = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
    return sorted_vals

# --- 混合输入组件 (核心交互) ---
def hybrid_input(label, field_key, history_list, icon="🔹"):
    """创建 下拉选择 + 手动输入 的组合组件"""
    # 选项列表：头部固定为 '✨ 手动输入'
    options = ["✨ 手动输入/新内容"] + history_list
    
    # 1. 下拉选择
    selected = st.selectbox(
        f"{icon} {label}", 
        options, 
        key=f"sel_{field_key}",
        label_visibility="collapsed"
    )
    
    final_value = ""
    
    # 2. 根据选择决定是否显示文本框
    if selected == "✨ 手动输入/新内容":
        # 手动输入模式
        final_value = st.text_input(
            f"输入新的{label}", 
            placeholder=f"在此输入新的{label}...",
            key=f"txt_{field_key}",
            label_visibility="collapsed"
        )
    else:
        # 历史选择模式
        final_value = selected
        # 显示一个只读的提示或者被禁用的输入框，保持界面高度一致
        st.markdown(f"<div style='font-size:12px; color:#94a3b8; margin-top:-15px; margin-bottom:15px; padding-left:5px;'>已选择历史: {selected}</div>", unsafe_allow_html=True)
        
    return final_value

# ==========================================
# 3. 界面构建 (UI Builder)
# ==========================================

# 顶部 Logo 区
st.markdown("""
    <div style='text-align:center; margin-bottom:30px; padding-top:20px;'>
        <div style='font-size:40px; font-weight:900; background: -webkit-linear-gradient(45deg, #6366f1, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>CHRONOS</div>
        <div style='font-size:12px; color:#64748b; letter-spacing:2px;'>时空行为可视化日志</div>
    </div>
""", unsafe_allow_html=True)

# === 区域 1: 时间控制 (5分钟刻度) ===
st.markdown('<div class="neon-card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">⏱️ 时间跨度 (TIME)</div>', unsafe_allow_html=True)

# 自动计算默认时间
if 'default_start' not in st.session_state:
    now = datetime.datetime.now()
    # 向下取整到最近的5分钟
    minute = (now.minute // 5) * 5
    rounded_now = now.replace(minute=minute, second=0, microsecond=0)
    
    st.session_state.default_start = rounded_now.time()
    # 尝试接续上一条
    if st.session_state.activities:
        last_end = datetime.datetime.fromisoformat(st.session_state.activities[-1]['end_time'])
        if last_end.date() == datetime.date.today():
            st.session_state.default_start = last_end.time()
    
    # 结束时间默认 +30分钟
    st.session_state.default_end = (datetime.datetime.combine(datetime.date.today(), st.session_state.default_start) + datetime.timedelta(minutes=30)).time()

c1, c2 = st.columns(2)
with c1:
    st.caption("开始时间")
    # 核心：step=300 秒 = 5分钟
    inp_start = st.time_input("Start", value=st.session_state.default_start, step=300, label_visibility="collapsed")
with c2:
    st.caption("结束时间")
    inp_end = st.time_input("End", value=st.session_state.default_end, step=300, label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True)


# === 区域 2: 五级分类 (完全掌控) ===
st.markdown('<div class="neon-card" style="border-left-color: #ec4899;">', unsafe_allow_html=True)
st.markdown('<div class="card-title">🧬 内容定义 (CONTEXT)</div>', unsafe_allow_html=True)

# 1. Episode (最高频的入口)
st.markdown("**🎯 行为片段 (Episode)** - *你在做什么？*")
episode_hist = get_history_options("episode")
val_episode = hybrid_input("行为片段", "episode", episode_hist, icon="")

# 智能预填充：如果选了历史Episode，尝试找回它上次的分类
prefill = {}
if val_episode in episode_hist and st.session_state.activities:
    # 倒序查找最近一次该episode的记录
    for act in reversed(st.session_state.activities):
        if act['episode'] == val_episode:
            prefill = act
            break

st.markdown("---")
st.markdown("**⛓️ 四级分类体系** - *定义性质*")

# 2x2 布局
col_a, col_b = st.columns(2)

with col_a:
    st.caption("1. 需求 (Demand)")
    # 如果有预填充，把历史值放到列表最前
    hist_demand = get_history_options("demand")
    val_demand = hybrid_input("需求", "demand", hist_demand)
    
    st.caption("3. 活动 (Activity)")
    hist_activity = get_history_options("activity")
    val_activity = hybrid_input("活动", "activity", hist_activity)

with col_b:
    st.caption("2. 企划 (Project)")
    hist_project = get_history_options("project")
    val_project = hybrid_input("企划", "project", hist_project)
    
    st.caption("4. 行为 (Behavior)")
    hist_behavior = get_history_options("behavior")
    val_behavior = hybrid_input("行为", "behavior", hist_behavior)

st.markdown('</div>', unsafe_allow_html=True)

# === 提交按钮 ===
if st.button("🚀 写入日志 (LOG ENTRY)"):
    if not val_episode:
        st.error("⚠️ 至少得写个名字吧！(行为片段)")
    else:
        # 1. 优先使用手动输入的值，如果没填手动，检查下拉是否选了
        # (Hybrid组件已经处理好了返回逻辑)
        
        # 2. 构建时间
        today = datetime.date.today()
        dt_start = datetime.datetime.combine(today, inp_start)
        dt_end = datetime.datetime.combine(today, inp_end)
        if dt_end < dt_start: dt_end += datetime.timedelta(days=1)
        duration = int((dt_end - dt_start).total_seconds() / 60)
        
        # 3. 记录
        new_record = {
            "id": int(time.time()),
            "episode": val_episode,
            "demand": val_demand or "未分类",
            "project": val_project or "未分类",
            "activity": val_activity or "未分类",
            "behavior": val_behavior or "未分类",
            "start_time": dt_start.isoformat(),
            "end_time": dt_end.isoformat(),
            "duration": duration,
            "color": random.choice(['#6366f1', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b']), # 随机霓虹色
            "created_at": datetime.datetime.now().isoformat()
        }
        
        st.session_state.activities.append(new_record)
        st.session_state.activities.sort(key=lambda x: x['start_time'])
        save_data(st.session_state.activities)
        
        # 4. 更新默认时间
        st.session_state.default_start = dt_end.time()
        st.session_state.default_end = (dt_end + datetime.timedelta(minutes=30)).time()
        
        st.success(f"⚡ 已写入: {val_episode}")
        time.sleep(0.5)
        st.rerun()

# ==========================================
# 4. 可视化与历史 (Visualization)
# ==========================================

if st.session_state.activities:
    st.markdown("---")
    st.markdown('<div style="text-align:center; font-weight:800; color:#94a3b8; margin-bottom:10px;">📅 今日时空分布 (VISUALIZATION)</div>', unsafe_allow_html=True)
    
    # 1. 数据准备
    df = pd.DataFrame(st.session_state.activities)
    
    # 过滤今天的数据用于画图
    today_str = datetime.date.today().isoformat()
    today_df = df[df['start_time'].str.startswith(today_str)].copy()
    
    if not today_df.empty:
        # 2. Plotly 甘特图
        fig = px.timeline(
            today_df, 
            x_start="start_time", 
            x_end="end_time", 
            y="demand", # Y轴按需求分类
            color="project", # 颜色按企划分类
            hover_data=["episode", "duration"],
            template="plotly_dark", # 深色主题
            height=300
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="", showgrid=True, gridcolor='#334155'),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    # 3. 卡片式历史列表
    st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
    for act in reversed(st.session_state.activities[-10:]): # 只显示最近10条
        s = datetime.datetime.fromisoformat(act['start_time']).strftime('%H:%M')
        e = datetime.datetime.fromisoformat(act['end_time']).strftime('%H:%M')
        
        st.markdown(f"""
        <div class="history-item" style="border-left-color: {act.get('color', '#10b981')}">
            <div>
                <div style="font-size:16px; font-weight:700; color:#fff;">{act['episode']}</div>
                <div style="font-size:12px; color:#94a3b8;">
                    {act['demand']} > {act['project']} > {act['activity']}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:14px; font-weight:bold; color:#e2e8f0;">{s} - {e}</div>
                <div style="font-size:12px; color:#64748b;">{act['duration']} min</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
