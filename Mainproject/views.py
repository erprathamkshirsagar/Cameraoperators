from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.gis.geoip2 import GeoIP2
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.http import urlencode
from datetime import datetime, date
import json
import random
import requests
import logging
from django.views import View
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator,EmptyPage
from Mainproject.models import ProductBooking
from django.utils import timezone
from urllib.parse import urlparse
from urllib.parse import parse_qs
from .models import (
    UserRegistration, Skill, Booking, GalleryItem, Category, Brand, 
    ProductModel, ProductItem, ProductImage, 
    UserVerification, ChatMessage,State, City, Taluka, Village,Country
)
from Manager.models import State, City, Taluka, Village,Country
from .forms import SkillForm, UserVerificationForm, GalleryUploadForm
from ipware import get_client_ip
from django.conf import settings


def signup(request):
    if request.method == "POST":

        # -------------------------
        # Personal Details
        # -------------------------
        first_name = request.POST.get("first_name", "").strip()
        middle_name = request.POST.get("middle_name", "").strip()
        surname = request.POST.get("surname", "").strip()
        dob = request.POST.get("dob")

        # -------------------------
        # Location IDs
        # -------------------------
        country_id = request.POST.get("country")
        state_id = request.POST.get("state")
        city_id = request.POST.get("city")
        taluka_id = request.POST.get("taluka")
        village_id = request.POST.get("village")
        pincode = request.POST.get("pincode", "").strip()

        # -------------------------
        # Contact & Firm
        # -------------------------
        mobile = request.POST.get("mobile", "").strip()
        insta_id = request.POST.get("insta_id", "").strip()
        address = request.POST.get("address", "").strip()
        firm_name = request.POST.get("firm_name", "").strip()
        firm_address = request.POST.get("firm_address", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # -------------------------
        # Basic Validation
        # -------------------------
        if not all([first_name, surname, dob, mobile, email, password, confirm_password]):
            messages.error(request, "Please fill all required fields.")
            return redirect("signup")

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("signup")

        if UserRegistration.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        if UserRegistration.objects.filter(mobile=mobile).exists():
            messages.error(request, "Mobile number already registered.")
            return redirect("signup")

        # -------------------------
        # Fetch Location Objects
        # -------------------------
        country = get_object_or_404(Country, id=country_id) if country_id else None
        state = get_object_or_404(State, id=state_id) if state_id else None
        city = get_object_or_404(City, id=city_id) if city_id else None
        taluka = get_object_or_404(Taluka, id=taluka_id) if taluka_id else None
        village = get_object_or_404(Village, id=village_id) if village_id else None

        # -------------------------
        # Save User
        # -------------------------
        UserRegistration.objects.create(
            first_name=first_name,
            middle_name=middle_name,
            surname=surname,
            dob=dob,
            country=country,
            state=state,
            city=city,
            taluka=taluka,
            village=village,
            pincode=pincode,
            mobile=mobile,
            insta_id=insta_id,
            address=address,
            firm_name=firm_name,
            firm_address=firm_address,
            email=email,
            password=make_password(password),
        )

        messages.success(request, "✅ Registration successful! Please login.")
        return redirect("login")

    # -------------------------
    # GET Request
    # -------------------------
    countries = Country.objects.all().order_by("name")
    categories = Category.objects.filter(parent__isnull=True)

    return render(
        request,
        "signup.html",
        {
            "countries": countries,
            "categories": categories,
        },
    )



def load_states(request):
    country_id = request.GET.get('country_id')
    states = State.objects.filter(country_id=country_id).order_by('name')
    return JsonResponse(list(states.values('id', 'name')), safe=False)


def load_cities(request):
    state_id = request.GET.get('state_id')
    cities = City.objects.filter(state_id=state_id).order_by('name')
    return JsonResponse(list(cities.values('id', 'name')), safe=False)

def load_talukas(request):
    city_id = request.GET.get('city_id')
    talukas = Taluka.objects.filter(city_id=city_id).order_by('name')
    return JsonResponse(list(talukas.values('id', 'name')), safe=False)

def load_villages(request):
    taluka_id = request.GET.get('taluka_id')
    villages = Village.objects.filter(taluka_id=taluka_id).order_by('name')
    return JsonResponse(list(villages.values('id', 'name')), safe=False)

def login(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")  # can be email or mobile
        password = request.POST.get("password")

        # Try to find user by email or mobile
        try:
            user = UserRegistration.objects.get(email=identifier)
        except UserRegistration.DoesNotExist:
            try:
                user = UserRegistration.objects.get(mobile=identifier)
            except UserRegistration.DoesNotExist:
                user = None

        if user and check_password(password, user.password):
            # ✅ Success
            request.session["user_id"] = user.id  # store session
            request.session["user_name"] = user.first_name
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect("dashboard")  # redirect to a dashboard/home
        else:
            messages.error(request, "Invalid credentials. Please try again.")
            return redirect("login")
    categories = Category.objects.filter(parent__isnull=True)  # main categories

    return render(request,'login.html', {
        "user_name": request.session.get("user_name"),
        "categories": categories
    })
from django.core.paginator import Paginator
from django.core.paginator import Paginator
from django.db.models.functions import Random
from django.db.models import Q
def dashboard(request):
    selected_category = request.GET.get('category')
    product_type = request.GET.get('type', 'all')

    # ---------------- Categories ----------------
    categories = Category.objects.filter(parent__isnull=True)
    product_parent = Category.objects.filter(name="Products").first()
    product_categories = (
        Category.objects.filter(parent=product_parent) if product_parent else Category.objects.none()
    )

    # Define mandatory categories by their names (exact match)
    mandatory_names = ['Camera', 'Light', 'Flash', 'Battery', 'Are The Fix']

    # Query mandatory categories (filter by name)
    mandatory_categories = product_categories.filter(name__in=mandatory_names)

    # Remaining categories excluding mandatory ones
    other_categories = product_categories.exclude(name__in=mandatory_names)

    # Slice other categories to show only first N (e.g. 5)
    sliced_other_categories = other_categories[:5]

    # Combine mandatory + sliced other categories
    # Use `list()` to force evaluation before combining QuerySets and Lists
    final_categories = list(mandatory_categories) + list(sliced_other_categories)

    # If you want to keep original order, sort or reorder here
    # For example, order mandatory categories by your manual list order:
    mandatory_order_map = {name: i for i, name in enumerate(mandatory_names)}
    final_categories.sort(key=lambda c: mandatory_order_map.get(c.name, 1000))

    # ---------------- Base Products ----------------
    base_products = ProductItem.objects.all()

    # ---------------- Products by type (no category filter here) ----------------
    sell_products_qs = ProductItem.objects.filter(type='sell').order_by(Random())
    rent_products_qs = ProductItem.objects.filter(type='rent').order_by(Random())
    resell_products_qs = ProductItem.objects.filter(type='resell').order_by(Random())

    # ---------------- All products (apply category filter if selected) ----------------
    all_products_qs = base_products.order_by(Random())
    if selected_category:
        all_products_qs = all_products_qs.filter(product_model__brand__category_id=selected_category)

    # ---------------- Pagination ----------------
    page_number = request.GET.get('page')

    sell_paginator = Paginator(sell_products_qs, 12)
    rent_paginator = Paginator(rent_products_qs, 12)
    resell_paginator = Paginator(resell_products_qs, 12)
    all_paginator = Paginator(all_products_qs, 12)

    sell_page_obj = sell_paginator.get_page(page_number)
    rent_page_obj = rent_paginator.get_page(page_number)
    resell_page_obj = resell_paginator.get_page(page_number)
    all_page_obj = all_paginator.get_page(page_number)

    # ---------------- Chunk list helper ----------------
    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    sell_chunks = list(chunk_list(list(sell_page_obj), 3))
    rent_chunks = list(chunk_list(list(rent_page_obj), 3))
    resell_chunks = list(chunk_list(list(resell_page_obj), 3))
    all_chunks = list(chunk_list(list(all_page_obj), 3))

    # ---------------- Freelancers ----------------
    freelancers_qs = (
        UserRegistration.objects
        .filter(profile_status="verified")
        .exclude(Q(profile_image__isnull=True) | Q(profile_image=''))
        .prefetch_related('skills', 'skills__category')
        .order_by(Random())
    )

    freelancers = []
    for f in freelancers_qs:
        skill = f.skills.order_by('-rate').first()
        if not skill:
            continue
        freelancers.append({
            'id': f.id,
            'name': f"{f.first_name} {f.surname}",
            'skill': skill.category.name if skill.category else skill.name,
            'rate': skill.rate or 0,
            'image': f.profile_image.url,
        })

    freelancer_chunks = list(chunk_list(freelancers, 3))

    # ---------------- Header Data ----------------
    header_data = get_header_data(request)

    # ---------------- Context ----------------
    context = {
        'sell_chunks': sell_chunks,
        'rent_chunks': rent_chunks,
        'resell_chunks': resell_chunks,
        'all_chunks': all_chunks,
        'freelancer_chunks': freelancer_chunks,
        'categories': categories,
        'product_categories': final_categories,  # Pass final combined categories here
        'selected_category': selected_category,
        'product_type': product_type,
    }
    context.update(header_data)

    return render(request, "index.html", context)


from django.db.models import Q
from django.core.paginator import Paginator

def search_results(request):
    
    return render(request, 'search_results.html', {    })

def search_suggestions(request):
    """
    Handles live search suggestions with Images.
    """
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    results = []
    
    # Define fallback images (Change these paths to match your actual static files)
    DEFAULT_PRODUCT_IMG = '/static/img/default-product.png' 
    DEFAULT_USER_IMG = '/static/img/default-user.png'

    if len(query) < 2:
        return JsonResponse({'results': []})

    # --- Search Products ---
    if search_type in ['product', 'all']:
        # Added prefetch_related('images') to avoid N+1 queries
        products = ProductItem.objects.filter(
            Q(title__icontains=query) | 
            Q(product_model__name__icontains=query) |
            Q(product_model__brand__name__icontains=query)
        ).select_related('product_model', 'product_model__brand').prefetch_related('images')[:5]

        for p in products:
            # Get first image if available
            img_obj = p.images.first()
            image_url = img_obj.image.url if img_obj and img_obj.image else DEFAULT_PRODUCT_IMG

            results.append({
                'category': 'Product',
                'name': p.title,
                'sub_text': f"{p.product_model.brand.name} - ₹{p.price}",
                'image': image_url,  # <--- Added Image
                'url': reverse('product_detail', args=[p.id])
            })

    # --- Search Freelancers ---
    if search_type in ['freelancer', 'all']:
        freelancers = UserRegistration.objects.filter(
            profile_status="verified"
        ).filter(
            Q(first_name__icontains=query) | 
            Q(surname__icontains=query) |
            Q(skills__category__name__icontains=query)
        ).distinct()[:5]

    for f in freelancers:
        # ❌ Must have profile image
        if not f.profile_image:
            continue

        # ❌ Must have at least one skill
        skill_obj = f.skills.first()
        if not skill_obj:
            continue

        # ✅ Skill name
        if hasattr(skill_obj, 'category') and skill_obj.category:
            top_skill = skill_obj.category.name
        elif hasattr(skill_obj, 'name'):
            top_skill = skill_obj.name
        else:
            continue  # invalid skill

        results.append({
            'category': 'Freelancer',
            'name': f"{f.first_name} {f.surname}",
            'sub_text': top_skill,
            'image': f.profile_image.url,  # always exists now
            'url': reverse('freelancer_profile', args=[f.id]),
        })


    return JsonResponse({'results': results})


def profile(request):
    if "user_id" not in request.session:
        messages.error(request, "Please login first.")
        return redirect("login")

    user = get_object_or_404(UserRegistration, id=request.session["user_id"])

    # ✅ COMMON HEADER DATA
    context = get_header_data(request)

    # Page-specific data
    context.update({
        "user": user,
        "countries": Country.objects.all(),
        "states": State.objects.all(),
        "cities": City.objects.all(),
        "talukas": Taluka.objects.all(),
        "villages": Village.objects.all(),
    })

    if request.method == "POST":
        # Basic Info
        user.first_name = request.POST.get("first_name", "").strip()
        user.middle_name = request.POST.get("middle_name", "").strip()
        user.surname = request.POST.get("surname", "").strip()
        user.insta_id = request.POST.get("insta_id", "").strip()
        user.address = request.POST.get("address", "").strip()
        user.firm_name = request.POST.get("firm_name", "").strip()
        user.firm_address = request.POST.get("firm_address", "").strip()

        # Profile Image
        if "profile_image" in request.FILES:
            user.profile_image = request.FILES["profile_image"]

        # Date of Birth
        dob_input = request.POST.get("dob", "").strip()
        if dob_input:
            try:
                user.dob = datetime.strptime(dob_input, "%d-%m-%Y").date()
            except ValueError:
                messages.error(request, "Invalid date format. Use DD-MM-YYYY.")
                return redirect("profile")

        # Safe Foreign Keys
        def get_fk(model, key):
            _id = request.POST.get(key)
            return model.objects.get(id=_id) if _id else None

        user.country = get_fk(Country, "country")
        user.state = get_fk(State, "state")
        user.city = get_fk(City, "city")
        user.taluka = get_fk(Taluka, "taluka")
        user.village = get_fk(Village, "village")

        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    # Display DOB
    user.dob_display = user.dob.strftime("%d-%m-%Y") if user.dob else ""

    return render(request, "profile.html", context)
def documentverification(request):
    # -------------------------------
    # Authentication check
    # -------------------------------
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    user = get_object_or_404(UserRegistration, id=user_id)

    # -------------------------------
    # Check existing documents
    # -------------------------------
    user_docs = UserVerification.objects.filter(user=user)
    already_uploaded = user_docs.exists()

    # -------------------------------
    # Categories (header/sidebar)
    # -------------------------------
    categories = Category.objects.filter(parent__isnull=True)

    # -------------------------------
    # Handle POST
    # -------------------------------
    if request.method == "POST":

        if already_uploaded:
            messages.warning(request, "Documents already uploaded. Please wait for verification.")
            return redirect("documentverification")

        form = UserVerificationForm(request.POST, request.FILES)

        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = user
            verification.status = "pending"  # ✅ explicit
            verification.save()

            messages.success(request, "✅ Documents uploaded successfully. Verification pending.")
            return redirect("documentverification")
        else:
            messages.error(request, "❌ Please correct the errors below.")

    else:
        form = UserVerificationForm()

    # -------------------------------
    # Header / Common Context
    # -------------------------------
    context = get_header_data(request)

    context.update({
        "user_name": user.first_name,
        "categories": categories,
        "form": form,
        "user_docs": user_docs,
        "already_uploaded": already_uploaded,
    })

    return render(request, "documentverification.html", context)

def freelancer(request):
    categories = Category.objects.filter(parent__isnull=True)

    user_id = request.session.get("user_id")
    profile_status = None
    skills = []
    form = SkillForm()

    if user_id:
        from .models import UserRegistration
        user = UserRegistration.objects.filter(id=user_id).first()
        if user:
            profile_status = user.profile_status

        # handle POST — add skill
        if request.method == 'POST':
            form = SkillForm(request.POST)
            if form.is_valid():
                skill = form.save(commit=False)
                skill.user = user  # assign the user instance, not just user_id
                skill.save()
                return redirect('freelancer')

        # show all skills of this user
        skills = Skill.objects.filter(user=user)
        
        # get_header_data returns a dictionary, so get it here
        context = get_header_data(request)
    else:
        context = {}  # if no user_id, empty context

    # add all your data to the context dict
    context.update({
        "user_name": request.session.get("user_name"),
        "categories": categories,
        "profile_status": profile_status,
        "form": form,
        "skills": skills,
    })

    return render(request, 'freelancer.html', context)



def delete_skill(request, skill_id):
    user_id = request.session.get("user_id")
    skill = get_object_or_404(Skill, id=skill_id, user_id=user_id)
    skill.delete()
    return redirect('freelancer')

def detect_city_from_request(request):
    ip, is_routable = get_client_ip(request)
    if not ip or ip.startswith("127.") or ip == "::1":
        # fallback IP for testing
        ip = "8.8.8.8"
    
    try:
        g = GeoIP2(settings.GEOIP_PATH)
        data = g.city(ip)
        city = data.get("city")
        if city:
            return city
        else:
            # fallback city name
            return "Unknown City"
    except Exception as e:
        print("GeoIP error:", e)
        return None

def freelancerdisplay(request):
    # 1. Subcategories setup
    freelancer_parent = Category.objects.filter(name="Freelancer").first()
    subcategories = Category.objects.filter(parent=freelancer_parent) if freelancer_parent else []

    # 2. User Session setup
    user_id = request.session.get("user_id")
    profile_status = None
    if user_id:
        user = UserRegistration.objects.filter(id=user_id).first()
        profile_status = user.profile_status if user else None

    # 3. Get filters from URL
    selected_category = request.GET.get("category", None)
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    selected_country = request.GET.get("country")
    selected_state = request.GET.get("state")
    selected_city = request.GET.get("city")
    selected_taluka = request.GET.get("taluka")
    selected_village = request.GET.get("village")
    
    # Get Search Query
    search_query = request.GET.get('q', '')

    # 4. Location Detection (if no location filters set)
    if not any([selected_country, selected_state, selected_city, selected_taluka, selected_village]):
        detected_city_name = detect_city_from_request(request) # Ensure this function is imported or defined
        if detected_city_name:
            city_obj = City.objects.filter(name__icontains=detected_city_name).first()
            if city_obj:
                request.session["current_city_id"] = city_obj.id

    # =========================================================
    # 5. BASE QUERY (Must be defined BEFORE applying search)
    # =========================================================
    freelancers = UserRegistration.objects.filter(profile_status="verified").annotate(
        skill_count=Count("skills")
    ).filter(skill_count__gt=0).prefetch_related("skills")

    # Exclude current user
    if user_id:
        freelancers = freelancers.exclude(id=user_id)

    # =========================================================
    # 6. APPLY SEARCH QUERY (Fixed Order & Field Name)
    # =========================================================
    if search_query:
        freelancers = freelancers.filter(
            Q(first_name__icontains=search_query) | 
            Q(surname__icontains=search_query) |  # <--- FIXED: used 'surname'
            Q(skills__name__icontains=search_query)
        ).distinct()

    # 7. Apply Skill Filters
    filter_applied = False
    skill_filter = Q()

    if selected_category:
        skill_filter &= Q(skills__category__id=selected_category)
        filter_applied = True
    if min_price:
        skill_filter &= Q(skills__rate__gte=min_price)
        filter_applied = True
    if max_price:
        skill_filter &= Q(skills__rate__lte=max_price)
        filter_applied = True
    
    freelancers = freelancers.filter(skill_filter)

    # 8. Apply Location Filters
    location_selected = any([selected_country, selected_state, selected_city, selected_taluka, selected_village])
    location_filter = Q()

    if location_selected:
        if selected_country:
            location_filter &= Q(country_id=selected_country)
        if selected_state:
            location_filter &= Q(state_id=selected_state)
        if selected_city:
            location_filter &= Q(city_id=selected_city)
        if selected_taluka:
            location_filter &= Q(taluka_id=selected_taluka)
        if selected_village:
            location_filter &= Q(village_id=selected_village)
    else:
        # Use detected location stored in session
        current_city = request.session.get("current_city_id")
        current_taluka = request.session.get("current_taluka_id")
        current_village = request.session.get("current_village_id")

        if current_village:
            location_filter &= Q(village_id=current_village)
        elif current_taluka:
            location_filter &= Q(taluka_id=current_taluka)
        elif current_city:
            location_filter &= Q(city_id=current_city)

    freelancers = freelancers.filter(location_filter).distinct()

    # 9. Randomize (Only if no specific search/filter)
    if not search_query and not filter_applied and not location_selected:
        freelancers = list(freelancers)
        random.shuffle(freelancers)

    # 10. Context Preparation
    current_city_name = None
    current_city_id = request.session.get("current_city_id")
    if current_city_id:
        city_obj = City.objects.filter(id=current_city_id).first()
        if city_obj:
            current_city_name = city_obj.name

    header_data = get_header_data(request) # Ensure this function is imported or defined

    context = {
        "freelancers": freelancers,
        "categories": Category.objects.filter(parent__isnull=True),
        "subcategories": subcategories,
        "selected_category": int(selected_category) if selected_category else None,
        "user_name": request.session.get("user_name"),
        "profile_status": profile_status,
        "min_price": min_price or "",
        "max_price": max_price or "",
        "countries": Country.objects.all(),
        "states": State.objects.all(),
        "cities": City.objects.all(),
        "talukas": Taluka.objects.all(),
        "villages": Village.objects.all(),
        "selected_country": int(selected_country) if selected_country else "",
        "selected_state": int(selected_state) if selected_state else "",
        "selected_city": int(selected_city) if selected_city else "",
        "selected_taluka": int(selected_taluka) if selected_taluka else "",
        "selected_village": int(selected_village) if selected_village else "",
        "current_city_name": current_city_name,
        "search_query": search_query, # Passed back to template
        "search_type": "freelancer",  # Keeps the dropdown on 'Freelancers'
    }

    context.update(header_data)

    return render(request, "freelancerdisplay.html", context)

@csrf_exempt
def set_user_location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lat = data.get("latitude")
            lng = data.get("longitude")

            if lat is None or lng is None:
                return JsonResponse({"error": "Latitude and longitude required"}, status=400)

            # Use Nominatim API to reverse geocode lat/lng to location data
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "format": "json",
                "lat": lat,
                "lon": lng,
                "zoom": 10,
                "addressdetails": 1,
            }
            response = requests.get(url, params=params, headers={"User-Agent": "MyApp"})
            geo_data = response.json()

            address = geo_data.get("address", {})

            city_name = address.get("city") or address.get("town") or address.get("village")
            taluka_name = address.get("county")  # approximate for taluka/district
            # You can add more address components if your model requires

            # Find matching DB objects
            city_obj = City.objects.filter(name__icontains=city_name).first() if city_name else None
            taluka_obj = Taluka.objects.filter(name__icontains=taluka_name).first() if taluka_name else None

            # Save IDs in session
            if city_obj:
                request.session["current_city_id"] = city_obj.id
            if taluka_obj:
                request.session["current_taluka_id"] = taluka_obj.id

            return JsonResponse({"message": "User location saved", "city": city_name, "taluka": taluka_name})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def get_nearby_freelancers(request):
    city_id = request.GET.get("city_id")
    taluka_id = request.GET.get("taluka_id")
    village_id = request.GET.get("village_id")

    users = UserRegistration.objects.none()

    # Filter by village > taluka > city hierarchy
    if village_id:
        users = UserRegistration.objects.filter(village_id=village_id, is_freelancer=True)
    if not users.exists() and taluka_id:
        users = UserRegistration.objects.filter(taluka_id=taluka_id, is_freelancer=True)
    if not users.exists() and city_id:
        users = UserRegistration.objects.filter(city_id=city_id, is_freelancer=True)

    user_list = [{
        "id": u.id,
        "name": f"{u.first_name} {u.surname}",
        "email": u.email,
        "city": u.city.name if u.city else None,
        "taluka": u.taluka.name if u.taluka else None,
        "village": u.village.name if u.village else None,
    } for u in users]

    return JsonResponse({"freelancers": user_list})


def get_location_ids(request):
    city_name = request.GET.get("city", "").strip()
    taluka_name = request.GET.get("taluka", "").strip()
    village_name = request.GET.get("village", "").strip()

    # Convert "null" strings to empty
    city_name = "" if city_name.lower() == "null" else city_name
    taluka_name = "" if taluka_name.lower() == "null" else taluka_name
    village_name = "" if village_name.lower() == "null" else village_name

    city_obj = City.objects.filter(name__icontains=city_name).first()
    taluka_obj = Taluka.objects.filter(name__icontains=taluka_name).first()
    village_obj = Village.objects.filter(name__icontains=village_name).first()

    return JsonResponse({
        "city_id": city_obj.id if city_obj else None,
        "taluka_id": taluka_obj.id if taluka_obj else None,
        "village_id": village_obj.id if village_obj else None,
    })

def freelancer_profile(request, id):
    # Main categories
    categories = Category.objects.filter(parent__isnull=True)

    # Session user info
    user_id = request.session.get("user_id")
    profile_status = None
    if user_id:
        user = UserRegistration.objects.filter(id=user_id).first()
        if user:
            profile_status = user.profile_status

    # Freelancer details
    freelancer = UserRegistration.objects.get(id=id)

    # Get gallery items for this freelancer
    gallery_items = list(freelancer.gallery_items.all())

    # Mark each gallery item if it's a video based on extension
    video_exts = ['.mp4', '.webm', '.ogg']
    for item in gallery_items:
        filename = item.media.name.lower()  # safer than url
        item.is_video = any(filename.endswith(ext) for ext in video_exts)

    # Optional: Pass active tab if you want tabs working dynamically
    active_tab = request.GET.get('tab', 'overview')

    return render(request, 'freelancer_profile.html', {
        'freelancer': freelancer,
        'user_name': request.session.get("user_name"),
        'categories': categories,
        'profile_status': profile_status,
        'active_tab': active_tab,
        'gallery_items': gallery_items,
    })

logger = logging.getLogger(__name__)

def booking_view(request, freelancer_id, skill_id):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    client_user = get_object_or_404(UserRegistration, id=user_id)
    freelancer = get_object_or_404(UserRegistration, id=freelancer_id)
    skill = get_object_or_404(Skill, id=skill_id, user=freelancer)

    if request.method == 'POST':
        logger.info("Booking POST request received")
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        location = request.POST.get('location')
        description = request.POST.get('description', '').strip()

        if not all([start_date_str, end_date_str, start_time_str, end_time_str, location]):
            messages.error(request, 'Please fill all the required fields.')
            logger.warning("Required fields missing")
            return redirect(request.path)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            messages.error(request, 'Invalid date or time format.')
            logger.warning("Date/time parse error")
            return redirect(request.path)

        if end_date < start_date:
            messages.error(request, 'End date cannot be before start date.')
            logger.warning("End date before start date")
            return redirect(request.path)

        if start_date == end_date and start_time >= end_time:
            messages.error(request, 'End time must be after start time.')
            logger.warning("End time before start time on same day")
            return redirect(request.path)

        conflict_exists = Booking.objects.filter(
            freelancer=freelancer,
            start_date__lte=end_date,
            end_date__gte=start_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if conflict_exists:
            messages.error(request, 'Freelancer is already booked for this time slot.')
            logger.warning("Booking conflict detected")
            return redirect(request.path)

        # Create booking
        booking = Booking.objects.create(
            freelancer=freelancer,
            skill=skill,
            client=client_user,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            location=location,
            description=description,
            status='pending'
        )
        logger.info(f"Booking created with ID {booking.id}")
        service_name = skill.category.name  # this gives the "Photographer" or category name
        price = skill.rate  # decimal number

        price_text = f"₹{price:,.2f}" if price else "-"

        booking_message = (
            "🎉 *New Booking Request Received!* 🎉\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Service:* {service_name} (Price: {price_text})\n"
            f"📅 *Date:* {start_date.strftime('%A, %d %B %Y')} \n"
            f"⏰ *Time:* {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}\n"
            f"📍 *Location:* {location}\n"
            f"📝 *Booking ID:* #{booking.id}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Please confirm your availability. Thank you! 🙌"
        )

        chat_msg = ChatMessage.objects.create(
            sender_id=client_user.id,
            receiver_id=freelancer.id,
            message=booking_message,
            is_read=False
        )
        logger.info(f"Chat message created with ID {chat_msg.id}")

        messages.success(request, 'Booking request sent successfully!')
        return redirect('client_bookings')

    return render(request, 'booking.html', {
        'freelancer': freelancer,
        'skill': skill,
    })


def chat(request):
    # Redirect to login if user not authenticated
    if "user_id" not in request.session:
        return redirect("login")

    user_id = request.session["user_id"]

    # Count all unread chat messages for current user (receiver)
    unread_chat_count = ChatMessage.objects.filter(
        receiver_id=user_id,
        is_read=False
    ).count()

    # Fetch main categories (top-level)
    categories = Category.objects.filter(parent__isnull=True)

    # Get users who have chatted with current user (sent or received messages)
    chat_users_qs = UserRegistration.objects.filter(
        Q(sent_messages__receiver_id=user_id) | Q(received_messages__sender_id=user_id)
    ).exclude(id=user_id).distinct()

    chat_list = []
    for u in chat_users_qs:
        # Last message exchanged between logged-in user and u
        last_msg = ChatMessage.objects.filter(
            Q(sender_id=user_id, receiver_id=u.id) | Q(sender_id=u.id, receiver_id=user_id)
        ).order_by("-timestamp").first()

        # Count unread messages sent by u to logged-in user
        unread_count = ChatMessage.objects.filter(
            sender_id=u.id,
            receiver_id=user_id,
            is_read=False
        ).count()

        chat_list.append({
            "id": u.id,
            "name": f"{u.first_name} {u.surname}".strip(),
            "profile_image": u.profile_image.url if u.profile_image else "/static/img/user.png",
            "last_message": last_msg.message if last_msg else "No messages yet",
            "profile_status": u.profile_status,
            "unread": unread_count,
        })

    return render(request, "chat.html", {
        "categories": categories,
        "user_id": user_id,
        "chat_users": chat_list,
        "open_chat_user_id": None,   # No chat opened initially
        "chat_user_name": "",
        "chat_user_photo": "",
        "profile_status": "",  # No profile status when no chat open
        "last_message": "",
        "unread_chat_count": unread_chat_count,  # Pass total unread count once here
        "user_name": request.session.get("user_name"),
    })


def chat_user(request, user_id):
    # Redirect if user not logged in
    if "user_id" not in request.session:
        return redirect("login")

    current_user_id = request.session["user_id"]
    categories = Category.objects.filter(parent__isnull=True)

    # Fetch the target user
    target = get_object_or_404(UserRegistration, id=user_id)
    full_name = f"{target.first_name} {target.surname}".strip()

    # Get last message exchanged between current user and target
    last_msg = ChatMessage.objects.filter(
        Q(sender_id=current_user_id, receiver_id=user_id) |
        Q(sender_id=user_id, receiver_id=current_user_id)
    ).order_by("-timestamp").first()

    # Count unread messages from target user to current user
    unread_count = ChatMessage.objects.filter(
        sender_id=user_id,
        receiver_id=current_user_id,
        is_read=False
    ).count()

    # Optionally, fetch chat list for sidebar too (optional, can be empty)
    # You can add chat_users list here if needed, else pass empty

    return render(request, "chat.html", {
        "user_id": current_user_id,
        "open_chat_user_id": user_id,
        "chat_user_name": full_name,
        "chat_user_photo": target.profile_image.url if target.profile_image else "/static/img/user.png",
        "profile_status": target.profile_status,
        "last_message": last_msg.message if last_msg else "No messages yet",
        "unread": unread_count,
        "chat_users": [],  # or fetch if you want sidebar populated
        "categories": categories,
        "user_name": request.session.get("user_name"),
    })

@csrf_exempt
def get_messages(request, user_id):
    current = request.session.get("user_id")

    # Mark as READ
    ChatMessage.objects.filter(
        sender_id=user_id,
        receiver_id=current,
        is_read=False
    ).update(is_read=True)

    msgs = ChatMessage.objects.filter(
        Q(sender_id=current, receiver_id=user_id) |
        Q(sender_id=user_id, receiver_id=current)
    ).order_by("timestamp").values("sender_id", "receiver_id", "message", "timestamp")

    return JsonResponse(list(msgs), safe=False)

@csrf_exempt
def send_message(request):
    if request.method == "POST":
        sender_id = request.session.get("user_id")
        receiver_id = request.POST.get("receiver_id")
        message = request.POST.get("message")

        ChatMessage.objects.create(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message
        )

        return JsonResponse({"status": "success"})
def get_chat_users(request):
    current = request.session.get("user_id")

    users = UserRegistration.objects.filter(
        Q(sent_messages__receiver_id=current) |
        Q(received_messages__sender_id=current)
    ).exclude(id=current).distinct()

    data = []
    for u in users:

        last_msg = ChatMessage.objects.filter(
            Q(sender_id=current, receiver_id=u.id) |
            Q(sender_id=u.id, receiver_id=current)
        ).order_by("-timestamp").first()

        unread_count = ChatMessage.objects.filter(
            sender_id=u.id,
            receiver_id=current,
            is_read=False
        ).count()

        data.append({
            "id": u.id,
            "name": f"{u.first_name} {u.surname}".strip(),
            "profile_image": u.profile_image.url if u.profile_image else "/static/img/user.png",
            "last_message": last_msg.message if last_msg else "",
            "unread": unread_count,
        })

    return JsonResponse(data, safe=False)



from geopy.geocoders import Nominatim

def get_city_from_latlng(lat, lng):
    geolocator = Nominatim(user_agent="myapp")
    location = geolocator.reverse((lat, lng), language='en')
    if location and 'city' in location.raw['address']:
        return location.raw['address']['city']
    elif 'town' in location.raw['address']:
        return location.raw['address']['town']
    elif 'village' in location.raw['address']:
        return location.raw['address']['village']
    return None

@csrf_exempt
def set_location(request):
    
    if request.method == "POST":
        data = json.loads(request.body)
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if not latitude or not longitude:
            return JsonResponse({"status": "error", "message": "No coordinates"}, status=400)

        try:
            # Reverse geocoding with OpenStreetMap
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&zoom=10&addressdetails=1"
            headers = {"User-Agent": "DjangoApp"}
            response = requests.get(url, headers=headers)
            geo_data = response.json()

            address = geo_data.get("address", {})
            city_name = address.get("city") or address.get("town") or address.get("village")

            # Match with DB
            city_obj = City.objects.filter(name__iexact=city_name).first()
            taluka_obj = Taluka.objects.filter(name__iexact=city_name).first()
            village_obj = Village.objects.filter(name__iexact=city_name).first()

            # Save detected locations in session
            request.session['current_city_id'] = city_obj.id if city_obj else None
            request.session['current_taluka_id'] = taluka_obj.id if taluka_obj else None
            request.session['current_village_id'] = village_obj.id if village_obj else None

            return JsonResponse({"status": "success", "city": city_name})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "failed"}, status=400)



