from django import forms
from .models import UserRegistration,UserVerification,ProductItem
from .models import Skill
from Manager.models import  Category

class RegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = UserRegistration
        fields = [
            "first_name", "middle_name", "surname", "dob", "city", "mobile", 
            "insta_id", "address", "firm_name", "firm_address", "email", "password"
        ]
        widgets = {
            "password": forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

from Manager.models import VerificationDocument

class VerificationDocumentForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document Name'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
        }

class UserVerificationForm(forms.ModelForm):
    class Meta:
        model = UserVerification
        fields = ["document", "front_image", "back_image"]


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['category', 'rate']  # <-- use 'category' instead of 'skill_name'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get the main "Freelancer" category
        try:
            freelancer_category = Category.objects.get(name="Freelancer", parent__isnull=True)
            # Get all subcategories of Freelancer
            subcategories = freelancer_category.subcategories.all()
            # Set queryset for the ForeignKey dropdown
            self.fields['category'].queryset = subcategories
            self.fields['category'].label = "Skill / Category"
        except Category.DoesNotExist:
            self.fields['category'].queryset = Category.objects.none()


from django.forms.widgets import ClearableFileInput

class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None:
            attrs = {}
        attrs['multiple'] = True
        
        self.attrs = attrs

class GalleryUploadForm(forms.Form):
    media = forms.FileField(
        widget=MultiFileInput(),
        required=True,
    )
