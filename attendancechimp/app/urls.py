from django.urls import path, include
from . import views

urlpatterns = [
    path('dumpUploads', views.dump_uploads, name='dump_uploads'),
    path('createQRCodeUpload', views.create_qr_code_upload, name='create_qr_code_upload'),
    path('createLecture', views.create_lecture, name='create_lecture'),
    path('createCourse', views.create_course, name='create_course'),
    path('new_course', views.new_course, name='new_course'),
    path('new_lecture', views.new_lecture, name='new_lecture'),
    path('new_qr_upload', views.new_qr_upload, name='new_qr_upload'),
    path('createUser', views.create_user, name='create_user'),
    path('new', views.new_user, name='new'),
    path('', views.index, name='home'),
    path('index.html', views.index, name='index_html'),
    path('time', views.time_view, name='time'),
    path('sum', views.sum_view, name='sum')
]
