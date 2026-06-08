from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='indexOfAccounts'),
    path('register/', views.register, name='register'),
    path('login/', views.connexion, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('search-family/', views.search_family, name='search_family'),
    path('join-request/<int:request_id>/approve/', views.approve_join_request, name='approve_join_request'),
    path('join-request/<int:request_id>/reject/',  views.reject_join_request,  name='reject_join_request'),
    path('member/<int:user_id>/remove/',           views.remove_member,        name='remove_member'),
    path('family/edit/',                           views.edit_family,          name='edit_family'),
]