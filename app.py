import streamlit as st
import pandas as pd
import json
import datetime
from datetime import timedelta
import pytz
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from streamlit_js_eval import streamlit_js_eval
import os

# 页面配置
st.set_page_config(
    page_title="个人活动日志工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化数据
def initialize_data():
    """初始化所有数据"""
    if 'activities' not in st.session_state:
        st.session_state.activities = []
    
    if 'location_categories' not in st.session_state:
        st.session_state.location_categories = {
            "居住场所": ['家', '宿舍', '酒店', '民宿', '亲友家'],
            "工作场所": ['办公室', '工厂', '店铺', '工地', '实验室'],
            "商业场所": ['超市', '商场', '餐厅', '银行', '理发店'],
            "教育场所": ['学校', '图书馆', '培训机构', '幼儿园', '大学'],
            "医疗场所": ['医院', '诊所', '药店', '体检中心', '康复中心'],
            "娱乐场所": ['电影院', 'KTV', '健身房', '游乐园', '咖啡厅'],
            "交通场所": ['地铁站', '公交站', '火车站', '机场', '停车场'],
            "公共场所": ['公园', '广场', '政府机关', '社区中心', '邮局'],
            "自然场所": ['山地', '海边', '森林', '湖泊', '河流'],
            "其他场所": ['未分类', '临时场所', '特殊场所']
        }
    
    if 'classification_system' not in st.session_state:
        st.session_state.classification_system = {
            "个人": {
                "个人生理": {
                    "睡觉休息": {"睡觉": ["夜间睡眠", "午睡", "小憩"], "休息": ["放松", "冥想", "发呆"]},
                    "进食": {"用餐": ["早餐", "午餐", "晚餐", "零食"], "饮水": ["喝水", "饮茶", "饮料"]},
                    "个人健康维护": {"洗漱": ["刷牙", "洗脸", "洗澡"], "健康检查": ["体检", "看医生"], "调理身体": ["按摩", "理疗", "泡脚"]}
                },
                "个人休闲": {
                    "娱乐消遣": {"看电视": ["电视剧", "电影", "综艺"], "游戏": ["手机游戏", "电脑游戏", "主机游戏"]},
                    "阅读学习": {"阅读": ["看书", "看新闻", "看杂志"], "学习": ["在线课程", "技能提升", "语言学习"]},
                    "运动锻炼": {"做操": ["太极", "八段锦", "广播体操"], "健身": ["跑步", "游泳", "器械训练"]}
                }
            },
            "家庭": {
                "家庭空间维护": {
                    "清洁打扫": {"打扫": ["扫地", "拖地", "整理"], "洗涤": ["洗衣", "晾衣", "熨烫"]}
                },
                "照顾家人": {
                    "照顾孩子": {"接送": ["上学接送", "活动接送"], "陪伴": ["陪玩", "作业辅导", "亲子时光"]}
                }
            },
            "工作": {
                "办公": {
                    "日常工作": {"会议": ["团队会议", "项目讨论", "客户会议"], "文档处理": ["报告编写", "邮件处理", "资料整理"]}
                }
            },
            "移动": {
                "交通出行": {
                    "通勤": {"上班通勤": ["地铁", "公交", "开车", "骑行"], "日常出行": ["步行", "打车", "骑车"]}
                }
            }
        }

# 保存数据到session state
def save_data():
    """数据自动保存在session state中"""
    pass

# 样式配置
def apply_custom_css():
    """应用自定义CSS样式"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .activity-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .location-tag {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 活动记录表单
def activity_form():
    """活动记录表单"""
    st.markdown('<div class="sub-header">📝 记录新活动</div>', unsafe_allow_html=True)
    
    with st.form("activity_form", clear_on_submit=False):
        # 时间信息
        col1, col2, col3 = st.columns(3)
        with col1:
            start_time = st.datetime_input("开始时间*", value=datetime.datetime.now())
        with col2:
            end_time = st.datetime_input("结束时间*", value=datetime.datetime.now())
        with col3:
            duration = st.number_input("持续时间(分钟)*", min_value=1, max_value=1440, 
                                     value=60, help="自动根据开始和结束时间计算")
        
        # 地点信息
        st.markdown("**📍 地点信息**")
        loc_col1, loc_col2, loc_col3 = st.columns(3)
        with loc_col1:
            location_category = st.selectbox("地点大类*", 
                                           options=[""] + list(st.session_state.location_categories.keys()))
        with loc_col2:
            location_tags = st.session_state.location_categories.get(location_category, [])
            location_tag = st.selectbox("地点标签", options=[""] + location_tags)
        with loc_col3:
            location_name = st.text_input("具体地点名称*", placeholder="如：中关村大厦A座")
        
        # 地图标点
        st.markdown("**🗺️ 地图标点**")
        map_placeholder = st.empty()
        
        # 初始化地图
        if 'map_center' not in st.session_state:
            st.session_state.map_center = [39.9042, 116.4074]  # 北京
        
        m = folium.Map(location=st.session_state.map_center, zoom_start=13)
        
        # 添加点击事件
        m.add_child(folium.LatLngPopup())
        
        # 显示地图
        map_data = st_folium(m, width=700, height=300, key="activity_map")
        
        # 处理地图点击
        coordinates = None
        if map_data.get("last_clicked"):
            lat = map_data["last_clicked"]["lat"]
            lng = map_data["last_clicked"]["lng"]
            coordinates = {"lat": lat, "lng": lng}
            st.success(f"已选择位置: 纬度 {lat:.4f}, 经度 {lng:.4f}")
        
        # 分类信息
        st.markdown("**🏷️ 活动分类**")
        
        class_col1, class_col2 = st.columns(2)
        with class_col1:
            demand_type = st.selectbox("需求类型*", 
                                     options=[""] + list(st.session_state.classification_system.keys()))
        with class_col2:
            projects = list(st.session_state.classification_system.get(demand_type, {}).keys())
            project_type = st.selectbox("企划类型*", options=[""] + projects)
        
        class_col3, class_col4 = st.columns(2)
        with class_col3:
            activities = list(st.session_state.classification_system.get(demand_type, {}).get(project_type, {}).keys())
            activity_type = st.selectbox("活动类型*", options=[""] + activities)
        with class_col4:
            behaviors_dict = st.session_state.classification_system.get(demand_type, {}).get(project_type, {}).get(activity_type, {})
            behaviors = list(behaviors_dict.keys()) if behaviors_dict else []
            behavior_type = st.selectbox("行为类型*", options=[""] + behaviors)
        
        episodes = behaviors_dict.get(behavior_type, []) if behavior_type else []
        episode_type = st.selectbox("片段描述", options=[""] + episodes)
        
        # 活动描述
        activity_description = st.text_area("活动描述", 
                                          placeholder="详细描述活动内容和情境...",
                                          height=100)
        
        # 提交按钮
        submitted = st.form_submit_button("✅ 添加活动", use_container_width=True)
        
        if submitted:
            # 验证必填字段
            if not all([start_time, end_time, duration, location_category, location_name, 
                       demand_type, project_type, activity_type, behavior_type]):
                st.error("请填写所有必填字段（标*的字段）")
                return
            
            # 创建活动对象
            activity = {
                "id": len(st.session_state.activities) + 1,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration,
                "location_category": location_category,
                "location_tag": location_tag,
                "location_name": location_name,
                "coordinates": coordinates,
                "demand": demand_type,
                "project": project_type,
                "activity": activity_type,
                "behavior": behavior_type,
                "episode": episode_type,
                "description": activity_description,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # 添加到活动列表
            st.session_state.activities.append(activity)
            st.session_state.activities.sort(key=lambda x: x["start_time"])
            
            st.success("🎉 活动添加成功！")
            st.rerun()

# 数据概览
def data_overview():
    """数据概览面板"""
    st.markdown('<div class="sub-header">📊 数据概览</div>', unsafe_allow_html=True)
    
    if not st.session_state.activities:
        st.info("暂无活动数据，请先添加活动记录")
        return
    
    # 计算统计指标
    total_activities = len(st.session_state.activities)
    total_duration = sum(activity["duration"] for activity in st.session_state.activities)
    total_hours = total_duration / 60
    unique_projects = len(set(activity["project"] for activity in st.session_state.activities))
    unique_locations = len(set(activity["location_name"] for activity in st.session_state.activities))
    avg_duration = total_duration / total_activities
    
    # 显示指标卡片
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{total_activities}</h3>
            <p>总活动数</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{total_hours:.1f}</h3>
            <p>总时长(小时)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{unique_projects}</h3>
            <p>涉及企划数</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{unique_locations}</h3>
            <p>访问地点数</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{avg_duration:.0f}</h3>
            <p>平均时长(分钟)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 需求类型分布
    st.markdown("**📈 需求类型分布**")
    demand_data = {}
    for activity in st.session_state.activities:
        demand = activity["demand"]
        duration = activity["duration"]
        demand_data[demand] = demand_data.get(demand, 0) + duration
    
    if demand_data:
        fig = px.pie(
            values=list(demand_data.values()),
            names=list(demand_data.keys()),
            title="各需求类型时间分布"
        )
        st.plotly_chart(fig, use_container_width=True)

# 活动记录列表
def activity_records():
    """活动记录列表"""
    st.markdown('<div class="sub-header">📋 活动记录</div>', unsafe_allow_html=True)
    
    if not st.session_state.activities:
        st.info("暂无活动记录")
        return
    
    # 搜索和筛选
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("🔍 搜索活动描述")
    with col2:
        demand_filter = st.selectbox("筛选需求类型", [""] + list(set(a["demand"] for a in st.session_state.activities)))
    with col3:
        date_filter = st.date_input("筛选日期")
    
    # 筛选活动
    filtered_activities = st.session_state.activities
    
    if search_term:
        filtered_activities = [a for a in filtered_activities 
                             if search_term.lower() in a.get("description", "").lower()]
    
    if demand_filter:
        filtered_activities = [a for a in filtered_activities if a["demand"] == demand_filter]
    
    if date_filter:
        filtered_activities = [a for a in filtered_activities 
                             if datetime.datetime.fromisoformat(a["start_time"]).date() == date_filter]
    
    # 显示活动记录
    for activity in reversed(filtered_activities):
        with st.container():
            start_time = datetime.datetime.fromisoformat(activity["start_time"])
            end_time = datetime.datetime.fromisoformat(activity["end_time"])
            
            st.markdown(f"""
            <div class="activity-card">
                <div style="font-weight: bold; color: #1f77b4; margin-bottom: 0.5rem;">
                    🕒 {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')} 
                    ({activity['duration']}分钟)
                </div>
                <div style="margin-bottom: 0.5rem;">
                    📍 {activity['location_category']} / 
                    {activity['location_tag'] or '未分类'} / 
                    {activity['location_name']}
                </div>
                <div style="background: #e3f2fd; padding: 0.5rem; border-radius: 5px; font-size: 0.9rem;">
                    {activity['demand']} → {activity['project']} → {activity['activity']} → 
                    {activity['behavior']} {f"→ {activity['episode']}" if activity['episode'] else ""}
                </div>
                {f"<div style='margin-top: 0.5rem; color: #666;'>{activity['description']}</div>" if activity['description'] else ""}
            </div>
            """, unsafe_allow_html=True)

# 时空分析
def spatiotemporal_analysis():
    """时空分析"""
    st.markdown('<div class="sub-header">🗺️ 时空分析</div>', unsafe_allow_html=True)
    
    if not st.session_state.activities:
        st.info("暂无活动数据")
        return
    
    # 地点类型分析
    st.markdown("**📍 地点类型分析**")
    location_data = {}
    for activity in st.session_state.activities:
        category = activity["location_category"]
        duration = activity["duration"]
        location_data[category] = location_data.get(category, 0) + duration
    
    if location_data:
        fig = px.bar(
            x=list(location_data.keys()),
            y=list(location_data.values()),
            title="各地点类型时间分布",
            labels={"x": "地点类型", "y": "总时长(分钟)"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 时间分布分析
    st.markdown("**⏰ 时间段分布**")
    time_slots = {"早晨(6-12)": 0, "下午(12-18)": 0, "晚上(18-22)": 0, "深夜(22-6)": 0}
    
    for activity in st.session_state.activities:
        start_time = datetime.datetime.fromisoformat(activity["start_time"])
        hour = start_time.hour
        
        if 6 <= hour < 12:
            time_slots["早晨(6-12)"] += activity["duration"]
        elif 12 <= hour < 18:
            time_slots["下午(12-18)"] += activity["duration"]
        elif 18 <= hour < 22:
            time_slots["晚上(18-22)"] += activity["duration"]
        else:
            time_slots["深夜(22-6)"] += activity["duration"]
    
    fig = px.pie(
        values=list(time_slots.values()),
        names=list(time_slots.keys()),
        title="各时间段活动分布"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 时空路径地图
    st.markdown("**🛣️ 时空活动路径**")
    
    # 创建地图
    if any(activity.get("coordinates") for activity in st.session_state.activities):
        m = folium.Map(location=st.session_state.map_center, zoom_start=12)
        
        # 添加活动点
        for i, activity in enumerate(st.session_state.activities):
            if activity.get("coordinates"):
                lat = activity["coordinates"]["lat"]
                lng = activity["coordinates"]["lng"]
                
                folium.Marker(
                    [lat, lng],
                    popup=f"""
                    <b>{activity['demand']} - {activity['project']}</b><br>
                    {activity['location_name']}<br>
                    {datetime.datetime.fromisoformat(activity['start_time']).strftime('%m-%d %H:%M')}
                    """,
                    tooltip=activity["location_name"],
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
        
        st_folium(m, width=700, height=400)

# 数据管理
def data_management():
    """数据管理功能"""
    st.markdown('<div class="sub-header">💾 数据管理</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📤 导出数据**")
        if st.button("导出为JSON", use_container_width=True):
            export_data = {
                "activities": st.session_state.activities,
                "location_categories": st.session_state.location_categories,
                "classification_system": st.session_state.classification_system,
                "export_time": datetime.datetime.now().isoformat(),
                "version": "1.0"
            }
            
            st.download_button(
                label="下载JSON文件",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"activity_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col2:
        st.markdown("**📥 导入数据**")
        uploaded_file = st.file_uploader("选择JSON文件", type=["json"])
        
        if uploaded_file is not None:
            try:
                import_data = json.load(uploaded_file)
                
                if st.button("导入数据", use_container_width=True):
                    if "activities" in import_data:
                        st.session_state.activities = import_data["activities"]
                    if "location_categories" in import_data:
                        st.session_state.location_categories = import_data["location_categories"]
                    if "classification_system" in import_data:
                        st.session_state.classification_system = import_data["classification_system"]
                    
                    st.success("数据导入成功！")
                    st.rerun()
            except Exception as e:
                st.error(f"文件解析失败: {e}")
    
    # 清空数据
    st.markdown("---")
    st.markdown("**⚠️ 危险操作**")
    if st.button("清空所有数据", type="secondary", use_container_width=True):
        if st.checkbox("我确认要清空所有数据，此操作不可恢复"):
            st.session_state.activities = []
            st.success("数据已清空")
            st.rerun()

# 主应用
def main():
    """主应用"""
    # 初始化和样式
    initialize_data()
    apply_custom_css()
    
    # 标题
    st.markdown('<div class="main-header">📊 个人活动日志工具</div>', unsafe_allow_html=True)
    st.markdown('基于时间地理学理论的"需求-企划-活动-行为-片段"五级分析系统')
    
    # 侧边栏导航
    with st.sidebar:
        st.title("导航菜单")
        page = st.radio(
            "选择功能",
            ["记录活动", "数据概览", "活动记录", "时空分析", "数据管理"],
            icons=["📝", "📊", "📋", "🗺️", "💾"]
        )
        
        st.markdown("---")
        st.markdown("### 使用说明")
        st.info("""
        1. 在**记录活动**页面添加新的活动
        2. 在**数据概览**查看统计分析
        3. 在**活动记录**浏览历史活动
        4. 在**时空分析**查看地点和时间分布
        5. 在**数据管理**导入导出数据
        """)
    
    # 页面路由
    if page == "记录活动":
        activity_form()
    elif page == "数据概览":
        data_overview()
    elif page == "活动记录":
        activity_records()
    elif page == "时空分析":
        spatiotemporal_analysis()
    elif page == "数据管理":
        data_management()

if __name__ == "__main__":
    main()
