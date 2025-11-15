# app.py
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
import os
import time
import requests
from geopy.geocoders import Nominatim
import math

# 页面配置
st.set_page_config(
    page_title="个人活动轨迹日志",
    page_icon="🛤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据存储路径
DATA_DIR = "data"
ACTIVITIES_FILE = os.path.join(DATA_DIR, "activities.json")
CLASSIFICATION_FILE = os.path.join(DATA_DIR, "classification_system.json")
LOCATION_CATEGORIES_FILE = os.path.join(DATA_DIR, "location_categories.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "activity_templates.json")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

def load_json_file(file_path, default_data):
    """从JSON文件加载数据，如果文件不存在则返回默认数据"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"加载文件 {file_path} 时出错: {e}")
    return default_data

def save_json_file(file_path, data):
    """保存数据到JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存文件 {file_path} 时出错: {e}")
        return False

# 初始化数据
def initialize_data():
    """初始化所有数据"""
    # 活动数据
    if 'activities' not in st.session_state:
        st.session_state.activities = load_json_file(ACTIVITIES_FILE, [])
    
    # 地点分类
    default_location_categories = {
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
    
    if 'location_categories' not in st.session_state:
        st.session_state.location_categories = load_json_file(
            LOCATION_CATEGORIES_FILE, default_location_categories
        )
    
    # 分类系统
    default_classification_system = {
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
    
    if 'classification_system' not in st.session_state:
        st.session_state.classification_system = load_json_file(
            CLASSIFICATION_FILE, default_classification_system
        )
    
    # 活动模板
    if 'activity_templates' not in st.session_state:
        st.session_state.activity_templates = load_json_file(TEMPLATES_FILE, {})
    
    # 初始化地图中心
    if 'map_center' not in st.session_state:
        st.session_state.map_center = [39.9042, 116.4074]  # 北京

# 保存数据
def save_all_data():
    """保存所有数据到文件"""
    save_json_file(ACTIVITIES_FILE, st.session_state.activities)
    save_json_file(LOCATION_CATEGORIES_FILE, st.session_state.location_categories)
    save_json_file(CLASSIFICATION_FILE, st.session_state.classification_system)
    save_json_file(TEMPLATES_FILE, st.session_state.activity_templates)

# 地点搜索功能
def search_location(query):
    """使用Nominatim搜索地点"""
    try:
        geolocator = Nominatim(user_agent="personal_activity_tracker")
        location = geolocator.geocode(query, addressdetails=True, country_codes='cn')
        
        if location:
            return {
                "name": location.address,
                "lat": location.latitude,
                "lng": location.longitude
            }
    except Exception as e:
        st.error(f"地点搜索失败: {e}")
    
    return None

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
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .activity-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .activity-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .template-card {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .template-card:hover {
        background-color: #c8e6c9;
        transform: translateX(5px);
    }
    .stButton button {
        width: 100%;
    }
    .quick-action-btn {
        margin: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 快速操作面板
def quick_actions():
    """快速操作面板"""
    st.markdown('<div class="sub-header">⚡ 快速操作</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🕒 记录当前活动", use_container_width=True):
            st.session_state.quick_start = True
            st.rerun()
    
    with col2:
        if st.button("📊 查看今日统计", use_container_width=True):
            st.session_state.show_today_stats = True
            st.rerun()
    
    with col3:
        if st.button("🗺️ 今日轨迹", use_container_width=True):
            st.session_state.show_today_track = True
            st.rerun()
    
    with col4:
        if st.button("💾 备份数据", use_container_width=True):
            save_all_data()
            st.success("数据已备份")

# 活动模板功能
def activity_templates():
    """活动模板管理"""
    st.markdown('<div class="sub-header">📋 活动模板</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 显示现有模板
        if st.session_state.activity_templates:
            st.markdown("**已保存的模板:**")
            for template_name, template_data in st.session_state.activity_templates.items():
                with st.container():
                    st.markdown(f"""
                    <div class="template-card">
                        <strong>{template_name}</strong><br>
                        <small>{template_data['demand']} → {template_data['project']} → {template_data['activity']}</small><br>
                        <small>📍 {template_data.get('location_name', '无地点')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 使用模板按钮
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(f"使用模板: {template_name}", key=f"use_{template_name}"):
                            # 填充表单数据
                            st.session_state.template_data = template_data
                            st.success(f"已加载模板: {template_name}")
                            st.rerun()
                    with col2:
                        if st.button("删除", key=f"del_{template_name}", type="secondary"):
                            del st.session_state.activity_templates[template_name]
                            save_all_data()
                            st.success(f"模板 '{template_name}' 已删除")
                            st.rerun()
        else:
            st.info("暂无活动模板，请先创建模板")
    
    with col2:
        # 创建新模板
        st.markdown("**创建新模板**")
        template_name = st.text_input("模板名称")
        template_demand = st.selectbox("需求类型", options=[""] + list(st.session_state.classification_system.keys()))
        template_project = st.selectbox("企划类型", options=[""] + list(st.session_state.classification_system.get(template_demand, {}).keys()))
        template_activity = st.selectbox("活动类型", options=[""] + list(st.session_state.classification_system.get(template_demand, {}).get(template_project, {}).keys()))
        template_behavior = st.selectbox("行为类型", options=[""] + list(st.session_state.classification_system.get(template_demand, {}).get(template_project, {}).get(template_activity, {}).keys()))
        template_location = st.text_input("常用地点")
        
        if st.button("保存模板", use_container_width=True):
            if template_name and template_demand and template_project and template_activity and template_behavior:
                st.session_state.activity_templates[template_name] = {
                    "demand": template_demand,
                    "project": template_project,
                    "activity": template_activity,
                    "behavior": template_behavior,
                    "location_name": template_location
                }
                save_all_data()
                st.success(f"模板 '{template_name}' 已保存")
                st.rerun()
            else:
                st.error("请填写完整信息")

# 智能地图组件 - 修复：将搜索功能移出表单
def smart_map_selector():
    """智能地图选择器"""
    st.markdown("**🗺️ 地点选择**")
    
    # 地点搜索 - 移出表单
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("搜索地点", placeholder="输入地点名称进行搜索...", key="location_search")
    with col2:
        search_clicked = st.button("搜索", use_container_width=True, key="search_button")
    
    searched_location = None
    if search_clicked and search_query:
        with st.spinner("搜索中..."):
            searched_location = search_location(search_query)
            if searched_location:
                st.success(f"找到: {searched_location['name']}")
                st.session_state.map_center = [searched_location['lat'], searched_location['lng']]
            else:
                st.error("未找到相关地点")
    
    # 常用地点快速选择 - 移出表单
    st.markdown("**📍 常用地点**")
    common_locations = ["家", "办公室", "学校", "健身房", "超市", "餐厅"]
    cols = st.columns(6)
    selected_common_location = None
    
    for i, loc in enumerate(common_locations):
        with cols[i]:
            if st.button(loc, use_container_width=True, key=f"common_{loc}"):
                selected_common_location = loc
    
    # 地图显示
    m = folium.Map(location=st.session_state.map_center, zoom_start=13)
    
    # 添加搜索结果的标记
    if searched_location:
        folium.Marker(
            [searched_location['lat'], searched_location['lng']],
            popup=searched_location['name'],
            tooltip="搜索结果",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    # 显示地图
    map_data = st_folium(m, width=700, height=400, key="smart_map")
    
    # 处理地图点击
    coordinates = None
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lng = map_data["last_clicked"]["lng"]
        coordinates = {"lat": lat, "lng": lng}
        st.success(f"📍 已选择位置: 纬度 {lat:.4f}, 经度 {lng:.4f}")
        
        # 更新地图中心
        st.session_state.map_center = [lat, lng]
    
    return coordinates, searched_location, selected_common_location

# 活动记录表单 - 修复：将所有按钮移出表单
def activity_form():
    """活动记录表单"""
    st.markdown('<div class="sub-header">📝 记录新活动</div>', unsafe_allow_html=True)
    
    # 检查是否有模板数据要填充
    prefilled_data = st.session_state.get('template_data', {})
    if prefilled_data:
        st.info(f"正在使用模板: {list(st.session_state.activity_templates.keys())[list(st.session_state.activity_templates.values()).index(prefilled_data)] if prefilled_data in st.session_state.activity_templates.values() else '未知模板'}")
    
    # 将地图选择器移出表单
    coordinates, searched_location, common_location = smart_map_selector()
    
    # 使用st.form的正确方式 - 只包含表单字段，不包含按钮
    with st.form(key="activity_form"):
        # 时间信息
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("开始日期*", value=datetime.date.today())
            start_time = st.time_input("开始时间*", value=datetime.time(9, 0))
            start_datetime = datetime.datetime.combine(start_date, start_time)
            
        with col2:
            end_date = st.date_input("结束日期*", value=datetime.date.today())
            end_time = st.time_input("结束时间*", value=datetime.time(10, 0))
            end_datetime = datetime.datetime.combine(end_date, end_time)
            
        with col3:
            # 自动计算持续时间
            if start_datetime and end_datetime:
                duration_minutes = max(1, int((end_datetime - start_datetime).total_seconds() / 60))
            else:
                duration_minutes = 60
                
            duration = st.number_input("持续时间(分钟)*", min_value=1, max_value=1440, 
                                     value=duration_minutes)
        
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
            # 如果有模板数据，预填充地点
            default_location = prefilled_data.get('location_name', '')
            # 如果选择了常用地点，更新地点名称
            if common_location and not default_location:
                default_location = common_location
            # 如果搜索到地点，更新地点名称
            if searched_location and not default_location:
                default_location = searched_location['name']
                
            location_name = st.text_input("具体地点名称*", placeholder="如：中关村大厦A座", value=default_location)
        
        # 分类信息
        st.markdown("**🏷️ 活动分类**")
        
        class_col1, class_col2 = st.columns(2)
        with class_col1:
            # 使用模板数据预填充
            default_demand = prefilled_data.get('demand', '')
            demand_type = st.selectbox("需求类型*", 
                                     options=[""] + list(st.session_state.classification_system.keys()),
                                     index=(list(st.session_state.classification_system.keys()).index(default_demand) + 1 
                                           if default_demand in st.session_state.classification_system else 0))
        with class_col2:
            projects = list(st.session_state.classification_system.get(demand_type, {}).keys())
            default_project = prefilled_data.get('project', '')
            project_type = st.selectbox("企划类型*", options=[""] + projects,
                                      index=(projects.index(default_project) + 1 
                                           if default_project in projects else 0))
        
        class_col3, class_col4 = st.columns(2)
        with class_col3:
            activities = list(st.session_state.classification_system.get(demand_type, {}).get(project_type, {}).keys())
            default_activity = prefilled_data.get('activity', '')
            activity_type = st.selectbox("活动类型*", options=[""] + activities,
                                       index=(activities.index(default_activity) + 1 
                                            if default_activity in activities else 0))
        with class_col4:
            behaviors_dict = st.session_state.classification_system.get(demand_type, {}).get(project_type, {}).get(activity_type, {})
            behaviors = list(behaviors_dict.keys()) if behaviors_dict else []
            default_behavior = prefilled_data.get('behavior', '')
            behavior_type = st.selectbox("行为类型*", options=[""] + behaviors,
                                       index=(behaviors.index(default_behavior) + 1 
                                            if default_behavior in behaviors else 0))
        
        # 活动描述
        activity_description = st.text_area("活动描述", 
                                          placeholder="详细描述活动内容和情境...",
                                          height=100)
        
        # 提交按钮 - 使用st.form_submit_button
        submitted = st.form_submit_button("✅ 添加活动", use_container_width=True)
    
    # 将其他按钮移出表单
    col1, col2 = st.columns(2)
    with col1:
        save_as_template = st.button("💾 保存为模板", use_container_width=True)
    with col2:
        clear_form = st.button("🗑️ 清空表单", use_container_width=True)
    
    if submitted:
        # 验证必填字段
        if not all([start_datetime, end_datetime, duration, location_category, location_name, 
                   demand_type, project_type, activity_type, behavior_type]):
            st.error("请填写所有必填字段（标*的字段）")
            return
        
        if duration <= 0:
            st.error("持续时间必须大于0")
            return
        
        # 创建活动对象
        activity = {
            "id": len(st.session_state.activities) + 1,
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "duration": duration,
            "location_category": location_category,
            "location_tag": location_tag,
            "location_name": location_name,
            "coordinates": coordinates,
            "demand": demand_type,
            "project": project_type,
            "activity": activity_type,
            "behavior": behavior_type,
            "description": activity_description,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # 添加到活动列表
        st.session_state.activities.append(activity)
        st.session_state.activities.sort(key=lambda x: x["start_time"])
        
        # 保存数据
        save_all_data()
        
        # 清除模板数据
        if 'template_data' in st.session_state:
            del st.session_state.template_data
        
        st.success("🎉 活动添加成功！")
        
        # 重新加载页面
        st.rerun()
    
    if save_as_template:
        template_name = f"{demand_type}_{project_type}_{activity_type}"
        if st.session_state.activity_templates.get(template_name):
            template_name = f"{template_name}_{len(st.session_state.activity_templates)}"
        
        st.session_state.activity_templates[template_name] = {
            "demand": demand_type,
            "project": project_type,
            "activity": activity_type,
            "behavior": behavior_type,
            "location_name": location_name
        }
        save_all_data()
        st.success(f"模板 '{template_name}' 已保存")
        st.rerun()
    
    if clear_form:
        # 清除模板数据
        if 'template_data' in st.session_state:
            del st.session_state.template_data
        st.rerun()

# 数据概览
def data_overview():
    """数据概览面板"""
    st.markdown('<div class="sub-header">📊 数据概览</div>', unsafe_allow_html=True)
    
    if not st.session_state.activities:
        st.info("📝 暂无活动数据，请先添加活动记录")
        return
    
    # 计算统计指标
    total_activities = len(st.session_state.activities)
    total_duration = sum(activity["duration"] for activity in st.session_state.activities)
    total_hours = total_duration / 60
    unique_projects = len(set(activity["project"] for activity in st.session_state.activities))
    unique_locations = len(set(activity["location_name"] for activity in st.session_state.activities))
    avg_duration = total_duration / total_activities
    
    # 今日统计
    today = datetime.date.today()
    today_activities = [a for a in st.session_state.activities 
                       if datetime.datetime.fromisoformat(a["start_time"]).date() == today]
    today_duration = sum(a["duration"] for a in today_activities)
    
    # 显示指标卡片
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    metrics = [
        (total_activities, "总活动数"),
        (f"{total_hours:.1f}", "总时长(小时)"),
        (unique_projects, "涉及企划数"),
        (unique_locations, "访问地点数"),
        (f"{avg_duration:.0f}", "平均时长(分钟)"),
        (len(today_activities), "今日活动数")
    ]
    
    for i, (value, label) in enumerate(metrics):
        with [col1, col2, col3, col4, col5, col6][i]:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{value}</h3>
                <p>{label}</p>
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
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(
                values=list(demand_data.values()),
                names=list(demand_data.keys()),
                title="各需求类型时间分布"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 时间分布图
            time_data = {}
            for activity in st.session_state.activities:
                hour = datetime.datetime.fromisoformat(activity["start_time"]).hour
                time_slot = f"{hour:02d}:00"
                time_data[time_slot] = time_data.get(time_slot, 0) + activity["duration"]
            
            if time_data:
                fig2 = px.bar(
                    x=list(time_data.keys()),
                    y=list(time_data.values()),
                    title="时间段活动分布",
                    labels={"x": "时间段", "y": "总时长(分钟)"}
                )
                st.plotly_chart(fig2, use_container_width=True)

# 活动记录列表
def activity_records():
    """活动记录列表"""
    st.markdown('<div class="sub-header">📋 活动记录</div>', unsafe_allow_html=True)
    
    if not st.session_state.activities:
        st.info("暂无活动记录")
        return
    
    # 搜索和筛选
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_term = st.text_input("🔍 搜索活动描述")
    with col2:
        demand_options = [""] + list(set(a["demand"] for a in st.session_state.activities))
        demand_filter = st.selectbox("筛选需求类型", demand_options)
    with col3:
        date_filter = st.date_input("筛选日期")
    with col4:
        # 批量操作
        if st.button("🗑️ 删除筛选结果", type="secondary"):
            if st.checkbox("确认删除所有筛选结果"):
                original_count = len(st.session_state.activities)
                # 这里需要实现删除逻辑
                st.warning("删除功能待实现")
    
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
            
            col1, col2 = st.columns([4, 1])
            with col1:
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
                        {f"<br><small>坐标: {activity['coordinates']['lat']:.4f}, {activity['coordinates']['lng']:.4f}</small>" if activity.get('coordinates') else ""}
                    </div>
                    <div style="background: #e3f2fd; padding: 0.5rem; border-radius: 5px; font-size: 0.9rem;">
                        {activity['demand']} → {activity['project']} → {activity['activity']} → {activity['behavior']}
                    </div>
                    {f"<div style='margin-top: 0.5rem; color: #666;'>{activity['description']}</div>" if activity['description'] else ""}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("删除", key=f"del_{activity['id']}", type="secondary"):
                    st.session_state.activities = [a for a in st.session_state.activities if a['id'] != activity['id']]
                    save_all_data()
                    st.success("活动已删除")
                    st.rerun()

# 时空轨迹分析
def spatiotemporal_analysis():
    """时空轨迹分析"""
    st.markdown('<div class="sub-header">🗺️ 时空轨迹分析</div>', unsafe_allow_html=True)
    
    if not st.session_state.activities:
        st.info("暂无活动数据")
        return
    
    # 选择日期查看轨迹
    dates = sorted(set(datetime.datetime.fromisoformat(a["start_time"]).date() 
                      for a in st.session_state.activities))
    
    if not dates:
        st.info("暂无活动数据")
        return
        
    col1, col2 = st.columns(2)
    with col1:
        selected_date = st.selectbox("选择查看日期", options=dates)
    with col2:
        # 多日轨迹选项
        multi_day = st.checkbox("显示多日轨迹")
    
    # 筛选活动
    if multi_day:
        # 显示最近7天的轨迹
        end_date = max(dates)
        start_date = end_date - timedelta(days=7)
        date_range_activities = [a for a in st.session_state.activities 
                               if start_date <= datetime.datetime.fromisoformat(a["start_time"]).date() <= end_date]
        daily_activities = date_range_activities
        display_date = f"{start_date} 至 {end_date}"
    else:
        # 单日轨迹
        daily_activities = [a for a in st.session_state.activities 
                           if datetime.datetime.fromisoformat(a["start_time"]).date() == selected_date]
        display_date = str(selected_date)
    
    if not daily_activities:
        st.info(f"{display_date} 没有活动记录")
        return
    
    # 创建轨迹地图
    st.markdown(f"**🛣️ {display_date} 的活动轨迹**")
    
    # 计算地图中心
    valid_activities = [a for a in daily_activities if a.get("coordinates")]
    
    if not valid_activities:
        st.warning("所选时间段的活动没有坐标信息，无法显示轨迹")
        return
    
    # 计算中心点
    lats = [a["coordinates"]["lat"] for a in valid_activities]
    lngs = [a["coordinates"]["lng"] for a in valid_activities]
    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)
    
    # 创建地图
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
    
    # 添加轨迹线
    coordinates = []
    for i, activity in enumerate(valid_activities):
        coords = (activity["coordinates"]["lat"], activity["coordinates"]["lng"])
        coordinates.append(coords)
        
        # 添加标记点
        start_time = datetime.datetime.fromisoformat(activity["start_time"])
        popup_text = f"""
        <b>{activity['demand']} - {activity['project']}</b><br>
        {activity['location_name']}<br>
        {start_time.strftime('%H:%M')} - {activity['duration']}分钟<br>
        {activity['description'] or '无描述'}
        """
        
        folium.Marker(
            coords,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{i+1}. {activity['demand']} - {activity['project']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # 添加轨迹线
    if len(coordinates) > 1:
        folium.PolyLine(
            coordinates,
            color='red',
            weight=3,
            opacity=0.8,
            popup=f"{display_date} 活动轨迹"
        ).add_to(m)
    
    # 显示地图
    st_folium(m, width=800, height=500)
    
    # 显示时间线
    st.markdown("**⏰ 时间线**")
    for i, activity in enumerate(daily_activities):
        start_time = datetime.datetime.fromisoformat(activity["start_time"])
        end_time = datetime.datetime.fromisoformat(activity["end_time"])
        
        with st.expander(f"{i+1}. {start_time.strftime('%H:%M')} - {activity['demand']} → {activity['project']} → {activity['activity']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**地点:** {activity['location_name']}")
                if activity.get('coordinates'):
                    st.write(f"**坐标:** {activity['coordinates']['lat']:.4f}, {activity['coordinates']['lng']:.4f}")
            with col2:
                st.write(f"**时长:** {activity['duration']}分钟")
                st.write(f"**行为:** {activity['behavior']}")
            
            if activity['description']:
                st.write(f"**描述:** {activity['description']}")

# 分类系统管理
def classification_management():
    """分类系统管理"""
    st.markdown('<div class="sub-header">🏷️ 分类系统管理</div>', unsafe_allow_html=True)
    
    st.info("在这里您可以自定义活动分类系统。分类系统采用四级结构：需求 → 企划 → 活动 → 行为")
    
    # 选择要编辑的层级
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        demand_options = list(st.session_state.classification_system.keys())
        selected_demand = st.selectbox("选择需求", options=demand_options)
    
    with col2:
        if selected_demand:
            project_options = list(st.session_state.classification_system[selected_demand].keys())
            selected_project = st.selectbox("选择企划", options=project_options)
    
    with col3:
        if selected_demand and selected_project:
            activity_options = list(st.session_state.classification_system[selected_demand][selected_project].keys())
            selected_activity = st.selectbox("选择活动", options=activity_options)
    
    with col4:
        if selected_demand and selected_project and selected_activity:
            behavior_options = list(st.session_state.classification_system[selected_demand][selected_project][selected_activity].keys())
            selected_behavior = st.selectbox("选择行为", options=behavior_options)
    
    # 编辑区域
    st.markdown("---")
    st.markdown("### 编辑分类")
    
    edit_col1, edit_col2 = st.columns(2)
    
    with edit_col1:
        st.markdown("**添加新分类**")
        
        new_demand = st.text_input("新需求名称")
        if st.button("添加需求") and new_demand:
            if new_demand not in st.session_state.classification_system:
                st.session_state.classification_system[new_demand] = {}
                save_all_data()
                st.success(f"已添加需求: {new_demand}")
                st.rerun()
        
        if selected_demand:
            new_project = st.text_input("新企划名称")
            if st.button("添加企划") and new_project:
                if new_project not in st.session_state.classification_system[selected_demand]:
                    st.session_state.classification_system[selected_demand][new_project] = {}
                    save_all_data()
                    st.success(f"已添加企划: {new_project}")
                    st.rerun()
        
        if selected_demand and selected_project:
            new_activity = st.text_input("新活动名称")
            if st.button("添加活动") and new_activity:
                if new_activity not in st.session_state.classification_system[selected_demand][selected_project]:
                    st.session_state.classification_system[selected_demand][selected_project][new_activity] = {}
                    save_all_data()
                    st.success(f"已添加活动: {new_activity}")
                    st.rerun()
        
        if selected_demand and selected_project and selected_activity:
            new_behavior = st.text_input("新行为名称")
            if st.button("添加行为") and new_behavior:
                if new_behavior not in st.session_state.classification_system[selected_demand][selected_project][selected_activity]:
                    st.session_state.classification_system[selected_demand][selected_project][selected_activity][new_behavior] = []
                    save_all_data()
                    st.success(f"已添加行为: {new_behavior}")
                    st.rerun()
    
    with edit_col2:
        st.markdown("**删除分类**")
        
        if selected_demand and len(st.session_state.classification_system) > 1:
            if st.button("删除当前需求", type="secondary"):
                del st.session_state.classification_system[selected_demand]
                save_all_data()
                st.success(f"已删除需求: {selected_demand}")
                st.rerun()
        
        if selected_demand and selected_project and len(st.session_state.classification_system[selected_demand]) > 1:
            if st.button("删除当前企划", type="secondary"):
                del st.session_state.classification_system[selected_demand][selected_project]
                save_all_data()
                st.success(f"已删除企划: {selected_project}")
                st.rerun()
        
        if selected_demand and selected_project and selected_activity and len(st.session_state.classification_system[selected_demand][selected_project]) > 1:
            if st.button("删除当前活动", type="secondary"):
                del st.session_state.classification_system[selected_demand][selected_project][selected_activity]
                save_all_data()
                st.success(f"已删除活动: {selected_activity}")
                st.rerun()
        
        if selected_demand and selected_project and selected_activity and selected_behavior and len(st.session_state.classification_system[selected_demand][selected_project][selected_activity]) > 1:
            if st.button("删除当前行为", type="secondary"):
                del st.session_state.classification_system[selected_demand][selected_project][selected_activity][selected_behavior]
                save_all_data()
                st.success(f"已删除行为: {selected_behavior}")
                st.rerun()

# 数据管理
# 在 app.py 的数据管理部分添加示例数据导入功能
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
                "activity_templates": st.session_state.activity_templates,
                "export_time": datetime.datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # 创建下载链接
            st.download_button(
                label="下载JSON文件",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"activity_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        st.markdown("---")
        st.markdown("**🎓 示例数据**")
        if st.button("生成同济学生示例数据", use_container_width=True):
            # 这里可以调用生成示例数据的函数
            st.info("请在代码中实现示例数据生成功能")
    
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
                    if "activity_templates" in import_data:
                        st.session_state.activity_templates = import_data["activity_templates"]
                    
                    save_all_data()
                    st.success("数据导入成功！")
                    st.rerun()
            except Exception as e:
                st.error(f"文件解析失败: {e}")
    
    # 清空数据
    st.markdown("---")
    st.markdown("**⚠️ 危险操作**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("清空活动数据", type="secondary", use_container_width=True):
            if st.checkbox("我确认要清空所有活动数据，此操作不可恢复"):
                st.session_state.activities = []
                save_all_data()
                st.success("活动数据已清空")
                st.rerun()
    with col2:
        if st.button("重置所有数据", type="secondary", use_container_width=True):
            if st.checkbox("我确认要重置所有数据，包括分类系统和模板"):
                st.session_state.activities = []
                st.session_state.classification_system = {}
                st.session_state.activity_templates = {}
                save_all_data()
                st.success("所有数据已重置")
                st.rerun()

# 主应用
def main():
    """主应用"""
    # 初始化和样式
    initialize_data()
    apply_custom_css()
    
    # 标题
    st.markdown('<div class="main-header">🛤️ 个人活动轨迹日志</div>', unsafe_allow_html=True)
    st.markdown('基于时间地理学理论的个人活动记录与分析系统')
    
    # 快速操作面板
    quick_actions()
    
    # 侧边栏导航
    with st.sidebar:
        st.title("导航菜单")
        
        # 使用简单的导航方式
        page_options = {
            "📝 记录活动": "记录活动",
            "📋 活动模板": "活动模板",
            "📊 数据概览": "数据概览", 
            "📋 活动记录": "活动记录",
            "🗺️ 时空轨迹": "时空轨迹",
            "🏷️ 分类管理": "分类管理",
            "💾 数据管理": "数据管理"
        }
        
        selected_page = st.selectbox("选择功能", options=list(page_options.keys()))
        page = page_options[selected_page]
        
        st.markdown("---")
        st.markdown("### 使用说明")
        st.info("""
        1. **记录活动**: 添加新的活动记录，包括时间、地点和分类
        2. **活动模板**: 创建和使用常用活动模板
        3. **数据概览**: 查看统计数据和图表分析
        4. **活动记录**: 浏览和搜索历史活动
        5. **时空轨迹**: 查看地图上的活动轨迹
        6. **分类管理**: 自定义活动分类系统
        7. **数据管理**: 导入导出数据
        """)
        
        st.markdown("---")
        st.markdown("### 数据状态")
        st.write(f"📊 活动记录: {len(st.session_state.activities)} 条")
        st.write(f"🏷️ 分类数量: {len(st.session_state.classification_system)} 个需求类型")
        st.write(f"📋 模板数量: {len(st.session_state.activity_templates)} 个")
        
        # 今日统计
        today = datetime.date.today()
        today_activities = [a for a in st.session_state.activities 
                           if datetime.datetime.fromisoformat(a["start_time"]).date() == today]
        st.write(f"🌞 今日活动: {len(today_activities)} 条")
        
        # 手动保存按钮
        if st.button("💾 手动保存数据", use_container_width=True):
            save_all_data()
            st.success("数据已保存")
    
    # 页面路由
    if page == "记录活动":
        activity_form()
    elif page == "活动模板":
        activity_templates()
    elif page == "数据概览":
        data_overview()
    elif page == "活动记录":
        activity_records()
    elif page == "时空轨迹":
        spatiotemporal_analysis()
    elif page == "分类管理":
        classification_management()
    elif page == "数据管理":
        data_management()

if __name__ == "__main__":
    main()
