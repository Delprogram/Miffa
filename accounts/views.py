from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login, logout
from .models import Relation
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm
from .models import Family, JoinRequest
from .decorators import admin_required
from datetime import date
from .models import Post, Reaction, Comment
import calendar as cal_module
import json
from datetime import date, timedelta
from .models import Event, RSVP
from django.core.mail import send_mail
from django.conf import settings

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    context = {"message": "Hello, World!"}
    template = loader.get_template('accounts/index.html')
    return HttpResponse(template.render(context, request))


def search_family(request):
    code = request.GET.get('q', '').strip().upper()
    families = Family.objects.filter(code=code).values('id', 'name', 'code')
    return JsonResponse(list(families), safe=False)



def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.birth_date = form.cleaned_data['birth_date']

            if user.role == 'member':
                family_id = request.POST.get('family_id')
                if not family_id:
                    form.add_error(None, "Vous devez choisir une famille pour vous inscrire en tant que membre.")
                    return render(request, 'accounts/register.html', {'form': form})
                user.save()
                join_request = JoinRequest.objects.create(user=user, family_id=family_id, relation='')

                # ─── Notifie l'admin de la famille ───
                family = join_request.family
                admins = User.objects.filter(family=family, role='admin')
                for admin in admins:
                    Notification.objects.create(
                        user=admin,
                        type='new_join_request',
                        message=f"{user.first_name} {user.last_name} demande à rejoindre votre famille.",
                        link='/accounts/admin-panel/'
                    )
                    send_mail(
                        subject="Nouvelle demande d'adhésion — MIFFA",
                        message=(
                            f"Bonjour {admin.first_name},\n\n"
                            f"{user.first_name} {user.last_name} souhaite rejoindre votre famille {family.name}.\n"
                            f"Connectez-vous pour approuver ou refuser cette demande :\n"
                            f"http://127.0.0.1:8000/accounts/admin-panel/\n\n"
                            f"— MIFFA"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin.email] if admin.email else [],
                        fail_silently=True,
                    )

            elif user.role == 'admin':
                family_name = request.POST.get('family_name', '').strip()
                if not family_name:
                    form.add_error(None, "Vous devez entrer un nom de famille.")
                    return render(request, 'accounts/register.html', {'form': form})
                user.save()
                family = Family.objects.create(name=family_name, created_by=user)
                user.family = family
                user.save()

            else:
                user.save()

            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def connexion(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error_message = None
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            error_message = "Nom d'utilisateur ou mot de passe incorrect."
    return render(request, 'accounts/login.html', {'error_message': error_message})

def deconnexion(request):
    logout(request)
    return redirect('indexOfAccounts')

@login_required
def dashboard(request):
    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'update_banner':
            if request.user.role != 'admin':
                raise PermissionDenied
            if 'banner' in request.FILES and request.user.family:
                request.user.family.banner = request.FILES['banner']
                request.user.family.save()
                messages.success(request, "Bannière mise à jour.")
            else:
                messages.warning(request, "Aucune image sélectionnée.")
            return redirect('dashboard')

        # Mise à jour profil
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name', user.last_name)
        user.email      = request.POST.get('email', user.email)
        user.bio        = request.POST.get('bio', user.bio)
        user.birth_date = request.POST.get('birth_date') or user.birth_date
        if 'photo' in request.FILES:
            user.photo = request.FILES['photo']
        user.save()
        messages.success(request, "Profil mis à jour avec succès.")
        return redirect('dashboard')

    return render(request, 'accounts/dashboard.html')



User = get_user_model()

@login_required
def members_list(request):
    if not request.user.family:
        messages.warning(request, "Vous devez appartenir à une famille pour accéder aux membres.")
        return redirect('dashboard')
    members = User.objects.filter(family=request.user.family)
    return render(request, 'accounts/members_list.html', {'members': members})


@login_required
def member_profile(request, member_id):
    member = get_object_or_404(User, id=member_id)
    if member.family != request.user.family:
        raise PermissionDenied
    relations = Relation.objects.filter(member=member).select_related('related_member')
    return render(request, 'accounts/member_profile.html', {
        'member': member,
        'relations': relations,
    })

from .models import Relation

@login_required
def search_members(request):
    query = request.GET.get('q', '').strip().lower()
    if not request.user.family:
        return JsonResponse([], safe=False)

    members = User.objects.filter(family=request.user.family).exclude(id=request.user.id)
    results = []
    for m in members:
        full_name = f"{m.first_name} {m.last_name}".lower()
        if query in full_name:
            results.append({
                'id': m.id,
                'name': f"{m.first_name} {m.last_name}",
                'photo': m.photo.url if m.photo else None,
                'initials': f"{m.first_name[:1].upper()}{m.last_name[:1].upper()}",
            })
    return JsonResponse(results[:10], safe=False)

from .models import Relation, RelationRequest

@login_required
def add_relation(request):
    if request.method == "POST":
        related_member_id = request.POST.get('related_member_id')
        relation_type     = request.POST.get('relation_type')

        if not related_member_id or not relation_type:
            messages.error(request, "Veuillez choisir un membre et une relation.")
            return redirect('add_relation')

        related_member = get_object_or_404(User, id=related_member_id, family=request.user.family)

        # Vérifie qu'une demande n'existe pas déjà
        if RelationRequest.objects.filter(from_user=request.user, to_user=related_member).exists():
            messages.warning(request, f"Une demande est déjà en attente avec {related_member.first_name}.")
            return redirect('add_relation')

        RelationRequest.objects.create(
            from_user=request.user,
            to_user=related_member,
            relation_type=relation_type,
        )
        Notification.objects.create(
            user=related_member,
            type='relation_request',
            message=f"{request.user.first_name} {request.user.last_name} souhaite vous définir comme {dict(RelationRequest.RELATION_CHOICES).get(relation_type)}.",
            link='/accounts/relations/add/'
        )
        messages.success(request, f"Demande envoyée à {related_member.first_name}. En attente de confirmation.")
        return redirect('add_relation')

    existing_relations = Relation.objects.filter(member=request.user).select_related('related_member')
    sent_requests      = RelationRequest.objects.filter(from_user=request.user, status='pending').select_related('to_user')
    received_requests  = RelationRequest.objects.filter(to_user=request.user, status='pending').select_related('from_user')

    return render(request, 'accounts/add_relation.html', {
        'existing_relations': existing_relations,
        'sent_requests':      sent_requests,
        'received_requests':  received_requests,
    })


@login_required
def accept_relation_request(request, request_id):
    rel_request = get_object_or_404(RelationRequest, id=request_id, to_user=request.user)

    # Crée la relation dans les deux sens
    Relation.objects.update_or_create(
        member=rel_request.from_user,
        related_member=rel_request.to_user,
        defaults={'relation_type': rel_request.relation_type}
    )


    inverse_type = RELATION_INVERSE.get(rel_request.relation_type, 'autre')
    Relation.objects.update_or_create(
        member=rel_request.to_user,
        related_member=rel_request.from_user,
        defaults={'relation_type': inverse_type}
    )

    rel_request.status = 'accepted'
    rel_request.save()
    messages.success(request, f"Relation avec {rel_request.from_user.first_name} confirmée.")
    Notification.objects.create(
        user=rel_request.from_user,
        type='relation_accepted',
        message=f"{request.user.first_name} {request.user.last_name} a accepté votre demande de relation.",
        link='/accounts/relations/add/'
    )
    return redirect('add_relation')


@login_required
def reject_relation_request(request, request_id):
    rel_request = get_object_or_404(RelationRequest, id=request_id, to_user=request.user)
    rel_request.status = 'rejected'
    rel_request.save()
    messages.info(request, f"Demande de {rel_request.from_user.first_name} refusée.")
    Notification.objects.create(
        user=rel_request.from_user,
        type='relation_rejected',
        message=f"{request.user.first_name} {request.user.last_name} a refusé votre demande de relation.",
        link='/accounts/relations/add/'
    )
    return redirect('add_relation')




@login_required
def delete_relation(request, relation_id):
    relation = get_object_or_404(Relation, id=relation_id, member=request.user)
    relation.delete()
    messages.success(request, "Relation supprimée.")
    return redirect('add_relation')

RELATION_INVERSE = {
    'parent': 'enfant',
    'enfant': 'parent',
    'grand_parent': 'petit_enfant',
    'petit_enfant': 'grand_parent',
    'oncle_tante': 'neveu_niece',
    'neveu_niece': 'oncle_tante',
    'conjoint': 'conjoint',
    'frere_soeur': 'frere_soeur',
    'cousin': 'cousin',
    'autre': 'autre',
}

GENERATION_DELTA = {
    'parent': -1, 'enfant': 1,
    'grand_parent': -2, 'petit_enfant': 2,
    'oncle_tante': -1, 'neveu_niece': 1,
    'conjoint': 0, 'frere_soeur': 0, 'cousin': 0, 'autre': 0,
}


@login_required
def family_tree(request):
    if not request.user.family:
        messages.warning(request, "Vous devez appartenir à une famille pour accéder à l'arbre généalogique.")
        return redirect('dashboard')

    family = request.user.family
    all_relations = Relation.objects.filter(
        member__family=family
    ).select_related('member', 'related_member')

    # ─── 1. Construit un graphe bidirectionnel ───
    # graph[user_id] = liste de (other_user_obj, relation_type, is_outgoing)
    graph = {}

    def add_edge(a, b, rel_type):
        graph.setdefault(a.id, []).append((b, rel_type))

    for rel in all_relations:
        add_edge(rel.member, rel.related_member, rel.relation_type)
        inverse_type = RELATION_INVERSE.get(rel.relation_type, 'autre')
        add_edge(rel.related_member, rel.member, inverse_type)

    # ─── 2. BFS depuis l'utilisateur courant pour assigner générations ───
    from collections import deque

    visited = {request.user.id: (request.user, 0, 'Vous')}  # id -> (member_obj, generation, label)
    queue = deque([request.user.id])

    while queue:
        current_id = queue.popleft()
        current_gen = visited[current_id][1]
        for neighbor, rel_type in graph.get(current_id, []):
            if neighbor.id not in visited:
                delta = GENERATION_DELTA.get(rel_type, 0)
                label = dict(Relation.RELATION_CHOICES).get(rel_type, rel_type)
                visited[neighbor.id] = (neighbor, current_gen + delta, label)
                queue.append(neighbor.id)

    # ─── 3. Regroupe par génération ───
    by_generation = {}
    for member_id, (member_obj, gen, label) in visited.items():
        by_generation.setdefault(gen, []).append((member_obj, label, member_id))

    # ─── 4. Calcule les positions ───
    nodes = []
    node_positions = {}  # id -> (x, y)
    node_w_gap = 130
    gen_gap = 160
    center_x = 550

    sorted_gens = sorted(by_generation.keys())
    min_gen = sorted_gens[0] if sorted_gens else 0

    for gen in sorted_gens:
        members_in_gen = by_generation[gen]
        y = (gen - min_gen) * gen_gap + 80
        start_x = center_x - (len(members_in_gen) - 1) * node_w_gap / 2

        for i, (member_obj, label, member_id) in enumerate(members_in_gen):
            x = start_x + i * node_w_gap
            node_positions[member_id] = (x, y)

            if member_id == request.user.id:
                category = 'self'
            elif gen < 0:
                category = 'ascendant'
            elif gen > 0:
                category = 'descendant'
            else:
                category = 'self'

            nodes.append({
                'member': member_obj,
                'category': category,
                'relation_label': label,
                'x': x, 'y': y,
            })

    # ─── 5. Construit les liens (arêtes uniques) ───
    links = []
    seen_edges = set()
    for rel in all_relations:
        if rel.member.id in node_positions and rel.related_member.id in node_positions:
            edge_key = frozenset([rel.member.id, rel.related_member.id])
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            x1, y1 = node_positions[rel.member.id]
            x2, y2 = node_positions[rel.related_member.id]

            if rel.member.id == request.user.id or rel.related_member.id == request.user.id:
                link_type = 'self'
            elif rel.relation_type in ['parent', 'grand_parent', 'oncle_tante']:
                link_type = 'ascendant'
            else:
                link_type = 'descendant'

            links.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'type': link_type})

    svg_width = max(1100, center_x + 450)
    svg_height = max(560, (len(sorted_gens) * gen_gap) + 200)

    # ─── 6. Résumé par génération pour la barre d'indicateurs ───
    generation_labels = {
        -3: "Arrière-grands-parents", -2: "Grands-parents", -1: "Parents",
        0: "Votre génération", 1: "Enfants", 2: "Petits-enfants", 3: "Arrière-petits-enfants",
    }

    generation_summary = []
    for gen in sorted_gens:
        count = len(by_generation[gen])
        if gen < 0:
            category = 'ascendant'
        elif gen > 0:
            category = 'descendant'
        else:
            category = 'self'

        label = generation_labels.get(gen, f"Génération {gen:+d}")
        generation_summary.append({
            'label': label,
            'count': count,
            'category': category,
        })

    return render(request, 'accounts/family_tree.html', {
        'nodes': nodes,
        'links': links,
        'svg_width': svg_width,
        'svg_height': svg_height,
        'generation_summary': generation_summary,
    })

    return render(request, 'accounts/family_tree.html', {
        'nodes': nodes,
        'links': links,
        'svg_width': svg_width,
        'svg_height': svg_height,
    })



