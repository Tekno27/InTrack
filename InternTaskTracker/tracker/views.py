import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, DurationField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ProfileUpdateForm, RegisterForm, TaskForm, UserUpdateForm
from .models import Category, Notification, Task, User

ZERO = Value(timedelta(), output_field=DurationField())


def is_supervisor(user):
    return user.is_authenticated and user.is_supervisor


supervisor_required = user_passes_test(is_supervisor)


def hours(duration):
    """Convert a timedelta (or None) to hours rounded to 1 decimal."""
    if not duration:
        return 0
    return round(duration.total_seconds() / 3600, 1)


def notify(user, title, message="", link=""):
    Notification.objects.create(user=user, title=title, message=message, link=link)


# ---------------------------------------------------------------- auth

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to InTrack! Your account has been created.")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


# ---------------------------------------------------------------- helpers

def filter_tasks(request, queryset):
    """Apply search & filter query parameters to a Task queryset."""
    params = request.GET
    if q := params.get("q", "").strip():
        queryset = queryset.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )
    if status := params.get("status"):
        queryset = queryset.filter(status=status)
    if priority := params.get("priority"):
        queryset = queryset.filter(priority=priority)
    if category := params.get("category"):
        queryset = queryset.filter(category_id=category)
    if date := params.get("date"):
        queryset = queryset.filter(date=date)
    if date_from := params.get("date_from"):
        queryset = queryset.filter(date__gte=date_from)
    if date_to := params.get("date_to"):
        queryset = queryset.filter(date__lte=date_to)
    if month := params.get("month"):  # format YYYY-MM
        try:
            year, mon = month.split("-")
            queryset = queryset.filter(date__year=int(year), date__month=int(mon))
        except ValueError:
            pass
    if intern := params.get("intern"):
        queryset = queryset.filter(intern_id=intern)
    return queryset


def week_bounds(today):
    start = today - timedelta(days=today.weekday())
    return start, start + timedelta(days=6)


def weekly_chart_data(queryset, today):
    """Hours per day for the current week (Mon..Sun)."""
    week_start, _ = week_bounds(today)
    labels, data = [], []
    for i in range(7):
        day = week_start + timedelta(days=i)
        total = queryset.filter(date=day).aggregate(
            t=Coalesce(Sum("duration"), ZERO))["t"]
        labels.append(day.strftime("%a"))
        data.append(hours(total))
    return labels, data


# ---------------------------------------------------------------- dashboard

@login_required
def dashboard(request):
    if request.user.is_supervisor:
        return supervisor_dashboard(request)
    return intern_dashboard(request)


def intern_dashboard(request):
    today = timezone.localdate()
    week_start, week_end = week_bounds(today)
    tasks = request.user.tasks.all()

    stats = {
        "hours_today": hours(tasks.filter(date=today).aggregate(
            t=Coalesce(Sum("duration"), ZERO))["t"]),
        "hours_week": hours(tasks.filter(date__range=(week_start, week_end)).aggregate(
            t=Coalesce(Sum("duration"), ZERO))["t"]),
        "hours_month": hours(tasks.filter(
            date__year=today.year, date__month=today.month).aggregate(
            t=Coalesce(Sum("duration"), ZERO))["t"]),
        "completed": tasks.filter(status=Task.Status.COMPLETED).count(),
        "pending": tasks.filter(status=Task.Status.PENDING).count(),
        "in_progress": tasks.filter(status=Task.Status.IN_PROGRESS).count(),
    }
    chart_labels, chart_data = weekly_chart_data(tasks, today)

    context = {
        "stats": stats,
        "recent_tasks": tasks.select_related("category")[:6],
        "chart_labels": chart_labels,
        "chart_data": chart_data,
    }
    return render(request, "dashboard/intern_dashboard.html", context)


def supervisor_dashboard(request):
    today = timezone.localdate()
    tasks = Task.objects.all()
    interns = User.objects.filter(role=User.Roles.INTERN)

    stats = {
        "total_interns": interns.count(),
        "total_tasks": tasks.count(),
        "active_tasks": tasks.filter(
            status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]).count(),
        "total_hours": hours(tasks.aggregate(t=Coalesce(Sum("duration"), ZERO))["t"]),
    }

    top_interns = (
        interns.annotate(
            total_hours=Coalesce(Sum("tasks__duration"), ZERO),
            task_count=Count("tasks"),
        )
        .order_by("-total_hours")[:5]
    )
    top_interns = [
        {"user": u, "hours": hours(u.total_hours), "task_count": u.task_count}
        for u in top_interns
    ]

    chart_labels, chart_data = weekly_chart_data(tasks, today)

    context = {
        "stats": stats,
        "top_interns": top_interns,
        "recent_tasks": tasks.select_related("intern", "category")[:8],
        "chart_labels": chart_labels,
        "chart_data": chart_data,
    }
    return render(request, "dashboard/supervisor_dashboard.html", context)