class AddPostView(View):
    def get(self, request):
        # Show empty form
        return render(request, 'add_post.html')

    def post(self, request):
        # Process submitted form data, files, etc.
        # TODO: handle uploaded photo/video/gallery
        return redirect('somewhere')  # redirect after successful post

def gallery(request):
    # Get the logged-in user ID from session
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    # Get the user object or 404
    user = get_object_or_404(UserRegistration, id=user_id)

    if request.method == 'POST':
        files = request.FILES.getlist('media')

        if not files:
            messages.error(request, "Please select files to upload.")
        else:
            # Validate each file's size and type (optional but recommended)
            video_extensions = ['.mp4', '.webm', '.ogg']
            max_video_size = 200 * 1024 * 1024  # 200 MB
            max_photo_size = 20 * 1024 * 1024   # 20 MB

            for f in files:
                filename = f.name.lower()
                is_video = any(filename.endswith(ext) for ext in video_extensions)

                # Validate file size based on type
                max_size = max_video_size if is_video else max_photo_size
                if f.size > max_size:
                    file_type = "video" if is_video else "photo"
                    messages.error(request, f"{file_type.capitalize()} '{f.name}' exceeds the maximum allowed size of {max_size // (1024*1024)} MB.")
                    return redirect('gallery')

            # Save valid files
            for f in files:
                GalleryItem.objects.create(user=user, media=f)

            messages.success(request, f"{len(files)} file(s) uploaded successfully!")
            return redirect('gallery')

    # Retrieve user's gallery items ordered by latest first
    gallery_items = GalleryItem.objects.filter(user=user).order_by('-uploaded_at')

    # Mark which items are videos (for template display logic)
    video_extensions = ['.mp4', '.webm', '.ogg']
    for item in gallery_items:
        filename = item.media.name.lower()
        item.is_video = any(filename.endswith(ext) for ext in video_extensions)

    # Additional context for rendering the page
    context = get_header_data(request)  # assuming this returns a dict
    categories = Category.objects.filter(parent__isnull=True)  # main categories

    context.update({
        'gallery_items': gallery_items,
        'categories': categories,
    })

    return render(request, 'gallery.html', context)


