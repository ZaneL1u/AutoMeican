import threading
import time

from django.apps import AppConfig


class MeicanConfig(AppConfig):
    name = "meican"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        应用准备就绪时执行
        启动时立即执行一次自动点餐任务
        """
        # 避免在migrate等管理命令时执行
        import sys

        if "runserver" in sys.argv or "gunicorn" in sys.argv[0]:
            # 延迟几秒执行，确保数据库连接等都已准备好
            def delayed_start():
                time.sleep(5)  # 等待5秒
                try:
                    from .cron import auto_order_meals

                    auto_order_meals()
                except Exception as e:
                    import logging

                    logger = logging.getLogger("meican")
                    logger.error(f"启动时执行自动点餐任务失败: {e}")

            # 在后台线程中执行，避免阻塞应用启动
            thread = threading.Thread(target=delayed_start)
            thread.daemon = True
            thread.start()