# ---------------------------------------------------------------- tasks

@login_required
def task_list(request):
    if request.user.is_supervisor:
        tasks = Task.objects.select_related("intern", "category")
    else:
        tasks = request.user.tasks.select_related("category")
    tasks = filter_tasks(request, tasks)

    paginator = Paginator(tasks, 10)
    page = paginator.get_page(request.GET.get("page"))

    total_hours = hours(tasks.aggregate(t=Coalesce(Sum("duration"), ZERO))["t"])

    context = {
        "page": page,
        "total_hours": total_hours,
        "categories": Category.objects.all(),
        "interns": (User.objects.filter(role=User.Roles.INTERN)
                    if request.user.is_supervisor else None),
        "statuses": Task.Status.choices,
        "priorities": Task.Priority.choices,
    }
    return render(request, "tasks/task_list.html", context)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task.objects.select_related("intern", "category"), pk=pk)
    if not request.user.is_supervisor and task.intern != request.user:
        messages.error(request, "You can only view your own tasks.")
        return redirect("task_list")
    return render(request, "tasks/task_detail.html", {"task": task})


@login_required
def task_create(request):
    if request.user.is_supervisor:
        messages.error(request, "Only interns can log tasks.")
        return redirect("dashboard")
    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.intern = request.user
            task.save()
            for supervisor in User.objects.filter(role=User.Roles.SUPERVISOR):
                notify(supervisor, "New task submitted",
                       f"{request.user} logged \"{task.title}\".",
                       link=f"/tasks/{task.pk}/")
            messages.success(request, "Task added successfully.")
            return redirect("task_list")
    else:
        form = TaskForm(initial={"date": timezone.localdate()})
    return render(request, "tasks/task_form.html", {"form": form, "title": "Add Task"})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, intern=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated successfully.")
            return redirect("task_detail", pk=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, "tasks/task_form.html", {"form": form, "title": "Edit Task"})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, intern=request.user)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect("task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


# ---------------------------------------------------------------- supervisor

@login_required
@supervisor_required
def intern_list(request):
    interns = User.objects.filter(role=User.Roles.INTERN).select_related("profile")
    if q := request.GET.get("q", "").strip():
        interns = interns.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(username__icontains=q) | Q(email__icontains=q)
        )
    interns = interns.annotate(
        total_hours=Coalesce(Sum("tasks__duration"), ZERO),
        task_count=Count("tasks"),
        completed_count=Count("tasks", filter=Q(tasks__status=Task.Status.COMPLETED)),
    )
    rows = [
        {"user": u, "hours": hours(u.total_hours), "task_count": u.task_count,
         "completed_count": u.completed_count}
        for u in interns
    ]
    return render(request, "supervisor/intern_list.html", {"rows": rows})


@login_required
@supervisor_required
def analytics(request):
    today = timezone.localdate()
    tasks = Task.objects.all()

    # Hours per week for the last 8 weeks
    week_labels, week_data = [], []
    this_week_start, _ = week_bounds(today)
    for i in range(7, -1, -1):
        start = this_week_start - timedelta(weeks=i)
        end = start + timedelta(days=6)
        total = tasks.filter(date__range=(start, end)).aggregate(
            t=Coalesce(Sum("duration"), ZERO))["t"]
        week_labels.append(start.strftime("%d %b"))
        week_data.append(hours(total))

    # Monthly productivity: hours in each of the last 6 months
    month_labels, month_data = [], []
    year, month = today.year, today.month
    months = []
    for _ in range(6):
        months.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    for y, m in reversed(months):
        total = tasks.filter(date__year=y, date__month=m).aggregate(
            t=Coalesce(Sum("duration"), ZERO))["t"]
        month_labels.append(f"{m:02d}/{y}")
        month_data.append(hours(total))

    # Task completion rate
    status_counts = {
        label: tasks.filter(status=value).count()
        for value, label in Task.Status.choices
    }

    # Hours per intern
    intern_rows = (
        User.objects.filter(role=User.Roles.INTERN)
        .annotate(total_hours=Coalesce(Sum("tasks__duration"), ZERO))
        .order_by("-total_hours")
    )
    intern_labels = [u.get_full_name() or u.username for u in intern_rows]
    intern_data = [hours(u.total_hours) for u in intern_rows]

    # Task distribution by category
    category_rows = (
        Category.objects.annotate(n=Count("tasks")).filter(n__gt=0).order_by("-n")
    )
    uncategorized = tasks.filter(category__isnull=True).count()
    category_labels = [c.name for c in category_rows]
    category_data = [c.n for c in category_rows]
    if uncategorized:
        category_labels.append("Uncategorized")
        category_data.append(uncategorized)

    context = {
        "week_labels": week_labels, "week_data": week_data,
        "month_labels": month_labels, "month_data": month_data,
        "status_labels": list(status_counts.keys()),
        "status_data": list(status_counts.values()),
        "intern_labels": intern_labels, "intern_data": intern_data,
        "category_labels": category_labels, "category_data": category_data,
    }
    return render(request, "supervisor/analytics.html", context)


