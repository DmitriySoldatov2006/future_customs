from django.urls import path

from . import views


urlpatterns = [
    path('', views.catalog_view, name='catalog'),
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    path('admin-panel/api/brands/', views.admin_panel_create_brand_view, name='admin_panel_create_brand'),
    path('admin-panel/api/brands/<int:brand_id>/update/', views.admin_panel_update_brand_view, name='admin_panel_update_brand'),
    path('admin-panel/api/brands/<int:brand_id>/delete/', views.admin_panel_delete_brand_view, name='admin_panel_delete_brand'),
    path('admin-panel/api/part-types/', views.admin_panel_create_part_type_view, name='admin_panel_create_part_type'),
    path('admin-panel/api/part-types/<int:part_type_id>/update/', views.admin_panel_update_part_type_view, name='admin_panel_update_part_type'),
    path('admin-panel/api/part-types/<int:part_type_id>/delete/', views.admin_panel_delete_part_type_view, name='admin_panel_delete_part_type'),
    path('admin-panel/api/products/', views.admin_panel_create_product_view, name='admin_panel_create_product'),
    path('admin-panel/api/products/<int:product_id>/update/', views.admin_panel_update_product_view, name='admin_panel_update_product'),
    path('admin-panel/api/products/<int:product_id>/delete/', views.admin_panel_delete_product_view, name='admin_panel_delete_product'),
    path('admin-panel/api/users/', views.admin_panel_users_view, name='admin_panel_users'),
    path('admin-panel/api/users/<int:user_id>/update/', views.admin_panel_update_user_view, name='admin_panel_update_user'),
    path('admin-panel/api/users/<int:user_id>/delete/', views.admin_panel_delete_user_view, name='admin_panel_delete_user'),
    path('admin-panel/api/car-brands/', views.admin_panel_car_brands_view, name='admin_panel_car_brands'),
    path('admin-panel/api/car-brands/<int:car_brand_id>/update/', views.admin_panel_update_car_brand_view, name='admin_panel_update_car_brand'),
    path('admin-panel/api/car-brands/<int:car_brand_id>/delete/', views.admin_panel_delete_car_brand_view, name='admin_panel_delete_car_brand'),
    path('admin-panel/api/car-models/', views.admin_panel_car_models_view, name='admin_panel_car_models'),
    path('admin-panel/api/car-models/<int:car_model_id>/update/', views.admin_panel_update_car_model_view, name='admin_panel_update_car_model'),
    path('admin-panel/api/car-models/<int:car_model_id>/delete/', views.admin_panel_delete_car_model_view, name='admin_panel_delete_car_model'),
    path('admin-panel/api/car-generations/', views.admin_panel_car_generations_view, name='admin_panel_car_generations'),
    path('admin-panel/api/car-generations/<int:car_generation_id>/update/', views.admin_panel_update_car_generation_view, name='admin_panel_update_car_generation'),
    path('admin-panel/api/car-generations/<int:car_generation_id>/delete/', views.admin_panel_delete_car_generation_view, name='admin_panel_delete_car_generation'),
    path('<slug:slug>/', views.product_detail_view, name='product_detail'),
]
