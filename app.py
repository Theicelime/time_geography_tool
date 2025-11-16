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
from collections import Counter, defaultdict
import numpy as np

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
LOCATION_TEMPLATES_FILE = os.path.join(DATA_DIR, "location_templates.json")
ACTIVITY_TEMPLATES_FILE = os.path.join(DATA_DIR, "activity_templates.json")

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
    
    # 分类系统
    default_classification_system = {
        "个人": {
            "个人生理": {
                "睡觉休息": {
                    "睡觉": ["夜间睡眠", "午睡", "小憩", "寝室睡觉", "卧室睡觉"],
                    "休息": ["放松", "冥想", "发呆"]
                },
                "进食": {
                    "用餐": ["早餐", "午餐", "晚餐", "零食"],
                    "饮水": ["喝水", "饮茶", "饮料"]
                },
                "个人健康维护": {
                    "洗漱": ["刷牙", "洗脸", "洗澡"],
                    "调理身体": ["按摩", "理疗", "泡脚", "推拿", "针灸"],
                    "健康监测": ["体检", "看医生", "吃药", "康复训练"]
                }
            },
            "个人休闲": {
                "娱乐消遣": {
                    "看电视": ["电视剧", "电影", "综艺"],
                    "游戏": ["手机游戏", "电脑游戏", "主机游戏"]
                },
                "阅读学习": {
                    "阅读": ["看书", "看新闻", "看杂志"],
                    "学习": ["在线课程", "技能提升", "语言学习"]
                },
                "运动锻炼": {
                    "做操": ["太极", "八段锦", "广播体操"],
                    "健身": ["跑步", "游泳", "器械训练"]
                }
            }
        },
        "家庭": {
            "家庭空间维护": {
                "清洁打扫": {
                    "打扫": ["扫地", "拖地", "整理", "倒垃圾"],
                    "洗涤": ["洗衣", "晾衣", "熨烫"]
                }
            },
            "照顾家人": {
                "照顾孩子": {
                    "接送": ["上学接送", "活动接送"],
                    "陪伴": ["陪玩", "作业辅导", "亲子时光"],
                    "学习辅导": ["检查作业", "批改作业", "带孩子复习"]
                }
            }
        }
    }
    
    if 'classification_system' not in st.session_state:
        st.session_state.classification_system = load_json_file(
            CLASSIFICATION_FILE, default_classification_system
        )
    
    # 地点模板
    default_location_templates = {
        "家": {
            "category": "居住场所",
            "tag": "家",
            "name": "家",
            "coordinates": None
        },
        "办公室": {
            "category": "工作场所", 
            "tag": "办公室",
            "name": "办公室",
            "coordinates": None
        },
        "学校": {
            "category": "教育场所",
            "tag": "学校", 
            "name": "学校",
            "coordinates": None
        }
    }
    
    if 'location_templates' not in st.session_state:
        st.session_state.location_templates = load_json_file(
            LOCATION_TEMPLATES_FILE, default_location_templates
        )
    
    # 活动模板
    if 'activity_templates' not in st.session_state:
        st.session_state.activity_templates = load_json_file(ACTIVITY_TEMPLATES_FILE, {})
    
    # 初始化地图中心
    if 'map_center' not in st.session_state:
        st.session_state.map_center = [39.9042, 116.4074]  # 北京

