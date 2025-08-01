#!/usr/bin/env python
"""
测试新的自助餐点餐逻辑
"""
import os

import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AutoMeican.settings')
django.setup()

from meican.models import MeicanUser, OrderRecord


def test_new_logic():
    print("=== 测试新的自助餐点餐逻辑 ===")
    
    # 检查当前用户
    users = MeicanUser.objects.filter(is_active=True)
    print(f"活跃用户数量: {users.count()}")
    
    for user in users:
        print(f"用户: {user.email}")
    
    # 检查现有订单
    orders = OrderRecord.objects.all()
    print(f"当前订单记录数量: {orders.count()}")
    
    for order in orders:
        meal_period = order.meal_period or '(空)'
        print(f"  {order.user.email} - {order.order_date} - {meal_period} - {order.meal_name} - 成功: {order.success}")
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_new_logic()
