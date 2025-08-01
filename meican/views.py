import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from meican.meican_service import MeicanService
from meican.models import MeicanUser, OrderRecord


class MeicanUsersView(View):
    def get(self, request):
        """
        Handle GET requests to retrieve Meican users.
        """
        users = MeicanUser.objects.all()

        # 为每个用户添加今天和以后的 Tab 状态及订单状态
        today = datetime.now().date()

        users_with_status = []
        for user in users:
            # 获取该用户今天及以后的所有 Tab 状态
            from .models import TabStatus

            user_tabs = TabStatus.objects.filter(
                user=user, order_date__gte=today
            ).order_by("order_date", "target_time")

            # 获取今天及以后的所有成功订单
            user_orders = OrderRecord.objects.filter(
                user=user, order_date__gte=today, success=True
            ).order_by("order_date", "meal_period")

            # 按日期分组 Tab 状态
            tabs_by_date = {}
            for tab in user_tabs:
                date_str = tab.order_date.isoformat()
                if date_str not in tabs_by_date:
                    tabs_by_date[date_str] = []
                tabs_by_date[date_str].append(
                    {
                        "title": tab.tab_title,
                        "status": tab.status,
                        "target_time": tab.target_time,
                        "has_buffet": "自助" in tab.tab_title,
                    }
                )

            # 按日期分组订单
            orders_by_date = {}
            for order in user_orders:
                date_str = order.order_date.isoformat()
                if date_str not in orders_by_date:
                    orders_by_date[date_str] = []
                orders_by_date[date_str].append(
                    {"meal_period": order.meal_period, "meal_name": order.meal_name}
                )

            # 统计今天和明天的状态（为了兼容现有模板）
            today_str = today.isoformat()
            tomorrow_str = (today + timedelta(days=1)).isoformat()

            today_orders = orders_by_date.get(today_str, [])
            tomorrow_orders = orders_by_date.get(tomorrow_str, [])

            today_meals = []
            for order in today_orders:
                if order["meal_period"]:
                    today_meals.append(f"{order['meal_period']}: {order['meal_name']}")
                else:
                    today_meals.append(order["meal_name"])

            tomorrow_meals = []
            for order in tomorrow_orders:
                if order["meal_period"]:
                    tomorrow_meals.append(
                        f"{order['meal_period']}: {order['meal_name']}"
                    )
                else:
                    tomorrow_meals.append(order["meal_name"])

            user_data = {
                "user": user,
                "today_ordered": len(today_orders) > 0,
                "today_meal": "; ".join(today_meals) if today_meals else None,
                "tomorrow_ordered": len(tomorrow_orders) > 0,
                "tomorrow_meal": "; ".join(tomorrow_meals) if tomorrow_meals else None,
                "tabs_by_date": tabs_by_date,
                "orders_by_date": orders_by_date,
                "tab_status_count": user_tabs.count(),
                "order_count": user_orders.count(),
            }
            users_with_status.append(user_data)

        return render(
            request,
            "users.html",
            {
                "users_with_status": users_with_status,
                "today": today,
                "tomorrow": today + timedelta(days=1),
            },
        )

    def post(self, request):
        """
        Handle POST requests to create a new Meican user.
        """
        email = request.POST.get("email")

        if not email:
            messages.error(request, "邮箱地址不能为空")
            return redirect("get_meican_users")

        try:
            # 先检查邮箱是否已存在
            if MeicanUser.objects.filter(email=email).exists():
                messages.error(request, "该邮箱已存在，请使用其他邮箱")
                return redirect("get_meican_users")

            # 尝试使用美餐服务登录验证
            meican_service = MeicanService()
            login_success, token, login_error = meican_service.login(email)

            if not login_success:
                messages.error(
                    request, f"美餐登录失败：{login_error}，请检查邮箱和密码配置"
                )
                return redirect("get_meican_users")

            # 登录成功，创建用户
            user = MeicanUser.objects.create(  # noqa: F841
                email=email, token=token, last_login_attempt=timezone.now()
            )

            # 立即尝试为新用户进行一次点餐
            order_results = []

            # 调用订餐方法
            try:
                success, result_data, error = meican_service.find_and_order_buffet(
                    email
                )

                if success:
                    # 处理成功的新订单
                    successful_orders = result_data.get("successful_orders", [])
                    if successful_orders:
                        for order_info in successful_orders:
                            order_results.append(f"订餐成功：{order_info}")

                    # 处理已有的订单信息
                    ordered_meals = result_data.get("ordered_meals", [])
                    if ordered_meals:
                        for meal_period in ordered_meals:
                            order_results.append(f"已订餐：{meal_period}")

                    # 如果没有任何订单，说明暂无可用的自助餐
                    if not successful_orders and not ordered_meals:
                        order_results.append("暂无可用的自助餐")
                else:
                    # 区分真正的错误和正常状态
                    if "暂无" in error or "没有找到" in error or "不可" in error:
                        order_results.append("暂无可用的自助餐")
                    else:
                        order_results.append(f"订餐失败：{error}")

            except Exception as e:
                order_results.append(f"订餐异常：{str(e)}")

            # 根据订餐结果显示相应的消息
            if order_results:
                result_message = (
                    f"用户 {email} 创建成功！已通过美餐登录验证。"
                    + " | ".join(order_results)
                )
            else:
                result_message = f"用户 {email} 创建成功！已通过美餐登录验证。"

            # 判断消息类型 - 优化消息分类
            has_success = any("成功" in result for result in order_results)
            has_ordered = any("已订餐" in result for result in order_results)
            has_no_buffet = any("暂无" in result for result in order_results)
            has_error = any(
                "失败" in result or "异常" in result for result in order_results
            )

            if has_success:
                messages.success(request, result_message)
            elif has_ordered or has_no_buffet:
                messages.success(
                    request, result_message
                )  # 已订餐和暂无可用也算正常情况
            elif has_error:
                messages.warning(request, result_message)
            else:
                messages.success(request, result_message)

        except Exception as e:
            messages.error(request, f"创建用户时发生错误：{str(e)}")

        return redirect("get_meican_users")


