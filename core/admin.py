from django.contrib import admin
from .models import Tag, Writeup


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['slug', 'writeup_count']
    prepopulated_fields = {'slug': ('slug',)}

    def writeup_count(self, obj):
        return obj.writeups.count()
    writeup_count.short_description = 'writeups'


@admin.register(Writeup)
class WriteupAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'tag_list', 'reading_time', 'featured']
    list_filter = ['tags', 'date', 'featured']
    list_editable = ['featured']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    date_hierarchy = 'date'
    ordering = ['-date']

    def tag_list(self, obj):
        return ', '.join(t.slug for t in obj.tags.all())
    tag_list.short_description = 'tags'
