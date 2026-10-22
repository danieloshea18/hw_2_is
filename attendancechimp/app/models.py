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

import logging
import string
import random

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------

class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    instructor_id = models.IntegerField(primary_key=True)
    last_name = models.CharField(max_length=256, null=False)
    first_name = models.CharField(max_length=256, null=False)
    department = models.CharField(max_length=256, null=False)
    email = models.CharField(max_length=25, null=False)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.IntegerField(primary_key=True)
    last_name = models.CharField(max_length=256, null=False)
    first_name = models.CharField(max_length=256, null=False)
    email = models.CharField(max_length=256, null=False)

# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class Course(models.Model):
    course_id = models.IntegerField(primary_key=True)
    course_title = models.CharField(max_length=256, null=False)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE)
    course_schedule = models.CharField(max_length=256, null=False)

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
    picture = models.ImageField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------



