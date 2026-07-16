from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Auth
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/",
         auth_views.PasswordResetView.as_view(),
         name="password_reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(),
         name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),
    path("password-reset/complete/",
         auth_views.PasswordResetCompleteView.as_view(),
         name="password_reset_complete"),

    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Tasks
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/add/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/", views.task_detail, name="task_detail"),
    path("tasks/<int:pk>/edit/", views.task_update, name="task_update"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),

    # Supervisor
    path("interns/", views.intern_list, name="intern_list"),
    path("analytics/", views.analytics, name="analytics"),

    # Reports
    path("reports/", views.reports, name="reports"),
    path("reports/export/csv/", views.export_csv, name="export_csv"),
    path("reports/export/excel/", views.export_excel, name="export_excel"),
    path("reports/export/pdf/", views.export_pdf, name="export_pdf"),

    # Profile & notifications
    path("profile/", views.profile, name="profile"),
    path("notifications/", views.notifications, name="notifications"),
]