@require_POST
def gallery_delete(request, pk):
    # Get the item, 404 if not found
    item = get_object_or_404(GalleryItem, pk=pk)

    # Optional: Check ownership/permission, if your app is multi-user
    # Uncomment and customize if needed:
    # if item.user != request.user:
    #     raise PermissionDenied("You don't have permission to delete this item.")

    try:
        # Delete the associated media file from storage (if exists)
        if item.media:
            item.media.delete(save=False)

        # Delete the database record
        item.delete()
        messages.success(request, "Media item deleted successfully.")
    except Exception as e:
        # Log the error if you have logging configured
        # logger.error(f"Error deleting gallery item {pk}: {e}")
        messages.error(request, "Failed to delete the media item. Please try again.")

    # Redirect back to gallery display page or wherever appropriate
    return redirect('gallery')


def freelancer_orders_view(request):
    user_id = request.session.get('user_id')

    # ✅ LOGIN CHECK
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect('login')

    # ✅ CURRENT USER
    owner = get_object_or_404(UserRegistration, id=user_id)

    # ✅ FREELANCER SERVICE BOOKINGS
    bookings = (
        Booking.objects
        .filter(freelancer=owner)
        .select_related("client", "skill")
        .order_by("-start_date", "-start_time")
    )

    # ✅ PRODUCT RENTAL BOOKINGS (OWNER = PRODUCT SELLER)
    product_bookings = (
        ProductBooking.objects
        .filter(product__user=owner)
        .select_related("product", "user")
        .order_by("-created_at")
    )

    # ✅ CONTEXT
    context = {
        "freelancer": owner,
        "owner": owner,
        "bookings": bookings,
        "product_bookings": product_bookings,
        "page_title": "My Orders",
    }

    # ✅ ADD COMMON HEADER DATA
    context.update(get_header_data(request))

    return render(request, "freelancer_orders.html", context)


