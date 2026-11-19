"""
models.py — Data model for AttendanceChimp.

AttendanceChimp is an electronic class attendance tool.  Instructors create
courses and lectures; each lecture is assigned a random QR code.  Students
photograph the QR code and upload the image.  The system decodes the QR code,
matches it to a lecture, and records the attendance.

Entities
--------
- InstructorProfile  : extends Django User → instructor-specific data
- StudentProfile     : extends Django User → student-specific data
- Course             : a course taught by one instructor
- Enrollment         : junction table linking students to courses
- Lecture            : a single class meeting (has a QR-code identifier)
- QRCodeUpload       : a student's uploaded QR-code photograph
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, time

import logging
import string
import random
import zoneinfo

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 

chicago_time = zoneinfo.ZoneInfo("America/Chicago")

# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------

class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    instructor_id = models.IntegerField(primary_key=True)
    last_name = models.CharField(max_length=256, null=False)
    first_name = models.CharField(max_length=256, null=False)
    department = models.CharField(max_length=256, null=False)
    email = models.CharField(max_length=25, null=False)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    student_id = models.IntegerField(primary_key=True)
    last_name = models.CharField(max_length=256, null=False)
    first_name = models.CharField(max_length=256, null=False)
    email = models.CharField(max_length=256, null=False)

# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class Course(models.Model):
    course_id = models.IntegerField(primary_key=True)
    course = models.CharField(max_length=65, unique=True, null=True, blank=True)
    course_title = models.CharField(max_length=256, null=False)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE)
    course_schedule = models.CharField(max_length=256, null=False)
    
    sun = models.BooleanField(default=False)
    mon = models.BooleanField(default=False)
    tue = models.BooleanField(default=False)
    wed = models.BooleanField(default=False)
    thu = models.BooleanField(default=False)
    fri = models.BooleanField(default=False)
    sat = models.BooleanField(default=False)
    
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    def meets_on_day(self, weekday):
        """Checks if a course meets on a particular day of the week"""
        days = [self.mon, self.tue, self.wed, self.thu, self.fri, self.sat, self.sun]
        return days[weekday]    

# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class Enrollment(models.Model):
    student_id = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)

# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

class Lecture(models.Model):
    lecture_id = models.IntegerField(primary_key=True)
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField(null=False)
    qr_identifier = models.CharField(max_length=256, null=False, unique=True)
    
# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------

class QRCodeUpload(models.Model):
    qrcode_id = models.CharField(max_length=256, primary_key=True)
    student_id = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    lecture_id = models.ForeignKey(Lecture, on_delete=models.CASCADE, null=True, blank=True)
    picture = models.ImageField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------

def is_instructor(user):
    """Checks if a user is an instructor"""
    if user.is_authenticated and InstructorProfile.objects.filter(user=user).exists():
        return True
    return False
def is_student(user):
    """Checks if a user is a student"""
    if user.is_authenticated and StudentProfile.objects.filter(user=user).exists():
        return True
    return False

def getUploadsForCourse(course):
    """Retrieves all valid QRCodeUpload objects related to a specific course"""
    try:
        course_info = Course.objects.get(course=course)
    except Course.DoesNotExist:
        return []
    
    if not course_info.start_time or not course_info.end_time:
        return []
    
    def time_conversion(value):
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            return datetime.strptime(value.strip(), "%H:%M").time()
        else:
            return None
    
    course_start = time_conversion(course_info.start_time)
    course_end = time_conversion(course_info.end_time)
    uploads = QRCodeUpload.objects.filter(lecture_id__course_id=course_info)
    valid_uploads = []
    
    for upload in uploads:
        time_stamp = upload.uploaded_at
        if not time_stamp:
            continue
        if timezone.is_aware(time_stamp):
            time_stamp = timezone.localtime(time_stamp, chicago_time)
        if not course_info.meets_on_day(time_stamp.weekday()):
            continue
        upload_time = time_stamp.time()
        if course_start <= upload_time <= course_end:
            valid_uploads.append(upload)
    return valid_uploads
