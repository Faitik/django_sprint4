from django.contrib import admin

from .models import (
    Category, Location, Post, Comment
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('text',)
    list_display = ('id', 'is_published', 'created_at', 'title',
                    'description', 'slug',)
    list_display_links = ('id',)
    list_filter = ('is_published',)
    empty_value_display = 'pub_date'


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ('text',)
    list_display = ('id', 'is_published', 'created_at', 'name',)
    list_display_links = ('id',)
    list_filter = ('is_published',)
    empty_value_display = 'Не задано'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    search_fields = ('text',)
    list_display = ('id', 'title', 'author', 'text', 'category',
                    'pub_date', 'location', 'is_published', 'created_at',)
    list_display_links = ('title',)
    list_editable = ('category', 'is_published', 'location',)
    list_filter = ('created_at',)
    empty_value_display = 'Не задано'


admin.site.register(Comment)
