"""
美餐 API 客户端
提供与美餐服务的交互功能
"""

import datetime
import json
import time
from urllib.parse import urlencode

import requests

from .exceptions import MeiCanError, MeiCanLoginFail, NoOrderAvailable
from .meican_models import TabStatus
from .utils import get_dishes, get_restaurants, get_tabs


class RestUrl(object):
    """用来存储 MeiCan Rest 接口的类"""

    @classmethod
    def get_base_url(cls, path, params=None, wrap=True):
        """
        :type path: str | unicode
        :type params: dict
        :type wrap: bool
        :rtype: str | unicode
        """
        if params:
            if wrap:
                params["noHttpGetCache"] = int(time.time() * 1000)
            path = "{}?{}".format(path, urlencode(sorted(params.items())))
        return "https://meican.com/{}".format(path)

    @classmethod
    def login(cls):
        return cls.get_base_url("account/directlogin")

    @classmethod
    def calender_items(cls, detail=False):
        today = datetime.date.today()
        one_week = datetime.timedelta(weeks=1)
        data = {
            "beginDate": today.strftime("%Y-%m-%d"),
            "endDate": (today + one_week).strftime("%Y-%m-%d"),
            "withOrderDetail": detail,
        }
        return cls.get_base_url("preorder/api/v2.1/calendarItems/list", data)

    @classmethod
    def calender_items_with_detail(cls):
        """获取包含订单详情的日历项目"""
        return cls.calender_items(detail=True)

    @classmethod
    def restaurants(cls, tab):
        """
        :type tab: Tab
        """
        data = {"tabUniqueId": tab.uid, "targetTime": tab.target_time}
        return cls.get_base_url("preorder/api/v2.1/restaurants/list", data)

    @classmethod
    def dishes(cls, restaurant):
        """
        :type restaurant: Restaurant
        """
        tab = restaurant.tab
        data = {
            "restaurantUniqueId": restaurant.uid,
            "tabUniqueId": tab.uid,
            "targetTime": tab.target_time,
        }
        return cls.get_base_url("preorder/api/v2.1/restaurants/show", data)

    @classmethod
    def order(cls, dish, address_uid=""):
        """
        :type dish: Dish
        :type address_uid: str
        """
        tab = dish.restaurant.tab
        address_uid = address_uid or tab.addresses[0].uid if tab.addresses else ""
        data = {
            "order": json.dumps([{"count": "1", "dishId": "{}".format(dish.id)}]),
            "tabUniqueId": tab.uid,
            "targetTime": tab.target_time,
            "corpAddressUniqueId": address_uid,
            "userAddressUniqueId": address_uid,
        }
        return cls.get_base_url("preorder/api/v2.1/orders/add", data, wrap=False)