@login_required
def news_feed(request):
    if not request.user.family:
        messages.warning(request, "Vous devez appartenir à une famille pour accéder à la Fil d'actualités.")
        return redirect('dashboard')

    posts = Post.objects.filter(family=request.user.family).select_related('author').prefetch_related('comments__author', 'reactions')

    for post in posts:
        post.user_reacted = post.reactions.filter(user=request.user).exists()

    # Anniversaires à venir (30 prochains jours)
    members = User.objects.filter(family=request.user.family).exclude(birth_date__isnull=True)
    today = date.today()
    upcoming_birthdays = []
    for m in members:
        next_bday = m.birth_date.replace(year=today.year)
        if next_bday < today:
            next_bday = next_bday.replace(year=today.year + 1)
        days_until = (next_bday - today).days
        if days_until <= 30:
            upcoming_birthdays.append({'member': m, 'days_until': days_until})
    upcoming_birthdays.sort(key=lambda x: x['days_until'])

    return render(request, 'accounts/news_feed.html', {
        'posts': posts,
        'upcoming_birthdays': upcoming_birthdays[:5],
    })


@login_required
def create_post(request):
    if request.method == "POST":
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        if content or image:
            Post.objects.create(
                author=request.user,
                family=request.user.family,
                content=content,
                image=image
            )
            family_members = User.objects.filter(family=request.user.family).exclude(id=request.user.id)
            for member in family_members:
                Notification.objects.create(
                    user=member,
                    type='new_post',
                    message=f"{request.user.first_name} a publié quelque chose dans le fil d'actualité.",
                    link='/accounts/feed/'
                )
            messages.success(request, "Publication créée.")
        else:
            messages.warning(request, "Ajoutez du texte ou une image.")
    return redirect('news_feed')


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, family=request.user.family)
    if post.author != request.user and request.user.role != 'admin':
        raise PermissionDenied
    post.delete()
    messages.success(request, "Publication supprimée.")
    return redirect('news_feed')


