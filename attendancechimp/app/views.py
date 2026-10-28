"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import datetime
import zoneinfo
import json
import io

#from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
#                      Lecture, QRCodeUpload, is_instructor, is_student,
#                      getUploadsForCourse)

from .models import InstructorProfile, StudentProfile
 
CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

def index(request):
    """Render the home page (index.html)."""
    
    time = datetime.now(CDT)
    current_time = time.strftime('%H:%M')
    context = {
        'current_time': current_time,
        'user': request.user
    }
    return render(request, 'app/index.html', context)

def time_view(request):
    """Returns current Central time formatted as HH:MM."""
    time = datetime.now(CDT)
    ct_formatted = time.strftime('%H:%M')
    return HttpResponse(ct_formatted)

def sum_view(request):
    """Reads query parameters, converts them to a #, returns response"""
    first_query = request.GET.get('n1')
    second_query = request.GET.get('n2')
    value = float(first_query) + float(second_query)
    return HttpResponse(f"<p>{value}</p>")
    


# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------

from django.views.decorators.http import require_GET

@require_GET
def new_user(request):
    """Displays a sign-up form to new users"""
    return render(request, 'app/new.html', {}) 

@csrf_exempt
def create_user(request):
    """Creates a new User with a student or instructor profile."""
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST requests are allowed")

    email = request.POST.get('email')
    user_name = request.POST.get('user_name')
    password = request.POST.get('password')
    is_student = request.POST.get('is_student')

    if not (email and user_name and password and is_student):
        return HttpResponseBadRequest("Missing required field(s)")
   
    if User.objects.filter(email=email).exists():
        return HttpResponseBadRequest("Email already registered")
    if User.objects.filter(username=user_name).exists():
        return HttpResponseBadRequest("Username already taken")

    user = User.objects.create_user(username=user_name, email=email, password=password)
    if is_student in ('0', 'instructor'):
        InstructorProfile.objects.create(user=user)
    else:
        StudentProfile.objects.create(user=user)
    
    login(request, user)
    return HttpResponse("New User created.", status=200)
 
# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