class MeiCan(object):
    def __init__(self, username, password, user_agent=None):
        """
        :type username: str | unicode
        :type password: str | unicode
        """
        self.responses = []
        self._session = requests.Session()
        user_agent = (
            user_agent
            or "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
        )
        self._session.headers["User-Agent"] = user_agent
        self._calendar_items = None
        self._tabs = None

        form_data = {
            "username": username,
            "password": password,
            "loginType": "username",
            "remember": True,
        }
        response = self._request("post", RestUrl.login(), form_data)
        if 200 != response.status_code or username not in response.text:
            raise MeiCanLoginFail("login fail because username or password incorrect")

    @property
    def tabs(self):
        """
        :rtype: list[Tab]
        """
        if not self._tabs:
            self.load_tabs()
        return self._tabs

    @property
    def next_available_tab(self):
        """
        :rtype: Tab
        """

        print("获取下一个可用的标签页...")

        available_tabs = [_ for _ in self.tabs if _.status == TabStatus.AVAIL]
        return available_tabs[0] if available_tabs else None

    @property
    def next_available_buffet_tab(self):
        """
        :rtype: Tab
        """

        print("获取下一个可以点的自助餐...")

        available_tabs = [
            _ for _ in self.tabs if _.status == TabStatus.AVAIL and "自助" in _.title
        ]

        return available_tabs[0] if available_tabs else None

    def load_tabs(self, refresh=False):
        try:
            if not self._calendar_items or refresh:
                self._calendar_items = self.http_get(RestUrl.calender_items())

                self._tabs = get_tabs(self._calendar_items)
        except Exception as e:
            raise MeiCanLoginFail(f"Failed to load tabs: {str(e)}")

    def get_restaurants(self, tab):
        """
        :type tab: Tab
        :rtype: list[Restaurant]
        """
        data = self.http_get(RestUrl.restaurants(tab))
        return get_restaurants(tab, data)

    def get_dishes(self, restaurant):
        """
        :type restaurant: Restaurant
        """
        data = self.http_get(RestUrl.dishes(restaurant))
        return get_dishes(restaurant, data)

    def list_dishes(self, tab=None):
        """
        :type tab: Tab
        :rtype: list[Dish]
        """
        tab = tab or self.next_available_tab
        if not tab:
            raise NoOrderAvailable("Currently no available orders")
        restaurants = self.get_restaurants(tab)
        dishes = []
        for restaurant in restaurants:
            dishes.extend(self.get_dishes(restaurant))
        return dishes

    def order(self, dish, address_uid=""):
        """
        :type dish: Dish
        :type address_uid: str
        """
        data = self.http_post(RestUrl.order(dish, address_uid=address_uid))
        return data

    def get_order_status(self, target_date=None):
        """
        获取指定日期的订单状态
        :param target_date: 目标日期，如果为None则获取今天和明天的状态
        :return: 包含订单信息的字典
        """
        try:
            # 获取包含订单详情的日历项目
            calendar_data = self.http_get(RestUrl.calender_items_with_detail())

            if target_date:
                target_dates = [target_date]
            else:
                today = datetime.date.today()
                tomorrow = today + datetime.timedelta(days=1)
                target_dates = [today, tomorrow]

            order_status = {}

            # 解析日历数据，查找已有订单
            if "dateList" in calendar_data:
                for date_item in calendar_data["dateList"]:
                    date_str = date_item.get("date", "")
                    if date_str:
                        try:
                            order_date = datetime.datetime.strptime(
                                date_str, "%Y-%m-%d"
                            ).date()

                            if order_date in target_dates:
                                # 检查这一天是否有订单
                                has_order = False
                                meal_name = ""

                                if "calendarItemList" in date_item:
                                    for calendar_item in date_item["calendarItemList"]:
                                        # 检查订单状态 - ORDER 表示已下单，AVAILABLE 等其他状态表示可下单但未下单
                                        item_status = calendar_item.get("status", "")
                                        if item_status == "ORDER":
                                            has_order = True
                                            meal_name = calendar_item.get("title", "")
                                            break
                                        # 如果状态是 CANCELED 或其他表示取消的状态，确保 has_order 为 False
                                        elif item_status in ["CANCELED", "CANCELLED"]:
                                            has_order = False

                                order_status[order_date] = {
                                    "has_order": has_order,
                                    "meal_name": meal_name,
                                }
                        except ValueError:
                            # 日期格式错误，跳过
                            continue

            # 确保所有目标日期都有状态信息，即使在日历数据中没有找到
            for target_date in target_dates:
                if target_date not in order_status:
                    order_status[target_date] = {
                        "has_order": False,
                        "meal_name": "",
                    }

            return order_status

        except Exception as e:
            print(f"获取订单状态失败: {e}")
            return {}

    def http_get(self, url, **kwargs):
        """
        :type url: str | unicode
        :rtype: dict | str | unicode
        """
        response = self._request("get", url, **kwargs)
        return response.json()

    def http_post(self, url, data=None, **kwargs):
        """
        :type url: str | unicode
        :type data: dict
        :rtype: dict | str | unicode
        """
        response = self._request("post", url, data, **kwargs)
        return response.json()

    def _request(self, method, url, data=None, **kwargs):
        """
        :type method: str | unicode
        :type url: str | unicode
        :type data: dict
        :type kwargs: dict
        :rtype: requests.Response
        """
        func = getattr(self._session, method)
        response = func(url, data=data, **kwargs)  # type: requests.Response
        response.encoding = response.encoding or "utf-8"
        self.responses.append(response)
        if response.status_code != 200:
            error = response.json()
            raise MeiCanError(
                "[{}] {}".format(
                    error.get("error", ""), error.get("error_description", "")
                )
            )
        return response