class DeleteUserView(View):
    def post(self, request, user_id):
        """
        Handle POST requests to delete a Meican user.
        """
        try:
            user = get_object_or_404(MeicanUser, id=user_id)
            user_email = user.email
            user.delete()
            messages.success(request, f"用户 {user_email} 已成功删除！")
        except Exception as e:
            messages.error(request, f"删除用户时发生错误：{str(e)}")

        return redirect("get_meican_users")


class UpdateOrderStatusView(View):
    def post(self, request, user_id):
        """
        刷新指定用户的状态：重新获取 Tab 状态并同步到数据库
        """
        try:
            user = get_object_or_404(MeicanUser, id=user_id)

            meican_service = MeicanService()

            # 使用新的刷新方法：登录 + 同步 Tab 状态 + 批量订餐
            success, result_info, error = meican_service.refresh_user_status(user)

            if success:
                # 提取有用的信息给用户
                sync_info = result_info.get("sync_info", {})
                order_info = result_info.get("order_info", {})

                synced_tabs = sync_info.get("synced_tabs", [])
                order_summary = order_info.get("summary", {})

                message_parts = []
                message_parts.append(f"已同步 {len(synced_tabs)} 个时段状态")

                if order_summary:
                    successful_count = order_summary.get("successful_count", 0)
                    already_ordered_count = order_summary.get(
                        "already_ordered_count", 0
                    )

                    if successful_count > 0:
                        message_parts.append(f"新订餐: {successful_count} 个")
                    if already_ordered_count > 0:
                        message_parts.append(f"已有订单: {already_ordered_count} 个")

                message = f"用户 {user.email} 状态已刷新 - " + "; ".join(message_parts)
                messages.success(request, message)
            else:
                messages.error(request, f"刷新用户 {user.email} 状态失败: {error}")

        except Exception as e:
            messages.error(request, f"刷新状态时发生错误: {str(e)}")

        return redirect("get_meican_users")


