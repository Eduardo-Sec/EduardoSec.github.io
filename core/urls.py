from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('writeups/', views.writeup_list, name='writeup_list'),
    path('writeups/search/', views.writeup_search, name='writeup_search'),
    path('writeups/<slug:slug>/', views.writeup_detail, name='writeup_detail'),
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/<slug:tag>/', views.tag_detail, name='tag_detail'),
    path('projects/', views.projects, name='projects'),
    path('resume/', views.resume, name='resume'),
    path('contact/', views.contact, name='contact'),
    path('pgp/', views.pgp, name='pgp'),
]
