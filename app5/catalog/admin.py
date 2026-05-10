from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'vin_number', 'category', 'price', 'in_stock', 'is_featured', 'created_at']
    list_filter = ['category', 'in_stock', 'is_featured']
    search_fields = ['name', 'brand', 'vin_number', 'short_description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'in_stock', 'is_featured']
