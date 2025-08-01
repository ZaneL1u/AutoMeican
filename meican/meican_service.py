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
            print(f"正在尝试登录用户: {email}")
            self.meican_client = MeiCan(email, password)
            logger.info(f"用户 {email} 登录成功")
            return True, "login_success", None
        except MeiCanLoginFail as e:
            logger.error(f"登录失败: {e}")
            return False, None, "用户名或密码错误"
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False, None, f"登录异常: {str(e)}"

    def sync_user_tabs_status(self, user):
        """
        同步用户的所有 Tab 状态到数据库
        :param user: MeicanUser 对象
        :return: (success, synced_tabs_info, error_message)
        """
        try:
            if not self.meican_client:
                return False, {}, "未登录"

            from .models import TabStatus

            # 获取所有 tabs
            all_tabs = self.meican_client.tabs
            if not all_tabs:
                return False, {}, "未获取到任何 Tab 信息"

            synced_tabs = []
            today = datetime.now().date()

            # 清除该用户今天及以后的所有 Tab 状态记录
            TabStatus.objects.filter(
                user=user, 
                order_date__gte=today
            ).delete()

            for tab in all_tabs:
                try:
                    # 计算对应的用餐日期
                    order_date = tab.target_time.date()
                    
                    # 只同步今天及以后的 Tab
                    if order_date < today:
                        continue

                    # 统一处理状态值
                    if hasattr(tab.status, "value"):
                        status_value = tab.status.value
                    elif hasattr(tab.status, "name"):
                        status_value = tab.status.name
                    else:
                        status_value = str(tab.status)

                    # 创建或更新 Tab 状态记录
                    tab_status, created = TabStatus.objects.update_or_create(
                        user=user,
                        tab_uid=tab.uid,
                        order_date=order_date,
                        defaults={
                            "tab_title": tab.title,
                            "target_time": tab.target_time,
                            "status": status_value,
                        }
                    )

                    synced_tabs.append({
                        "tab_title": tab.title,
                        "order_date": order_date.isoformat(),
                        "status": status_value,
                        "created": created
                    })

                    logger.info(f"用户 {user.email} Tab '{tab.title}' 状态已同步: {status_value}")

                except Exception as tab_error:
                    logger.error(f"同步 Tab {tab.title} 状态时出错: {tab_error}")
                    continue

            return True, {"synced_tabs": synced_tabs}, None

        except Exception as e:
            logger.error(f"同步用户 Tab 状态失败: {e}")
            return False, {}, f"同步 Tab 状态失败: {str(e)}"

    def order_all_available_buffets(self, user):
        """
        为用户订购所有可用的自助餐
        :param user: MeicanUser 对象
        :return: (success, order_results, error_message)
        """
        try:
            if not self.meican_client:
                return False, {}, "未登录"

            # 获取所有包含"自助"的 tabs
            all_buffet_tabs = [
                tab for tab in self.meican_client.tabs if "自助" in tab.title
            ]

            if not all_buffet_tabs:
                return True, {"message": "当前没有自助餐可订"}, None

            successful_orders = []
            already_ordered = []
            unavailable_tabs = []

            for tab in all_buffet_tabs:
                print(f"检查自助餐标签页: {tab.title}, 状态: {tab.status}")

                # 统一处理状态检查
                if hasattr(tab.status, "value"):
                    status_value = tab.status.value
                elif hasattr(tab.status, "name"):
                    status_value = tab.status.name
                else:
                    status_value = str(tab.status)

                # 计算订单日期
                order_date = tab.target_time.date()

                # 如果这个时段已经订过餐，跳过
                if status_value in ["ORDERED", "ORDER"]:
                    already_ordered.append({
                        "tab_title": tab.title,
                        "order_date": order_date.isoformat(),
                        "status": status_value
                    })
                    logger.info(f"时段 {tab.title} 已订餐，跳过")
                    continue

                # 如果这个时段不可用，跳过
                if status_value not in ["AVAILABLE", "AVAIL"]:
                    unavailable_tabs.append({
                        "tab_title": tab.title,
                        "order_date": order_date.isoformat(),
                        "status": status_value
                    })
                    logger.info(f"时段 {tab.title} 不可订餐 (状态: {status_value})，跳过")
                    continue

                # 尝试下单
                order_success, meal_name, error = self._order_buffet_for_tab(tab, user)
                
                if order_success:
                    successful_orders.append({
                        "tab_title": tab.title,
                        "order_date": order_date.isoformat(),
                        "meal_name": meal_name,
                        "tab_uid": tab.uid
                    })
                    logger.info(f"用户 {user.email} 在时段 {tab.title} 成功下单: {meal_name}")
                else:
                    logger.error(f"用户 {user.email} 在时段 {tab.title} 下单失败: {error}")

            # 汇总结果
            order_results = {
                "successful_orders": successful_orders,
                "already_ordered": already_ordered,
                "unavailable_tabs": unavailable_tabs,
                "summary": {
                    "successful_count": len(successful_orders),
                    "already_ordered_count": len(already_ordered),
                    "unavailable_count": len(unavailable_tabs)
                }
            }

            return True, order_results, None

        except Exception as e:
            logger.error(f"批量订餐失败: {e}")
            return False, {}, f"批量订餐失败: {str(e)}"

    def _order_buffet_for_tab(self, tab, user):
        """
        为特定 Tab 下单自助餐
        :param tab: Tab 对象
        :param user: MeicanUser 对象
        :return: (success, meal_name, error_message)
        """
        try:
            # 获取这个时段的所有菜品
            dishes = self.meican_client.list_dishes(tab)
            if not dishes:
                return False, None, f"时段 {tab.title} 没有可订购的菜品"

            # 查找自助餐（包含"自助"关键词的菜品）
            buffet_dishes = [dish for dish in dishes if "自助" in dish.name]

            if not buffet_dishes:
                return False, None, f"时段 {tab.title} 没有找到自助餐菜品"

            # 随机选择一个自助餐
            selected_dish = random.choice(buffet_dishes)
            logger.info(f"为时段 {tab.title} 选择自助餐: {selected_dish.name}")

            # 下单
            order_result = self.meican_client.order(selected_dish)
            logger.info(f"时段 {tab.title} 订餐结果: {order_result}")

            # 记录到数据库
            from .models import OrderRecord
            order_date = tab.target_time.date()
            
            OrderRecord.objects.update_or_create(
                user=user,
                order_date=order_date,
                meal_period=tab.title,
                defaults={
                    "meal_name": selected_dish.name,
                    "success": True,
                    "error_message": None,
                    "tab_uid": tab.uid,
                },
            )

            return True, selected_dish.name, None

        except Exception as e:
            error_msg = f"下单失败: {str(e)}"
            logger.error(f"时段 {tab.title} 订餐失败: {e}")
            
            # 记录失败的订单
            try:
                from .models import OrderRecord
                order_date = tab.target_time.date()
                
                OrderRecord.objects.update_or_create(
                    user=user,
                    order_date=order_date,
                    meal_period=tab.title,
                    defaults={
                        "meal_name": "",
                        "success": False,
                        "error_message": error_msg,
                        "tab_uid": tab.uid,
                    },
                )
            except Exception as db_error:
                logger.error(f"记录失败订单时出错: {db_error}")
            
            return False, None, error_msg

    def refresh_user_status(self, user):
        """
        刷新用户状态：登录 + 同步 Tab 状态 + 订餐
        用于前端刷新功能
        :param user: MeicanUser 对象
        :return: (success, result_info, error_message)
        """
        try:
            # 1. 登录
            success, _, error = self.login(user.email)
            if not success:
                return False, {}, f"登录失败: {error}"

            # 2. 同步 Tab 状态
            sync_success, sync_info, sync_error = self.sync_user_tabs_status(user)
            if not sync_success:
                return False, {}, f"同步状态失败: {sync_error}"

            # 3. 尝试订餐所有可用的自助餐
            order_success, order_info, order_error = self.order_all_available_buffets(user)
            
            # 汇总结果
            result_info = {
                "user_email": user.email,
                "sync_info": sync_info,
                "order_info": order_info,
                "refresh_time": datetime.now().isoformat()
            }

            if not order_success:
                result_info["order_error"] = order_error

            return True, result_info, None

        except Exception as e:
            logger.error(f"刷新用户 {user.email} 状态失败: {e}")
            return False, {}, f"刷新状态失败: {str(e)}"

    # 保留原有方法以保持兼容性
    def find_and_order_buffet(self, email=None, password=None):
        """
        查找并订购自助餐（兼容性方法，内部调用新的方法）
        :param email: 邮箱（可选，如果未提供则需要先调用login）
        :param password: 密码
        :return: (success, message)
        """
        try:
            # 如果提供了邮箱，先获取用户对象
            if email:
                from .models import MeicanUser
                try:
                    user = MeicanUser.objects.get(email=email)
                except MeicanUser.DoesNotExist:
                    return False, "", f"用户 {email} 不存在"

                # 登录
                success, _, error = self.login(email, password)
                if not success:
                    return False, "", error
            else:
                # 如果没有提供邮箱，确保已登录
                if not self.meican_client:
                    return False, "", "未登录"
                return False, "", "需要提供用户信息"

            # 同步状态并订餐
            sync_success, sync_info, sync_error = self.sync_user_tabs_status(user)
            order_success, order_info, order_error = self.order_all_available_buffets(user)

            if order_success:
                summary = order_info.get("summary", {})
                successful_count = summary.get("successful_count", 0)
                already_ordered_count = summary.get("already_ordered_count", 0)
                
                messages = []
                if successful_count > 0:
                    messages.append(f"新订餐成功: {successful_count} 个时段")
                if already_ordered_count > 0:
                    messages.append(f"已有订单: {already_ordered_count} 个时段")
                
                message = "; ".join(messages) if messages else "没有找到可订购的自助餐"
                
                # 返回兼容格式
                return_data = {
                    'successful_orders': [f"{item['tab_title']}: {item['meal_name']}" for item in order_info.get("successful_orders", [])],
                    'ordered_meals': [item['tab_title'] for item in order_info.get("already_ordered", [])],
                    'message': message
                }
                
                return True, return_data, ""
            else:
                return False, order_error if order_error else "订餐失败"

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
        查询订单状态（兼容性方法，已被新的同步方法替代）
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
                    
                    # 使用新的同步方法
                    sync_success, sync_info, sync_error = self.sync_user_tabs_status(user)
                    
                    return (
                        True,
                        {
                            "order_status": order_status,
                            "updated_records": [f"已同步 {len(sync_info.get('synced_tabs', []))} 个 Tab 状态"],
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