@login_required
def toggle_reaction(request, post_id):
    post = get_object_or_404(Post, id=post_id, family=request.user.family)
    reaction, created = Reaction.objects.get_or_create(post=post, user=request.user)
    if not created:
        reaction.delete()
    else:
        # Notif seulement si c'est un nouveau like et que ce n'est pas son propre post
        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                type='new_like',
                message=f"{request.user.first_name} {request.user.last_name} a aimé votre publication.",
                link='/accounts/feed/'
            )
    return redirect('news_feed')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, family=request.user.family)
    content = request.POST.get('content', '').strip()
    if content:
        Comment.objects.create(post=post, author=request.user, content=content)
        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                type='new_comment',
                message=f"{request.user.first_name} {request.user.last_name} a commenté votre publication : « {content[:50]}{'...' if len(content) > 50 else ''} »",
                link='/accounts/feed/'
            )
    return redirect('news_feed')



@login_required
def calendar_view(request):
    if not request.user.family:
        messages.warning(request, "Vous devez appartenir à une famille pour accéder au calendrier.")
        return redirect('dashboard')

    today = date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    # Navigation mois précédent/suivant
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    cal_module.setfirstweekday(cal_module.MONDAY)
    month_days = cal_module.monthcalendar(year, month)

    events = Event.objects.filter(family=request.user.family, date__year=year, date__month=month)
    events_by_day = {}
    for ev in events:
        events_by_day.setdefault(ev.date.day, []).append(ev)

    calendar_days = []
    for week in month_days:
        for day_num in week:
            if day_num == 0:
                calendar_days.append({'number': '', 'in_month': False, 'is_today': False, 'events': []})
            else:
                is_today = (day_num == today.day and month == today.month and year == today.year)
                calendar_days.append({
                    'number': day_num,
                    'in_month': True,
                    'is_today': is_today,
                    'events': events_by_day.get(day_num, []),
                })

    # Événements à venir (30 prochains jours, toutes dates)
    upcoming_events = Event.objects.filter(
        family=request.user.family, date__gte=today, date__lte=today + timedelta(days=30)
    ).order_by('date')[:6]

    # JSON pour le détail JS
    all_family_events = Event.objects.filter(family=request.user.family)
    events_json = []
    for ev in all_family_events:
        my_rsvp = RSVP.objects.filter(event=ev, user=request.user).first()
        attendees = RSVP.objects.filter(event=ev, status='yes').select_related('user')
        events_json.append({
            'id': ev.id,
            'title': ev.title,
            'date_display': ev.date.strftime('%d/%m/%Y'),
            'time': ev.time.strftime('%H:%M') if ev.time else None,
            'location': ev.location,
            'description': ev.description,
            'created_by': f"{ev.created_by.first_name} {ev.created_by.last_name}" if ev.created_by else "Inconnu",
            'my_rsvp': my_rsvp.status if my_rsvp else None,
            'attendees': [f"{a.user.first_name} {a.user.last_name}" for a in attendees],
            'can_delete': ev.created_by == request.user or request.user.role == 'admin',
        })

    return render(request, 'accounts/calendar_view.html', {
        'month_name': cal_module.month_name[month],
        'year': year,
        'prev_month': prev_month, 'prev_year': prev_year,
        'next_month': next_month, 'next_year': next_year,
        'calendar_days': calendar_days,
        'upcoming_events': upcoming_events,
        'events_json': json.dumps(events_json),
    })


