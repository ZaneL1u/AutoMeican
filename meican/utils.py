"""
数据解析工具函数
用于处理美餐 API 返回的数据
"""

from .meican_models import Dish, Restaurant, Section, Tab


def get_tabs(data):
    """
    从日期列表数据中提取标签页

    :type data: dict
    :rtype: list[Tab]
    """
    tabs = []
    for day in data["dateList"]:
        tabs.extend([Tab(_) for _ in day["calendarItemList"]])
    return tabs


def get_restaurants(tab, data):
    """
    从餐厅列表数据中提取餐厅

    :type tab: Tab
    :type data: dict
    :rtype: list[Restaurant]
    """
    restaurants = []
    for restaurant_data in data["restaurantList"]:
        restaurants.append(Restaurant(tab, restaurant_data))
    return restaurants


def get_dishes(restaurant, data):
    """
    从菜品列表数据中提取菜品

    :type restaurant: Restaurant
    :type data: dict
    :rtype: list[Dish]
    """
    sections = {}
    for section_data in data.get("sectionList", []):
        section = Section(section_data)
        sections[section.id] = section
    dishes = []
    for dish_data in data["dishList"]:
        if dish_data.get("isSection", False) or dish_data.get("priceString") is None:
            continue
        dishes.append(Dish(restaurant, dish_data, sections))
    return dishes
