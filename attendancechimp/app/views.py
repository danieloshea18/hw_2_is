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

@login_required
def new_course(request):
    """Renders form for course creation"""
    return render(request, "app/new_course.html")

@login_required
def new_lecture(request):
    """Renders form for creating a lecture"""
    return render(request, 'app/new_lecture.html')

@login_required
def new_qr_upload(request):
    """Renders form for uploading a QR code"""
    return render(request, "app/new_qr_upload.html")

@csrf_exempt
def createCourse(request):
    """Creates a new Course row using POST data"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not request.user.is_authenticated or not InstructorProfile.objects.filter(user=request.user).exists():
        return HttpResponse("Error: user must be an instructor", status=401)
    
    course_name = request.POST.get('course-name')
    start_time = request.POST.get('start-time')
    end_time = request.POST.get('end-time')
    
    day_fields = {'day-mon': 'Mon', 'day-tue': 'Tue', 'day-wed': 'Wed', 'day-thu': 'Thu', 'day-fri': 'Fri'}
    chosen_days = [value for key, value in day_fields.items() if request.POST.get(key)]
    
    course = Course.objects.create(name=course_name, start_time=start_time, end_time=end_time, days=",".join(chosen_days), instructor=request.user.instructorprofile)
    
    return HttpResponse("You have successfully created a course.", status=200)

@csrf_exempt
def create_lecture(request):
    """Creates a new lecture linked to a particular course"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not request.user.is_authenticated or not InstructorProfile.objects.filter(user=request.user).exists():
        return HttpResponse("Error: User must be an instructor.", status=401)
    
    course_name = request.POST.get('choice')
    try:
        course = Course.objects.get(name=course_name)
    except Course.DoesNotExist:
        return HttpResponse("Course does not exist.", status=404)
    
    Lecture.objects.create(course=course)
    return HttpResponse("You have successfully created a new lecture", status=200)

@csrf_exempt
def create_qr_code_upload(request):
    """Create a QRCodeUpload from a student's image upload"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not request.user.is_authenticated or not StudentProfile.objects.filter(user=request.user).exists():
        return HttpResponse("Error: User must be a student.", status=401)
    
    image = request.FILES.get("imageUpload")
    if not image:
        return HttpResponse("Error: imageUpload file is missing.", status=400)

    QRCodeUpload.objects.create(student=request.user.studentprofile, image=image, upload_time=timezone.now())
    return HttpResponse("Your QR code has been successfully uploaded.", status=200)

@require_GET
def dumpUploads(request):
    """Returns a JSON list of QR code uploads"""
    if request.method != 'GET':
        return HttpResponse(status=405)
    valid_instructor = request.user.is_authenticated and hasattr(request.user, 'instructorprofile')
    if not valid_instructor:
        return HttpResponse("Error: You are not a verified instructor.", status=401)
    
    data = [
        {
            "username": upload.student.username,
            "upload_time": upload.upload_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        for upload in QRCodeUpload.objects.select_related("student")
    ]
    return JsonResponse(data, safe=False)
    
# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