def cancel_booking(request, booking_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect('login')

    booking = get_object_or_404(Booking, id=booking_id)

    # Only allow correct freelancer
    if booking.freelancer.id != user_id:
        messages.error(request, "You don't have permission to cancel this booking.")
        return redirect('orders')

    if request.method == "POST":
        cancel_reason = request.POST.get("cancel_reason")

        booking.status = "cancelled"
        booking.cancel_reason = cancel_reason
        booking.save()

        # Send notification message to client
        cancel_message = (
            f"⚠️ Booking #{booking.id} has been *cancelled* by the freelancer.\n"
            "Please contact through chat if you have any questions."
        )

        ChatMessage.objects.create(
            sender_id=booking.freelancer.id,
            receiver_id=booking.client.id,
            message=cancel_message,
            is_read=False
        )

        messages.success(request, "Booking cancelled successfully.")
        return redirect('orders')

    return redirect('orders')



@require_POST
def accept_booking(request, booking_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect('login')

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.freelancer.id != user_id:
        messages.error(request, "You don't have permission to accept this booking.")
        return redirect('orders')

    booking.status = 'accepted'
    booking.save()

    # Get freelancer's mobile number - adjust field name as per your UserRegistration model
    freelancer_mobile = getattr(booking.freelancer, 'mobile', None)  # or 'phone_number'

    # Prepare message including mobile number if available
    if freelancer_mobile:
        contact_info = f"\n📞 Freelancer Contact: {freelancer_mobile}"
    else:
        contact_info = ""

    accept_message = (
        f"✅ Booking #{booking.id} has been *accepted* by the freelancer.{contact_info}\n"
        "Looking forward to a great collaboration!"
    )

    ChatMessage.objects.create(
        sender_id=booking.freelancer.id,
        receiver_id=booking.client.id,
        message=accept_message,
        is_read=False
    )

    messages.success(request, "Booking accepted successfully.")
    return redirect('orders')



def client_bookings_view(request):
    user_id = request.session.get("user_id")

    # Check login
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    # Get logged-in user
    client = get_object_or_404(UserRegistration, id=user_id)

    # Get main categories
    categories = Category.objects.filter(parent__isnull=True)

    # Get header context data
    context = get_header_data(request)

    # FREELANCER BOOKINGS
    bookings = (
        Booking.objects
        .filter(client=client)
        .select_related("freelancer", "skill")
        .order_by("-start_date", "-start_time")
    )

    # PRODUCT RENTAL BOOKINGS
    product_bookings = (
        ProductBooking.objects
        .filter(user=client)          # <-- FIELD CORRECT
        .select_related("product")
        .order_by("-created_at")
    )

    # Merge context dictionaries and pass to template
    # context is expected to be a dict, so:
    context.update({
        "client": client,
        "bookings": bookings,
        "product_bookings": product_bookings,
        "categories": categories,
    })

    return render(request, "mybooking.html", context)



def productmanagement(request):
    # --- LOGIN CHECK ---
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    user = get_object_or_404(UserRegistration, id=user_id)

    # --- CATEGORY, BRAND, MODEL DROPDOWNS ---
    # Get main categories (parents with no parent)
    categories = Category.objects.filter(parent__isnull=True)

    # To get product-specific categories under "Products" parent if needed
    product_parent = Category.objects.filter(name="Products").first()
    product_categories = Category.objects.filter(parent=product_parent) if product_parent else []

    selected_category = request.GET.get("category")
    selected_brand = request.GET.get("brand")
    selected_model = request.GET.get("model")
    selected_type = request.GET.get("type")

    brands = Brand.objects.filter(category_id=selected_category) if selected_category else Brand.objects.none()
    models = ProductModel.objects.filter(brand_id=selected_brand) if selected_brand else ProductModel.objects.none()

    # ----------- SAVE PRODUCT ----------
    if request.method == "POST":
        product_model_id = request.POST.get("product_model")
        title = request.POST.get("title")
        type_ = request.POST.get("type")
        price = request.POST.get("price") or None
        rent_per_day = request.POST.get("rent_per_day") or None
        description = request.POST.get("description")

        # Validate required fields here as needed

        product = ProductItem.objects.create(
            user=user,
            product_model_id=product_model_id,
            title=title,
            type=type_,
            price=price,
            rent_per_day=rent_per_day,
            description=description,
        )

        # Save uploaded images
        images = request.FILES.getlist("images")
        for img in images:
            ProductImage.objects.create(product=product, image=img)

        messages.success(request, "Product added successfully!")
        return redirect("productmanagement")

    # ----------- FILTER PRODUCTS ----------
    items = ProductItem.objects.filter(user=user)

    if selected_type:
        items = items.filter(type=selected_type)
    if selected_category:
        items = items.filter(product_model__brand__category_id=selected_category)
    if selected_brand:
        items = items.filter(product_model__brand_id=selected_brand)
    if selected_model:
        items = items.filter(product_model_id=selected_model)

    # Prefetch related images for better performance in template
    items = items.prefetch_related('images')

    # Get header data context
    context = get_header_data(request)

    # Add all variables to context
    context.update({
        "categories": categories,
        "product_categories": product_categories,  # If you want to use it separately in template
        "brands": brands,
        "models": models,
        "items": items,
        "selected_category": selected_category,
        "selected_brand": selected_brand,
        "selected_model": selected_model,
        "selected_type": selected_type,
        "user_name": request.session.get("user_name"),
    })

    return render(request, "productmanagement.html", context)



def delete_product(request, id):
    product = ProductItem.objects.filter(id=id).first()
    if product:
        product.delete()
        messages.success(request, "Product deleted successfully!")
    else:
        messages.error(request, "Product not found!")
    return redirect("productmanagement")


def update_product(request, id):
    product = get_object_or_404(ProductItem, id=id)

    if request.method == "POST":
        # Update fields from POST data
        product.title = request.POST.get("title")
        product.type = request.POST.get("type")
        product.price = request.POST.get("price") or None
        product.rent_per_day = request.POST.get("rent_per_day") or None
        product.description = request.POST.get("description")

        # Save product
        product.save()

        # Images update if any uploaded
        if request.FILES.getlist("images"):
            product.productimage_set.all().delete()
            for img in request.FILES.getlist("images"):
                ProductImage.objects.create(product=product, image=img)

        messages.success(request, "Product updated successfully!")
        return redirect("productmanagement")

    # On GET, render a template with a pre-filled form
    return render(request, "update_product.html", {"product": product})

from django.db.models import Q
def product_display(request):
    # Get filter values from the URL parameters
    selected_type = request.GET.get('type')  # product type (rent, sell, etc.)
    selected_country = request.GET.get('country')
    selected_state = request.GET.get('state')
    selected_city = request.GET.get('city')
    selected_taluka = request.GET.get('taluka')
    selected_village = request.GET.get('village')

    selected_category = request.GET.get('category')
    selected_brand = request.GET.get('brand')
    selected_model = request.GET.get('model')

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('q', '')  # Get search term from query parameter

    # Fetch categories for the filter dropdowns
    categories = Category.objects.filter(parent__isnull=True)
    main_categories = Category.objects.filter(parent__isnull=True)
    product_parent = Category.objects.filter(name="Products").first()
    product_categories = Category.objects.filter(parent=product_parent) if product_parent else Category.objects.none()

    # Location options
    countries = Country.objects.all()
    states = State.objects.filter(country_id=selected_country) if selected_country else State.objects.none()
    cities = City.objects.filter(state_id=selected_state) if selected_state else City.objects.none()
    talukas = Taluka.objects.filter(city_id=selected_city) if selected_city else Taluka.objects.none()
    villages = Village.objects.filter(taluka_id=selected_taluka) if selected_taluka else Village.objects.none()

    # Brands and models
    brands = Brand.objects.filter(category_id=selected_category) if selected_category else Brand.objects.none()
    models = ProductModel.objects.filter(brand_id=selected_brand) if selected_brand else ProductModel.objects.none()

    # Base product query
    products = ProductItem.objects.all().select_related(
        'product_model__brand__category',
        'user__country', 'user__state', 'user__city', 'user__taluka', 'user__village'
    ).prefetch_related('images')

    # Exclude products from the current user if logged in
    if request.user.is_authenticated:
        products = products.exclude(user=request.user)

    # Filter by product type (sell, rent, resell)
    if selected_type in ['sell', 'rent', 'resell']:
        products = products.filter(type=selected_type)

    # Location filters
    if selected_country:
        products = products.filter(user__country_id=selected_country)
    if selected_state:
        products = products.filter(user__state_id=selected_state)
    if selected_city:
        products = products.filter(user__city_id=selected_city)
    if selected_taluka:
        products = products.filter(user__taluka_id=selected_taluka)
    if selected_village:
        products = products.filter(user__village_id=selected_village)

    # Category filter
    if selected_category:
        products = products.filter(product_model__brand__category_id=selected_category)

    # Brand filter
    if selected_brand:
        products = products.filter(product_model__brand_id=selected_brand)

    # Model filter
    if selected_model:
        products = products.filter(product_model_id=selected_model)

    # Search query filtering
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(product_model__name__icontains=search_query) |
            Q(product_model__brand__name__icontains=search_query)
        )
    # Price filtering
    try:
        if min_price:
            products = products.filter(price__gte=float(min_price))
        if max_price:
            products = products.filter(price__lte=float(max_price))
    except ValueError:
        pass  # Ignore price filter if there's a value error

    # Pagination logic
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_obj = paginator.get_page(request.GET.get('page'))

    # Context data to pass to the template
    context = get_header_data(request)
    context.update({
        'products': page_obj,
        'page_obj': page_obj,
        'countries': countries,
        'states': states,
        'cities': cities,
        'talukas': talukas,
        'villages': villages,
        'categories': categories,
        'main_categories': main_categories,
        'product_categories': product_categories,
        'brands': brands,
        'models': models,
        'selected_type': selected_type,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'selected_model': selected_model,
        'selected_country': int(selected_country) if selected_country and selected_country.isdigit() else None,
        'selected_state': int(selected_state) if selected_state and selected_state.isdigit() else None,
        'selected_city': int(selected_city) if selected_city and selected_city.isdigit() else None,
        'selected_taluka': int(selected_taluka) if selected_taluka and selected_taluka.isdigit() else None,
        'selected_village': int(selected_village) if selected_village and selected_village.isdigit() else None,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search_query,
        'search_type': 'product', # To keep dropdown selected


    })

    return render(request, 'products.html', context)



def enquiry_view(request, product_id):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    enquirer = get_object_or_404(UserRegistration, id=user_id)
    product = get_object_or_404(ProductItem, id=product_id)
    owner = product.user

    if owner == enquirer:
        messages.warning(request, "You cannot send enquiry on your own product.")
        return redirect('product_detail', product_id=product.id)

    # Get current user name in priority order
    if hasattr(enquirer, 'name') and enquirer.name:
        enquirer_name = enquirer.name
    elif hasattr(enquirer, 'first_name') and hasattr(enquirer, 'surname'):
        enquirer_name = f"{enquirer.first_name} {enquirer.surname}".strip()
    elif hasattr(enquirer, 'username'):
        enquirer_name = enquirer.username
    else:
        enquirer_name = 'User'

    enquiry_message = (
        "✉️ *New Enquiry Received!* ✉️\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Product:* {product.title}\n"
        f"👤 *Enquirer:* {enquirer_name}\n"
        "📝 Message: Hello, I am interested in your product. Please provide more details. Thank you!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    chat_msg = ChatMessage.objects.create(
        sender=enquirer,
        receiver=owner,
        message=enquiry_message,
        is_read=False,
        timestamp=timezone.now()
    )
    logger.info(f"Enquiry chat message created with ID {chat_msg.id}")

    messages.success(request, "Your enquiry has been sent successfully! The owner will contact you soon.")

    return redirect('product_detail', product_id=product.id)


def product_detail(request, product_id):
    product = get_object_or_404(ProductItem, id=product_id)

    referer = request.META.get('HTTP_REFERER', '')
    back_url_name = 'product_display'  # single product listing view

    # Default: no query params
    back_url_params = {}

    if referer:
        parsed_url = urlparse(referer)
        query_params = parse_qs(parsed_url.query)
        product_type = query_params.get('type', [None])[0]

        if product_type in ['rent', 'sell', 'resell']:
            back_url_params['type'] = product_type




    back_url = reverse(back_url_name)
    if back_url_params:
        back_url += '?' + urlencode(back_url_params)

    context = {
        'product': product,
        'images': product.images.all(),
        'back_url': back_url,
    }

    context.update(get_header_data(request))

    return render(request, 'product_detail.html', context)

# Show booking form page
def book_product_form(request, product_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect('login')

    product = get_object_or_404(ProductItem, id=product_id)

    context = {
        'product': product
    }
    return render(request, 'book_product.html', context)

def book_product(request, product_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect('login')

    user = get_object_or_404(UserRegistration, id=user_id)
    product = get_object_or_404(ProductItem, id=product_id)

    booked_dates = ProductBooking.objects.filter(product=product).values('start_date', 'end_date')
    today = timezone.localdate()

    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        if not start_date_str or not end_date_str:
            messages.error(request, "Please select both start and end dates.")
            return redirect('book_product', product_id=product_id)

        try:
            start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('book_product', product_id=product_id)

        if start_date < today or end_date < today:
            messages.error(request, "Booking dates cannot be in the past.")
            return redirect('book_product', product_id=product_id)

        if end_date < start_date:
            messages.error(request, "End date cannot be before start date.")
            return redirect('book_product', product_id=product_id)

        overlapping = ProductBooking.objects.filter(
            product=product,
            start_date__lte=end_date,
            end_date__gte=start_date,
        ).exists()

        if overlapping:
            messages.error(request, "Sorry, this product is already booked for some or all of the selected dates.")
            return redirect('book_product', product_id=product_id)

        ProductBooking.objects.create(
            product=product,
            user=user,
            start_date=start_date,
            end_date=end_date
        )

        delta_days = (end_date - start_date).days + 1
        messages.success(request, f"Product booked successfully for {delta_days} day(s)!")
        return redirect('product_detail', product_id=product_id)

    # For GET request, prepare context
    context = {
        'product': product,
        'booked_dates': booked_dates,
        'today': today,
        'images': product.images.all(),
    }

    # Get header data and merge into context
    header_context = get_header_data(request)
    context.update(header_context)

    return render(request, 'book_product.html', context)


def get_header_data(request):
    categories = Category.objects.filter(parent__isnull=True)

    user_id = request.session.get("user_id")
    profile_status = None
    unread_chat_count = 0
    user_name = request.session.get("user_name")

    if user_id:
        user = UserRegistration.objects.filter(id=user_id).first()
        if user:
            profile_status = user.profile_status

        unread_chat_count = ChatMessage.objects.filter(
            receiver_id=user_id,
            is_read=False
        ).count()

    return {
        "categories": categories,
        "profile_status": profile_status,
        "unread_chat_count": unread_chat_count,
        "user_name": user_name,
    }



def logout_view(request):
    # Clear all session data
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect("dashboard")  # Redirect to login page

