---
title: "Expanding the portfolio site, security, features, and dev workflow"
date: 2026-04-05
tags: ["project"]
draft: false
---

After the first writeup I had a working site with a GitHub Actions workflow, branch protection, and a PR based deployment process. That was a solid foundation but there was a lot left to build out. This covers everything I added after that, the security improvements, new pages, and the smaller details that make the site feel more complete.

---

## GPG key and commit signing

The first thing I tackled was setting up a GPG key for commit signing. Every commit I push to GitHub now shows a green Verified badge, which is a small but meaningful signal for a security professional. It means the commits are cryptographically tied to my key and anyone can verify they actually came from me.

Setting it up on Windows involved installing Gpg4win, generating a 4096 bit RSA key with a two year expiration, and configuring Git to sign every commit automatically. The key generation command is straightforward:

```bash
gpg --full-generate-key
```

After generating the key I exported the public key and added it to GitHub under Settings, SSH and GPG keys. Then I configured Git:

```bash
git config --global user.signingkey C40C15BD0B031356
git config --global commit.gpgsign true
git config --global gpg.program "C:\Program Files\GnuPG\bin\gpg.exe"
```

One thing worth noting is that GPG prompts for your passphrase on the first commit of each session, then caches it for a while. So it is not as disruptive as it sounds in practice.

---

## PGP page

Since I had a GPG key I added a PGP page to the site at `/pgp`. It shows my key ID, fingerprint, instructions for fetching the key from a keyserver, and the full public key block for manual import. Anyone who wants to send me an encrypted message can use it.

The key ID is `C40C15BD0B031356` and the fingerprint is `25F2 D400 EBA7 D3E9 0861 1CEA C40C 15BD 0B03 1356`. I also added PGP to the nav so it is easy to find.

---

## Mobile hamburger nav

The nav was getting cramped on mobile with all the links in a row. I added a hamburger menu that collapses the links on smaller screens. On desktop it stays exactly the same. The implementation is straightforward, a button in the nav HTML, some CSS to hide and show the links, and a small JavaScript toggle:

```javascript
document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  toggle.addEventListener('click', function() {
    links.classList.toggle('open');
  });
});
```

---

## Search on the writeups page

I added Fuse.js powered search to the writeups page. Hugo generates a JSON index of all content at `/index.json` which Fuse.js loads and searches client side. The search input filters the writeups list in real time as you type, with a fallback message if nothing matches.

To enable the JSON output I added this to `hugo.toml`:

```toml
[outputs]
  home = ["HTML", "RSS", "JSON"]
```

The search field fits the site's monospace aesthetic and focuses with a purple glow that matches the accent color. No external dependencies beyond Fuse.js loaded from a CDN.

---

## Resume page

I built a styled resume page at `/resume` that matches the site's dark theme rather than just uploading a PDF. The page has a download PDF button at the top for anyone who needs the traditional format, but the primary experience is the styled HTML version.

The resume covers my SOC Analyst Intern role at UNO's MATRIX Project, my education at UNO and UNL, and a skills section that matches the tools grid on the homepage. Phone number is left off since it is a public page.

---

## Custom 404 page

The default GitHub Pages 404 is generic and white. I created a custom one at `themes/ebustamante/layouts/404.html` that matches the site's design with a `// error` tag, a styled 404 heading, and two buttons for going home or contacting me. GitHub Pages automatically serves `404.html` for any missing URL.

---

## security.txt

I added a `security.txt` file at `/.well-known/security.txt`. It is a standard file that tells security researchers how to contact you if they find a vulnerability on your site. The file points to my email and my PGP page for encrypted disclosure. Worth noting that GitHub Pages does not serve the `.well-known` directory correctly due to server level restrictions, so this one will have to wait until I migrate to self hosted Nginx on the P3. It works correctly in local development though.

---

## RSS feed with XSL stylesheet

Hugo generates an RSS feed automatically but the raw XML view in the browser is ugly and confusing. I created an XSL stylesheet that renders the feed as a styled HTML page matching the rest of the site. The feed is filtered to only include writeups, not static pages like About or Contact.

The stylesheet lives at `static/feed.xsl` and the RSS template at `layouts/_default/rss.xml` references it with an `<?xml-stylesheet?>` processing instruction. The rendered page has the same dark background, purple accents, and monospace typography as the rest of the site, along with a brief explanation of what RSS is and how to use it.

---

## Open Graph meta tags

I added Open Graph and Twitter Card meta tags to the base template so the site previews correctly when shared on LinkedIn, Discord, or anywhere else. The tags are dynamic, pulling the page title and description for individual pages and falling back to the site description for the homepage.

I also updated the site title in `hugo.toml` to be more descriptive for SEO purposes, going from just my name to "Eduardo Bustamante, Cybersecurity Student and SOC Analyst" which hits the recommended 50 to 60 character range.

---

## Reading time on writeups

Hugo has a built in `.ReadingTime` variable that calculates estimated reading time based on word count. I added it to the writeup single template alongside the date and tag. Small detail but it makes the posts feel more like proper articles.

---

## Tags and categories

I set up a full tags taxonomy so writeups can be categorized and filtered. The tags I am using are detection, malware, ctf, forensics, project, tooling, and notes. Each tag has its own page listing all writeups with that tag, and there is a tags index at `/tags/` showing all tags with post counts.

Clicking a tag on a writeup takes you to that tag's page. There is also a "browse by tag" link on the writeups list page for discoverability. The tag system uses Hugo's built in taxonomy support with a custom layout for both the individual tag pages and the terms index.

---

## Takeaways

Most of these features took under an hour each to implement. The ones that took longer were the RSS stylesheet, which involved learning enough XSL to get the browser rendering correctly, and the tags system, which required understanding Hugo's taxonomy lookup order. Everything else was pretty straightforward once I knew what I was building.

The site is at a good place now. The main thing missing is more writeups, which is what I will be focusing on next. The infrastructure is solid enough that adding content is the highest leverage thing I can do at this point.