# 保存数据
def save_all_data():
    """保存所有数据到文件"""
    save_json_file(ACTIVITIES_FILE, st.session_state.activities)
    save_json_file(CLASSIFICATION_FILE, st.session_state.classification_system)
    save_json_file(LOCATION_TEMPLATES_FILE, st.session_state.location_templates)
    save_json_file(ACTIVITY_TEMPLATES_FILE, st.session_state.activity_templates)

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
    .location-card {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .location-card:hover {
        background-color: #bbdefb;
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

# 智能地图组件
def smart_map_selector():
    """智能地图选择器"""
    st.markdown("**🗺️ 地点选择**")
    
    # 地点搜索
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
    
    # 显示地图
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
    
    return coordinates, searched_location

# 获取所有片段选项
def get_all_episodes():
    """获取所有片段选项"""
    episodes = []
    for demand, projects in st.session_state.classification_system.items():
        for project, activities in projects.items():
            for activity, behavior_dict in activities.items():
                for behavior, episode_list in behavior_dict.items():
                    for episode in episode_list:
                        episodes.append({
                            "demand": demand,
                            "project": project,
                            "activity": activity,
                            "behavior": behavior,
                            "episode": episode,
                            "full_path": f"{demand} > {project} > {activity} > {behavior} > {episode}"
                        })
    return episodes

# 通过片段查找完整分类
def find_classification_by_episode(episode_name):
    """通过片段名称查找完整分类"""
    for demand, projects in st.session_state.classification_system.items():
        for project, activities in projects.items():
            for activity, behavior_dict in activities.items():
                for behavior, episodes in behavior_dict.items():
                    if episode_name in episodes:
                        return {
                            "demand": demand,
                            "project": project,
                            "activity": activity,
                            "behavior": behavior,
                            "episode": episode_name
                        }
    return None

# 活动记录表单
def activity_form():
    """活动记录表单"""
    st.markdown('<div class="sub-header">📝 记录新活动</div>', unsafe_allow_html=True)
    
    # 初始化时间状态
    if 'start_datetime' not in st.session_state:
        st.session_state.start_datetime = datetime.datetime.now()
    if 'end_datetime' not in st.session_state:
        st.session_state.end_datetime = datetime.datetime.now() + timedelta(hours=1)
    
    # 检查是否有模板数据要填充
    prefilled_data = st.session_state.get('template_data', {})
    
    # 先显示地图选择器（在表单外）
    coordinates, searched_location = smart_map_selector()
    
    # 使用st.form的正确方式
    with st.form(key="activity_form"):
        # 时间信息
        col1, col2 = st.columns(2)
        with col1:
            # 使用session_state来保持时间状态
            start_date = st.date_input("开始日期*", value=st.session_state.start_datetime.date())
            start_time = st.time_input("开始时间*", value=st.session_state.start_datetime.time())
            new_start_datetime = datetime.datetime.combine(start_date, start_time)
            
        with col2:
            end_date = st.date_input("结束日期*", value=st.session_state.end_datetime.date())
            end_time = st.time_input("结束时间*", value=st.session_state.end_datetime.time())
            new_end_datetime = datetime.datetime.combine(end_date, end_time)
            
            # 自动计算持续时间
            if new_start_datetime and new_end_datetime:
                if new_end_datetime > new_start_datetime:
                    duration = int((new_end_datetime - new_start_datetime).total_seconds() / 60)
                    st.write(f"**持续时间:** {duration} 分钟")
                else:
                    st.error("结束时间必须晚于开始时间")
                    duration = 60
            else:
                duration = 60
        
        # 地点信息
        st.markdown("**📍 地点信息**")
        
        # 地点模板选择
        location_templates = list(st.session_state.location_templates.keys())
        selected_location_template = st.selectbox(
            "选择地点模板", 
            options=[""] + location_templates,
            help="从预设地点模板中选择，或手动输入新地点"
        )
        
        if selected_location_template:
            # 使用地点模板
            template = st.session_state.location_templates[selected_location_template]
            location_category = template["category"]
            location_tag = template["tag"]
            location_name = template["name"]
            coordinates = template["coordinates"]
            
            st.info(f"已选择地点: {location_category} - {location_tag} - {location_name}")
        else:
            # 手动输入地点
            loc_col1, loc_col2, loc_col3 = st.columns(3)
            with loc_col1:
                location_category = st.text_input("地点大类*", placeholder="如：居住场所")
            with loc_col2:
                location_tag = st.text_input("地点标签*", placeholder="如：家")
            with loc_col3:
                location_name = st.text_input("具体地点名称*", placeholder="如：中关村大厦A座")
            
            # 如果有搜索到地点，更新地点名称
            if searched_location and not location_name:
                location_name = searched_location['name']
        
        # 活动信息
        st.markdown("**🏷️ 活动分类**")
        
        # 获取所有片段选项
        all_episodes = get_all_episodes()
        episode_options = {e["episode"]: e for e in all_episodes}
        
        # 片段选择
        selected_episode = st.selectbox(
            "选择行为片段*", 
            options=[""] + list(episode_options.keys()),
            help="选择预定义的行为片段，系统将自动匹配完整分类"
        )
        
        # 如果选择了片段，自动填充分类
        if selected_episode and selected_episode in episode_options:
            episode_data = episode_options[selected_episode]
            demand_type = episode_data["demand"]
            project_type = episode_data["project"]
            activity_type = episode_data["activity"]
            behavior_type = episode_data["behavior"]
            
            st.success(f"自动匹配: {demand_type} → {project_type} → {activity_type} → {behavior_type} → {selected_episode}")
        else:
            # 如果没有匹配的片段，允许手动输入
            st.warning("未找到匹配的行为片段，请手动输入完整分类")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                demand_type = st.text_input("需求类型", placeholder="如：个人")
            with col2:
                project_type = st.text_input("企划类型", placeholder="如：个人生理")
            with col3:
                activity_type = st.text_input("活动类型", placeholder="如：睡觉休息")
            with col4:
                behavior_type = st.text_input("行为类型", placeholder="如：睡觉")
            with col5:
                selected_episode = st.text_input("行为片段*", placeholder="如：寝室睡觉")
        
        # 活动描述
        activity_description = st.text_area("活动描述", 
                                          placeholder="详细描述活动内容和情境...",
                                          height=100)
        
        # 表单提交按钮
        submitted = st.form_submit_button("✅ 添加活动", use_container_width=True)
        
        # 如果表单被提交，更新session_state中的时间
        if submitted:
            st.session_state.start_datetime = new_start_datetime
            st.session_state.end_datetime = new_end_datetime
    
    # 其他按钮（在表单外）
    col1, col2 = st.columns(2)
    with col1:
        clear_form = st.button("🗑️ 清空表单", use_container_width=True)
    
    if submitted:
        # 验证必填字段
        required_fields = [
            new_start_datetime, new_end_datetime, 
            'location_category' in locals() and location_category,
            'location_tag' in locals() and location_tag,
            'location_name' in locals() and location_name,
            selected_episode
        ]
        
        if not all(required_fields):
            st.error("请填写所有必填字段（标*的字段）")
            return
        
        if new_end_datetime <= new_start_datetime:
            st.error("结束时间必须晚于开始时间")
            return
        
        # 计算持续时间
        duration = int((new_end_datetime - new_start_datetime).total_seconds() / 60)
        
        # 创建活动对象
        activity = {
            "id": len(st.session_state.activities) + 1,
            "start_time": new_start_datetime.isoformat(),
            "end_time": new_end_datetime.isoformat(),
            "duration": duration,
            "location_category": location_category,
            "location_tag": location_tag,
            "location_name": location_name,
            "coordinates": coordinates,
            "demand": demand_type if 'demand_type' in locals() else "",
            "project": project_type if 'project_type' in locals() else "",
            "activity": activity_type if 'activity_type' in locals() else "",
            "behavior": behavior_type if 'behavior_type' in locals() else "",
            "episode": selected_episode,
            "description": activity_description,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # 添加到活动列表
        st.session_state.activities.append(activity)
        st.session_state.activities.sort(key=lambda x: x["start_time"])
        
        # 自动保存地点模板
        if not selected_location_template and location_tag and location_tag not in st.session_state.location_templates:
            st.session_state.location_templates[location_tag] = {
                "category": location_category,
                "tag": location_tag,
                "name": location_name,
                "coordinates": coordinates
            }
            st.success(f"📍 已自动保存地点模板: {location_tag}")
        
        # 自动保存活动模板
        if selected_episode and selected_episode not in st.session_state.activity_templates:
            st.session_state.activity_templates[selected_episode] = {
                "demand": demand_type if 'demand_type' in locals() else "",
                "project": project_type if 'project_type' in locals() else "",
                "activity": activity_type if 'activity_type' in locals() else "",
                "behavior": behavior_type if 'behavior_type' in locals() else "",
                "episode": selected_episode
            }
            st.success(f"📋 已自动保存活动模板: {selected_episode}")
        
        # 保存数据
        save_all_data()
        
        # 清除模板数据
        if 'template_data' in st.session_state:
            del st.session_state.template_data
        
        st.success("🎉 活动添加成功！")
        st.rerun()
    
    if clear_form:
        # 清除模板数据和重置时间
        if 'template_data' in st.session_state:
            del st.session_state.template_data
        # 重置时间为当前时间
        st.session_state.start_datetime = datetime.datetime.now()
        st.session_state.end_datetime = datetime.datetime.now() + timedelta(hours=1)
        st.rerun()

# 创建行为类型时间分布图 - 根据参考图重新设计
def create_activity_sequence_chart(start_date=None, end_date=None, level="demand"):
    """创建活动序列图 - 根据参考图4-14重新设计
    
    Args:
        start_date: 开始日期
        end_date: 结束日期  
        level: 分类层级，可以是 'demand', 'project', 'activity'
    """
    if not st.session_state.activities:
        st.info("暂无活动数据")
        return
    
    # 过滤日期范围
    filtered_activities = st.session_state.activities
    if start_date and end_date:
        filtered_activities = [
            a for a in filtered_activities 
            if start_date <= datetime.datetime.fromisoformat(a["start_time"]).date() <= end_date
        ]
    
    if not filtered_activities:
        st.info("选定日期范围内没有活动数据")
        return
    
    # 准备数据 - 按日期和小时分组
    chart_data = []
    
    for activity in filtered_activities:
        start_time = datetime.datetime.fromisoformat(activity["start_time"])
        date = start_time.date()
        hour = start_time.hour
        
        # 根据选择的层级获取分类
        if level == "demand":
            category = activity.get("demand", "未分类")
        elif level == "project":
            category = activity.get("project", "未分类")
        elif level == "activity":
            category = activity.get("activity", "未分类")
        else:
            category = activity.get("demand", "未分类")
        
        chart_data.append({
            "date": date,
            "hour": hour,
            "category": category,
            "duration": activity["duration"],
            "demand": activity.get("demand", ""),
            "project": activity.get("project", ""),
            "activity": activity.get("activity", ""),
            "location": activity.get("location_name", "")
        })
    
    # 创建数据框
    df = pd.DataFrame(chart_data)
    
    if df.empty:
        st.info("没有符合条件的数据")
        return
    
    # 创建数据透视表 - 按日期和小时统计
    pivot_df = df.pivot_table(
        index='date', 
        columns='hour', 
        values='category', 
        aggfunc=lambda x: x.mode()[0] if len(x.mode()) > 0 else '无活动',
        fill_value='无活动'
    )
    
    # 确保24小时完整
    for h in range(24):
        if h not in pivot_df.columns:
            pivot_df[h] = '无活动'
    
    # 按小时排序
    pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)
    
    # 创建堆叠柱状图
    # 首先需要将数据转换为长格式
    long_data = []
    for date in pivot_df.index:
        for hour in pivot_df.columns:
            category = pivot_df.loc[date, hour]
            long_data.append({
                'date': date,
                'hour': hour,
                'category': category
            })
    
    long_df = pd.DataFrame(long_data)
    
    # 创建颜色映射
    categories = long_df['category'].unique()
    colors = px.colors.qualitative.Set3[:len(categories)]
    color_map = {cat: color for cat, color in zip(categories, colors)}
    
    # 创建堆叠柱状图
    fig = px.bar(
        long_df,
        x='date',
        color='category',
        color_discrete_map=color_map,
        title=f"居民活动序列 - 按{level}分类",
        labels={
            "date": "日期",
            "category": level,
            "count": "活动数量"
        },
        height=500
    )
    
    # 调整布局
    fig.update_layout(
        xaxis_title="日期",
        yaxis_title="活动类型分布",
        legend_title=level,
        barmode='stack',
        xaxis=dict(tickangle=45)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 添加24小时分布视图
    st.markdown("**🕐 24小时活动分布**")
    
    # 按小时统计活动类型
    hour_data = []
    for hour in range(24):
        hour_activities = [a for a in filtered_activities 
                          if datetime.datetime.fromisoformat(a["start_time"]).hour == hour]
        
        if hour_activities:
            # 统计该小时的主要活动类型
            categories = [a.get(level, "未分类") for a in hour_activities]
            category_counts = Counter(categories)
            main_category = category_counts.most_common(1)[0][0]
            
            hour_data.append({
                "hour": hour,
                "category": main_category,
                "count": len(hour_activities)
            })
        else:
            hour_data.append({
                "hour": hour,
                "category": "无活动",
                "count": 0
            })
    
    hour_df = pd.DataFrame(hour_data)
    
    # 创建24小时分布图
    fig_hour = px.bar(
        hour_df,
        x='hour',
        y='count',
        color='category',
        color_discrete_map=color_map,
        title="24小时活动类型分布",
        labels={
            "hour": "小时",
            "count": "活动数量",
            "category": level
        }
    )
    
    fig_hour.update_layout(
        xaxis=dict(tickvals=list(range(0, 24, 2)))
    )
    
    st.plotly_chart(fig_hour, use_container_width=True)

# 增强的数据概览
def data_overview():
    """增强的数据概览面板"""
    st.markdown('<div class="sub-header">📊 数据概览</div>', unsafe_allow_html=True)
    
    if not st.session_state.activities:
        st.info("📝 暂无活动数据，请先添加活动记录")
        return
    
    # 计算统计指标
    total_activities = len(st.session_state.activities)
    total_duration = sum(activity["duration"] for activity in st.session_state.activities)
    total_hours = total_duration / 60
    
    # 获取日期范围
    dates = [datetime.datetime.fromisoformat(a["start_time"]).date() for a in st.session_state.activities]
    min_date = min(dates) if dates else datetime.date.today()
    max_date = max(dates) if dates else datetime.date.today()
    
    # 日期范围选择
    st.markdown("### 📅 选择日期范围")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("开始日期", value=min_date)
    with col2:
        end_date = st.date_input("结束日期", value=max_date)
    with col3:
        level = st.selectbox(
            "分类层级", 
            options=["demand", "project", "activity"],
            format_func=lambda x: {"demand": "需求", "project": "企划", "activity": "活动"}[x]
        )
    
    # 显示活动序列图
    st.markdown("### 🕐 活动序列图")
    create_activity_sequence_chart(start_date, end_date, level)
    
    # 基本统计信息
    st.markdown("### 📈 基本统计")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总活动数", total_activities)
    with col2:
        st.metric("总时长", f"{total_hours:.1f} 小时")
    with col3:
        st.metric("记录天数", (max_date - min_date).days + 1)
    with col4:
        st.metric("日均活动", f"{total_activities/((max_date - min_date).days + 1):.1f}")
    
    # 其他分析图表
    st.markdown("### 🔍 详细分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 需求类型分布
        demand_data = {}
        for activity in st.session_state.activities:
            demand = activity["demand"]
            duration = activity["duration"]
            demand_data[demand] = demand_data.get(demand, 0) + duration
        
        if demand_data:
            fig_demand = px.pie(
                values=list(demand_data.values()),
                names=list(demand_data.keys()),
                title="各需求类型时间分布"
            )
            st.plotly_chart(fig_demand, use_container_width=True)
    
    with col2:
        # 时间段分布
        time_slots = {
            "深夜(0-6)": 0, "早晨(6-9)": 0, "上午(9-12)": 0,
            "中午(12-14)": 0, "下午(14-18)": 0, "晚上(18-24)": 0
        }
        
        for activity in st.session_state.activities:
            start_time = datetime.datetime.fromisoformat(activity["start_time"])
            hour = start_time.hour
            
            if 0 <= hour < 6:
                time_slots["深夜(0-6)"] += activity["duration"]
            elif 6 <= hour < 9:
                time_slots["早晨(6-9)"] += activity["duration"]
            elif 9 <= hour < 12:
                time_slots["上午(9-12)"] += activity["duration"]
            elif 12 <= hour < 14:
                time_slots["中午(12-14)"] += activity["duration"]
            elif 14 <= hour < 18:
                time_slots["下午(14-18)"] += activity["duration"]
            else:
                time_slots["晚上(18-24)"] += activity["duration"]
        
        fig_time = px.bar(
            x=list(time_slots.keys()),
            y=list(time_slots.values()),
            title="各时间段活动时长分布",
            labels={"x": "时间段", "y": "总时长(分钟)"}
        )
        st.plotly_chart(fig_time, use_container_width=True)

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
        episode_options = [""] + list(set(a.get("episode", "") for a in st.session_state.activities if a.get("episode")))
        episode_filter = st.selectbox("筛选行为片段", episode_options)
    with col3:
        date_filter = st.date_input("筛选日期")
    
    # 筛选活动
    filtered_activities = st.session_state.activities
    
    if search_term:
        filtered_activities = [a for a in filtered_activities 
                             if search_term.lower() in a.get("description", "").lower()]
    
    if episode_filter:
        filtered_activities = [a for a in filtered_activities if a.get("episode") == episode_filter]
    
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
                        {activity['location_tag']} / 
                        {activity['location_name']}
                    </div>
                    <div style="background: #e3f2fd; padding: 0.5rem; border-radius: 5px; font-size: 0.9rem;">
                        {activity['demand']} → {activity['project']} → {activity['activity']} → {activity['behavior']} → {activity['episode']}
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

# 地点模板管理
def location_templates_management():
    """地点模板管理"""
    st.markdown('<div class="sub-header">📍 地点模板管理</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 现有地点模板
        st.markdown("**💾 已保存的地点模板**")
        if st.session_state.location_templates:
            for template_name, template_data in st.session_state.location_templates.items():
                with st.container():
                    coord_info = ""
                    if template_data.get("coordinates"):
                        coord_info = f"<br><small>坐标: {template_data['coordinates']['lat']:.4f}, {template_data['coordinates']['lng']:.4f}</small>"
                    
                    st.markdown(f"""
                    <div class="location-card">
                        <strong>{template_name}</strong><br>
                        <small>大类: {template_data['category']}</small><br>
                        <small>标签: {template_data['tag']}</small><br>
                        <small>名称: {template_data['name']}</small>
                        {coord_info}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"使用地点", key=f"use_loc_{template_name}"):
                            st.session_state.location_template_data = template_data
                            st.success(f"已选择地点模板: {template_name}")
                            st.rerun()
                    with col_btn2:
                        if st.button("删除", key=f"del_loc_{template_name}", type="secondary"):
                            del st.session_state.location_templates[template_name]
                            save_all_data()
                            st.success(f"地点模板 '{template_name}' 已删除")
                            st.rerun()
        else:
            st.info("暂无地点模板")
    
    with col2:
        # 创建新地点模板
        st.markdown("**✏️ 创建地点模板**")
        
        with st.form("location_template_form"):
            loc_category = st.text_input("地点大类*", placeholder="如：居住场所")
            loc_tag = st.text_input("地点标签*", placeholder="如：家")
            loc_name = st.text_input("具体地点名称*", placeholder="如：中关村大厦A座")
            
            # 地图选择器
            coordinates, searched_location = smart_map_selector()
            
            submitted = st.form_submit_button("保存地点模板", use_container_width=True)
            
            if submitted:
                if loc_category and loc_tag and loc_name:
                    if loc_tag not in st.session_state.location_templates:
                        st.session_state.location_templates[loc_tag] = {
                            "category": loc_category,
                            "tag": loc_tag,
                            "name": loc_name,
                            "coordinates": coordinates
                        }
                        save_all_data()
                        st.success(f"地点模板 '{loc_tag}' 已保存")
                        st.rerun()
                    else:
                        st.error("该地点标签已存在")
                else:
                    st.error("请填写完整信息")

# 活动模板管理
def activity_templates_management():
    """活动模板管理"""
    st.markdown('<div class="sub-header">📋 活动模板管理</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 现有活动模板
        st.markdown("**💾 已保存的活动模板**")
        if st.session_state.activity_templates:
            for template_name, template_data in st.session_state.activity_templates.items():
                with st.container():
                    st.markdown(f"""
                    <div class="template-card">
                        <strong>{template_name}</strong><br>
                        <small>{template_data['demand']} → {template_data['project']} → {template_data['activity']} → {template_data['behavior']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"使用模板", key=f"use_act_{template_name}"):
                            st.session_state.template_data = template_data
                            st.success(f"已加载模板: {template_name}")
                            st.rerun()
                    with col_btn2:
                        if st.button("删除", key=f"del_act_{template_name}", type="secondary"):
                            del st.session_state.activity_templates[template_name]
                            save_all_data()
                            st.success(f"活动模板 '{template_name}' 已删除")
                            st.rerun()
        else:
            st.info("暂无活动模板")
    
    with col2:
        # 创建新活动模板
        st.markdown("**✏️ 创建活动模板**")
        
        with st.form("activity_template_form"):
            temp_demand = st.text_input("需求类型*", placeholder="如：个人")
            temp_project = st.text_input("企划类型*", placeholder="如：个人生理")
            temp_activity = st.text_input("活动类型*", placeholder="如：睡觉休息")
            temp_behavior = st.text_input("行为类型*", placeholder="如：睡觉")
            temp_episode = st.text_input("行为片段*", placeholder="如：寝室睡觉")
            
            submitted = st.form_submit_button("保存活动模板", use_container_width=True)
            
            if submitted:
                if temp_demand and temp_project and temp_activity and temp_behavior and temp_episode:
                    if temp_episode not in st.session_state.activity_templates:
                        st.session_state.activity_templates[temp_episode] = {
                            "demand": temp_demand,
                            "project": temp_project,
                            "activity": temp_activity,
                            "behavior": temp_behavior,
                            "episode": temp_episode
                        }
                        save_all_data()
                        st.success(f"活动模板 '{temp_episode}' 已保存")
                        st.rerun()
                    else:
                        st.error("该行为片段已存在")
                else:
                    st.error("请填写完整信息")

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
                "classification_system": st.session_state.classification_system,
                "location_templates": st.session_state.location_templates,
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
    
    with col2:
        st.markdown("**📥 导入数据**")
        uploaded_file = st.file_uploader("选择JSON文件", type=["json"])
        
        if uploaded_file is not None:
            try:
                import_data = json.load(uploaded_file)
                
                if st.button("导入数据", use_container_width=True):
                    if "activities" in import_data:
                        st.session_state.activities = import_data["activities"]
                    if "classification_system" in import_data:
                        st.session_state.classification_system = import_data["classification_system"]
                    if "location_templates" in import_data:
                        st.session_state.location_templates = import_data["location_templates"]
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
                initialize_data()
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
            "📍 地点模板": "地点模板", 
            "📋 活动模板": "活动模板",
            "📊 数据概览": "数据概览", 
            "📋 活动记录": "活动记录",
            "💾 数据管理": "数据管理"
        }
        
        selected_page = st.selectbox("选择功能", options=list(page_options.keys()))
        page = page_options[selected_page]
        
        st.markdown("---")
        st.markdown("### 使用说明")
        st.info("""
        1. **记录活动**: 添加新的活动记录，包括时间、地点和分类
        2. **地点模板**: 管理常用地点模板
        3. **活动模板**: 管理常用活动模板  
        4. **数据概览**: 查看统计数据和图表分析
        5. **活动记录**: 浏览和搜索历史活动
        6. **数据管理**: 导入导出数据
        """)
        
        st.markdown("---")
        st.markdown("### 数据状态")
        st.write(f"📊 活动记录: {len(st.session_state.activities)} 条")
        st.write(f"📍 地点模板: {len(st.session_state.location_templates)} 个")
        st.write(f"📋 活动模板: {len(st.session_state.activity_templates)} 个")
        
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
    elif page == "地点模板":
        location_templates_management()
    elif page == "活动模板":
        activity_templates_management()
    elif page == "数据概览":
        data_overview()
    elif page == "活动记录":
        activity_records()
    elif page == "数据管理":
        data_management()

if __name__ == "__main__":
    main()
