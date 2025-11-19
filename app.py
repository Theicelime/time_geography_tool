# app.py
import streamlit as st
import json
import datetime
from datetime import timedelta
import os
import time
import pandas as pd

# ==========================================
# 1. 配置与样式 (UI/UX 核心优化)
# ==========================================
st.set_page_config(
    page_title="时空轨迹日志",
    page_icon="🕰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 定义色彩系统 (莫兰迪色系/Notion风格)
COLORS = {
    "个人": "#FFD700",   # 金色
    "工作": "#4169E1",   # 皇家蓝
    "交通": "#20B2AA",   # 浅海洋绿
    "社交": "#FF69B4",   # 亮粉
    "Gap":  "#E0E0E0",   # 灰色(空缺)
    "Bg":   "#F7F9FC"    # 背景色
}

# 注入自定义 CSS
st.markdown(f"""
<style>
    /* 全局背景 */
    .stApp {{
        background-color: {COLORS['Bg']};
    }}
    
    /* 隐藏顶部 Hamburger 菜单和 Footer (让界面更像 App) */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* 标题样式 */
    .main-title {{
        font-size: 1.5rem;
        font-weight: 700;
        color: #333;
        margin-bottom: 0.5rem;
        padding-left: 0.5rem;
        border-left: 5px solid #1f77b4;
    }}
    
    /* 卡片容器样式 */
    .card-container {{
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }}
    
    /* 移动端时间轴样式 */
    .timeline-wrapper {{
        width: 100%;
        height: 24px;
        background-color: #eee;
        border-radius: 12px;
        display: flex;
        overflow: hidden;
        margin-bottom: 10px;
        border: 1px solid #ddd;
    }}
    .timeline-segment {{
        height: 100%;
        transition: all 0.3s;
    }}
    
    /* 优化输入框在手机上的点击体验 */
    .stSelectbox, .stTextInput, .stTimeInput {{
        margin-bottom: 5px;
    }}
    div[data-baseweb="select"] > div {{
        background-color: #fff;
        border-radius: 8px;
    }}
    
    /* 大按钮样式 */
    .big-btn button {{
        width: 100%;
        height: 50px !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        background-color: #1f77b4 !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(31, 119, 180, 0.3);
    }}
    .big-btn button:active {{
        transform: scale(0.98);
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 数据管理 (Data Handling)
# ==========================================
DATA_DIR = "data"
ACTIVITIES_FILE = os.path.join(DATA_DIR, "activities.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")
os.makedirs(DATA_DIR, exist_ok=True)

def load_data(file, default):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 初始化 Session State
if 'activities' not in st.session_state:
    st.session_state.activities = load_data(ACTIVITIES_FILE, [])
    # 确保按时间排序
    st.session_state.activities.sort(key=lambda x: x['start_time'])

if 'templates' not in st.session_state:
    # 默认模板：Emoji + 名称 + 默认分类
    defaults = {
        "😴 睡觉": {"cat": "个人", "loc": "家"},
        "🚇 通勤": {"cat": "交通", "loc": "移动中"},
        "💻 工作": {"cat": "工作", "loc": "公司"},
        "🍱 吃饭": {"cat": "个人", "loc": "餐厅"},
        "📱 玩手机": {"cat": "个人", "loc": "家"}
    }
    st.session_state.templates = load_data(TEMPLATES_FILE, defaults)

# ==========================================
# 3. 核心组件函数
# ==========================================

def render_24h_timeline():
    """渲染顶部的 24 小时多彩时间条"""
    today = datetime.date.today().isoformat()
    today_acts = [a for a in st.session_state.activities if a['start_time'].startswith(today)]
    
    # 计算 HTML 片段
    segments = []
    last_end_min = 0
    
    sorted_acts = sorted(today_acts, key=lambda x: x['start_time'])
    
    for act in sorted_acts:
        start_dt = datetime.datetime.fromisoformat(act['start_time'])
        end_dt = datetime.datetime.fromisoformat(act['end_time'])
        
        # 转换为当天的分钟数 (0-1440)
        start_min = start_dt.hour * 60 + start_dt.minute
        end_min = end_dt.hour * 60 + end_dt.minute
        
        # 1. 处理空隙 (Gap)
        if start_min > last_end_min:
            gap_width = ((start_min - last_end_min) / 1440) * 100
            segments.append(f'<div class="timeline-segment" style="width:{gap_width}%; background-color:{COLORS["Gap"]};" title="空缺"></div>')
            
        # 2. 处理活动
        width = ((end_min - start_min) / 1440) * 100
        # 根据分类简单配色
        color = COLORS.get("个人", "#ccc")
        if "工作" in act.get('description', '') or "工作" in act.get('episode', ''): color = COLORS["工作"]
        elif "通勤" in act.get('episode', ''): color = COLORS["交通"]
        
        segments.append(f'<div class="timeline-segment" style="width:{width}%; background-color:{color};" title="{act["episode"]}"></div>')
        last_end_min = end_min
        
    # 处理剩余时间
    if last_end_min < 1440:
        rem_width = ((1440 - last_end_min) / 1440) * 100
        segments.append(f'<div class="timeline-segment" style="width:{rem_width}%; background-color:{COLORS["Gap"]}; opacity: 0.5;" title="剩余时间"></div>')
        
    html = f"""
    <div style="margin-bottom:5px; font-size:12px; color:#666; display:flex; justify-content:space-between;">
        <span>00:00</span><span>今日时间轴</span><span>24:00</span>
    </div>
    <div class="timeline-wrapper">
        {''.join(segments)}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def mobile_input_form():
    """手机端极简输入表单"""
    
    # 1. 顶部显示 24H 状态
    with st.container():
        st.markdown('<div class="main-title">📅 今日轨迹</div>', unsafe_allow_html=True)
        render_24h_timeline()

    # 2. 计算智能默认时间
    now = datetime.datetime.now()
    default_start = now
    default_end = now
    
    # 查找今日最后一条记录
    if st.session_state.activities:
        last_act = st.session_state.activities[-1]
        last_end = datetime.datetime.fromisoformat(last_act['end_time'])
        
        # 如果最后一条记录是今天(或者昨天很晚)，且不是未来时间，则开始时间自动接续
        if last_end <= now:
            default_start = last_end
        else:
            # 如果最后一条记录在未来(比如误操作)，默认当前时间
            default_start = now
    
    # 3. 卡片式表单区域
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    # === 时间控制区 (左右布局) ===
    st.caption("⏱️ 时间设定")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        # Streamlit 的 time_input 默认步长 15分钟，step=60 可以精确到分
        input_start_time = st.time_input("开始", value=default_start.time(), step=60)
    with col_t2:
        # 结束时间默认为当前
        input_end_time = st.time_input("结束", value=default_end.time(), step=60)
        
    # === 内容控制区 ===
    st.caption("📝 活动内容")
    
    # 模板快速选择 (Pills 样式模拟)
    template_names = list(st.session_state.templates.keys())
    selected_template = st.selectbox("选择常见活动 (或直接输入)", [""] + template_names)
    
    # 如果选了模板，自动填入地点；没选则允许手动
    default_loc = ""
    default_desc = ""
    if selected_template:
        t_data = st.session_state.templates[selected_template]
        default_loc = t_data['loc']
        default_desc = selected_template
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        # 如果用户想自定义，可以在 selectbox 选空然后下面自己写，或者直接覆盖
        # 这里为了手机方便，直接用 Text Input，如果选了模板会覆盖 Value
        # 注意：Streamlit 更新 Input value 需要用 key session state
        
        # 这里做一个简单处理：如果选了模板，episode 就是模板名
        # 如果没选，提供一个输入框
        episode_input = st.text_input("活动名称", value=selected_template.split(" ")[-1] if selected_template else "", placeholder="例如: 喝咖啡")
        
    with col_c2:
        location_input = st.text_input("地点", value=default_loc, placeholder="例如: 公司")
        
    st.markdown('</div>', unsafe_allow_html=True) # End card
    
    # === 提交按钮 ===
    # 计算时长用于显示
    # 注意：这里只是静态显示，不会随上面时间变化实时变(除非rerun)，但提交时会准确计算
    submit_container = st.container()
    with submit_container:
        st.markdown('<div class="big-btn">', unsafe_allow_html=True)
        submitted = st.button("✅ 确认记录")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # === 处理提交逻辑 ===
    if submitted:
        # 1. 构建完整的 datetime
        today_date = datetime.date.today()
        dt_start = datetime.datetime.combine(today_date, input_start_time)
        dt_end = datetime.datetime.combine(today_date, input_end_time)
        
        # 跨天处理：如果结束时间 小于 开始时间，说明跨天了(或者是第二天凌晨)
        # 这里简单处理：假设是跨到第二天
        if dt_end < dt_start:
            dt_end += timedelta(days=1)
            
        duration = int((dt_end - dt_start).total_seconds() / 60)
        
        if duration <= 0:
            st.error("⚠️ 结束时间必须晚于开始时间")
        elif not episode_input:
            st.error("⚠️ 请填写活动名称")
        else:
            # 保存数据
            new_act = {
                "id": int(time.time()),
                "start_time": dt_start.isoformat(),
                "end_time": dt_end.isoformat(),
                "duration": duration,
                "episode": episode_input,
                "location_name": location_input,
                "description": selected_template, # 存一下原始模板名作为分类参考
                "created_at": datetime.datetime.now().isoformat()
            }
            
            st.session_state.activities.append(new_act)
            # 重新排序
            st.session_state.activities.sort(key=lambda x: x['start_time'])
            save_data(ACTIVITIES_FILE, st.session_state.activities)
            
            st.success(f"已记录: {episode_input} ({duration}分钟)")
            time.sleep(0.5)
            st.rerun()

def timeline_list_view():
    """下方的详细列表视图"""
    st.markdown("### 📜 详细记录")
    
    if not st.session_state.activities:
        st.info("今天还没有记录哦，快去添加吧！")
        return

    # 按倒序显示，最近的在最上面
    for i, act in enumerate(reversed(st.session_state.activities)):
        start = datetime.datetime.fromisoformat(act['start_time'])
        end = datetime.datetime.fromisoformat(act['end_time'])
        
        # 卡片样式
        st.markdown(f"""
        <div style="background:white; padding:12px; border-radius:8px; border-left:4px solid #1f77b4; margin-bottom:10px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="font-weight:bold; font-size:16px;">{act['episode']}</div>
                <div style="color:#888; font-size:14px;">{act['duration']} min</div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:5px; color:#666; font-size:14px;">
                <span>🕒 {start.strftime('%H:%M')} - {end.strftime('%H:%M')}</span>
                <span>📍 {act.get('location_name', '未知')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 删除按钮 (为了美观放这里，虽然有点破坏纯HTML感，但必须要有交互)
        col_del, col_empty = st.columns([1, 5])
        with col_del:
            if st.button("🗑️", key=f"del_{act['id']}", help="删除此条"):
                st.session_state.activities = [a for a in st.session_state.activities if a['id'] != act['id']]
                save_data(ACTIVITIES_FILE, st.session_state.activities)
                st.rerun()

# ==========================================
# 4. 统计面板 (简易版)
# ==========================================
def stats_view():
    st.markdown('<div class="main-title">📊 数据统计</div>', unsafe_allow_html=True)
    
    if not st.session_state.activities:
        st.write("暂无数据")
        return
        
    df = pd.DataFrame(st.session_state.activities)
    df['start_dt'] = pd.to_datetime(df['start_time'])
    df['date'] = df['start_dt'].dt.date
    
    # 今日概览
    today = datetime.date.today()
    today_df = df[df['date'] == today]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("今日活动数", len(today_df))
    with col2:
        total_min = today_df['duration'].sum()
        st.metric("记录时长", f"{total_min/60:.1f}小时")
    with col3:
        gap = 1440 - total_min
        st.metric("未记录(空缺)", f"{gap/60:.1f}小时", delta_color="inverse")
        
    st.markdown("---")
    st.caption("💡 提示：保持记录连续性可以获得更准确的时空分析。")

# ==========================================
# 5. 主程序入口
# ==========================================
def main():
    # 侧边栏导航
    with st.sidebar:
        st.title("功能菜单")
        page = st.radio("前往", ["📝 记录", "📊 统计", "⚙️ 设置"])
        st.markdown("---")
        if st.button("🗑️ 清空所有数据"):
            st.session_state.activities = []
            save_data(ACTIVITIES_FILE, [])
            st.rerun()

    if page == "📝 记录":
        mobile_input_form()
        timeline_list_view()
    elif page == "📊 统计":
        stats_view()
    elif page == "⚙️ 设置":
        st.markdown("### 模板管理")
        st.info("此处未来可添加更多自定义模板功能")
        st.json(st.session_state.templates)

if __name__ == "__main__":
    main()
