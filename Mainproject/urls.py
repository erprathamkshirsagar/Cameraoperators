from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.dashboard),
    path('dashboard/', views.dashboard,name='dashboard'),
    path('profile/', views.profile,name='profile'),
    path('search/', views.search_results, name='search_results'),  # <-- make sure this exists
    path('signup/', views.signup, name='signup'),
    path('ajax/load-states/', views.load_states, name='ajax_load_states'),
    path('documentverification/', views.documentverification,name='documentverification'),
    path('ajax/load-cities/', views.load_cities, name='ajax_load_cities'),
    path('ajax/load-talukas/', views.load_talukas, name='ajax_load_talukas'),
    path('ajax/load-villages/', views.load_villages, name='ajax_load_villages'),
    path("logout/", views.logout_view, name="logout"),
    path('login/', views.login, name='login'),
    path('freelancer/', views.freelancer, name='freelancer'),
    path('freelancerdisplay/', views.freelancerdisplay, name='freelancerdisplay'),
    path('search/', views.search_results, name='search_results'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('book-product/<int:product_id>/', views.book_product, name='book_product'),
    path('product/<int:product_id>/book/', views.book_product_form, name='book_product_form'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('delete-skill/<int:skill_id>/', views.delete_skill, name='delete_skill'),
    path('set_location/', views.set_location, name='set_location'),
    path('chat/', views.chat, name='chat'),
    path('freelancer/<int:id>/', views.freelancer_profile, name='freelancer_profile'),
    path('chat/<int:user_id>/', views.chat_user, name='chat_with_user'),
    path("chat/<int:user_id>/", views.chat_user, name="chat_user"),
    path("get_messages/<int:user_id>/", views.get_messages, name="get_messages"),
    path("send_message/", views.send_message, name="send_message"),
    path("get_chat_users/", views.get_chat_users),
    path('booking/<int:freelancer_id>/<int:skill_id>/', views.booking_view, name='booking_page'),
    path('gallery/', views.gallery, name='gallery'),
    path('gallery/delete/<int:pk>/', views.gallery_delete, name='gallery_delete'),
    path('orders/', views.freelancer_orders_view, name='orders'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('my-bookings/', views.client_bookings_view, name='client_bookings'),
    path('orders/accept/<int:booking_id>/', views.accept_booking, name='accept_booking'),
    path('orders/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('productmanagement/',views.productmanagement,name='productmanagement'),
    path('delete-product/<int:id>/', views.delete_product, name='delete_product'),
    path("update-product/<int:id>/", views.update_product, name="update_product"),
    path("api/set-user-location/", views.set_user_location, name="set_user_location"),
    path('api/get-location-ids/', views.get_location_ids, name='get_location_ids'),
    path('api/get-nearby-freelancers/',views.get_nearby_freelancers, name='get_nearby_freelancers'),
    path('enquiry/<int:product_id>/', views.enquiry_view, name='enquiry'),
    path('products/', views.product_display, name='product_display'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



