from django.db import models
from Manager.models import Country, State, City, Taluka, Village, VerificationDocument, Category

# -----------------------------
# User Registration Model
# -----------------------------
class UserRegistration(models.Model):
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    surname = models.CharField(max_length=100)
    dob = models.DateField()

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    taluka = models.ForeignKey(Taluka, on_delete=models.SET_NULL, null=True, blank=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True, blank=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True)

    mobile = models.CharField(max_length=15)
    insta_id = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()
    firm_name = models.CharField(max_length=200, blank=True, null=True)
    firm_address = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_freelancer = models.BooleanField(default=False)

    PROFILE_STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('verified', 'Verified'),
    ]
    profile_status = models.CharField(max_length=20, choices=PROFILE_STATUS_CHOICES, default='unverified')

    def __str__(self):
        return f"{self.first_name} {self.surname} ({self.email})"


# -----------------------------
# User Verification Model
# -----------------------------
class UserVerification(models.Model):
    STATUS_CHOICES = [
        ("unverified", "Unverified"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    document = models.ForeignKey(VerificationDocument, on_delete=models.CASCADE)
    front_image = models.ImageField(upload_to="verification_docs/front/")
    back_image = models.ImageField(upload_to="verification_docs/back/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unverified")

    def __str__(self):
        return f"{self.user.email} - {self.document.name} ({self.status})"


# -----------------------------
# Skill Model
# -----------------------------
class Skill(models.Model):
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='skills')
    category = models.ForeignKey(
    Category,
    on_delete=models.CASCADE,
    related_name='skills',
    limit_choices_to={'parent__name': 'Freelancer'},
    null=True,  # temporary
    blank=True
)
    rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Enter rate per event/day")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.category.name} (₹{self.rate})"



class ChatMessage(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(
        UserRegistration, on_delete=models.CASCADE, related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        UserRegistration, on_delete=models.CASCADE, related_name='received_messages'
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']


from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
class GalleryItem(models.Model):
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='gallery_items')
    media = models.FileField(upload_to='gallery_media/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gallery item by {self.user.first_name} at {self.uploaded_at}"


class Brand(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ProductModel(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.brand.name} {self.name}"

class ProductItem(models.Model):
    TYPE_CHOICES = (
        ('sell', 'Sell'),
        ('rent', 'Rent'),
        ('resell', 'Resell'),
    )

    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    product_model = models.ForeignKey(ProductModel, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    price = models.IntegerField(null=True, blank=True)
    rent_per_day = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(ProductItem, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/")




class Booking(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
    ]

    freelancer = models.ForeignKey(
        'UserRegistration', 
        on_delete=models.CASCADE, 
        related_name='freelancer_bookings'
    )
    skill = models.ForeignKey('Skill', on_delete=models.CASCADE)
    client = models.ForeignKey(
        'UserRegistration', 
        on_delete=models.CASCADE, 
        related_name='client_bookings'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255, default='Not specified', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='booked')
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)  # optional description field


    cancel_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.client} booked {self.freelancer} from {self.start_date} to {self.end_date}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'


from django.db import models
from django.utils import timezone
from Mainproject.models import ProductItem, UserRegistration

from datetime import timedelta

class ProductBooking(models.Model):
    product = models.ForeignKey(ProductItem, on_delete=models.CASCADE, related_name='rent_bookings')
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Booking'
        verbose_name_plural = 'Product Bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.title} booked by {self.user.first_name} from {self.start_date} to {self.end_date}"

    def overlaps(self, start, end):
        """Check if this booking overlaps with a given date range"""
        return self.start_date <= end and start <= self.end_date

    # -------------------------------
    # NEW: Total Days Calculation
    # -------------------------------
    def total_days(self):
        """How many days booked"""
        return (self.end_date - self.start_date).days + 1   # inclusive

    # -------------------------------
    # NEW: Total Rent Amount
    # -------------------------------
    def total_bill(self):
        """Total rent = days * rent_per_day"""
        if self.product.rent_per_day:
            return self.total_days() * self.product.rent_per_day
        return 0