class AutoOrderView(View):
    def post(self, request):
        """
        Handle POST requests for auto ordering buffet for all users.
        """
        try:
            # 获取所有活跃用户
            users = MeicanUser.objects.filter(is_active=True)

            if not users.exists():
                return JsonResponse({"success": False, "message": "没有找到可用的用户"})

            meican_service = MeicanService()
            today = datetime.now().date()

            # 统计各种状态的用户数量
            new_order_count = 0  # 有新订单的用户
            already_ordered_count = 0  # 全部已订餐的用户
            no_buffet_count = 0  # 没有可用自助餐的用户
            error_count = 0  # 真正出错的用户
            total_count = users.count()

            order_details = []

            for user in users:
                user_has_new_order = False
                user_all_ordered = False
                user_no_buffet = False
                user_has_error = False

                try:
                    # 尝试为用户订餐
                    success, result_data, error = meican_service.find_and_order_buffet(
                        user.email
                    )

                    if success:
                        # 处理成功的新订单
                        successful_orders = result_data.get("successful_orders", [])
                        if successful_orders:
                            user_has_new_order = True
                            for order_info in successful_orders:
                                if ": " in order_info:
                                    meal_period, meal_name = order_info.split(": ", 1)
                                else:
                                    meal_period = "未知时段"
                                    meal_name = order_info

                                # 更新数据库记录
                                OrderRecord.objects.update_or_create(
                                    user=user,
                                    order_date=today,
                                    meal_period=meal_period,
                                    defaults={
                                        "meal_name": meal_name,
                                        "success": True,
                                        "error_message": None,
                                    },
                                )
                                order_details.append(
                                    f"{user.email}: 新订餐成功 - {meal_period}: {meal_name}"
                                )

                        # 处理已有的订单
                        ordered_meals = result_data.get("ordered_meals", [])
                        if ordered_meals:
                            # 如果只有已订餐，没有新订单，认为是全部已订餐
                            if not successful_orders:
                                user_all_ordered = True
                            for meal_period in ordered_meals:
                                order_details.append(
                                    f"{user.email}: 已订餐 - {meal_period}"
                                )

                        # 如果既没有新订单也没有已有订单，说明没有可用的自助餐
                        if not successful_orders and not ordered_meals:
                            user_no_buffet = True
                            order_details.append(
                                f"{user.email}: 当前时段暂无可用的自助餐"
                            )

                    else:
                        # 处理失败情况
                        user_has_error = True
                        # 记录失败到数据库
                        OrderRecord.objects.update_or_create(
                            user=user,
                            order_date=today,
                            meal_period="自动点餐",
                            defaults={
                                "meal_name": "",
                                "success": False,
                                "error_message": error,
                            },
                        )
                        order_details.append(f"{user.email}: 订餐失败 - {error}")

                except Exception as e:
                    user_has_error = True
                    order_details.append(f"{user.email}: 订餐异常 - {str(e)}")

                # 统计用户状态
                if user_has_new_order:
                    new_order_count += 1
                elif user_all_ordered:
                    already_ordered_count += 1
                elif user_no_buffet:
                    no_buffet_count += 1
                elif user_has_error:
                    error_count += 1

            # 构建响应消息
            message_parts = []

            if new_order_count > 0:
                message_parts.append(f"新订餐: {new_order_count}人")

            if already_ordered_count > 0:
                message_parts.append(f"已订餐: {already_ordered_count}人")

            if no_buffet_count > 0:
                message_parts.append(f"暂无可用自助餐: {no_buffet_count}人")

            if error_count > 0:
                message_parts.append(f"失败: {error_count}人")

            # 判断整体操作是否成功
            # 只要不是所有用户都出错，就认为操作成功
            is_success = error_count < total_count

            if is_success:
                if new_order_count > 0:
                    main_message = (
                        f"自助点餐完成！共处理 {total_count} 位用户，"
                        + "，".join(message_parts)
                    )
                elif already_ordered_count + no_buffet_count == total_count:
                    main_message = (
                        f"自助点餐检查完成！共处理 {total_count} 位用户，"
                        + "，".join(message_parts)
                    )
                else:
                    main_message = (
                        f"自助点餐处理完成！共处理 {total_count} 位用户，"
                        + "，".join(message_parts)
                    )
            else:
                main_message = (
                    f"自助点餐部分失败！共处理 {total_count} 位用户，"
                    + "，".join(message_parts)
                )

            return JsonResponse(
                {
                    "success": is_success,
                    "message": main_message,
                    "details": order_details,
                    "summary": {
                        "total": total_count,
                        "new_orders": new_order_count,
                        "already_ordered": already_ordered_count,
                        "no_buffet": no_buffet_count,
                        "errors": error_count,
                    },
                }
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"自助点餐失败：{str(e)}"}
            )


class UsersApiView(View):
    def get(self, request):
        """
        API endpoint to get users list with order status.
        """
        users = MeicanUser.objects.all()
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        users_data = []
        for user in users:
            # 获取今天的所有成功订单
            today_orders = OrderRecord.objects.filter(
                user=user, order_date=today, success=True
            )

            # 获取明天的所有成功订单
            tomorrow_orders = OrderRecord.objects.filter(
                user=user, order_date=tomorrow, success=True
            )

            # 合并今天的订单信息
            today_meals = []
            if today_orders.exists():
                for order in today_orders:
                    if order.meal_period:
                        today_meals.append(f"{order.meal_period}: {order.meal_name}")
                    else:
                        today_meals.append(order.meal_name)

            # 合并明天的订单信息
            tomorrow_meals = []
            if tomorrow_orders.exists():
                for order in tomorrow_orders:
                    if order.meal_period:
                        tomorrow_meals.append(f"{order.meal_period}: {order.meal_name}")
                    else:
                        tomorrow_meals.append(order.meal_name)

            user_data = {
                "id": user.id,
                "email": user.email,
                "today_ordered": today_orders.exists(),
                "today_meal": "; ".join(today_meals) if today_meals else None,
                "tomorrow_ordered": tomorrow_orders.exists(),
                "tomorrow_meal": "; ".join(tomorrow_meals) if tomorrow_meals else None,
            }
            users_data.append(user_data)

        return JsonResponse(
            {
                "success": True,
                "users": users_data,
                "today": today.strftime("%Y-%m-%d"),
                "tomorrow": tomorrow.strftime("%Y-%m-%d"),
            }
        )


