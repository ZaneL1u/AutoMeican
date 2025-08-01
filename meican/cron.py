"""
定时任务模块 - 自动点餐功能
优化版：每个用户每次定时任务只登录一次，获取所有可用的 tabs 并同步状态，然后批量订餐
"""

import logging
from datetime import datetime

from django.utils import timezone

from meican.meican_service import MeicanService
from meican.models import MeicanUser

logger = logging.getLogger("meican")


def auto_order_meals():
    """
    自动点餐任务 - 每个用户登录一次，同步 Tab 状态并处理所有可用的自助餐时段
    """
    logger.info("开始执行自动点餐任务")

    # 获取所有活跃用户
    active_users = MeicanUser.objects.filter(is_active=True)
    logger.info(f"找到 {active_users.count()} 个活跃用户")

    total_success = 0
    total_failed = 0

    for user in active_users:
        try:
            # 为该用户执行完整的流程（登录 + 同步状态 + 批量订餐）
            success, result_info = _process_user_complete_flow(user)

            if success:
                total_success += 1

                # 提取摘要信息
                order_info = result_info.get("order_info", {})
                summary = order_info.get("summary", {})

                successful_orders = summary.get("successful_count", 0)
                already_ordered = summary.get("already_ordered_count", 0)
                unavailable = summary.get("unavailable_count", 0)

                logger.info(
                    f"用户 {user.email} 处理完成 - 新订餐:{successful_orders}, 已有订单:{already_ordered}, 不可用:{unavailable}"
                )
            else:
                total_failed += 1
                logger.warning(f"用户 {user.email} 处理失败: {result_info}")

        except Exception as e:
            total_failed += 1
            logger.error(f"为用户 {user.email} 处理订单时发生错误: {str(e)}")

    logger.info(f"自动点餐任务执行完成 - 成功:{total_success}, 失败:{total_failed}")


def _process_user_complete_flow(user):
    """
    为单个用户执行完整流程：登录 -> 同步 Tab 状态 -> 批量订餐
    :param user: MeicanUser 实例
    :return: (success, result_info)
    """
    meican_service = MeicanService()

    try:
        logger.info(f"开始为用户 {user.email} 执行完整流程...")

        # 1. 登录（只登录一次）
        success, _, error = meican_service.login(user.email)
        if not success:
            return False, f"登录失败: {error}"

        logger.info(f"用户 {user.email} 登录成功")

        # 2. 同步 Tab 状态到数据库
        sync_success, sync_info, sync_error = meican_service.sync_user_tabs_status(user)
        if not sync_success:
            logger.warning(f"用户 {user.email} 同步状态失败: {sync_error}")
            # 即使同步失败也继续尝试订餐
        else:
            synced_tabs = sync_info.get("synced_tabs", [])
            logger.info(f"用户 {user.email} 已同步 {len(synced_tabs)} 个 Tab 状态")

        # 3. 批量订购所有可用的自助餐
        order_success, order_info, order_error = (
            meican_service.order_all_available_buffets(user)
        )

        if not order_success:
            logger.warning(f"用户 {user.email} 批量订餐失败: {order_error}")

        # 4. 更新用户最后登录时间
        user.last_login_attempt = timezone.now()
        user.save()

        # 汇总结果
        result_info = {
            "user_email": user.email,
            "sync_info": sync_info if sync_success else {"error": sync_error},
            "order_info": order_info if order_success else {"error": order_error},
            "process_time": timezone.now().isoformat(),
        }

        # 如果订餐成功或者至少同步成功，都算作成功
        overall_success = order_success or sync_success

        return overall_success, result_info

    except Exception as e:
        error_msg = f"处理用户流程时发生异常: {str(e)}"
        logger.error(f"用户 {user.email}: {error_msg}")
        return False, error_msg


def manual_order_for_user(user_email, force_refresh=True):
    """
    手动为指定用户执行完整流程（用于测试或手动触发）
    :param user_email: 用户邮箱
    :param force_refresh: 是否强制刷新状态
    :return: (success, message)
    """
    try:
        user = MeicanUser.objects.get(email=user_email, is_active=True)

        if force_refresh:
            # 使用完整流程
            success, result_info = _process_user_complete_flow(user)
        else:
            # 只执行订餐，不刷新状态
            meican_service = MeicanService()
            success, _, error = meican_service.login(user.email)
            if not success:
                return False, f"登录失败: {error}"

            order_success, order_info, order_error = (
                meican_service.order_all_available_buffets(user)
            )
            success = order_success
            result_info = order_info if order_success else order_error

        if success:
            if isinstance(result_info, dict) and "order_info" in result_info:
                summary = result_info["order_info"].get("summary", {})
                successful_count = summary.get("successful_count", 0)
                already_ordered_count = summary.get("already_ordered_count", 0)

                message_parts = []
                if successful_count > 0:
                    message_parts.append(f"新订餐成功: {successful_count} 个时段")
                if already_ordered_count > 0:
                    message_parts.append(f"已有订单: {already_ordered_count} 个时段")

                message = (
                    f"用户 {user_email} 处理完成 - " + "; ".join(message_parts)
                    if message_parts
                    else f"用户 {user_email} 处理完成，无可订餐时段"
                )
            else:
                message = f"用户 {user_email} 处理完成"

            return True, message
        else:
            return False, f"用户 {user_email} 处理失败: {result_info}"

    except MeicanUser.DoesNotExist:
        return False, f"用户 {user_email} 不存在或未激活"
    except Exception as e:
        return False, f"手动处理时发生错误: {str(e)}"


def refresh_user_tabs_only(user_email):
    """
    仅刷新用户的 Tab 状态，不执行订餐（用于前端刷新功能）
    :param user_email: 用户邮箱
    :return: (success, message)
    """
    try:
        user = MeicanUser.objects.get(email=user_email, is_active=True)

        meican_service = MeicanService()

        # 登录
        success, _, error = meican_service.login(user.email)
        if not success:
            return False, f"登录失败: {error}"

        # 只同步状态，不订餐
        sync_success, sync_info, sync_error = meican_service.sync_user_tabs_status(user)

        if sync_success:
            synced_tabs = sync_info.get("synced_tabs", [])
            return (
                True,
                f"用户 {user_email} Tab 状态已刷新，共同步 {len(synced_tabs)} 个时段",
            )
        else:
            return False, f"用户 {user_email} 状态刷新失败: {sync_error}"

    except MeicanUser.DoesNotExist:
        return False, f"用户 {user_email} 不存在或未激活"
    except Exception as e:
        return False, f"刷新状态时发生错误: {str(e)}"


# 保留原有函数名以保持兼容性，但内部调用新的逻辑
def _order_for_user(user, date):
    """
    为单个用户下单 (保留原有接口用于兼容性，现在调用新的完整流程)
    :param user: MeicanUser 实例
    :param date: 日期对象（暂时未使用，因为新逻辑会处理所有可用日期）
    :return: (success, error_message)
    """
    success, result_info = _process_user_complete_flow(user)
    if success:
        return True, "处理完成"
    else:
        return False, result_info
