from django import template
from django.utils.html import format_html

from tracker.models import Category, Task, User

register = template.Library()

STATUS_ICONS = {
    "PENDING": "bi-pause-circle-fill",
    "IN_PROGRESS": "bi-play-circle-fill",
    "SUBMITTED": "bi-hourglass-split",
    "CHANGES_REQUESTED": "bi-arrow-counterclockwise",
    "APPROVED": "bi-patch-check-fill",
    "COMPLETED": "bi-patch-check-fill",
}

PRIORITY_ICONS = {
    "LOW": "bi-chevron-down",
    "MEDIUM": "bi-dash-lg",
    "HIGH": "bi-chevron-up",
}

STATUS_LABELS = dict(Task.Status.choices)
PRIORITY_LABELS = dict(Task.Priority.choices)


@register.simple_tag
def status_badge(task_or_status, label=None):
    """Render a status badge with icon + text (not color-only)."""
    if hasattr(task_or_status, "status"):
        status = task_or_status.status
        text = label or task_or_status.get_status_display()
    else:
        status = str(task_or_status)
        text = label or STATUS_LABELS.get(status, status.replace("_", " ").title())
    icon = STATUS_ICONS.get(status, "bi-circle-fill")
    return format_html(
        '<span class="badge status-{} badge-with-icon">'
        '<i class="bi {}" aria-hidden="true"></i>'
        '<span>{}</span></span>',
        status.lower(), icon, text,
    )


@register.simple_tag
def priority_badge(task_or_priority, label=None):
    if hasattr(task_or_priority, "priority"):
        priority = task_or_priority.priority
        text = label or task_or_priority.get_priority_display()
    else:
        priority = str(task_or_priority)
        text = label or PRIORITY_LABELS.get(priority, priority.title())
    icon = PRIORITY_ICONS.get(priority, "bi-dash-lg")
    return format_html(
        '<span class="badge priority-{} badge-with-icon">'
        '<i class="bi {}" aria-hidden="true"></i>'
        '<span>{}</span></span>',
        priority.lower(), icon, text,
    )


@register.simple_tag
def assigned_badge(task):
    if not getattr(task, "is_assigned", False):
        return ""
    assigner = ""
    if task.assigned_by_id:
        assigner = task.assigned_by.get_full_name() or task.assigned_by.username
    title = f"Assigned by {assigner}" if assigner else "Assigned by supervisor"
    return format_html(
        '<span class="badge bg-info-subtle text-info ms-1 badge-with-icon" title="{}">'
        '<i class="bi bi-person-check-fill" aria-hidden="true"></i>'
        '<span>Assigned</span></span>',
        title,
    )


@register.inclusion_tag("partials/active_filters.html", takes_context=True)
def active_filters(context, clear_url_name="task_list"):
    request = context["request"]
    params = request.GET
    chips = []

    if q := params.get("q", "").strip():
        chips.append({"label": "Search", "value": q})
    if status := params.get("status", "").strip():
        chips.append({"label": "Status", "value": STATUS_LABELS.get(status, status)})
    if priority := params.get("priority", "").strip():
        chips.append({"label": "Priority", "value": PRIORITY_LABELS.get(priority, priority)})
    if category := params.get("category", "").strip():
        cat = Category.objects.filter(pk=category).first()
        chips.append({"label": "Category", "value": cat.name if cat else category})
    if intern := params.get("intern", "").strip():
        user = User.objects.filter(pk=intern).first()
        chips.append({
            "label": "Intern",
            "value": (user.get_full_name() or user.username) if user else intern,
        })
    if date_from := params.get("date_from", "").strip():
        chips.append({"label": "From", "value": date_from})
    if date_to := params.get("date_to", "").strip():
        chips.append({"label": "To", "value": date_to})
    if month := params.get("month", "").strip():
        chips.append({"label": "Month", "value": month})
    if period := params.get("period", "").strip():
        chips.append({"label": "Period", "value": period.title()})

    return {
        "chips": chips,
        "count": len(chips),
        "clear_url_name": clear_url_name,
    }
