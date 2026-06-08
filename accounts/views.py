from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login, logout

from .forms import CustomUserCreationForm
from .models import Family, JoinRequest
from .decorators import admin_required


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
                JoinRequest.objects.create(user=user, family_id=family_id, relation='')

            elif user.role == 'admin':
                family_name = request.POST.get('family_name', '').strip()
                if not family_name:
                    form.add_error(None, "Vous devez entrer un nom de famille.")
                    return render(request, 'accounts/register.html', {'form': form})
                user.save()
                family = Family.objects.create(name=family_name, created_by=user)
                user.family = family  # ← lie l'admin à sa famille
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