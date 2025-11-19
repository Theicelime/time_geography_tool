# app.py
import streamlit as st
import pandas as pd
import json
import datetime
from datetime import timedelta
import folium
from streamlit_folium import st_folium
import plotly.express as px
import os
import time
from geopy.geocoders import Nominatim
from collections import Counter

# 1. 页面配置 - 修改：默认收起侧边栏，适配移动端
st.set_page_config(
    page_title="个人活动轨迹日志",
    page_icon="🛤️",
    layout="wide",
    initial_sidebar_state="collapsed" # 手机端默认收起
)

# 数据存储路径
DATA_DIR = "data"
ACTIVITIES_FILE = os.path.join(DATA_DIR, "activities.json")
CLASSIFICATION_FILE = os.path.join(DATA_DIR, "classification_system.json")
LOCATION_TEMPLATES_FILE = os.path.join(DATA_DIR, "location_templates.json")
ACTIVITY_TEMPLATES_FILE = os.path.join(DATA_DIR, "activity_templates.json")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# --- 基础工具函数 (保持不变) ---
def load_json_file(file_path, default_data):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"加载文件 {file_path} 时出错: {e}")
    return default_data

def save_json_file(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存文件 {file_path} 时出错: {e}")
        return False

def initialize_data():
    if 'activities' not in st.session_state:
        st.session_state.activities = load_json_file(ACTIVITIES_FILE, [])
    
    # 默认分类系统 (精简版，防止代码过长)
    default_classification_system = {
        "个人": {
            "个人生理": {"睡觉休息": {"睡觉": ["夜间睡眠", "午睡"], "休息": ["放松"]}, "进食": {"用餐": ["早餐", "午餐", "晚餐"]}},
            "个人休闲": {"娱乐消遣": {"看电视": ["追剧"], "游戏": ["手游"]}, "运动锻炼": {"健身": ["跑步"]}}
        },
        "工作": {"职业工作": {"办公": {"日常办公": ["开会", "写代码", "文档处理"]}}}
    }
    
    if 'classification_system' not in st.session_state:
        st.session_state.classification_system = load_json_file(CLASSIFICATION_FILE, default_classification_system)
    
    default_location_templates = {
        "家": {"category": "居住场所", "tag": "家", "name": "家", "coordinates": None},
        "公司": {"category": "工作场所", "tag": "公司", "name": "办公室", "coordinates": None}
    }
    
    if 'location_templates' not in st.session_state:
        st.session_state.location_templates = load_json_file(LOCATION_TEMPLATES_FILE, default_location_templates)
    
    if 'activity_templates' not in st.session_state:
        st.session_state.activity_templates = load_json_file(ACTIVITY_TEMPLATES_FILE, {})
    
    if 'map_center' not in st.session_state:
        st.session_state.map_center = [39.9042, 116.4074]

def save_all_data():
    save_json_file(ACTIVITIES_FILE, st.session_state.activities)
    save_json_file(CLASSIFICATION_FILE, st.session_state.classification_system)
    save_json_file(LOCATION_TEMPLATES_FILE, st.session_state.location_templates)
    save_json_file(ACTIVITY_TEMPLATES_FILE, st.session_state.activity_templates)

def search_location(query):
    try:
        geolocator = Nominatim(user_agent="personal_activity_tracker_mobile")
        location = geolocator.geocode(query, addressdetails=True, country_codes='cn')
        if location:
            return {"name": location.address, "lat": location.latitude, "lng": location.longitude}
    except:
        return None
    return None

def get_all_episodes():
    episodes = []
    for demand, projects in st.session_state.classification_system.items():
        for project, activities in projects.items():
            for activity, behavior_dict in activities.items():
                for behavior, episode_list in behavior_dict.items():
                    for episode in episode_list:
                        episodes.append({
                            "demand": demand, "project": project, "activity": activity,
                            "behavior": behavior, "episode": episode
                        })
    return episodes

# --- 2. 样式配置 - 修改：增加移动端触摸优化 ---
def apply_custom_css():
    st.markdown("""
    <style>
    /* 移动端大标题 */
    .main-header { font-size: 1.8rem; color: #1f77b4; text-align: center; margin-bottom: 1rem; font-weight: bold; }
    .sub-header { font-size: 1.3rem; color: #2e86ab; margin: 1rem 0; border-bottom: 2px solid #f0f2f6; }
    
    /* 卡片样式 */
    .activity-card {
        background-color: #f8f9fa; padding: 0.8rem; border-radius: 8px;
        border-left: 4px solid #1f77b4; margin-bottom: 0.8rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* 移动端按钮优化：增大点击区域 */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        height: 3.5rem !important; /* 增加高度方便手指点击 */
        font-weight: bold;
    }
    
    /* 调整Tabs样式 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; flex: 1; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 智能地图组件 ---
def smart_map_selector():
    # 简化版地图逻辑
    search_query = st.text_input("🔍 搜索地点", key="loc_search_mobile")
    if search_query:
        res = search_location(search_query)
        if res:
            st.session_state.map_center = [res['lat'], res['lng']]
            st.success(f"已定位: {res['name']}")
            return {"lat": res['lat'], "lng": res['lng']}, res
            
    m = folium.Map(location=st.session_state.map_center, zoom_start=13)
    map_data = st_folium(m, height=300, width="100%", key="smart_map_mobile")
    
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lng = map_data["last_clicked"]["lng"]
        return {"lat": lat, "lng": lng}, None
    return None, None

# --- 4. 核心逻辑：活动记录表单 (重构版) ---
def activity_form():
    st.markdown('<div class="sub-header">📝 记录活动</div>', unsafe_allow_html=True)
    
    # 将界面分为手机版和电脑版
    tab_mobile, tab_desktop = st.tabs(["📱 手机极简模式", "💻 电脑完整模式"])
    
    # ====== 📱 手机极简模式 ======
    with tab_mobile:
        # 1. 一键打卡区
        st.markdown("**⚡ 一键记录 (基于模板)**")
        templates = list(st.session_state.activity_templates.items())
        
        if not templates:
            st.info("👋 暂无模板！请先在'完整模式'录入一次并保存为模板，或在'活动模板'中添加。")
        else:
            # 自动计算时间：从上一个活动结束开始，到当前时间结束
            last_end_time = datetime.datetime.now()
            if st.session_state.activities:
                last_end_time = datetime.datetime.fromisoformat(st.session_state.activities[-1]["end_time"])
            
            current_time = datetime.datetime.now()
            
            # 如果上个活动结束时间在未来(修正错误数据)，或者间隔太久(超过12小时)，就默认当前时间往前推30分钟
            if last_end_time > current_time or (current_time - last_end_time).total_seconds() > 43200:
                start_time_proposal = current_time - timedelta(minutes=30)
                is_continuation = False
            else:
                start_time_proposal = last_end_time
                is_continuation = True

            duration_proposal = int((current_time - start_time_proposal).total_seconds() / 60)
            if duration_proposal < 1: duration_proposal = 1

            # 网格布局按钮
            cols = st.columns(3)
            for idx, (name, temp_data) in enumerate(templates):
                with cols[idx % 3]:
                    # 按钮显示：模板名
                    if st.button(f"{name}", key=f"mob_btn_{idx}", use_container_width=True):
                        # 构建数据
                        new_activity = {
                            "id": len(st.session_state.activities) + 1,
                            "start_time": start_time_proposal.isoformat(),
                            "end_time": current_time.isoformat(),
                            "duration": duration_proposal,
                            "location_category": "快速记录", 
                            "location_tag": "移动端", 
                            "location_name": "一键打卡",
                            "coordinates": None,
                            "demand": temp_data.get("demand", ""),
                            "project": temp_data.get("project", ""),
                            "activity": temp_data.get("activity", ""),
                            "behavior": temp_data.get("behavior", ""),
                            "episode": name,
                            "description": "通过手机一键打卡记录",
                            "created_at": datetime.datetime.now().isoformat()
                        }
                        st.session_state.activities.append(new_activity)
                        save_all_data()
                        # 使用 Toast 提示
                        msg = f"✅ 已记录: {name} ({duration_proposal}分钟)"
                        st.toast(msg, icon="🎉")
                        time.sleep(1)
                        st.rerun()
            
            if is_continuation:
                st.caption(f"🕒 默认接续上个活动，从 {start_time_proposal.strftime('%H:%M')} 开始")
            else:
                st.caption("🕒 间隔过久，默认记录过去30分钟")

        st.markdown("---")
        
        # 2. 手动快速录入 (非模板)
        st.markdown("**✏️ 快速补录**")
        with st.form("mobile_quick_form"):
            # 选择行为
            all_eps = [e["episode"] for e in get_all_episodes()]
            m_episode = st.selectbox("做什么?", [""] + all_eps)
            
            # 时间选择 (简化为时长)
            m_duration = st.slider("持续时长 (分钟)", 5, 240, 60, step=5)
            
            # 地点选择
            loc_opts = [""] + list(st.session_state.location_templates.keys())
            m_location = st.selectbox("在哪?", loc_opts)
            
            m_submit = st.form_submit_button("提交记录")
            
            if m_submit and m_episode:
                # 查找完整分类
                full_cls = None
                for e in get_all_episodes():
                    if e["episode"] == m_episode:
                        full_cls = e
                        break
                
                # 计算时间
                m_end = datetime.datetime.now()
                m_start = m_end - timedelta(minutes=m_duration)
                
                # 地点信息
                loc_cat, loc_tag, loc_name = "移动端", "手动", "未知"
                if m_location and m_location in st.session_state.location_templates:
                    lt = st.session_state.location_templates[m_location]
                    loc_cat, loc_tag, loc_name = lt["category"], lt["tag"], lt["name"]
                
                act = {
                    "id": len(st.session_state.activities) + 1,
                    "start_time": m_start.isoformat(),
                    "end_time": m_end.isoformat(),
                    "duration": m_duration,
                    "location_category": loc_cat,
                    "location_tag": loc_tag,
                    "location_name": loc_name,
                    "coordinates": None,
                    "demand": full_cls["demand"] if full_cls else "",
                    "project": full_cls["project"] if full_cls else "",
                    "activity": full_cls["activity"] if full_cls else "",
                    "behavior": full_cls["behavior"] if full_cls else "",
                    "episode": m_episode,
                    "description": "手机快速补录",
                    "created_at": datetime.datetime.now().isoformat()
                }
                st.session_state.activities.append(act)
                
                # 自动保存为模板以便下次一键使用
                if m_episode not in st.session_state.activity_templates and full_cls:
                    st.session_state.activity_templates[m_episode] = full_cls
                    st.toast(f"✨ 已自动将 '{m_episode}' 加入常用模板")
                
                save_all_data()
                st.toast("✅ 补录成功!")
                time.sleep(1)
                st.rerun()

    # ====== 💻 电脑完整模式 (保留原有的精细操作) ======
    with tab_desktop:
        # 初始化时间
        if 'start_datetime' not in st.session_state:
            st.session_state.start_datetime = datetime.datetime.now()
        if 'end_datetime' not in st.session_state:
            st.session_state.end_datetime = datetime.datetime.now() + timedelta(hours=1)
            
        # 地图选择
        coordinates, searched_location = smart_map_selector()
        
        with st.form(key="activity_form_desktop"):
            col1, col2 = st.columns(2)
            with col1:
                d_start = st.time_input("开始时间", st.session_state.start_datetime.time())
                d_start_date = st.date_input("开始日期", st.session_state.start_datetime.date())
            with col2:
                d_end = st.time_input("结束时间", st.session_state.end_datetime.time())
                d_end_date = st.date_input("结束日期", st.session_state.end_datetime.date())
            
            # 合并时间
            dt_start = datetime.datetime.combine(d_start_date, d_start)
            dt_end = datetime.datetime.combine(d_end_date, d_end)
            
            # 地点
            st.markdown("**📍 地点**")
            l_temp = st.selectbox("地点模板", [""] + list(st.session_state.location_templates.keys()))
            l_name_input = st.text_input("或手动输入地点名称", value=searched_location['name'] if searched_location else "")
            
            # 活动
            st.markdown("**🏷️ 内容**")
            all_episodes_list = [e["episode"] for e in get_all_episodes()]
            selected_ep = st.selectbox("行为片段", [""] + all_episodes_list)
            desc = st.text_area("备注")
            
            submitted = st.form_submit_button("✅ 添加详细记录", use_container_width=True)
            
            if submitted and selected_ep:
                # 处理地点
                l_cat, l_tag, l_name = "其他", "自定义", l_name_input
                if l_temp:
                    t = st.session_state.location_templates[l_temp]
                    l_cat, l_tag, l_name = t["category"], t["tag"], t["name"]
                
                # 处理分类
                cls_data = {}
                for e in get_all_episodes():
                    if e["episode"] == selected_ep:
                        cls_data = e
                        break
                
                duration = int((dt_end - dt_start).total_seconds() / 60)
                
                act = {
                    "id": len(st.session_state.activities) + 1,
                    "start_time": dt_start.isoformat(),
                    "end_time": dt_end.isoformat(),
                    "duration": duration,
                    "location_category": l_cat,
                    "location_tag": l_tag,
                    "location_name": l_name,
                    "coordinates": coordinates,
                    "demand": cls_data.get("demand", ""),
                    "project": cls_data.get("project", ""),
                    "activity": cls_data.get("activity", ""),
                    "behavior": cls_data.get("behavior", ""),
                    "episode": selected_ep,
                    "description": desc,
                    "created_at": datetime.datetime.now().isoformat()
                }
                st.session_state.activities.append(act)
                save_all_data()
                st.success("记录添加成功")
                st.rerun()

# --- 5. 数据展示 (适配移动端) ---
def data_overview():
    st.markdown('<div class="sub-header">📊 数据概览</div>', unsafe_allow_html=True)
    if not st.session_state.activities:
        st.info("暂无数据")
        return

    # 关键指标卡片 - 移动端用两列显示
    df = pd.DataFrame(st.session_state.activities)
    total_time = df['duration'].sum() / 60
    today = datetime.date.today()
    today_acts = [a for a in st.session_state.activities if a['start_time'].startswith(today.isoformat())]
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("总时长 (小时)", f"{total_time:.1f}")
    with c2:
        st.metric("今日活动 (个)", len(today_acts))
        
    # 图表：只显示一个最重要的饼图
    st.markdown("### 活动分布")
    if not df.empty:
        fig = px.pie(df, names='demand', values='duration', title='需求类型分布', hole=0.4)
        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig, use_container_width=True)

    # 列表：最近5条记录
    st.markdown("### 🕒 最近记录")
    for a in reversed(st.session_state.activities[-5:]):
        start = datetime.datetime.fromisoformat(a['start_time']).strftime('%H:%M')
        end = datetime.datetime.fromisoformat(a['end_time']).strftime('%H:%M')
        st.info(f"**{a['episode']}** | {start}-{end} | {a['duration']}分钟")

# --- 6. 其他管理功能 (保持精简) ---
def template_management():
    st.markdown('<div class="sub-header">📋 模板管理</div>', unsafe_allow_html=True)
    st.caption("在这里添加的模板会出现在'手机极简模式'的快捷按钮中。")
    
    # 简单的添加模板表单
    with st.form("add_temp"):
        new_ep = st.text_input("行为名称 (如: 坐地铁)")
        c1, c2 = st.columns(2)
        with c1: demand = st.text_input("需求 (如: 个人)")
        with c2: project = st.text_input("企划 (如: 交通)")
        submit = st.form_submit_button("添加模板", use_container_width=True)
        
        if submit and new_ep:
            st.session_state.activity_templates[new_ep] = {
                "demand": demand, "project": project, "activity": "移动", "behavior": "乘坐", "episode": new_ep
            }
            save_all_data()
            st.success(f"模板 {new_ep} 已添加")
            st.rerun()
            
    # 删除模板
    if st.session_state.activity_templates:
        st.write("现有模板 (点击删除):")
        for name in list(st.session_state.activity_templates.keys()):
            if st.button(f"🗑️ {name}", key=f"del_{name}"):
                del st.session_state.activity_templates[name]
                save_all_data()
                st.rerun()

def activity_list_view():
    st.markdown('<div class="sub-header">📋 历史记录</div>', unsafe_allow_html=True)
    if st.session_state.activities:
        if st.button("🗑️ 删除最后一条记录", type="secondary", use_container_width=True):
            st.session_state.activities.pop()
            save_all_data()
            st.rerun()
            
        for a in reversed(st.session_state.activities):
            with st.expander(f"{a['start_time'][5:16].replace('T', ' ')} - {a['episode']}"):
                st.write(f"时长: {a['duration']}分钟")
                st.write(f"地点: {a['location_name']}")
                st.write(f"分类: {a['demand']}>{a['project']}")
                if st.button("删除此条", key=f"del_act_{a['id']}"):
                    st.session_state.activities = [x for x in st.session_state.activities if x['id'] != a['id']]
                    save_all_data()
                    st.rerun()

# --- 主程序 ---
def main():
    initialize_data()
    apply_custom_css()
    
    # 手机端简化标题
    st.markdown('<div class="main-header">🛤️ 轨迹日志</div>', unsafe_allow_html=True)
    
    # 底部导航栏 (使用 selectbox 模拟移动端底部 Tab 切换)
    menu_options = ["📝 记录", "📊 概览", "📋 历史", "⚙️ 模板"]
    # 使用 icons 让菜单更直观
    selected = st.sidebar.radio("导航", menu_options)
    
    # 手机端如果不展开 Sidebar，看不到菜单，所以在主界面顶部放一个横向选择
    # 为了美观，我们只在 Sidebar 收起时主要依赖这个
    page = st.selectbox("切换功能", menu_options, label_visibility="collapsed")
    
    if "记录" in page:
        activity_form()
    elif "概览" in page:
        data_overview()
    elif "历史" in page:
        activity_list_view()
    elif "模板" in page:
        template_management()
    
    # 侧边栏额外功能
    with st.sidebar:
        st.markdown("---")
        if st.button("📥 导出数据"):
            st.download_button("下载 JSON", json.dumps(st.session_state.activities, indent=2, ensure_ascii=False), "data.json")
        if st.button("🗑️ 清空所有数据"):
            st.session_state.activities = []
            save_all_data()
            st.rerun()

if __name__ == "__main__":
    main()
