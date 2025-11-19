import streamlit as st
import json
import datetime
import os
import time
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ==========================================
# 1. 赛博空间配置 (Cyber Config)
# ==========================================
st.set_page_config(
    page_title="Chronos Map",
    page_icon="🛰️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
ACTIVITIES_FILE = os.path.join(DATA_DIR, "activities.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")

# --- 霓虹 CSS 系统 ---
st.markdown("""
<style>
    /* 深空背景 */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #020617 100%);
        color: #e2e8f0;
    }
    header, footer, #MainMenu { visibility: hidden; }
    
    /* 玻璃拟态卡片 */
    .glass-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    /* 标题 */
    .neon-text {
        font-family: 'Courier New', monospace;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #4ade80, #2dd4bf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 15px;
    }
    
    /* 输入组件定制 */
    .stSelectbox div[data-baseweb="select"] > div, 
    .stTextInput input, .stTimeInput input {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #fff !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }
    
    /* 按钮特效 */
    .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        height: 55px !important;
        border-radius: 16px !important;
        font-weight: bold !important;
        font-size: 18px !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        box-shadow: 0 0 25px rgba(139, 92, 246, 0.7);
        transform: scale(1.02);
    }
    
    /* 地图容器微调 */
    iframe { border-radius: 16px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 数据与逻辑核心
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

# 初始化 Session
if 'activities' not in st.session_state:
    st.session_state.activities = load_json(ACTIVITIES_FILE, [])
if 'templates' not in st.session_state:
    st.session_state.templates = load_json(TEMPLATES_FILE, {})
    
# 智能提取历史分类选项
def get_options(field):
    # 从 activities 中提取所有唯一的分类值
    values = set([a.get(field, "") for a in st.session_state.activities if a.get(field)])
    # 加上 "➕ 新建..." 选项
    return sorted(list(values)) + ["➕ 新建/自定义..."]

# ==========================================
# 3. UI 构建
# ==========================================

# 顶部 Logo
st.markdown("""
    <div style='text-align:center; padding: 20px 0 30px 0;'>
        <div style='font-size:32px;'>🌌 CHRONOS <span style='font-size:14px; vertical-align:middle; background:#333; padding:2px 6px; border-radius:4px;'>MAP</span></div>
    </div>
""", unsafe_allow_html=True)

# ------------------------------------------
# 卡片 A: 行为定义 (Context)
# ------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="neon-text">01 // 行为定义 (CONTEXT)</div>', unsafe_allow_html=True)

# 1. 核心入口：选择模板 OR 新建
# 获取所有已知的行为片段(Episode)名称
known_episodes = list(st.session_state.templates.keys())
episode_options = ["✨ 输入新内容..."] + known_episodes

selected_episode_opt = st.selectbox("准备做什么？", episode_options, label_visibility="collapsed")

final_episode_name = ""
final_template = {}
is_new_template = False

if selected_episode_opt == "✨ 输入新内容...":
    # === 新建模式 ===
    is_new_template = True
    col_ep, col_tip = st.columns([3, 1])
    with col_ep:
        final_episode_name = st.text_input("输入活动名称", placeholder="如: 探索火星", label_visibility="collapsed")
    
    if final_episode_name:
        # 检查是否碰巧输了一个已存在的名字
        if final_episode_name in st.session_state.templates:
             st.info(f"💡 发现 '{final_episode_name}' 已有模板，将使用旧分类")
             final_template = st.session_state.templates[final_episode_name]
             is_new_template = False
        else:
            # 真正的全新内容 -> 显示分类选择器
            st.markdown("""<div style='margin: 10px 0; height:1px; background:rgba(255,255,255,0.1);'></div>""", unsafe_allow_html=True)
            st.caption("构建分类体系 (第一次输入需完善，下次自动记住)")
            
            # 辅助函数：处理 下拉+新建 的逻辑
            def smart_select(label, field_name):
                opts = get_options(field_name)
                sel = st.selectbox(label, opts, key=f"sel_{field_name}")
                if sel == "➕ 新建/自定义...":
                    return st.text_input(f"输入新{label}", key=f"txt_{field_name}")
                return sel

            c1, c2 = st.columns(2)
            with c1:
                d = smart_select("需求 (Demand)", "demand")
                a = smart_select("活动 (Activity)", "activity")
            with c2:
                p = smart_select("企划 (Project)", "project")
                b = smart_select("行为 (Behavior)", "behavior")
            
            final_template = {"demand": d, "project": p, "activity": a, "behavior": b}

else:
    # === 模板模式 ===
    final_episode_name = selected_episode_opt
    final_template = st.session_state.templates[selected_episode_opt]
    # 显示一个漂亮的 Badge 告诉用户已经自动填好了
    st.markdown(f"""
    <div style='display:flex; gap:10px; margin-top:10px;'>
        <span style='background:rgba(16, 185, 129, 0.2); color:#34d399; padding:4px 12px; border-radius:12px; font-size:12px; border:1px solid rgba(16, 185, 129, 0.3);'>
            ✓ 已加载模板
        </span>
        <span style='color:#94a3b8; font-size:12px; padding-top:4px;'>
            {final_template.get('demand', '')} > {final_template.get('activity', '')}
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------
# 卡片 B: 时空定位 (Space-Time)
# ------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="neon-text">02 // 时空定位 (LOCATOR)</div>', unsafe_allow_html=True)

# 1. 时间 (5分钟刻度)
if 'def_start' not in st.session_state:
    # 默认逻辑：接续上一条，或者当前时间取整
    now = datetime.datetime.now()
    if st.session_state.activities:
        last = st.session_state.activities[-1]
        try:
            last_end = datetime.datetime.fromisoformat(last['end_time'])
            st.session_state.def_start = last_end.time()
        except: st.session_state.def_start = now.time()
    else:
        st.session_state.def_start = now.time()
        
    st.session_state.def_end = (datetime.datetime.combine(datetime.date.today(), st.session_state.def_start) + datetime.timedelta(minutes=30)).time()

c_t1, c_t2 = st.columns(2)
with c_t1:
    st.caption("开始")
    inp_start = st.time_input("S", value=st.session_state.def_start, step=300, label_visibility="collapsed")
with c_t2:
    st.caption("结束")
    inp_end = st.time_input("E", value=st.session_state.def_end, step=300, label_visibility="collapsed")

# 2. 地点与地图
st.markdown("""<div style='margin: 15px 0 5px 0; font-size:12px; color:#94a3b8;'>LOCATION</div>""", unsafe_allow_html=True)

# 地点名称输入
col_loc, col_map_btn = st.columns([4, 1])
with col_loc:
    inp_loc_name = st.text_input("地点名称", placeholder="如: 望京SOHO", label_visibility="collapsed")
with col_map_btn:
    show_map = st.toggle("🌍", help="打开地图选点")

lat, lng = None, None

# 只有当开关打开时才加载地图，节省资源，保持页面清爽
if show_map:
    st.caption("👆 点击地图选择位置")
    # 默认坐标：北京 (或者你可以设为上一条记录的坐标)
    default_loc = [39.9042, 116.4074] 
    if st.session_state.activities:
        last_act = st.session_state.activities[-1]
        if last_act.get('lat'):
            default_loc = [last_act['lat'], last_act['lng']]
            
    m = folium.Map(location=default_loc, zoom_start=14, tiles="CartoDB dark_matter")
    
    # 如果有点击，添加标记
    if 'map_clicked' in st.session_state and st.session_state.map_clicked:
        folium.Marker(
            [st.session_state.map_clicked['lat'], st.session_state.map_clicked['lng']],
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    map_data = st_folium(m, height=250, width="100%", key="map_picker")
    
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lng = map_data["last_clicked"]["lng"]
        st.session_state.map_clicked = {"lat": lat, "lng": lng} # 存一下，防止刷新消失
        st.info(f"📍 已定位: {lat:.4f}, {lng:.4f}")

st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------
# 提交按钮
# ------------------------------------------
if st.button("🚀 写入时空日志"):
    if not final_episode_name:
        st.error("⚠️ 请输入活动名称")
    else:
        # 1. 如果是新模板，保存它
        if is_new_template:
            st.session_state.templates[final_episode_name] = final_template
            save_json(TEMPLATES_FILE, st.session_state.templates)
            
        # 2. 计算时间
        today = datetime.date.today()
        dt_start = datetime.datetime.combine(today, inp_start)
        dt_end = datetime.datetime.combine(today, inp_end)
        if dt_end < dt_start: dt_end += datetime.timedelta(days=1)
        duration = int((dt_end - dt_start).total_seconds() / 60)
        
        # 3. 保存记录
        new_rec = {
            "id": int(time.time()),
            "episode": final_episode_name,
            # 展开分类
            "demand": final_template.get("demand", "未分类"),
            "project": final_template.get("project", "未分类"),
            "activity": final_template.get("activity", "未分类"),
            "behavior": final_template.get("behavior", "未分类"),
            # 时间与地点
            "start_time": dt_start.isoformat(),
            "end_time": dt_end.isoformat(),
            "duration": duration,
            "location": inp_loc_name,
            "lat": lat if lat else (st.session_state.get('map_clicked', {}).get('lat')),
            "lng": lng if lng else (st.session_state.get('map_clicked', {}).get('lng')),
            "created_at": datetime.datetime.now().isoformat()
        }
        
        st.session_state.activities.append(new_rec)
        st.session_state.activities.sort(key=lambda x: x['start_time'])
        save_json(ACTIVITIES_FILE, st.session_state.activities)
        
        # 4. 更新默认时间
        st.session_state.def_start = dt_end.time()
        st.session_state.def_end = (dt_end + datetime.timedelta(minutes=30)).time()
        
        st.balloons() # 庆祝一下
        time.sleep(1)
        st.rerun()

# ------------------------------------------
# 卡片 C: 仪表盘 (Dashboard) - 甜甜圈图
# ------------------------------------------
if st.session_state.activities:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="neon-text">03 // 时空分布 (VISUALS)</div>', unsafe_allow_html=True)
    
    # 准备数据
    df = pd.DataFrame(st.session_state.activities)
    today_str = datetime.date.today().isoformat()
    today_df = df[df['start_time'].str.startswith(today_str)]
    
    if not today_df.empty:
        # 🎨 甜甜圈图
        fig = px.pie(
            today_df, 
            values='duration', 
            names='demand', 
            hole=0.6, # 甜甜圈孔径
            color_discrete_sequence=px.colors.qualitative.Plotly, # 鲜艳配色
            title="今日需求分布 (Demand)"
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#e2e8f0',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=30, b=0, l=0, r=0),
            height=300
        )
        
        # 中心显示总时长
        total_min = today_df['duration'].sum()
        fig.add_annotation(text=f"{total_min//60}h {total_min%60}m", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="white")
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.caption("今日暂无数据")

    st.markdown('</div>', unsafe_allow_html=True)
