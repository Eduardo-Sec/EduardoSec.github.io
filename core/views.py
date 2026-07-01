from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.db.models import Q
from django.utils.safestring import mark_safe

from .models import Tag, Writeup
from .markdown import render_markdown


def _site_context():
    return {
        'site_title': settings.SITE_TITLE,
        'site_description': settings.SITE_DESCRIPTION,
        'certs_in_progress': settings.CERTS_IN_PROGRESS,
        'tools_and_technologies': settings.TOOLS_AND_TECHNOLOGIES,
        'analyst_start_date': settings.ANALYST_START_DATE,
    }


def home(request):
    ctx = _site_context()
    ctx['recent_writeups'] = Writeup.objects.prefetch_related('tags')[:3]
    ctx['writeup_count'] = Writeup.objects.count()
    return render(request, 'home.html', ctx)


def about(request):
    return render(request, 'about.html', _site_context())


def writeup_list(request):
    ctx = _site_context()
    ctx['writeups'] = Writeup.objects.prefetch_related('tags')
    ctx['tags'] = Tag.objects.all()
    return render(request, 'writeups/list.html', ctx)


def writeup_search(request):
    q = request.GET.get('q', '').strip()
    tag = request.GET.get('tag', '').strip()

    qs = Writeup.objects.prefetch_related('tags')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(body__icontains=q))
    if tag:
        qs = qs.filter(tags__slug=tag)

    return render(request, 'writeups/_rows.html', {'writeups': qs})


def writeup_detail(request, slug):
    writeup = get_object_or_404(Writeup, slug=slug)
    content_html, toc_html = render_markdown(writeup.body)

    related = (
        Writeup.objects
        .filter(tags__in=writeup.tags.all())
        .exclude(pk=writeup.pk)
        .distinct()[:3]
    )

    ctx = _site_context()
    ctx.update({
        'writeup': writeup,
        'content_html': mark_safe(content_html),
        'toc_html': mark_safe(toc_html),
        'related_writeups': related,
    })
    return render(request, 'writeups/single.html', ctx)


def tag_list(request):
    ctx = _site_context()
    ctx['tags'] = Tag.objects.prefetch_related('writeups')
    return render(request, 'tags/list.html', ctx)


def tag_detail(request, tag):
    tag_obj = get_object_or_404(Tag, slug=tag)
    ctx = _site_context()
    ctx['tag'] = tag_obj
    ctx['writeups'] = tag_obj.writeups.prefetch_related('tags')
    return render(request, 'tags/detail.html', ctx)


def projects(request):
    return render(request, 'projects.html', _site_context())


def resume(request):
    return render(request, 'resume.html', _site_context())


def contact(request):
    return render(request, 'contact.html', _site_context())


def pgp(request):
    return render(request, 'pgp.html', _site_context())
