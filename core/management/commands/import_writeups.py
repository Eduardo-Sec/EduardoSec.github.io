"""
Import Hugo markdown writeups into the database.

Usage:
    python manage.py import_writeups
    python manage.py import_writeups --clear   # wipe existing before import
"""
import re
from pathlib import Path
from datetime import date

from django.core.management.base import BaseCommand
from django.conf import settings

from core.models import Tag, Writeup


CONTENT_DIR = Path(settings.BASE_DIR) / 'content' / 'writeups'

# Simple frontmatter parser — handles the YAML subset used in Hugo writeups.
_FM_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def _parse_frontmatter(text):
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    body = text[m.end():]
    fm = {}
    for line in m.group(1).splitlines():
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip()
        val = val.strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        elif val.startswith('[') and val.endswith(']'):
            inner = val[1:-1]
            val = [v.strip().strip('"').strip("'") for v in inner.split(',') if v.strip()]
        elif val.lower() == 'true':
            val = True
        elif val.lower() == 'false':
            val = False
        fm[key] = val
    return fm, body


class Command(BaseCommand):
    help = 'Import Hugo markdown writeups into the Writeup model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing writeups and tags before importing',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Writeup.objects.all().delete()
            Tag.objects.all().delete()
            self.stdout.write('Cleared existing writeups and tags.')

        files = sorted(CONTENT_DIR.glob('*.md'))
        created = updated = skipped = 0

        for path in files:
            if path.name == '_index.md':
                continue

            raw = path.read_text(encoding='utf-8')
            fm, body = _parse_frontmatter(raw)

            if fm.get('draft', False):
                self.stdout.write(f'  skip (draft): {path.name}')
                skipped += 1
                continue

            title = fm.get('title', path.stem)
            slug = path.stem
            raw_date = fm.get('date', '')
            if isinstance(raw_date, str):
                try:
                    parts = raw_date.strip().split('-')
                    pub_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                except (ValueError, IndexError):
                    pub_date = date.today()
            else:
                pub_date = raw_date  # already a date if pyyaml parsed it

            description = fm.get('description', '')
            tag_slugs = fm.get('tags', [])
            if isinstance(tag_slugs, str):
                tag_slugs = [tag_slugs]

            writeup, was_created = Writeup.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'date': pub_date,
                    'description': description,
                    'body': body.strip(),
                },
            )

            tag_objs = []
            for ts in tag_slugs:
                tag, _ = Tag.objects.get_or_create(slug=ts.strip())
                tag_objs.append(tag)
            writeup.tags.set(tag_objs)

            action = 'created' if was_created else 'updated'
            self.stdout.write(f'  {action}: {slug}')
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done — {created} created, {updated} updated, {skipped} skipped.'
            )
        )
