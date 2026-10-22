"""
The LLM I used: Claude
My Prompt:
Build a Python Django models.py for an AttendanceChimp app involving relational databases. The AttendanceChimp app tracks attendance using QR codes with the different roles of users including instructors and students (each representing a distinct table). For courses, each course involves one instructor while students can also be enrolled in multiple classes. For the lectures table, individual class meetings occur regularly and each is associated with a specific course. And for QR code uploads, photos are uploaded by students with each upload connecting a specific student to a particular lecture.
For context, the Entity Relationship diagram for this schema involves separate InstructorProfile and StudentProfile tables that have relevant associated attributes. The Course table has a name, instructor, and meeting schedule as attributes. The Enrollment table links students to their courses (a many to many relationship). At the same time, the Lecture table is linked to a course, contains a date, as well as a QR identifier. And lastly, the QR codeUpload table is linked to a student and optionally a lecture. For the attendancechimp/app/models.py directory, write an explanatory docstring and helper functions if necessary to define Django Model classes for each of the aforementioned tables that are relevant for implementation of the AttendanceChimp app. 
"""

"""
AttendanceChimp Application Data Models

This module defines the relational database schema for AttendanceChimp, 
an automated attendance-tracking system using QR codes.

Schema Relationships:
- User Roles: Uses separate InstructorProfile and StudentProfile models linked 
  one-to-one with Django's built-in User model.
- Course: Managed by one Instructor; enrolled by many Students through 
  an explicit Enrollment join table.
- Lecture: Specific class sessions belonging to a Course, carrying 
  meeting dates and unique QR identifiers.
- QRCodeUpload: Tracks student submission of QR photos linked to a 
  StudentProfile and (optionally) a specific Lecture.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class InstructorProfile(models.Model):
    """
    Profile table representing an instructor user in AttendanceChimp.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="instructor_profile"
    )
    department = models.CharField(max_length=100, blank=True)
    office_location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Prof. {self.user.get_full_name() or self.user.username}"


class StudentProfile(models.Model):
    """
    Profile table representing a student user in AttendanceChimp.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="student_profile"
    )
    student_id_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.student_id_number})"

    def get_enrolled_courses(self):
        """Helper function to retrieve all courses the student is active in."""
        return Course.objects.filter(
            enrollments__student=self, 
            enrollments__is_active=True
        )


class Course(models.Model):
    """
    Represents an academic course taught by a single instructor.
    """
    name = models.CharField(max_length=200)
    course_code = models.CharField(max_length=20, unique=True)
    meeting_schedule = models.CharField(
        max_length=250, 
        help_text="e.g., 'MWF 10:30 AM - 11:20 AM in Ryerson 251'"
    )
    instructor = models.ForeignKey(
        InstructorProfile, 
        on_delete=models.CASCADE, 
        related_name="courses"
    )
    students = models.ManyToManyField(
        StudentProfile, 
        through="Enrollment", 
        related_name="courses"
    )

    def __str__(self):
        return f"{self.course_code}: {self.name}"


class Enrollment(models.Model):
    """
    Explicit join table mapping Students to Courses (Many-to-Many).
    Tracks active enrollment status and join date.
    """
    student = models.ForeignKey(
        StudentProfile, 
        on_delete=models.CASCADE, 
        related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name="enrollments"
    )
    date_enrolled = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "course")
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.student} in {self.course}"


class Lecture(models.Model):
    """
    Represents an individual class session for a specific Course, 
    associated with a unique QR code identifier for attendance verification.
    """
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name="lectures"
    )
    date = models.DateTimeField(default=timezone.now)
    qr_identifier = models.CharField(
        max_length=255, 
        unique=True, 
        help_text="Unique token or string encoded within the generated QR code"
    )

    def __str__(self):
        return f"{self.course.course_code} - Session on {self.date.strftime('%Y-%m-%d %H:%M')}"

    def total_attendance(self):
        """Helper function returning count of distinct student uploads for this lecture."""
        return self.qr_uploads.values("student").distinct().count()


class QRCodeUpload(models.Model):
    """
    Represents a QR code image upload submitted by a student.
    Optionally links to a specific Lecture once matched/verified.
    """
    student = models.ForeignKey(
        StudentProfile, 
        on_delete=models.CASCADE, 
        related_name="qr_uploads"
    )
    lecture = models.ForeignKey(
        Lecture, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="qr_uploads",
        help_text="Associated lecture once QR code processing succeeds"
    )
    photo = models.ImageField(upload_to="qr_scans/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(
        default=False, 
        help_text="True if the uploaded image matches a valid lecture QR identifier"
    )

    def __str__(self):
        status = "Verified" if self.is_verified else "Pending/Unmatched"
        return f"Upload #{self.id} by {self.student} ({status})"
