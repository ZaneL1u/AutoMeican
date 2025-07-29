from django.urls import path

from . import views

urlpatterns = [
    path("", views.MeicanUsersView.as_view(), name="get_meican_users"),
    path("delete/<int:user_id>/", views.DeleteUserView.as_view(), name="delete_user"),
    path(
        "update-status/<int:user_id>/",
        views.UpdateOrderStatusView.as_view(),
        name="update_order_status",
    ),
    path("auto-order/", views.AutoOrderView.as_view(), name="auto_order"),
    # API endpoints
    path("api/users/", views.UsersApiView.as_view(), name="api_users"),
    path(
        "api/users/create/", views.CreateUserApiView.as_view(), name="api_create_user"
    ),
    path(
        "api/users/<int:user_id>/delete/",
        views.DeleteUserApiView.as_view(),
        name="api_delete_user",
    ),
]
