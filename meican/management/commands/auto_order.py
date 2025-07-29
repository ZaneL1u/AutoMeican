"""
Django 管理命令 - 手动触发自动点餐
"""

from django.core.management.base import BaseCommand

from meican.cron import auto_order_meals, manual_order_for_user


class Command(BaseCommand):
    help = "手动触发自动点餐或为指定用户下单"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            type=str,
            help="为指定用户邮箱下单",
        )
        parser.add_argument(
            "--date",
            type=str,
            help="指定日期 (YYYY-MM-DD 格式)",
        )

    def handle(self, *args, **options):
        if options["user"]:
            # 为指定用户下单
            user_email = options["user"]
            date_str = options.get("date")

            if date_str:
                from datetime import datetime

                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    self.stdout.write(
                        self.style.ERROR("日期格式错误，请使用 YYYY-MM-DD 格式")
                    )
                    return
            else:
                date = None

            success, message = manual_order_for_user(user_email, date)

            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR(message))
        else:
            # 执行全体用户自动点餐
            self.stdout.write("开始执行自动点餐任务...")
            auto_order_meals()
            self.stdout.write(self.style.SUCCESS("自动点餐任务执行完成"))


if __name__ == "__main__":
    Command().handle()
