from django.contrib import admin
from django.utils.html import format_html
# from django_summernote.admin import SummernoteModelAdmin
from . import models
from mptt.admin import MPTTModelAdmin
from datetime import datetime

        
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author','display_mask', 'publish_date','display_comfirmed']
    search_fields = ['title', 'content']
    list_filter = ['publish_date', 'author']
    list_per_page = 10
    
    def display_mask(self, obj):
        return format_html('<img src="{}" width="50" height="50" />', obj.mask.url)
    display_mask.short_description = 'Mask Image'
    
    def display_comfirmed(self, obj):
        if obj.comfirmed:
            return format_html('<span style="color: green;">{}</span>', 'Comfirmed')
        return format_html('<span style="color: red;">{}</span>', 'Not Comfirmed')
    display_comfirmed.admin_order_field = 'comfirmed'  # Allows column order sorting
    display_comfirmed.short_description = 'Comfirmed'  # Column header
    
    def make_published(self, request, queryset):
        queryset.update(comfirmed=True)
    make_published.short_description = "Mark selected posts as comfirmed"

    def make_unpublished(self,request,queryset):
        queryset.update(comfirmed=False)
    make_unpublished.short_description = "Mark selected posts as uncomfirmed"
    
    actions = [make_published,make_unpublished]
    
class CommentAdmin(MPTTModelAdmin,admin.ModelAdmin):
    list_display = ['content', 'author','post','created_time']  # 你可以根据需要自定义其他选项
    mptt_level_indent = 20  # 控制缩进  
    search_fields = ['author','post', 'content']
    list_filter = ['created_time', 'author']
    list_per_page = 10 

admin.site.register(models.Post, PostAdmin)
admin.site.register(models.Comment)
admin.site.register(models.Like)
admin.site.register(models.Favorite)
