"""
定时任务模块 - 自动点餐功能
"""

import logging
from datetime import datetime, timedelta

from django.utils import timezone

from meican.meican_service import MeicanService
from meican.models import MeicanUser, OrderRecord

logger = logging.getLogger("meican")


def auto_order_meals():
    """
    自动点餐任务 - 每天 9:00 执行
    检查今天和明天的菜单，如果有「自助午餐」就自动下单
    """
    logger.info("开始执行自动点餐任务")

    # 获取所有活跃用户
    active_users = MeicanUser.objects.filter(is_active=True)
    logger.info(f"找到 {active_users.count()} 个活跃用户")

    # 检查今天和明天
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    dates_to_check = [today, tomorrow]

    for date in dates_to_check:
        date_str = date.strftime("%Y-%m-%d")
        logger.info(f"检查日期: {date_str}")

        for user in active_users:
            try:
                # 检查该用户该日期是否已经下过单
                existing_order = OrderRecord.objects.filter(
                    user=user, order_date=date, success=True
                ).first()

                if existing_order:
                    logger.info(f"用户 {user.email} 在 {date_str} 已有成功订单，跳过")
                    continue

                # 为该用户下单
                success, error_msg = _order_for_user(user, date)

                if success:
                    logger.info(f"用户 {user.email} 在 {date_str} 自动下单成功")
                else:
                    logger.warning(
                        f"用户 {user.email} 在 {date_str} 自动下单失败: {error_msg}"
                    )

            except Exception as e:
                logger.error(
                    f"为用户 {user.email} 处理 {date_str} 订单时发生错误: {str(e)}"
                )

    logger.info("自动点餐任务执行完成")


def _order_for_user(user, date):
    """
    为单个用户在指定日期下单
    :param user: MeicanUser 实例
    :param date: 日期对象
    :return: (success, error_message)
    """
    meican_service = MeicanService()
    date_str = date.strftime("%Y-%m-%d")
    print("开始为用户 {} 在 {} 下单...".format(user.email, date_str))

    try:
        # 使用新的整合方法直接查找并下单自助午餐
        success, dish_name, error_msg = meican_service.find_and_order_buffet(user.email)

        print(f"下单结果: {'成功' if success else '失败'}")

        if success:
            if dish_name:
                # 成功下单
                OrderRecord.objects.update_or_create(
                    user=user,
                    order_date=date,
                    defaults={
                        "meal_name": dish_name,
                        "success": True,
                        "error_message": None,
                    },
                )

                logger.info(f"用户 {user.email} 在 {date_str} 成功下单: {dish_name}")

                # 更新用户最后登录时间
                user.last_login_attempt = timezone.now()
                user.save()

                return True, None
            else:
                # 没有找到自助午餐，但不算错误
                logger.info(f"用户 {user.email} 在 {date_str} 没有找到自助午餐")
                return True, None
        else:
            # 下单失败
            OrderRecord.objects.update_or_create(
                user=user,
                order_date=date,
                defaults={
                    "meal_name": "",
                    "success": False,
                    "error_message": error_msg,
                },
            )
            return False, error_msg

    except Exception as e:
        error_msg = f"处理订单时发生异常: {str(e)}"
        OrderRecord.objects.update_or_create(
            user=user,
            order_date=date,
            defaults={"meal_name": "", "success": False, "error_message": error_msg},
        )
        return False, error_msg


def manual_order_for_user(user_email, date=None):
    """
    手动为指定用户下单（用于测试或手动触发）
    :param user_email: 用户邮箱
    :param date: 日期，如果为None则为今天
    :return: (success, message)
    """
    if date is None:
        date = datetime.now().date()

    try:
        user = MeicanUser.objects.get(email=user_email, is_active=True)
        success, error_msg = _order_for_user(user, date)

        if success:
            return True, f"用户 {user_email} 在 {date} 下单成功"
        else:
            return False, f"用户 {user_email} 在 {date} 下单失败: {error_msg}"

    except MeicanUser.DoesNotExist:
        return False, f"用户 {user_email} 不存在或未激活"
    except Exception as e:
        return False, f"手动下单时发生错误: {str(e)}"
