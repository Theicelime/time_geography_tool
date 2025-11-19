import streamlit as st
import json
import datetime
import os
import time
import pandas as pd

# ==========================================
# 1. 页面配置 & iOS 风格 CSS
# ==========================================
st.set_page_config(
    page_title="OneDay",
    page_icon="🕰️",
    layout="centered", # 手机端用 centered 布局更好看，不会太宽
    initial_sidebar_state="collapsed"
)

# 定义数据文件
DATA_FILE = "data/activities.json"
if not os.path.exists("data"): os.makedirs("data")

# --- CSS 美化核心 ---
st.markdown("""
<style>
    /* 全局背景色：iOS 浅灰 */
    .stApp {
        background-color: #F2F2F7;
    }
    
    /* 隐藏顶部红线和菜单 */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 标题样式 */
    .ios-header {
        font-size: 22px;
        font-weight: 800;
        color: #000;
        padding: 20px 0 10px 0;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 卡片样式：白色圆角，阴影 */
    .ios-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    
    /* 输入框标签样式 */
    .label-text {
        font-size: 13px;
        color: #8E8E93;
        margin-bottom: 5px;
        font-weight: 600;
    }
    
    /* 提交按钮：iOS 蓝色大按钮 */
    .stButton button {
        background-color: #007AFF !important;
        color: white !important;
        border-radius: 12px !important;
        height: 50px !important;
        font-size: 17px !important;
        font-weight: 600 !important;
        border: none !important;
        width: 100%;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
    }
    .stButton button:active {
        transform: scale(0.98);
        background-color: #005ECB !important;
    }
    
    /* 调整 Streamlit 原生组件间距 */
    .stTimeInput, .stTextInput, .stSelectbox {
        margin-bottom: 0px;
    }
    
    /* 历史记录条目 */
    .history-item {
        padding: 12px 0;
        border-bottom: 1px solid #E5E5EA;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .history-item:last-child { border-bottom: none; }
    
    /* 时间轴容器 */
    .timeline-bar {
        height: 12px;
        border-radius: 6px;
        background-color: #E5E5EA;
        overflow: hidden;
        display: flex;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 逻辑处理 (Session State 防止跳变)
# ==========================================

# 加载数据
if 'activities' not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            st.session_state.activities = json.load(f)
    else:
        st.session_state.activities = []

# --- 核心修复：初始化输入框状态，防止刷新重置 ---
# 只有当 session_state 中没有值时，才初始化默认值
# 这样你在输入时，页面刷新也不会把你的时间改回去
if 'input_start' not in st.session_state:
    # 默认开始时间：最后一条记录的结束时间，或者当前时间
    if st.session_state.activities:
        last_end_str = st.session_state.activities[-1]['end_time']
        st.session_state.input_start = datetime.datetime.fromisoformat(last_end_str).time()
    else:
        st.session_state.input_start = datetime.datetime.now().time()

if 'input_end' not in st.session_state:
    # 默认结束时间：开始时间 + 1小时
    st.session_state.input_end = (datetime.datetime.combine(datetime.date.today(), st.session_state.input_start) + datetime.timedelta(hours=1)).time()

if 'input_act' not in st.session_state:
    st.session_state.input_act = ""

if 'input_loc' not in st.session_state:
    st.session_state.input_loc = ""

# ==========================================
# 3. 界面渲染
# ==========================================

# --- 顶部：今日时间轴可视化 ---
def render_timeline():
    today_str = datetime.date.today().isoformat()
    # 筛选今天的活动
    today_acts = [a for a in st.session_state.activities if a['start_time'].startswith(today_str)]
    
    st.markdown('<div class="ios-header">今日轨迹</div>', unsafe_allow_html=True)
    
    # 计算时间轴 HTML
    segments = ""
    # 简单的 0-24h 映射
    timeline_html = '<div class="timeline-bar">'
    
    # 这里做一个简单的可视化逻辑：把一天按分钟(1440)切分
    # 为了性能，我们只渲染已有的片段
    
    # 先排序
    today_acts.sort(key=lambda x: x['start_time'])
    
    last_min = 0
    for act in today_acts:
        s = datetime.datetime.fromisoformat(act['start_time'])
        e = datetime.datetime.fromisoformat(act['end_time'])
        s_min = s.hour * 60 + s.minute
        e_min = e.hour * 60 + e.minute
        
        # Gap (空闲时间 - 灰色)
        if s_min > last_min:
            width = ((s_min - last_min) / 1440) * 100
            timeline_html += f'<div style="width:{width}%; background:#E5E5EA;"></div>'
            
        # Activity (活动时间 - 蓝色)
        act_width = ((e_min - s_min) / 1440) * 100
        # 根据不同活动给点颜色（这里简单用蓝色，你可以扩展）
        color = "#007AFF" 
        if "睡" in act['episode']: color = "#5856D6" # 紫色
        if "吃" in act['episode']: color = "#FF9500" # 橙色
        if "工作" in act['episode']: color = "#34C759" # 绿色
        
        timeline_html += f'<div style="width:{act_width}%; background:{color};"></div>'
        last_min = e_min

    # 剩余的灰色
    if last_min < 1440:
        rem_width = ((1440 - last_min) / 1440) * 100
        timeline_html += f'<div style="width:{rem_width}%; background:#E5E5EA;"></div>'
        
    timeline_html += '</div>'
    
    # 渲染卡片
    st.markdown(f"""
    <div class="ios-card">
        <div style="display:flex; justify-content:space-between; color:#8E8E93; font-size:12px; font-weight:600;">
            <span>00:00</span>
            <span>12:00</span>
            <span>24:00</span>
        </div>
        {timeline_html}
        <div style="text-align:center; margin-top:10px; font-size:14px; color:#333;">
            已记录: <b>{len(today_acts)}</b> 个活动
        </div>
    </div>
    """, unsafe_allow_html=True)

render_timeline()

# --- 中部：输入表单 ---
st.markdown('<div class="label-text" style="margin-left:5px;">新建记录</div>', unsafe_allow_html=True)
with st.container():
    # 使用 HTML 容器模拟卡片背景，Streamlit 组件放在里面
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    
    # 1. 活动与地点 (并排)
    c1, c2 = st.columns([3, 2])
    with c1:
        # 使用 key 来绑定 session_state，这样值就会固定住
        act_name = st.text_input("活动内容", key="input_act", placeholder="如: 睡觉、工作")
    with c2:
        loc_name = st.text_input("地点", key="input_loc", placeholder="如: 家")
    
    st.write("") # 增加一点间距
    
    # 2. 时间选择 (并排)
    # 关键点：key绑定session_state，step=60允许精确到分钟
    t1, t2 = st.columns(2)
    with t1:
        start_t = st.time_input("开始时间", key="input_start", step=60)
    with t2:
        end_t = st.time_input("结束时间", key="input_end", step=60)

    st.markdown('</div>', unsafe_allow_html=True)

    # 3. 提交按钮
    if st.button("保存记录"):
        # === 验证与保存逻辑 (只在点击时运行) ===
        
        # 构建完整的 datetime 对象
        today = datetime.date.today()
        dt_start = datetime.datetime.combine(today, start_t)
        dt_end = datetime.datetime.combine(today, end_t)
        
        # 逻辑修正：如果结束时间小于开始时间，视为跨天（次日）
        # 比如：开始 23:00，结束 01:00 -> 结束其实是明天的 01:00
        if dt_end < dt_start:
            dt_end += datetime.timedelta(days=1)
            is_cross_day = True
        else:
            is_cross_day = False
            
        duration = int((dt_end - dt_start).total_seconds() / 60)
        
        if not act_name:
            st.toast("⚠️ 请填写活动内容", icon="❌")
        elif duration == 0:
             st.toast("⚠️ 持续时间不能为 0", icon="❌")
        else:
            # 保存数据
            new_record = {
                "id": int(time.time()),
                "episode": act_name,
                "location_name": loc_name if loc_name else "未知",
                "start_time": dt_start.isoformat(),
                "end_time": dt_end.isoformat(),
                "duration": duration,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            st.session_state.activities.append(new_record)
            # 按开始时间排序
            st.session_state.activities.sort(key=lambda x: x['start_time'])
            
            # 写入文件
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.activities, f, ensure_ascii=False, indent=2)
            
            # --- 智能重置逻辑 ---
            # 保存成功后，下一次的“开始时间”自动变成这次的“结束时间”
            # 但“结束时间”暂不预设，或设为+1小时
            # 注意：这里修改 session_state，下一次 rerun 就会生效
            st.session_state.input_start = dt_end.time() # 转回 time 对象
            st.session_state.input_end = (dt_end + datetime.timedelta(hours=1)).time()
            st.session_state.input_act = "" # 清空活动名
            # 地点通常不变，不清除 input_loc
            
            if is_cross_day:
                st.toast(f"已保存 (跨天): {act_name}", icon="🌙")
            else:
                st.toast(f"已保存: {act_name}", icon="✅")
            
            time.sleep(0.5)
            st.rerun()

# --- 底部：历史列表 ---
st.markdown('<div class="label-text" style="margin-left:5px; margin-top:20px;">记录列表</div>', unsafe_allow_html=True)
st.markdown('<div class="ios-card" style="padding:10px 20px;">', unsafe_allow_html=True)

if not st.session_state.activities:
    st.markdown('<div style="text-align:center; color:#C7C7CC; padding:20px;">暂无记录</div>', unsafe_allow_html=True)
else:
    # 倒序显示
    for act in reversed(st.session_state.activities):
        s_time = datetime.datetime.fromisoformat(act['start_time']).strftime('%H:%M')
        e_time = datetime.datetime.fromisoformat(act['end_time']).strftime('%H:%M')
        
        # 简单的删除交互
        col_info, col_del = st.columns([5, 1])
        with col_info:
            st.markdown(f"""
            <div style="font-weight:600; font-size:16px; color:#000;">{act['episode']} <span style="font-weight:400; color:#8E8E93; font-size:14px; margin-left:5px;">@{act['location_name']}</span></div>
            <div style="color:#8E8E93; font-size:13px; margin-top:2px;">{s_time} - {e_time} · {act['duration']} 分钟</div>
            """, unsafe_allow_html=True)
            st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True) # Spacer
        
        with col_del:
            if st.button("✕", key=f"del_{act['id']}", help="删除"):
                st.session_state.activities = [a for a in st.session_state.activities if a['id'] != act['id']]
                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.activities, f)
                st.rerun()
                
st.markdown('</div>', unsafe_allow_html=True)
