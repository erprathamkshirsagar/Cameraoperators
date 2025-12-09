from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt



def adminlogin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admindashboard')
        else:
            messages.error(request, "Invalid credentials or not a staff/admin user.")

    return render(request, 'adminlogin.html')


@login_required
def admindashboard(request):
    return render(request, 'admindashboard.html')


from django.contrib.auth import logout

def adminlogout(request):
    logout(request)
    return redirect('dashboard')

from django.shortcuts import render, redirect
from .models import Category

from django.shortcuts import render, redirect, get_object_or_404
from .models import Category,Country, State, City, Taluka, Village

def manage_categories(request):
    if request.method == "POST":
        name = request.POST['name']
        parent_id = request.POST.get('parent')
        parent = Category.objects.get(id=parent_id) if parent_id else None
        Category.objects.create(name=name, parent=parent)
        return redirect('manage_categories')

    categories = Category.objects.prefetch_related('subcategories').all()
    return render(request, 'manage_categories.html', {'categories': categories})

def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.name = request.POST.get("name")
        parent_id = request.POST.get("parent")
        category.parent = Category.objects.get(id=parent_id) if parent_id else None
        category.save()
        return redirect("manage_categories")

    categories = Category.objects.exclude(id=category.id)  # avoid self parent
    return render(request, "edit_category.html", {"category": category, "categories": categories})

def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return redirect("manage_categories")
from django.http import JsonResponse

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse

def manage_locations(request):
    if request.method == "POST":
        action = request.POST.get("action")
        response = {"status": "error"}
        if action == "add_country":
            name = request.POST.get("country_name")
            if name:
                country = Country.objects.create(name=name)
                response = {"status": "success", "id": country.id, "name": country.name}

        elif action == "add_state":
            country_id = request.POST.get("country_id")
            name = request.POST.get("state_name")
            if country_id and name:
                country = get_object_or_404(Country, id=country_id)
                state = State.objects.create(name=name, country=country)
                response = {"status": "success", "id": state.id, "name": state.name}

        elif action == "add_city":
            state_id = request.POST.get("state_id")
            name = request.POST.get("city_name")
            if state_id and name:
                state = get_object_or_404(State, id=state_id)
                city = City.objects.create(name=name, state=state)
                response = {"status": "success", "id": city.id, "name": city.name}

        elif action == "add_taluka":
            city_id = request.POST.get("city_id")
            name = request.POST.get("taluka_name")
            if city_id and name:
                city = get_object_or_404(City, id=city_id)
                taluka = Taluka.objects.create(name=name, city=city)
                response = {"status": "success", "id": taluka.id, "name": taluka.name}

        elif action == "add_village":
            taluka_id = request.POST.get("taluka_id")
            name = request.POST.get("village_name")
            if taluka_id and name:
                taluka = get_object_or_404(Taluka, id=taluka_id)
                village = Village.objects.create(name=name, taluka=taluka)
                response = {"status": "success", "id": village.id, "name": village.name}


        # ----------- DELETE ACTIONS -------------
        elif action == "delete_country":
            id = request.POST.get("id")
            Country.objects.filter(id=id).delete()
            response = {"status": "success"}

        elif action == "delete_state":
            id = request.POST.get("id")
            State.objects.filter(id=id).delete()
            response = {"status": "success"}

        elif action == "delete_city":
            id = request.POST.get("id")
            City.objects.filter(id=id).delete()
            response = {"status": "success"}

        elif action == "delete_taluka":
            id = request.POST.get("id")
            Taluka.objects.filter(id=id).delete()
            response = {"status": "success"}

        elif action == "delete_village":
            id = request.POST.get("id")
            Village.objects.filter(id=id).delete()
            response = {"status": "success"}

        # If request is AJAX, return JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(response)
        
        return redirect('manage_locations')

    # GET request → display page
    countries = Country.objects.all()
    return render(request, "manage_locations.html", {"countries": countries})


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import VerificationDocument
from Mainproject.forms import VerificationDocumentForm

