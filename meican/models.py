from django.db import models


class MeicanUser(models.Model):
    email = models.CharField(max_length=100, unique=True)
    token = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_attempt = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email


class TabStatus(models.Model):
    """用户的 Tab 状态表 - 用于存储每个用户的可点餐时段状态"""
    user = models.ForeignKey(
        MeicanUser, on_delete=models.CASCADE, related_name="tab_statuses"
    )
    tab_uid = models.CharField(max_length=100)  # Tab 的唯一标识
    tab_title = models.CharField(max_length=200)  # Tab 标题（如"午餐 12:00-13:00"）
    target_time = models.DateTimeField()  # 目标时间
    status = models.CharField(max_length=20)  # 状态（AVAILABLE, ORDERED, CLOSED 等）
    order_date = models.DateField()  # 对应的用餐日期
    last_updated = models.DateTimeField(auto_now=True)  # 最后更新时间
    
    class Meta:
        unique_together = ["user", "tab_uid", "order_date"]  # 每个用户每个Tab每天只有一条记录
        indexes = [
            models.Index(fields=['user', 'order_date']),
            models.Index(fields=['order_date', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.order_date} - {self.tab_title} - {self.status}"


class OrderRecord(models.Model):
    user = models.ForeignKey(
        MeicanUser, on_delete=models.CASCADE, related_name="orders"
    )
    order_date = models.DateField()  # 点餐的日期（不是下单日期）
    meal_period = models.CharField(max_length=50, default="")  # 用餐时段（如"早餐"、"午餐"、"晚餐"等）
    meal_name = models.CharField(max_length=200)
    order_time = models.DateTimeField(auto_now_add=True)  # 实际下单时间
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    tab_uid = models.CharField(max_length=100, blank=True, null=True)  # 关联的 Tab UID

    class Meta:
        unique_together = ["user", "order_date", "meal_period"]  # 每个用户每天每个时段只能有一个订单记录

    def __str__(self):
        return f"{self.user.email} - {self.order_date} - {self.meal_period} - {self.meal_name}"
