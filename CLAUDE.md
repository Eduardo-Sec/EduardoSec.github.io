# Project Context

## What this is
Portfolio site for Eduardo Bustamante (ebustamante.dev) — a cybersecurity/CS sophomore at UNO with dual NSA CAE concentrations, working as a Cybersecurity Engineer Intern at Sera Digital Corp. The site documents homelab builds, detection engineering work, and CTF writeups.

## Migration goal
Migrating from Hugo static site (GitHub Pages) to a self-hosted Django app on Rocky Linux 9 (10.10.10.60), served by Nginx, tunneled through Cloudflare Zero Trust. The Hugo theme and content are in this repo and serve as the source of truth for design and content.

## Stack decisions
- Django 5.2 LTS (app server, Python 3.11)
- Nginx (reverse proxy)
- HTMX (dynamic filtering/search on writeups, no JS framework)
- mistune (server-side markdown rendering)
- SQLite for now, Postgres later if needed
- Writeups stored as markdown in the database (TextField), not flat files
- Cloudflare Zero Trust tunnel for public access (no open inbound ports)

## Design direction
"Signal intelligence" aesthetic. Dark background, emerald green primary accent (#10b981 range) with a gold secondary accent (#c9a227 range) used sparingly for featured/highlight treatment, bright white primary text. Clean, purposeful, more Darktrace/Snyk than hacker cave. NOT generic cybersecurity stock-photo energy.

Specific design elements already established:
- Section markers use ▸ (not //)
- Shield monogram as logo
- SOC dashboard panel on homepage (live data-style readouts, status indicators, borders, labels)
- Scroll fade-in animations on homepage sections
- Dark theme throughout, no light mode

## Writeup style rules (for any generated content)
- No em dashes
- No colons in prose
- First-person, conversational, honest about troubleshooting
- Tags limited to: detection, malware, ctf, forensics, project, tooling, notes

## Tag taxonomy
detection, malware, ctf, forensics, project, tooling, notes — no tags outside this set

## Current Hugo structure (source of truth)
- themes/ebustamante/layouts/ — all templates
- themes/ebustamante/static/css/main.css — all styles
- content/writeups/ — markdown writeups with frontmatter
- static/ — static assets
- hugo.toml — site config

## Django app structure to build
- portfolio/ (Django project root)
- core/ (main app: views, models, urls)
- templates/ (mirrors Hugo layouts)
- static/ (mirrors Hugo static, bring CSS over directly)
- content/writeups/ markdown files are the seed data — import into DB on first run

## Deployment workflow
Claude Code edits files locally in this repo. When ready to deploy:
1. git push to GitHub
2. SSH into 10.10.10.60 and git pull
3. Restart gunicorn/nginx

## Key constraints
- Never break the signal intelligence aesthetic
- Keep all frontend in Django templates + HTMX, no React/Vue
- Writeup URLs should match current Hugo URLs for SEO continuity
- Mobile responsive

## UI/UX Skill
The UI/UX Pro Max skill is installed at `.claude/skills/`. Use it for all frontend work.

When generating UI, apply the following overrides to the skill's recommendations:
- Category: Cybersecurity Platform (use its reasoning rules as the base)
- Style: HUD / Sci-Fi FUI blended with Dark Mode (OLED) — NOT generic cyber
- Colors: Override skill palette with #10b981 (emerald primary), #c9a227 (gold secondary/accent), deep near-black background with a subtle emerald tint, bright white text
- Typography: Clean monospace for data/code elements, sans-serif for prose
- Anti-patterns for this project: light mode, stock photo cyber aesthetic, neon green (this is emerald, not neon), matrix rain, skulls, padlock icons, generic "hacker" visual language
- The design language is signal intelligence — think Darktrace, Snyk, Cloudflare dashboard — not CTF team website
