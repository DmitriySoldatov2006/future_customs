from django.contrib import admin

from .models import Brand, Category, CategoryCharacteristic, CategoryCharacteristicOption, Product


class CategoryCharacteristicOptionInline(admin.TabularInline):
    model = CategoryCharacteristicOption
    extra = 1


class CategoryCharacteristicInline(admin.StackedInline):
    model = CategoryCharacteristic
    extra = 1


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CategoryCharacteristicInline]


@admin.register(CategoryCharacteristic)
class CategoryCharacteristicAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'category', 'allows_custom_value', 'sort_order']
    list_filter = ['category', 'allows_custom_value']
    search_fields = ['name', 'key', 'category__name']
    inlines = [CategoryCharacteristicOptionInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'article',
        'brand',
        'vin_number',
        'category',
        'price',
        'stock_quantity',
        'in_stock',
        'is_featured',
        'created_at',
    ]
    list_filter = ['category', 'in_stock', 'is_featured']
    search_fields = ['name', 'article', 'brand', 'vin_number', 'short_description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock_quantity', 'in_stock', 'is_featured']
