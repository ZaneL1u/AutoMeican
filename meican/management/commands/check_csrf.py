"""
Django 管理命令 - 检查和修复 CSRF 配置
"""

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "检查和显示 CSRF 配置信息"

    def handle(self, *args, **options):
        self.stdout.write("=== CSRF 配置检查 ===")

        # 显示当前配置
        self.stdout.write(f"DEBUG: {settings.DEBUG}")
        self.stdout.write(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

        if hasattr(settings, "CSRF_TRUSTED_ORIGINS"):
            self.stdout.write(f"CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")
        else:
            self.stdout.write(self.style.WARNING("CSRF_TRUSTED_ORIGINS 未设置"))

        # 显示 Cookie 设置
        csrf_cookie_secure = getattr(settings, "CSRF_COOKIE_SECURE", None)
        csrf_cookie_samesite = getattr(settings, "CSRF_COOKIE_SAMESITE", None)

        self.stdout.write(f"CSRF_COOKIE_SECURE: {csrf_cookie_secure}")
        self.stdout.write(f"CSRF_COOKIE_SAMESITE: {csrf_cookie_samesite}")

        # 给出建议
        self.stdout.write("\n=== 建议 ===")
        if settings.DEBUG:
            self.stdout.write(
                self.style.SUCCESS("开发模式：CSRF 设置已针对开发环境优化")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "生产模式：请确保 CSRF_TRUSTED_ORIGINS 包含正确的域名"
                )
            )

        self.stdout.write("\n如果仍有 CSRF 错误，请检查：")
        self.stdout.write("1. 请求的 Origin 头是否在 CSRF_TRUSTED_ORIGINS 中")
        self.stdout.write("2. 表单是否包含 {% csrf_token %}")
        self.stdout.write("3. Ajax 请求是否包含 CSRF token")
