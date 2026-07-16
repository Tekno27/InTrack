from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Auth
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("invite/<str:token>/", views.accept_invite, name="accept_invite"),
    path("password-change/",
         auth_views.PasswordChangeView.as_view(
             template_name="registration/password_change_form.html",
             success_url="/password-change/done/",
         ),
         name="password_change"),
    path("password-change/done/",
         auth_views.PasswordChangeDoneView.as_view(
             template_name="registration/password_change_done.html",
         ),
         name="password_change_done"),
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
    path("tasks/<int:pk>/submit/", views.task_submit, name="task_submit"),
    path("tasks/<int:pk>/review/", views.task_review, name="task_review"),
    path("tasks/<int:pk>/attachment/", views.task_attachment, name="task_attachment"),

    # Team (department head)
    path("team/", views.team_list, name="team_list"),
    path("team/invite/", views.invite_user, name="invite_user"),
    path("team/assign/", views.assign_intern, name="assign_intern"),
    path("team/<int:pk>/resend-invite/", views.resend_invite, name="resend_invite"),
    path("team/categories/", views.category_list, name="category_list"),
    path("team/categories/add/", views.category_create, name="category_create"),
    path("team/categories/<int:pk>/edit/", views.category_edit, name="category_edit"),

    # Supervisor / head
    path("interns/", views.intern_list, name="intern_list"),
    path("analytics/", views.analytics, name="analytics"),

    # Reports
    path("reports/", views.reports, name="reports"),
    path("reports/export/csv/", views.export_csv, name="export_csv"),
    path("reports/export/excel/", views.export_excel, name="export_excel"),
    path("reports/export/pdf/", views.export_pdf, name="export_pdf"),

    # Chat
    path("chat/", views.chat_inbox, name="chat_inbox"),
    path("chat/start/", views.chat_start, name="chat_start"),
    path("chat/<int:pk>/", views.chat_thread, name="chat_thread"),

    # Profile & notifications
    path("profile/", views.profile, name="profile"),
    path("notifications/", views.notifications, name="notifications"),
]
