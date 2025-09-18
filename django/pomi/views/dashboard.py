from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.shortcuts import render
from .navbar import get_navbar_context
from pomi.models.ticket import Ticket


@login_required
def home(request):
    ctx = get_navbar_context(request, current_page='dashboard')
    now = timezone.now()

    qs = Ticket.objects.all()

    # --- KPIs
    total = qs.count()
    open_states = ['pending', 'in_progress']
    open_count = qs.filter(state__in=open_states).count()
    resolved_count = qs.filter(state='resolved').count()
    closed_count = qs.filter(state='closed').count()

    # Promedio de tiempo de resolución (tickets con closed_at)
    res_delta = qs.exclude(closed_at__isnull=True).aggregate(
        avg=Avg(ExpressionWrapper(F('closed_at') - F('created_at'), output_field=DurationField()))
    )['avg']
    avg_res_hours = round(res_delta.total_seconds()/3600, 2) if res_delta else 0.0

    # Edad promedio de tickets abiertos
    open_created = list(qs.filter(state__in=open_states).values_list('created_at', flat=True))
    if open_created:
        secs = [(now - dt).total_seconds() for dt in open_created]
        avg_open_hours = round(sum(secs) / len(secs) / 3600, 2)
    else:
        avg_open_hours = 0.0

    # --- Distribuciones
    by_state = list(qs.values('state').annotate(n=Count('id')).order_by())
    by_priority = list(qs.values('priority').annotate(n=Count('id')).order_by())

    # Carga por agente (incluye "Sin asignar")
    agent_rows = (
        qs.values(
            'atendido_por__id',
            'atendido_por__user__first_name',
            'atendido_por__user__last_name',
            'atendido_por__user__username',
        )
        .annotate(n=Count('id'))
        .order_by('-n')
    )

    by_agent = []
    for r in agent_rows:
        if r['atendido_por__id'] is None:
            name = 'Sin asignar'
        else:
            fname = (r['atendido_por__user__first_name'] or '').strip()
            lname = (r['atendido_por__user__last_name'] or '').strip()
            uname = (r['atendido_por__user__username'] or 'Agente').strip()
            name = (f"{fname} {lname}".strip() or uname)
        by_agent.append({'name': name, 'n': r['n']})

    # --- Tendencia últimos 14 días
    start = now.date() - timedelta(days=13)
    created_q = (
        Ticket.objects.filter(created_at__date__gte=start)
        .annotate(d=TruncDate('created_at'))
        .values('d').annotate(n=Count('id'))
        .values_list('d', 'n')
    )
    closed_q = (
        Ticket.objects.filter(closed_at__isnull=False, closed_at__date__gte=start)
        .annotate(d=TruncDate('closed_at'))
        .values('d').annotate(n=Count('id'))
        .values_list('d', 'n')
    )
    created_map = {d: n for d, n in created_q}
    closed_map = {d: n for d, n in closed_q}

    days = [start + timedelta(days=i) for i in range(14)]
    trend_labels = [d.strftime('%Y-%m-%d') for d in days]
    trend_created = [created_map.get(d, 0) for d in days]
    trend_closed = [closed_map.get(d, 0) for d in days]

    # --- Mapeos legibles
    state_label = {
        'pending': 'Pendiente',
        'in_progress': 'En Progreso',
        'resolved': 'Resuelto',
        'closed': 'Cerrado',
    }
    # Orden visual sugerido
    state_order = ['pending', 'in_progress', 'resolved', 'closed']
    prio_order = ['Alta', 'Media', 'Baja']  # invertir para impacto visual

    # Ordenar distribuciones
    by_state_sorted = []
    state_counts = {row['state']: row['n'] for row in by_state}
    for k in state_order:
        by_state_sorted.append({'label': state_label[k], 'n': state_counts.get(k, 0)})

    pr_counts = {row['priority']: row['n'] for row in by_priority}
    by_priority_sorted = [{'label': p, 'n': pr_counts.get(p, 0)} for p in prio_order]

    # --- Empaquetar datos para gráficos
    chart = {
        'state': {
            'labels': [row['label'] for row in by_state_sorted],
            'data': [row['n'] for row in by_state_sorted],
        },
        'priority': {
            'labels': [row['label'] for row in by_priority_sorted],
            'data': [row['n'] for row in by_priority_sorted],
        },
        'agent': {
            'labels': [row['name'] for row in by_agent],
            'data': [row['n'] for row in by_agent],
        },
        'trend': {
            'labels': trend_labels,
            'created': trend_created,
            'closed': trend_closed,
        }
    }

    ctx.update({
        'page_title': 'Dashboard',
        'page_subtitle': 'Vista general del sistema',
        'kpi': {
            'total': total,
            'open': open_count,
            'resolved': resolved_count,
            'closed': closed_count,
            'avg_res_hours': avg_res_hours,
            'avg_open_hours': avg_open_hours,
        },
        'chart': chart,
    })
    return render(request, 'dashboard/dashboard.html', ctx)
