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
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.utils import timezone
from datetime import datetime
import zoneinfo
import json
import io
import uuid
import random
import logging

from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
                      Lecture, QRCodeUpload, getUploadsForCourse,
                      is_instructor, is_student)

CDT = zoneinfo.ZoneInfo("America/Chicago")
logger = logging.getLogger(__name__)

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
    indv_role = request.POST.get('is_student')

    if not (email and user_name and password and indv_role):
        return HttpResponseBadRequest("Missing required field(s)")
   
    if User.objects.filter(email=email).exists():
        return HttpResponseBadRequest("Email already registered")
    if User.objects.filter(username=user_name).exists():
        return HttpResponseBadRequest("Username already taken")

    user = User.objects.create_user(username=user_name, email=email, password=password)
    if indv_role in ('0', 'instructor'):
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
def create_course(request):
    """Creates a new Course row using POST data"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not is_instructor(request.user):
        return HttpResponse("Error: user must be an instructor", status=401)
    
    course_number = (request.POST.get('course-number') or request.POST.get('course') or request.POST.get(course_number') or request.POST.get(course-name))
    course_name = (request.POST.get('course-name') or request.POST.get('course_title') or course_number or "")
    start_time = request.POST.get('start_time') or request.POST.get('start-time') or None
    end_time = request.POST.get('end_time') or request.POST.get('end-time') or None
    
    mon = (request.POST.get('mon') or request.POST.get('day-mon') or '').strip().lower() in ('true', '1', 'on', 'yes')
    tue = (request.POST.get('tue') or request.POST.get('day-tue') or '').strip().lower() in ('true', '1', 'on', 'yes')
    wed = (request.POST.get('wed') or request.POST.get('day-wed') or '').strip().lower() in ('true', '1', 'on', 'yes')
    thu = (request.POST.get('thu') or request.POST.get('day-thu') or '').strip().lower() in ('true', '1', 'on', 'yes')
    fri = (request.POST.get('fri') or request.POST.get('day-fri') or '').strip().lower() in ('true', '1', 'on', 'yes')
    sat = (request.POST.get('sat') or request.POST.get('day-sat') or '').strip().lower() in ('true', '1', 'on', 'yes')
    sun = (request.POST.get('sun') or request.POST.get('day-sun') or '').strip().lower() in ('true', '1', 'on', 'yes')

    day_fields = {'day-mon': 'Mon', 'day-tue': 'Tue', 'day-wed': 'Wed', 'day-thu': 'Thu', 'day-fri': 'Fri'}
    chosen_days = [label for key, label in day_fields.items() if request.POST.get(key)]
    schedule = f"{','.join(chosen_days)} {start_time}-{end_time}".strip()
    
    course_id_generator = random.randint(10000, 99999)
    Course.objects.create(
        course_id=course_id_generator,
        course=course_number,
        course_title=course_name,
        course_schedule=schedule,
        instructor=request.user.instructorprofile,
        mon=mon,
        tue=tue,
        wed=wed,
        thu=thu,
        fri=fri,
        sat=sat,
        sun=sun,
        start_time=start_time,
        end_time=end_time
    )
    
    return HttpResponse("You have successfully created a course.", status=200)

@csrf_exempt
def create_lecture(request):
    """Creates a new lecture linked to a particular course"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not is_instructor(request.user):
        return HttpResponse("Error: User must be an instructor.", status=401)
    
    choice = request.POST.get('choice') or request.POST.get('course') or request.POST.get('course_id')
    course = (Course.objects.filter(course=choice).first() or Course.objects.filter(course_title=choice).first())
    if course is None:
        return HttpResponse("Course does not exist.", status=404)
    
    Lecture.objects.create(
        course_id=course,
        date=timezone.now().date(),
        qr_identifier=str(uuid.uuid4())
    )
    
    return HttpResponse("You have successfully created a new lecture", status=200)

@csrf_exempt
def create_qr_code_upload(request):
    """Create a QRCodeUpload from a student's image upload"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not is_student(request.user):
        return HttpResponse("Error: User must be a student.", status=401)
    
    image_file = request.FILES.get("imageUpload")
    if not image_file:
        return HttpResponse("Error: imageUpload file is missing.", status=400)
    
    lecture = None
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode
        image = Image.open(image_file)
        decoded_img = decode(image)
        if decoded_img:
            qr_data = decoded_img[0].data.decode("utf-8").strip()
            lecture = Lecture.objects.filter(qr_identifier=qr_data).first()
            if lecture is None:
                logger.warning("QR has no assigned lecture: %s", qr_data)
        else:
            logger.warning("Uploaded image doesn't contain a proper QR code")
        image_file.seek(0)
    except Exception as e:
        logger.warning("QR decode was unsuccessful: %s", e)
        try:
            image_file.seek(0)
        except Exception:
            pass

    QRCodeUpload.objects.create(
        qrcode_id=str(uuid.uuid4()),
        student_id=request.user.studentprofile,
        lecture_id=lecture,
        picture=image_file
    )
    return HttpResponse("Your QR code has been successfully uploaded.", status=200)

@require_GET
def dump_uploads(request):
    """Returns a JSON list of QR code uploads"""
    if request.method != 'GET':
        return HttpResponse(status=405)
    valid_instructor = request.user.is_authenticated and hasattr(request.user, 'instructorprofile')
    if not valid_instructor:
        return HttpResponse("Error: You are not a verified instructor.", status=401)
    
    uploads = QRCodeUpload.objects.select_related('student_id__user').all()
    data = [
        {
            "username": upload.student_id.user.username,
            "upload_time": upload.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for upload in uploads
    ]
    return JsonResponse(data, safe=False)
    
# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------

@require_GET
def getUploads(request):
    """Returns JSON list of valid QR code uploads for a course"""
    if not is_instructor(request.user):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    course = request.GET.get("course")
    if not course:
        return JsonResponse({"error": "Missing course parameter"}, status=400)
    
    upload_info = []
    for upload in getUploadsForCourse(course):
        time_stamp = upload.uploaded_at
        if time_stamp and timezone.is_aware(time_stamp):
            time_stamp = timezone.localtime(time_stamp, CDT)
        student_user = upload.student_id.user
        upload_info.append({
            "username": student_user.username if student_user else None,
            "upload_time": time_stamp.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return JsonResponse(upload_info, safe=False)