@login_required
def create_event(request):
    if request.method == "POST":
        Event.objects.create(
            family=request.user.family,
            created_by=request.user,
            title=request.POST.get('title'),
            date=request.POST.get('date'),
            time=request.POST.get('time') or None,
            location=request.POST.get('location', ''),
            description=request.POST.get('description', ''),
            event_type=request.POST.get('event_type', 'autre'),
        )
        family_members = User.objects.filter(family=request.user.family).exclude(id=request.user.id)
        for member in family_members:
            Notification.objects.create(
                user=member,
                type='new_event',
                message=f"{request.user.first_name} a créé un événement : {request.POST.get('title')}.",
                link='/accounts/calendar/'
            )
        messages.success(request, "Événement créé.")
    return redirect('calendar_view')


@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, family=request.user.family)
    if event.created_by != request.user and request.user.role != 'admin':
        raise PermissionDenied
    event.delete()
    messages.success(request, "Événement supprimé.")
    return redirect('calendar_view')


@login_required
def rsvp_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, family=request.user.family)
    status = request.POST.get('status')
    if status in ['yes', 'no']:
        RSVP.objects.update_or_create(event=event, user=request.user, defaults={'status': status})
    return redirect('calendar_view')


@login_required
@admin_required
def approve_join_request(request, request_id):
    join_request = get_object_or_404(JoinRequest, id=request_id)
    if join_request.family != request.user.family:
        raise PermissionDenied
    join_request.status = 'approved'
    join_request.save()
    join_request.user.family = join_request.family
    join_request.user.save()
    messages.success(request, f"{join_request.user.username} a été approuvé.")

    Notification.objects.create(
        user=join_request.user,
        type='join_approved',
        message=f"Votre demande d'adhésion à la famille {join_request.family.name} a été approuvée. Définissez votre relation avec un membre.",
        link='/accounts/relations/add/'
    )
    send_mail(
        subject="Votre demande a été approuvée — MIFFA",
        message=(
            f"Bonjour {join_request.user.first_name},\n\n"
            f"Votre demande pour rejoindre {join_request.family.name} a été approuvée !\n"
            f"Rendez-vous ici pour définir votre lien de parenté avec les membres de la famille :\n"
            f"http://127.0.0.1:8000/accounts/relations/add/\n\n"
            f"— MIFFA"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[join_request.user.email] if join_request.user.email else [],
        fail_silently=True,
    )
    return redirect('dashboard')

@login_required
@admin_required
def reject_join_request(request, request_id):
    join_request = get_object_or_404(JoinRequest, id=request_id)
    if join_request.family != request.user.family:
        raise PermissionDenied
    join_request.status = 'rejected'
    join_request.save()
    messages.success(request, f"Demande de {join_request.user.username} refusée.")
    return redirect('dashboard')


@login_required
@admin_required
def remove_member(request, user_id):
    from .models import User
    member = get_object_or_404(User, id=user_id)
    if member.family != request.user.family:
        raise PermissionDenied
    member.family = None
    member.save()
    messages.success(request, f"{member.username} a été retiré de la famille.")
    return redirect('dashboard')


@login_required
@admin_required
def edit_family(request):
    family = request.user.family
    if not family:
        raise PermissionDenied
    if request.method == "POST":
        family.name = request.POST.get('family_name', family.name).strip()
        family.save()
        messages.success(request, "Famille mise à jour.")
        return redirect('dashboard')
    return render(request, 'accounts/edit_family.html', {'family': family})

@login_required
@admin_required
def admin_panel(request):
    family = request.user.family
    if not family:
        raise PermissionDenied

    pending_requests = JoinRequest.objects.filter(family=family, status='pending')
    members = family.members.all() if hasattr(family, 'members') else User.objects.filter(family=family)

    return render(request, 'accounts/admin.html', {
        'pending_requests': pending_requests,
        'members': members,
    })

from .models import Notification

@login_required
def notifications(request):
    notifs = Notification.objects.filter(user=request.user)
    return render(request, 'accounts/notifications.html', {'notifications': notifs})

@login_required
def mark_notification_read(request, notif_id):
    try:
        notif = Notification.objects.get(id=notif_id, user=request.user)
        link = notif.link
        notif.delete()
        if link:
            return redirect(link)
    except Notification.DoesNotExist:
        pass
    return redirect('notifications')

import json
from .models import Album, MediaItem

def detect_media_type(filename):
    ext = filename.lower().split('.')[-1]
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        return 'image'
    elif ext in ['mp4', 'mov', 'avi', 'webm']:
        return 'video'
    return 'document'


@login_required
def media_library(request):
    if not request.user.family:
        messages.warning(request, "Vous devez appartenir à une famille pour accéder à la Médiathèque.")
        return redirect('dashboard')

    albums_qs = Album.objects.filter(family=request.user.family)
    albums = []
    for album in albums_qs:
        first_image = album.items.filter(media_type='image').first()
        albums.append({
            'id': album.id,
            'title': album.title,
            'created_at': album.created_at,
            'created_by': album.created_by,
            'item_count': album.items.count(),
            'cover_image': first_image.file.url if first_image else None,
        })

    return render(request, 'accounts/media_library.html', {'albums': albums})


@login_required
def create_album(request):
    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        if title:
            album = Album.objects.create(
                family=request.user.family,
                created_by=request.user,
                title=title,
                description=request.POST.get('description', ''),
            )

            # Notifie les autres membres de la famille
            family_members = User.objects.filter(family=request.user.family).exclude(id=request.user.id)
            for member in family_members:
                Notification.objects.create(
                    user=member,
                    type='new_album',
                    message=f"{request.user.first_name} {request.user.last_name} a créé un nouvel album : « {title} ».",
                    link='/accounts/media/'
                )

            messages.success(request, "Album créé.")
            return redirect('album_detail', album_id=album.id)
        messages.error(request, "Le nom de l'album est requis.")
    return redirect('media_library')


@login_required
def upload_media(request, album_id):
    album = get_object_or_404(Album, id=album_id, family=request.user.family)
    if request.method == "POST":
        files = request.FILES.getlist('files')
        for f in files:
            MediaItem.objects.create(
                album=album,
                uploaded_by=request.user,
                file=f,
                media_type=detect_media_type(f.name),
            )

        if files:
            # Notifie les autres membres de la famille
            family_members = User.objects.filter(family=request.user.family).exclude(id=request.user.id)
            count = len(files)
            for member in family_members:
                Notification.objects.create(
                    user=member,
                    type='new_media',
                    message=f"{request.user.first_name} {request.user.last_name} a ajouté {count} fichier{'s' if count > 1 else ''} à l'album « {album.title} ».",
                    link=f'/accounts/media/album/{album.id}/'
                )

        messages.success(request, f"{len(files)} fichier(s) ajouté(s).")
    return redirect('album_detail', album_id=album.id)


@login_required
def album_detail(request, album_id):
    album = get_object_or_404(Album, id=album_id, family=request.user.family)
    media_items = album.items.all()

    media_json = [{
        'id': item.id,
        'type': item.media_type,
        'url': item.file.url,
        'name': item.file.name.split('/')[-1],
    } for item in media_items]

    return render(request, 'accounts/album_detail.html', {
        'album': album,
        'media_items': media_items,
        'media_json': json.dumps(media_json),
    })



@login_required
def delete_album(request, album_id):
    album = get_object_or_404(Album, id=album_id, family=request.user.family)
    if album.created_by != request.user and request.user.role != 'admin':
        raise PermissionDenied
    album.delete()
    messages.success(request, "Album supprimé.")
    return redirect('media_library')

from .models import TimelineEvent

TIMELINE_ICONS = {
    'naissance': 'fa-baby',
    'mariage': 'fa-rings-wedding',
    'diplome': 'fa-graduation-cap',
    'demenagement': 'fa-truck-moving',
    'deces': 'fa-dove',
    'autre': 'fa-star',
}

@login_required
def timeline_view(request):
    if not request.user.family:
        messages.warning(request, "Vous devez appartenir à une famille pour accéder à la chronologie.")
        return redirect('dashboard')

    events = TimelineEvent.objects.filter(family=request.user.family).select_related('member').order_by('-date')
    family_members = User.objects.filter(family=request.user.family)

    # Regroupe par année
    groups = {}
    for ev in events:
        year = ev.date.year
        groups.setdefault(year, []).append(ev)

    timeline_groups = []
    for i, year in enumerate(sorted(groups.keys(), reverse=True)):
        year_events = []
        for j, ev in enumerate(groups[year]):
            year_events.append({
                'id': ev.id,
                'title': ev.title,
                'date': ev.date,
                'description': ev.description,
                'event_type': ev.event_type,
                'icon': TIMELINE_ICONS.get(ev.event_type, 'fa-star'),
                'member': ev.member,
                'side': 'left' if j % 2 == 0 else 'right',
                'can_delete': ev.created_by == request.user or request.user.role == 'admin',
            })
        timeline_groups.append({'year': year, 'events': year_events})

    return render(request, 'accounts/timeline_view.html', {
        'timeline_groups': timeline_groups,
        'family_members': family_members,
    })


@login_required
def create_timeline_event(request):
    if request.method == "POST":
        member_id = request.POST.get('member_id')
        title = request.POST.get('title', '').strip()
        date_val = request.POST.get('date')

        if member_id and title and date_val:
            member = get_object_or_404(User, id=member_id, family=request.user.family)
            TimelineEvent.objects.create(
                family=request.user.family,
                member=member,
                created_by=request.user,
                title=title,
                date=date_val,
                event_type=request.POST.get('event_type', 'autre'),
                description=request.POST.get('description', ''),
            )
            messages.success(request, "Événement ajouté à la chronologie.")
        else:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
    return redirect('timeline_view')


@login_required
def delete_timeline_event(request, event_id):
    event = get_object_or_404(TimelineEvent, id=event_id, family=request.user.family)
    if event.created_by != request.user and request.user.role != 'admin':
        raise PermissionDenied
    event.delete()
    messages.success(request, "Événement supprimé.")
    return redirect('timeline_view')