class CreateUserApiView(View):
    def post(self, request):
        """
        API endpoint to create a new user.
        """
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse({"success": False, "message": "邮箱地址不能为空"})

            # 先检查邮箱是否已存在
            if MeicanUser.objects.filter(email=email).exists():
                return JsonResponse(
                    {"success": False, "message": "该邮箱已存在，请使用其他邮箱"}
                )

            # 尝试使用美餐服务登录验证
            meican_service = MeicanService()
            login_success, token, login_error = meican_service.login(email)

            if not login_success:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"美餐登录失败：{login_error}，请检查邮箱和密码配置",
                    }
                )

            # 登录成功，创建用户
            user = MeicanUser.objects.create(
                email=email, token=token, last_login_attempt=timezone.now()
            )

            # 立即尝试为新用户进行一次点餐（今天）
            today = datetime.now().date()
            order_results = []

            # 为今天订餐
            try:
                today_success, result_data, today_error = (
                    meican_service.find_and_order_buffet(email)
                )

                if today_success:
                    # 处理成功的新订单
                    successful_orders = result_data.get("successful_orders", [])
                    if successful_orders:
                        for order_info in successful_orders:
                            if ": " in order_info:
                                meal_period, meal_name = order_info.split(": ", 1)
                            else:
                                meal_period = "未知时段"
                                meal_name = order_info

                            OrderRecord.objects.create(
                                user=user,
                                order_date=today,
                                meal_period=meal_period,
                                meal_name=meal_name,
                                success=True,
                            )
                            order_results.append(
                                f"今日{meal_period}订餐成功：{meal_name}"
                            )

                    # 记录已有的订单信息
                    ordered_meals = result_data.get("ordered_meals", [])
                    if ordered_meals:
                        for meal_period in ordered_meals:
                            order_results.append(f"今日{meal_period}已订餐")

                    # 如果没有任何订单，说明暂无可用的自助餐
                    if not successful_orders and not ordered_meals:
                        order_results.append("今日暂无可用的自助餐")
                else:
                    # 区分真正的错误和正常状态
                    if (
                        "暂无" in today_error
                        or "没有找到" in today_error
                        or "不可" in today_error
                    ):
                        order_results.append("今日暂无可用的自助餐")
                    else:
                        OrderRecord.objects.create(
                            user=user,
                            order_date=today,
                            meal_period="自动点餐",
                            meal_name="",
                            success=False,
                            error_message=today_error,
                        )
                        order_results.append(f"今日订餐失败：{today_error}")
            except Exception as today_e:
                order_results.append(f"今日订餐异常：{str(today_e)}")

            # 构建响应消息 - 优化消息类型判断
            has_success = any("成功" in result for result in order_results)
            has_ordered = any("已订餐" in result for result in order_results)
            has_no_buffet = any("暂无" in result for result in order_results)

            if order_results:
                order_summary = " | ".join(order_results)
                if has_success or has_ordered or has_no_buffet:
                    # 有正常结果（成功、已订餐或暂无可用）
                    result_message = (
                        f"用户 {email} 创建成功！已通过美餐登录验证。{order_summary}"
                    )
                else:
                    # 只有错误
                    result_message = (
                        f"用户 {email} 创建成功，但订餐遇到问题：{order_summary}"
                    )
            else:
                result_message = f"用户 {email} 创建成功！已通过美餐登录验证。"

            return JsonResponse(
                {
                    "success": True,
                    "message": result_message,
                    "user": {"id": user.id, "email": user.email},
                    "order_results": order_results,
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "无效的JSON数据"})
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"创建用户时发生错误：{str(e)}"}
            )


class DeleteUserApiView(View):
    def delete(self, request, user_id):
        """
        API endpoint to delete a user.
        """
        try:
            user = get_object_or_404(MeicanUser, id=user_id)
            user_email = user.email
            user.delete()

            return JsonResponse(
                {"success": True, "message": f"用户 {user_email} 已成功删除！"}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"删除用户时发生错误：{str(e)}"}
            )
