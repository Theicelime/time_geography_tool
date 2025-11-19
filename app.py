import streamlit as st
import json
import datetime
import os
import time
import pandas as pd

# ==========================================
# 1. 页面配置
# ==========================================
st.set_page_config(
    page_title="OneDay",
    page_icon="🕰️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 确保数据目录存在
if not os.path.exists("data"):
    os.makedirs("data")
DATA_FILE = "data/activities.json"

# ==========================================
# 2. CSS 美化 (iOS 风格)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #F2F2F7; }
    header, footer, #MainMenu { visibility: hidden; }
    
    /* 标题区 */
    .ios-header {
        font-size: 20px; font-weight: 700; color: #1C1C1E;
        padding: 15px 5px; display: flex; justify-content: space-between; align-items: center;
    }
    
    /* 卡片通用样式 */
    .ios-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* 按钮样式优化 */
    .stButton button {
        background-color: #007AFF !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        width: 100%;
    }
    
    /* 紧凑布局调整 */
    .stTimeInput div, .stDateInput div, .stTextInput div { margin-bottom: 0px; }
    
    /* 时间轴 */
    .timeline-container {
        height: 16px; background-color: #E5E5EA; border-radius: 8px;
        display: flex; overflow: hidden; margin-top: 8px;
    }
    .timeline-seg { height: 100%; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 数据加载与状态管理
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return [] # 文件损坏时返回空列表

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if 'activities' not in st.session_state:
    st.session_state.activities = load_data()

# 初始化输入状态 (只在第一次加载时运行)
if 'input_init' not in st.session_state:
    st.session_state.input_date = datetime.date.today()
    st.session_state.input_start = datetime.datetime.now().time()
    
    # 尝试从最后一条记录获取接续时间
    if st.session_state.activities:
        try:
            last_act = st.session_state.activities[-1]
            last_end = datetime.datetime.fromisoformat(last_act['end_time'])
            st.session_state.input_date = last_end.date() # 接续日期
            st.session_state.input_start = last_end.time() # 接续时间
        except:
            pass
            
    st.session_state.input_end = (datetime.datetime.combine(datetime.date.today(), st.session_state.input_start) + datetime.timedelta(hours=1)).time()
    st.session_state.input_init = True

# ==========================================
# 4. 组件：可视化时间轴
# ==========================================
def render_timeline(current_date):
    """渲染指定日期的24小时时间轴"""
    date_str = current_date.isoformat()
    
    # 获取当天的活动 (注意：这里简化了逻辑，只显示start_time在今天的，或者涉及今天的)
    # 为了可视化简单，我们只渲染“start_time”在今天的活动
    day_acts = [a for a in st.session_state.activities if a['start_time'].startswith(date_str)]
    day_acts.sort(key=lambda x: x['start_time'])
    
    html_segments = ""
    last_min = 0
    
    for act in day_acts:
        s = datetime.datetime.fromisoformat(act['start_time'])
        e = datetime.datetime.fromisoformat(act['end_time'])
        
        s_min = s.hour * 60 + s.minute
        e_min = e.hour * 60 + e.minute
        
        # 修正跨天显示：如果 e_min < s_min (比如23:00到01:00)，说明跨天了
        # 在当天的时间轴上，它应该一直延伸到24:00 (1440)
        is_cross_day = False
        if e_min < s_min or (e.date() > s.date()):
            e_min = 1440 
            is_cross_day = True
            
        # 绘制 Gap (空闲)
        if s_min > last_min:
            width = ((s_min - last_min) / 1440) * 100
            html_segments += f'<div class="timeline-seg" style="width:{width}%; background-color:#E5E5EA;"></div>'
            
        # 绘制 Activity
        width = ((e_min - s_min) / 1440) * 100
        color = "#007AFF" if not is_cross_day else "#5856D6" # 跨天显示紫色
        html_segments += f'<div class="timeline-seg" style="width:{width}%; background-color:{color};" title="{act["episode"]}"></div>'
        
        last_min = e_min
        
    # 绘制剩余
    if last_min < 1440:
        width = ((1440 - last_min) / 1440) * 100
        html_segments += f'<div class="timeline-seg" style="width:{width}%; background-color:#E5E5EA;"></div>'

    st.markdown(f"""
    <div class="ios-card">
        <div style="font-size:14px; font-weight:600; color:#333; margin-bottom:4px;">
            📊 {current_date.strftime('%m-%d')} 时间分布
        </div>
        <div class="timeline-container">
            {html_segments}
        </div>
        <div style="display:flex; justify-content:space-between; font-size:10px; color:#888; margin-top:4px;">
            <span>00:00</span><span>12:00</span><span>24:00</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. 主界面逻辑
# ==========================================

# 顶部标题栏
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown('<div class="ios-header">DailyLog</div>', unsafe_allow_html=True)
with c2:
    if st.button("重置", help="如果数据坏了点这里"):
        st.session_state.activities = []
        save_data([])
        st.rerun()

# 1. 输入区域
st.markdown('<div class="ios-card">', unsafe_allow_html=True)
st.caption("📝 新建活动")

# 第一行：日期 + 活动名
col_d1, col_d2 = st.columns([1, 2])
with col_d1:
    # 绑定 input_date，允许修改日期补录
    date_val = st.date_input("日期", key="input_date", label_visibility="collapsed")
with col_d2:
    act_val = st.text_input("做什么?", key="input_act", placeholder="如: 睡觉、工作", label_visibility="collapsed")

# 第二行：开始时间 + 结束时间
col_t1, col_t2 = st.columns(2)
with col_t1:
    st.caption("开始时间")
    start_val = st.time_input("Start", key="input_start", step=60, label_visibility="collapsed")
with col_t2:
    st.caption("结束时间")
    end_val = st.time_input("End", key="input_end", step=60, label_visibility="collapsed")

# 提交按钮
if st.button("保存记录"):
    # 构建时间对象
    dt_start = datetime.datetime.combine(date_val, start_val)
    dt_end = datetime.datetime.combine(date_val, end_val)
    
    # 智能跨天处理
    # 如果 结束 < 开始，假设是跨到第二天
    if dt_end < dt_start:
        dt_end += datetime.timedelta(days=1)
        
    duration = int((dt_end - dt_start).total_seconds() / 60)
    
    if not act_val:
        st.toast("⚠️ 请填写活动内容")
    else:
        new_act = {
            "id": int(time.time()),
            "episode": act_val,
            "start_time": dt_start.isoformat(),
            "end_time": dt_end.isoformat(),
            "duration": duration,
            "location": "手动记录"
        }
        
        st.session_state.activities.append(new_act)
        st.session_state.activities.sort(key=lambda x: x['start_time'])
        save_data(st.session_state.activities)
        
        # 自动准备下一条记录
        # 下一次开始 = 这一次结束
        st.session_state.input_start = dt_end.time()
        # 如果跨天了，日期也要变
        st.session_state.input_date = dt_end.date()
        # 结束时间默认 +1 小时
        st.session_state.input_end = (dt_end + datetime.timedelta(hours=1)).time()
        st.session_state.input_act = ""
        
        st.toast(f"✅ 已保存: {act_val}")
        time.sleep(0.5)
        st.rerun()
        
st.markdown('</div>', unsafe_allow_html=True)

# 2. 可视化展示 (展示选择日期的进度)
render_timeline(date_val)

# 3. 历史记录列表 (倒序)
if st.session_state.activities:
    st.markdown("### 📋 记录列表")
    # 仅显示最近 10 条
    for act in reversed(st.session_state.activities[-10:]):
        s = datetime.datetime.fromisoformat(act['start_time'])
        e = datetime.datetime.fromisoformat(act['end_time'])
        
        # 计算是哪天
        day_label = s.strftime('%m-%d')
        if s.date() == datetime.date.today():
            day_label = "今天"
            
        with st.container():
            st.markdown(f"""
            <div class="ios-card" style="padding: 12px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:600; color:#000;">{act['episode']}</div>
                    <div style="font-size:12px; color:#888;">
                        <span style="background:#eee; padding:2px 4px; border-radius:4px;">{day_label}</span> 
                        {s.strftime('%H:%M')} - {e.strftime('%H:%M')} ({act['duration']}m)
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 删除按钮 (独立一行，防止布局挤压)
            if st.button("🗑️ 删除", key=f"del_{act['id']}"):
                st.session_state.activities = [a for a in st.session_state.activities if a['id'] != act['id']]
                save_data(st.session_state.activities)
                st.rerun()
