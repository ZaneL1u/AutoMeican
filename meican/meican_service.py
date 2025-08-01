import logging
import random
from datetime import datetime, timedelta

from django.conf import settings

# 导入美餐 API 客户端和异常
from .api_client import MeiCan
from .exceptions import MeiCanLoginFail, NoOrderAvailable

logger = logging.getLogger("meican")


class MeicanService:
    """美餐服务类，处理登录、获取菜单、下单等操作"""

    def __init__(self):
        self.meican_client = None

    def login(self, email, password=None):
        """
        登录美餐 - 使用 api_client.MeiCan
        :param email: 邮箱
        :param password: 密码，如果为None则使用全局密码
        :return: (success, token, error_message)
        """
        if password is None:
            password = settings.MEICAN_GLOBAL_PASSWORD

        try:
            # 使用新的 API 客户端进行登录
            print(f"正在尝试登录用户: {email, password}")
            self.meican_client = MeiCan(email, password)
            logger.info(f"用户 {email} 登录成功")
            return True, "login_success", None
        except MeiCanLoginFail as e:
            logger.error(f"登录失败: {e}")
            return False, None, "用户名或密码错误"
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False, None, f"登录异常: {str(e)}"

    def find_and_order_buffet(self, email=None, password=None):
        """
        查找并订购自助餐
        :param email: 邮箱（可选，如果未提供则需要先调用login）
        :param password: 密码
        :return: (success, message)
        """
        try:
            # 如果提供了邮箱，先登录
            if email:
                success, _, error = self.login(email, password)

                print(f"登录结果: {'成功' if success else '失败'}")

                if not success:
                    return False, "", error

            # 确保已登录
            if not self.meican_client:
                return False, "", "未登录"

            # 首先查询并更新订单状态
            print("正在查询当前订单状态...")
            status_success, status_info, status_error = (
                self.query_and_update_order_status(email, password)
            )

            if status_success and "updated_records" in status_info:
                updated_records = status_info["updated_records"]
                if updated_records:
                    logger.info(f"订单状态已更新: {', '.join(updated_records)}")
                    print(f"订单状态已更新: {', '.join(updated_records)}")

            # 查找所有包含"自助"的标签页（不管状态）
            all_buffet_tabs = [
                tab for tab in self.meican_client.tabs if "自助" in tab.title
            ]

            if not all_buffet_tabs:
                return False, "", "当前没有自助餐可订"

            ordered_meals = []
            successful_orders = []

            # 遍历所有自助餐标签页
            for tab in all_buffet_tabs:
                print(f"检查标签页: {tab.title}, 状态: {tab.status}")

                # 统一处理状态检查
                if hasattr(tab.status, "value"):
                    status_value = tab.status.value
                elif hasattr(tab.status, "name"):
                    status_value = tab.status.name
                else:
                    status_value = str(tab.status)

                # 如果这个时段已经订过餐，跳过
                if status_value in ["ORDERED", "ORDER"]:
                    ordered_meals.append(f"{tab.title}")
                    logger.info(f"时段 {tab.title} 已订餐，跳过")
                    continue

                # 如果这个时段不可用，跳过
                if status_value not in ["AVAILABLE", "AVAIL"]:
                    logger.info(
                        f"时段 {tab.title} 不可订餐 (状态: {status_value})，跳过"
                    )
                    continue

                try:
                    # 获取这个时段的所有菜品
                    dishes = self.meican_client.list_dishes(tab)
                    if not dishes:
                        logger.info(f"时段 {tab.title} 没有可订购的菜品")
                        continue

                    # 查找自助餐（包含"自助"关键词的菜品）
                    buffet_dishes = [dish for dish in dishes if "自助" in dish.name]

                    print(
                        f"时段 {tab.title} 找到的自助餐菜品: {[d.name for d in buffet_dishes]}"
                    )

                    if not buffet_dishes:
                        logger.info(f"时段 {tab.title} 没有找到自助餐菜品")
                        continue

                    # 随机选择一个自助餐
                    selected_dish = random.choice(buffet_dishes)
                    logger.info(f"为时段 {tab.title} 选择自助餐: {selected_dish.name}")

                    # 下单
                    order_result = self.meican_client.order(selected_dish)
                    logger.info(f"时段 {tab.title} 订餐结果: {order_result}")

                    successful_orders.append(f"{tab.title}: {selected_dish.name}")

                except Exception as order_error:
                    logger.error(f"时段 {tab.title} 订餐失败: {order_error}")
                    continue

            # 汇总结果
            result_messages = []
            if ordered_meals:
                result_messages.append(f"已有订单: {', '.join(ordered_meals)}")
            if successful_orders:
                result_messages.append(f"新订餐成功: {', '.join(successful_orders)}")

            # 返回成功的订单列表和已有订单列表，用于后续的数据库记录
            return_data = {
                'successful_orders': successful_orders,
                'ordered_meals': ordered_meals,
                'message': "; ".join(result_messages) if result_messages else "没有找到可订购的自助餐"
            }

            if successful_orders:
                return True, return_data, ""
            elif ordered_meals:
                return True, return_data, ""  # 即使只有已有订单，也算成功，因为不需要重复点餐
            else:
                return False, return_data, "没有找到可订购的自助餐"

        except NoOrderAvailable as e:
            logger.error(f"没有可用订单: {e}")
            return False, "当前没有可用的订餐时段"
        except Exception as e:
            logger.error(f"订餐失败: {e}")
            return False, f"订餐失败: {str(e)}"

    def get_restaurants_and_dishes(self, email=None, password=None):
        """
        获取餐厅和菜品列表（用于调试）
        """
        try:
            if email:
                success, _, error = self.login(email, password)
                if not success:
                    return None, error

            if not self.meican_client:
                return None, "未登录"

            tab = self.meican_client.next_available_tab
            if not tab:
                return None, "当前没有可用的订餐时段"

            restaurants = self.meican_client.get_restaurants(tab)
            all_dishes = []

            for restaurant in restaurants:
                dishes = self.meican_client.get_dishes(restaurant)
                all_dishes.extend(dishes)

            return {
                "tab": {
                    "uid": tab.uid,
                    "name": getattr(tab, "name", "Unknown"),
                    "status": tab.status.name
                    if hasattr(tab.status, "name")
                    else str(tab.status),
                },
                "restaurants": [
                    {
                        "uid": r.uid,
                        "name": r.name,
                        "dishes_count": len(self.meican_client.get_dishes(r)),
                    }
                    for r in restaurants
                ],
                "dishes": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "price": getattr(d, "price", "Unknown"),
                        "restaurant": d.restaurant.name,
                    }
                    for d in all_dishes
                ],
            }, None

        except Exception as e:
            logger.error(f"获取菜品信息失败: {e}")
            return None, f"获取菜品信息失败: {str(e)}"

    def query_and_update_order_status(self, email=None, password=None):
        """
        查询今天和明天的订单状态，并更新到数据库
        :param email: 邮箱（可选，如果未提供则需要先调用login）
        :param password: 密码
        :return: (success, status_info, error_message)
        """
        try:
            # 如果提供了邮箱，先登录
            if email:
                success, _, error = self.login(email, password)
                if not success:
                    return False, {}, error

            # 确保已登录
            if not self.meican_client:
                return False, {}, "未登录"

            # 获取订单状态
            order_status = self.meican_client.get_order_status()

            # 更新数据库中的记录
            if email:
                from .models import MeicanUser, OrderRecord

                try:
                    user = MeicanUser.objects.get(email=email)
                    today = datetime.now().date()
                    tomorrow = today + timedelta(days=1)

                    updated_records = []

                    # 更新今天的记录
                    if today in order_status:
                        status_info = order_status[today]
                        existing_order = OrderRecord.objects.filter(
                            user=user, order_date=today, success=True
                        ).first()

                        if status_info["has_order"]:
                            # 美餐上有订单
                            if not existing_order:
                                # 数据库中没有成功记录，创建记录
                                OrderRecord.objects.filter(
                                    user=user, order_date=today
                                ).delete()

                                OrderRecord.objects.get_or_create(
                                    user=user,
                                    order_date=today,
                                    defaults={
                                        "meal_name": status_info["meal_name"],
                                        "success": True,
                                    },
                                )
                                updated_records.append(
                                    f"今日订单状态已更新: {status_info['meal_name']}"
                                )
                        else:
                            # 美餐上没有订单
                            if existing_order:
                                # 数据库中有成功记录，需要删除（订单已被取消）
                                OrderRecord.objects.filter(
                                    user=user, order_date=today, success=True
                                ).delete()
                                updated_records.append("今日订单已取消，状态已更新")

                    # 更新明天的记录
                    if tomorrow in order_status:
                        status_info = order_status[tomorrow]
                        existing_order = OrderRecord.objects.filter(
                            user=user, order_date=tomorrow, success=True
                        ).first()

                        if status_info["has_order"]:
                            # 美餐上有订单
                            if not existing_order:
                                # 数据库中没有成功记录，创建记录
                                OrderRecord.objects.filter(
                                    user=user, order_date=tomorrow
                                ).delete()

                                OrderRecord.objects.get_or_create(
                                    user=user,
                                    order_date=tomorrow,
                                    defaults={
                                        "meal_name": status_info["meal_name"],
                                        "success": True,
                                    },
                                )
                                updated_records.append(
                                    f"明日订单状态已更新: {status_info['meal_name']}"
                                )
                        else:
                            # 美餐上没有订单
                            if existing_order:
                                # 数据库中有成功记录，需要删除（订单已被取消）
                                OrderRecord.objects.filter(
                                    user=user, order_date=tomorrow, success=True
                                ).delete()
                                updated_records.append("明日订单已取消，状态已更新")

                    return (
                        True,
                        {
                            "order_status": order_status,
                            "updated_records": updated_records,
                        },
                        None,
                    )

                except Exception as db_error:
                    logger.error(f"更新数据库记录失败: {db_error}")
                    return (
                        True,
                        {"order_status": order_status},
                        f"数据库更新失败: {str(db_error)}",
                    )

            return True, {"order_status": order_status}, None

        except Exception as e:
            logger.error(f"查询订单状态失败: {e}")
            return False, {}, f"查询订单状态失败: {str(e)}"
