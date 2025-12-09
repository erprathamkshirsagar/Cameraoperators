# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.adminlogin, name='adminlogin'),
    
    path('admindashboard/', views.admindashboard, name='admindashboard'),
    path('manage_categories/', views.manage_categories, name='manage_categories'),
    path('adminuserdetails/', views.adminuserdetails, name='adminuserdetails'),
    path('productmanager/', views.productmanager, name='productmanager'),

    path('edit-category/<int:category_id>/', views.edit_category, name="edit_category"),
    path('delete-category/<int:category_id>/', views.delete_category, name="delete_category"),
    path('manage_locations/', views.manage_locations, name='manage_locations'),
    path('verifydocuments/', views.verifydocumentslist, name='verifydocumentslist'),
    path('logout/', views.adminlogout, name='adminlogout'),
    path('view_user/<int:user_id>/', views.view_user_details, name='view_user_details'),
    path('update_document_status/<int:verification_id>/<str:status>/', views.update_document_status, name='update_document_status'),
    path('delete_document/<int:verification_id>/', views.delete_document, name='delete_document'),
    path('productmanager/', views.productmanager, name='productmanager'),
  # ---------------- PRODUCT MANAGER ----------------

    # -------- CATEGORY --------
    path('category/save/', views.save_category, name='save_category'),
    path('category/delete/<int:id>/', views.delete_category, name='delete_category'),
    path('product/save/', views.save_product, name='save_product'),

    # -------- BRAND --------
    path('brand/save/', views.save_brand, name='save_brand'),
    path('brand/delete/<int:id>/', views.delete_brand, name='delete_brand'),

# urls.py
    path('manager/verify_profile_status/<int:user_id>/', views.verify_profile_status, name='verify_profile_status'),

]
