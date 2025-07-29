from django.db import models


class MeicanUser(models.Model):
    email = models.CharField(max_length=100, unique=True)
    token = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_attempt = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email


class OrderRecord(models.Model):
    user = models.ForeignKey(
        MeicanUser, on_delete=models.CASCADE, related_name="orders"
    )
    order_date = models.DateField()  # 点餐的日期（不是下单日期）
    meal_name = models.CharField(max_length=200)
    order_time = models.DateTimeField(auto_now_add=True)  # 实际下单时间
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ["user", "order_date"]  # 每个用户每天只能有一个订单记录

    def __str__(self):
        return f"{self.user.email} - {self.order_date} - {self.meal_name}"
