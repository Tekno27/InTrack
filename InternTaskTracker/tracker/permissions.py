from django.db.models import Q

from .models import Category, Task, User


def visible_interns_for(user):
    """Interns the current user is allowed to manage/view."""
    qs = User.objects.filter(role=User.Roles.INTERN, is_active=True)
    if user.is_head:
        return qs.filter(department=user.department)
    if user.is_supervisor:
        return qs.filter(supervisor=user)
    return qs.none()


def visible_tasks_for(user):
    """Tasks the current user may see."""
    qs = Task.objects.select_related("intern", "category", "assigned_by")
    if user.is_intern:
        return qs.filter(intern=user)
    if user.is_supervisor:
        return qs.filter(intern__supervisor=user)
    if user.is_head:
        return qs.filter(intern__department=user.department)
    return qs.none()


def assignable_interns_for(user):
    """Interns a supervisor/head may assign tasks to."""
    return visible_interns_for(user)


def categories_for(user):
    """Categories available to the user (global + department)."""
    qs = Category.objects.all()
    if user.department_id:
        return qs.filter(Q(department__isnull=True) | Q(department=user.department))
    return qs.filter(department__isnull=True)


def can_view_task(user, task):
    return visible_tasks_for(user).filter(pk=task.pk).exists()


def can_edit_task(user, task):
    """Interns edit their own tasks; assigners can edit assigned tasks they created."""
    if task.status == Task.Status.APPROVED:
        # Approved work is locked for interns; management may still adjust.
        if user.is_intern:
            return False
    if task.status == Task.Status.SUBMITTED and user.is_intern:
        return False
    if user.is_intern and task.intern_id == user.pk:
        return True
    if user.is_management and task.assigned_by_id == user.pk:
        return True
    if user.is_head and task.intern.department_id == user.department_id:
        return True
    return False


def can_delete_task(user, task):
    if task.status in {Task.Status.SUBMITTED, Task.Status.APPROVED}:
        if user.is_intern:
            return False
    if user.is_intern and task.intern_id == user.pk and not task.is_assigned:
        return True
    if user.is_management and task.assigned_by_id == user.pk:
        return True
    if user.is_head and task.intern.department_id == user.department_id:
        return True
    return False


def can_review_task(user, task):
    """Supervisor (of the intern) or department head may review submitted work."""
    if not user.is_management or task.status != Task.Status.SUBMITTED:
        return False
    return visible_interns_for(user).filter(pk=task.intern_id).exists()


def can_submit_task(user, task):
    return (
        user.is_intern
        and task.intern_id == user.pk
        and task.can_submit_for_review
    )


def can_message(user, other):
    """Return True if `user` is allowed to start/continue a direct chat with `other`."""
    if not user.is_authenticated or not other.is_authenticated:
        return False
    if user.pk == other.pk:
        return False
    if not other.is_active:
        return False

    # Supervisors and heads may message any other supervisor/head company-wide.
    if user.is_management and other.is_management:
        return True

    # Interns may message other interns in the same department.
    if user.is_intern and other.is_intern:
        return (
            user.department_id is not None
            and user.department_id == other.department_id
        )

    # Intern <-> assigned supervisor
    if user.is_intern and other.is_supervisor:
        return user.supervisor_id == other.pk
    if user.is_supervisor and other.is_intern:
        return other.supervisor_id == user.pk

    # Intern <-> department head
    if user.is_intern and other.is_head:
        return (
            user.department_id is not None
            and user.department_id == other.department_id
        )
    if user.is_head and other.is_intern:
        return (
            other.department_id is not None
            and other.department_id == user.department_id
        )

    return False


def messageable_users_for(user):
    """Users available in the 'new chat' picker for `user`."""
    others = User.objects.filter(is_active=True).exclude(pk=user.pk)
    allowed_ids = [u.pk for u in others if can_message(user, u)]
    return User.objects.filter(pk__in=allowed_ids).order_by("first_name", "username")
