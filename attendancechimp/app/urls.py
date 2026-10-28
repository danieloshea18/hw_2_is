from django.urls import path, include
from . import views

urlpatterns = [
    path('createUser', views.create_user, name='create_user'),
    path('new', views.new_user, name='new'),
    path('', views.index, name='home'),
    path('index.html', views.index, name='index_html'),
    path('time', views.time_view, name='time'),
    path('sum', views.sum_view, name='sum')
]
