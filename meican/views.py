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

        # 为每个用户添加今天和明天的订单状态
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        users_with_status = []
        for user in users:
            # 获取今天的订单状态
            today_order = OrderRecord.objects.filter(
                user=user, order_date=today, success=True
            ).first()

            # 获取明天的订单状态
            tomorrow_order = OrderRecord.objects.filter(
                user=user, order_date=tomorrow, success=True
            ).first()

            user_data = {
                "user": user,
                "today_ordered": bool(today_order),
                "today_meal": today_order.meal_name if today_order else None,
                "tomorrow_ordered": bool(tomorrow_order),
                "tomorrow_meal": tomorrow_order.meal_name if tomorrow_order else None,
            }
            users_with_status.append(user_data)

        return render(
            request,
            "users.html",
            {
                "users_with_status": users_with_status,
                "today": today,
                "tomorrow": tomorrow,
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

            # 立即尝试为新用户进行一次点餐（今天和明天）
            order_results = []

            # 调用订餐方法，该方法会自动处理今天和明天的订餐
            # 并在内部创建相应的 OrderRecord
            try:
                success, meal_name, error = meican_service.find_and_order_buffet(email)

                if success:
                    if meal_name:
                        order_results.append(f"订餐成功：{meal_name}")
                    else:
                        order_results.append("订餐状态已更新")
                else:
                    order_results.append(f"订餐失败：{error}")

            except Exception as e:
                order_results.append(f"订餐异常：{str(e)}")

            # 额外查询一下当前的订单状态，确保用户能看到完整信息
            try:
                status_success, status_info, status_error = (
                    meican_service.query_and_update_order_status(email)
                )
                if status_success and "updated_records" in status_info:
                    updated_records = status_info.get("updated_records", [])
                    if updated_records:
                        order_results.extend(updated_records)
            except Exception:
                # 状态查询失败不影响主要流程
                pass

            # 根据订餐结果显示相应的消息
            result_message = (
                f"用户 {email} 创建成功！已通过美餐登录验证。"
                + " | ".join(order_results)
            )

            # 判断消息类型
            if any("成功" in result for result in order_results):
                if all("成功" in result for result in order_results):
                    messages.success(request, result_message)
                else:
                    messages.warning(request, result_message)
            else:
                messages.warning(request, result_message)

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
        更新指定用户的订单状态
        """
        try:
            user = get_object_or_404(MeicanUser, id=user_id)

            meican_service = MeicanService()
            success, status_info, error = meican_service.query_and_update_order_status(
                user.email
            )

            if success:
                updated_records = status_info.get("updated_records", [])
                if updated_records:
                    message = f"用户 {user.email} 订单状态已更新: {', '.join(updated_records)}"
                    messages.success(request, message)
                else:
                    messages.info(request, f"用户 {user.email} 订单状态无需更新")
            else:
                messages.error(request, f"更新用户 {user.email} 订单状态失败: {error}")

        except Exception as e:
            messages.error(request, f"更新订单状态时发生错误: {str(e)}")

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
            tomorrow = today + timedelta(days=1)

            success_count = 0
            total_count = users.count()
            order_results = []

            for user in users:
                try:
                    # 检查今日是否已点餐
                    today_ordered = OrderRecord.objects.filter(
                        user=user, order_date=today, success=True
                    ).exists()

                    if not today_ordered:
                        # 尝试为今天订餐
                        success, meal_name, error = (
                            meican_service.find_and_order_buffet(user.email)
                        )

                        if success:
                            OrderRecord.objects.create(
                                user=user,
                                order_date=today,
                                meal_name=meal_name,
                                success=True,
                            )
                            order_results.append(
                                f"{user.email}: 今日订餐成功 - {meal_name}"
                            )
                            success_count += 1
                        else:
                            OrderRecord.objects.create(
                                user=user,
                                order_date=today,
                                meal_name="",
                                success=False,
                                error_message=error,
                            )
                            order_results.append(
                                f"{user.email}: 今日订餐失败 - {error}"
                            )
                    else:
                        order_results.append(f"{user.email}: 今日已订餐")
                        success_count += 1

                    # 检查明日是否已点餐
                    tomorrow_ordered = OrderRecord.objects.filter(
                        user=user, order_date=tomorrow, success=True
                    ).exists()

                    if not tomorrow_ordered:
                        # 尝试为明天订餐
                        success, meal_name, error = (
                            meican_service.find_and_order_buffet(user.email)
                        )

                        if success:
                            OrderRecord.objects.create(
                                user=user,
                                order_date=tomorrow,
                                meal_name=meal_name,
                                success=True,
                            )
                            order_results.append(
                                f"{user.email}: 明日订餐成功 - {meal_name}"
                            )
                        else:
                            OrderRecord.objects.create(
                                user=user,
                                order_date=tomorrow,
                                meal_name="",
                                success=False,
                                error_message=error,
                            )
                            order_results.append(
                                f"{user.email}: 明日订餐失败 - {error}"
                            )
                    else:
                        order_results.append(f"{user.email}: 明日已订餐")

                except Exception as e:
                    order_results.append(f"{user.email}: 订餐异常 - {str(e)}")

            # 构建响应消息
            if success_count > 0:
                message = (
                    f"自助点餐完成！成功为 {success_count}/{total_count} 位用户处理订餐"
                )
                return JsonResponse(
                    {"success": True, "message": message, "details": order_results}
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "所有用户订餐都失败了",
                        "details": order_results,
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
            # 获取今天的订单状态
            today_order = OrderRecord.objects.filter(
                user=user, order_date=today, success=True
            ).first()

            # 获取明天的订单状态
            tomorrow_order = OrderRecord.objects.filter(
                user=user, order_date=tomorrow, success=True
            ).first()

            user_data = {
                "id": user.id,
                "email": user.email,
                "today_ordered": bool(today_order),
                "today_meal": today_order.meal_name if today_order else None,
                "tomorrow_ordered": bool(tomorrow_order),
                "tomorrow_meal": tomorrow_order.meal_name if tomorrow_order else None,
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

            # 立即尝试为新用户进行一次点餐（今天和明天）
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            order_results = []

            # 为今天订餐
            try:
                today_success, today_meal, today_error = (
                    meican_service.find_and_order_buffet(email)
                )

                if today_success:
                    OrderRecord.objects.create(
                        user=user, order_date=today, meal_name=today_meal, success=True
                    )
                    order_results.append(f"今日订餐成功：{today_meal}")
                else:
                    OrderRecord.objects.create(
                        user=user,
                        order_date=today,
                        meal_name="",
                        success=False,
                        error_message=today_error,
                    )
                    order_results.append(f"今日订餐失败：{today_error}")
            except Exception as today_e:
                order_results.append(f"今日订餐异常：{str(today_e)}")

            # 为明天订餐
            try:
                tomorrow_success, tomorrow_meal, tomorrow_error = (
                    meican_service.find_and_order_buffet(email)
                )

                if tomorrow_success:
                    OrderRecord.objects.create(
                        user=user,
                        order_date=tomorrow,
                        meal_name=tomorrow_meal,
                        success=True,
                    )
                    order_results.append(f"明日订餐成功：{tomorrow_meal}")
                else:
                    OrderRecord.objects.create(
                        user=user,
                        order_date=tomorrow,
                        meal_name="",
                        success=False,
                        error_message=tomorrow_error,
                    )
                    order_results.append(f"明日订餐失败：{tomorrow_error}")
            except Exception as tomorrow_e:
                order_results.append(f"明日订餐异常：{str(tomorrow_e)}")

            # 构建响应消息
            result_message = (
                f"用户 {email} 创建成功！已通过美餐登录验证。"
                + " | ".join(order_results)
            )

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