def verifydocumentslist(request):
    documents = VerificationDocument.objects.all().order_by('id')

    # Handle Add
    if request.method == "POST" and 'add_document' in request.POST:
        form = VerificationDocumentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Document type added successfully")
            return redirect('verifydocumentslist')

    # Handle Edit
    if request.method == "POST" and 'edit_document' in request.POST:
        doc_id = request.POST.get('doc_id')
        document = get_object_or_404(VerificationDocument, pk=doc_id)
        form = VerificationDocumentForm(request.POST, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document type updated successfully")
            return redirect('verifydocumentslist')

    # Handle Delete
    if request.method == "POST" and 'delete_document' in request.POST:
        doc_id = request.POST.get('doc_id')
        document = get_object_or_404(VerificationDocument, pk=doc_id)
        document.delete()
        messages.success(request, "Document type deleted successfully")
        return redirect('verifydocumentslist')

    # Empty form for add
    form = VerificationDocumentForm()
    return render(request, 'verifydocumentslist.html', {'documents': documents, 'form': form})

from Mainproject.models import UserRegistration, UserVerification  # Assuming these models exist
from django.contrib import messages

def adminuserdetails(request):
    """
    Admin view: Show all users with basic info and a button to view full details.
    """
    users = UserRegistration.objects.select_related('city', 'village').all().order_by('id')

    context = {
        'users': users
    }
    return render(request, 'adminuserdetails.html', context)


def view_user_details(request, user_id):
    """
    Admin view: Show full details of a particular user along with verification documents.
    Also calculates if all documents are verified to manage profile status updates.
    """
    # Fetch the user instance
    user = get_object_or_404(UserRegistration, id=user_id)

    # Fetch all verification documents for this user
    verifications = UserVerification.objects.select_related('user', 'document').filter(user_id=user.id).order_by('-id')

    # Determine if all documents are verified
    all_verified = verifications.exists() and all(v.status == 'verified' for v in verifications)

    context = {
        'user': user,
        'verifications': verifications,
        'all_verified': all_verified,  # Pass this to the template
    }

    return render(request, 'view_user_details.html', context)

@csrf_exempt
def verify_profile_status(request, user_id):
    """
    AJAX view to mark a user's profile status as 'verified'.
    """
    if request.method == "POST":
        # Get the user instance
        user = get_object_or_404(UserRegistration, id=user_id)

        # Update profile_status to 'verified' unconditionally
        user.profile_status = "verified"  # Make sure 'profile_status' field exists in your model
        user.save()

        return JsonResponse({"success": True, "status": "verified"})

    return JsonResponse({"success": False, "message": "Invalid request method."})

@require_POST
def update_document_status(request, verification_id, status):
    verification = get_object_or_404(UserVerification, id=verification_id)
    if status not in ['verified', 'rejected']:
        return JsonResponse({'success': False, 'message': 'Invalid status.'})
    verification.status = status
    verification.save()
    return JsonResponse({
        'success': True,
        'status': verification.status,
        'document': str(verification.document)
    })

@require_POST
def delete_document(request, verification_id):
    verification = get_object_or_404(UserVerification, id=verification_id)
    doc_name = str(verification.document)
    verification.delete()
    return JsonResponse({'success': True, 'message': f'Document "{doc_name}" deleted.'})



from Mainproject.models import Category,Brand,ProductModel

from django.shortcuts import render
from Mainproject.models import Category, Brand, ProductModel

import json

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from Mainproject.models import Category, Brand, ProductModel


from Mainproject.models import Category,Brand,ProductModel

from django.shortcuts import render
from Mainproject.models import Category, Brand, ProductModel

def productmanager(request):
    products_category = Category.objects.get(name="Products")

    categories = Category.objects.filter(
        parent=products_category
    ).prefetch_related(
        'brand_set__productmodel_set'
    )

    return render(request, 'productmanager.html', {
        'categories': categories,
        'products_category': products_category
    })

@csrf_exempt
def save_category(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    data = json.loads(request.body)
    category_id = data.get("id")
    name = data.get("name")

    if not name:
        return JsonResponse({"error": "Category name required"}, status=400)

    try:
        products_category = Category.objects.get(name="Products")
    except Category.DoesNotExist:
        return JsonResponse({"error": "Products category missing"}, status=500)

    if category_id:
        Category.objects.filter(
            id=category_id,
            parent=products_category   # ✅ protects Freelancer
        ).update(name=name)
    else:
        Category.objects.create(
            name=name,
            parent=products_category   # ✅ ALWAYS under Products
        )

    return JsonResponse({"status": "success"})

@csrf_exempt
def delete_category(request, id):
    try:
        products_category = Category.objects.get(name="Products")
    except Category.DoesNotExist:
        return JsonResponse({"error": "Products category missing"}, status=500)

    Category.objects.filter(
        id=id,
        parent=products_category
    ).delete()

    return JsonResponse({"status": "success"})


@csrf_exempt
def save_brand(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    data = json.loads(request.body)
    brand_id = data.get("id")
    name = data.get("name")
    category_id = data.get("category_id")

    if not name:
        return JsonResponse({"error": "Brand name required"}, status=400)

    if brand_id:
        Brand.objects.filter(id=brand_id).update(name=name)
    else:
        if not category_id:
            return JsonResponse({"error": "Category ID required"}, status=400)

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return JsonResponse({"error": "Category not found"}, status=404)

        Brand.objects.create(name=name, category=category)

    return JsonResponse({"status": "success"})



@csrf_exempt
def delete_brand(request, id):
    Brand.objects.filter(id=id).delete()
    return JsonResponse({"status": "success"})
@csrf_exempt
def save_product(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    data = json.loads(request.body)
    product_id = data.get("id")
    name = data.get("name")
    brand_id = data.get("brand_id")

    if not name:
        return JsonResponse({"error": "Product name required"}, status=400)

    if product_id:
        ProductModel.objects.filter(id=product_id).update(name=name)
    else:
        if not brand_id:
            return JsonResponse({"error": "Brand ID required"}, status=400)

        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return JsonResponse({"error": "Brand not found"}, status=404)

        ProductModel.objects.create(name=name, brand=brand)

    return JsonResponse({"status": "success"})

@csrf_exempt
def delete_product(request, id):
    ProductModel.objects.filter(id=id).delete()
    return JsonResponse({"status": "success"})