# ---------------------------------------------------------------- reports

def report_queryset(request):
    """Tasks visible to the current user, with report period + filters applied."""
    if request.user.is_supervisor:
        tasks = Task.objects.select_related("intern", "category")
    else:
        tasks = request.user.tasks.select_related("intern", "category")

    today = timezone.localdate()
    period = request.GET.get("period", "")
    if period == "daily":
        tasks = tasks.filter(date=today)
    elif period == "weekly":
        start, end = week_bounds(today)
        tasks = tasks.filter(date__range=(start, end))
    elif period == "monthly":
        tasks = tasks.filter(date__year=today.year, date__month=today.month)

    return filter_tasks(request, tasks).order_by("date", "start_time")


@login_required
def reports(request):
    tasks = report_queryset(request)
    total_hours = hours(tasks.aggregate(t=Coalesce(Sum("duration"), ZERO))["t"])
    context = {
        "tasks": tasks[:200],
        "task_count": tasks.count(),
        "total_hours": total_hours,
        "categories": Category.objects.all(),
        "interns": (User.objects.filter(role=User.Roles.INTERN)
                    if request.user.is_supervisor else None),
        "statuses": Task.Status.choices,
        "priorities": Task.Priority.choices,
    }
    return render(request, "reports/reports.html", context)


def report_rows(tasks, include_intern):
    header = ["Date", "Title", "Category", "Priority", "Status",
              "Start", "End", "Hours"]
    if include_intern:
        header.insert(1, "Intern")
    rows = [header]
    for t in tasks:
        row = [
            t.date.strftime("%Y-%m-%d"),
            t.title,
            t.category.name if t.category else "-",
            t.get_priority_display(),
            t.get_status_display(),
            t.start_time.strftime("%H:%M"),
            t.end_time.strftime("%H:%M"),
            t.duration_hours,
        ]
        if include_intern:
            row.insert(1, t.intern.get_full_name() or t.intern.username)
        rows.append(row)
    return rows


@login_required
def export_csv(request):
    tasks = report_queryset(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="intrack_report.csv"'
    writer = csv.writer(response)
    for row in report_rows(tasks, request.user.is_supervisor):
        writer.writerow(row)
    return response


@login_required
def export_excel(request):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    tasks = report_queryset(request)
    wb = Workbook()
    ws = wb.active
    ws.title = "Tasks"

    rows = report_rows(tasks, request.user.is_supervisor)
    header_fill = PatternFill("solid", fgColor="2563EB")
    header_font = Font(color="FFFFFF", bold=True)
    for row in rows:
        ws.append(row)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
    for col in ws.columns:
        width = max(len(str(c.value or "")) for c in col) + 2
        ws.column_dimensions[col[0].column_letter].width = min(width, 40)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="intrack_report.xlsx"'
    wb.save(response)
    return response


@login_required
def export_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    tasks = report_queryset(request)
    total = hours(tasks.aggregate(t=Coalesce(Sum("duration"), ZERO))["t"])

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="intrack_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4),
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("InTrack — Task Report", styles["Title"]),
        Paragraph(
            f"Generated {timezone.localdate():%d %b %Y} · "
            f"{tasks.count()} task(s) · {total} hours total",
            styles["Normal"]),
        Spacer(1, 12),
    ]

    data = report_rows(tasks, request.user.is_supervisor)
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    doc.build(elements)
    return response


# ---------------------------------------------------------------- profile

@login_required
def profile(request):
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, "accounts/profile.html",
                  {"user_form": user_form, "profile_form": profile_form})


# ---------------------------------------------------------------- notifications

@login_required
def notifications(request):
    items = request.user.notifications.all()[:50]
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "notifications/notification_list.html", {"items": items})
