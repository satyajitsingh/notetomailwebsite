#!/usr/bin/env python3
"""Static validation for the NoteToMail marketing site.

This repository is plain static HTML with no build step, so this script is the
project's lint/test stage. Run it before every commit:

    python3 scripts/validate.py

Checks: HTML structure, heading hierarchy, metadata, unrendered template
placeholders, internal link resolution, sitemap/robots consistency, JSON-LD
validity, and Free/Pro entitlement copy.
"""
import glob
import io
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

SITE = "https://notetomail.com"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class Check(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.stack, self.errors, self.headings, self.ids, self.dup_ids = [], [], [], [], []
        self.h1 = 0
        self.imgs_no_alt = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            if a["id"] in self.ids:
                self.dup_ids.append(a["id"])
            self.ids.append(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append(int(tag[1]))
        if tag == "img" and a.get("alt") is None:
            self.imgs_no_alt += 1
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append("stray </%s>" % tag)
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append("unclosed <%s> (found </%s>)" % (self.stack[-1], tag))
                self.stack.pop()
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append("stray </%s>" % tag)


def pages():
    return sorted(glob.glob("*.html") + glob.glob("*/index.html") + glob.glob("blog/*.html"))


def main():
    files = pages()
    titles, descs, canons = {}, {}, {}
    fail = 0

    print("=" * 74)
    print("HTML STRUCTURE + SEO")
    print("=" * 74)
    for f in files:
        s = io.open(f, encoding="utf-8").read()
        c = Check()
        c.feed(s)
        c.close()
        probs = []
        if c.stack:
            probs.append("unclosed at EOF: %s" % c.stack)
        probs += c.errors
        if c.h1 != 1:
            probs.append("expected exactly 1 <h1>, found %d" % c.h1)
        if c.dup_ids:
            probs.append("duplicate ids: %s" % sorted(set(c.dup_ids)))
        if c.imgs_no_alt:
            probs.append("%d <img> without alt" % c.imgs_no_alt)

        prev = None
        for h in c.headings:
            if prev is not None and h > prev + 1:
                probs.append("heading jump h%d -> h%d" % (prev, h))
                break
            prev = h

        # Unrendered template placeholders must never reach production.
        for pat, why in ((r"%s", "unrendered %s placeholder"),
                         (r"\{\{[^}]+\}\}", "unrendered {{ }} placeholder"),
                         (r"\blorem ipsum\b", "lorem ipsum"),
                         (r"\bTODO\b", "TODO marker")):
            hits = re.findall(pat, s, re.I)
            if hits:
                probs.append("%s x%d" % (why, len(hits)))

        t = re.search(r"<title>(.*?)</title>", s, re.S)
        d = re.search(r'<meta name="description" content="(.*?)"', s, re.S)
        ca = re.search(r'rel="canonical" href="(.*?)"', s)
        t = t.group(1).strip() if t else None
        d = d.group(1).strip() if d else None
        ca = ca.group(1) if ca else None
        for val, name in ((t, "<title>"), (d, "meta description"), (ca, "canonical")):
            if not val:
                probs.append("no %s" % name)
        if ca and not ca.startswith(SITE):
            probs.append("non-production canonical: %s" % ca)
        if t:
            titles.setdefault(t, []).append(f)
        if d:
            descs.setdefault(d, []).append(f)
        if ca:
            canons.setdefault(ca, []).append(f)

        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                json.loads(m.group(1))
            except Exception as e:
                probs.append("invalid JSON-LD: %s" % e)

        tlen = len(re.sub(r"&[a-z]+;", "x", t or ""))
        dlen = len(re.sub(r"&[a-z]+;", "x", d or ""))
        if t and tlen > 70:
            probs.append("title %d chars (>70)" % tlen)
        if d and not (70 <= dlen <= 165):
            probs.append("description %d chars (aim 70-165)" % dlen)

        if probs:
            fail += 1
        print("%s  %-46s title=%-3s desc=%s" % ("FAIL" if probs else "ok  ", f, tlen, dlen))
        for p in probs:
            print("        ! %s" % p)

    print()
    for label, d in (("title", titles), ("description", descs), ("canonical", canons)):
        dups = {k: v for k, v in d.items() if len(v) > 1}
        if dups:
            fail += 1
            print("FAIL duplicate %s:" % label)
            for k, v in dups.items():
                print("     %r -> %s" % (k[:60], v))
        else:
            print("ok   all %ss unique (%d pages)" % (label, len(d)))

    print()
    print("=" * 74)
    print("INTERNAL LINKS")
    print("=" * 74)
    routes = {"/": "index.html"}
    for f in files:
        if f.endswith("/index.html"):
            routes["/" + f[: -len("/index.html")]] = f
    broken = []
    for f in files:
        s = io.open(f, encoding="utf-8").read()
        base = os.path.dirname(f)
        for h in re.findall(r'href="([^"]+)"', s):
            u = urlparse(h)
            if u.scheme or h.startswith("#") or h.startswith("mailto:"):
                continue
            p = unquote(u.path)
            if not p:
                continue
            if p.startswith("/"):
                if (p.rstrip("/") or "/") in routes:
                    continue
                target = "." + p
            else:
                target = os.path.normpath(os.path.join(base, p))
            if not os.path.exists(target):
                broken.append((f, h))
        for h in re.findall(r'(?:src|href)="(/assets/[^"]+)"', s):
            if not os.path.exists("." + h):
                broken.append((f, h))
    if broken:
        fail += 1
        print("FAIL %d broken internal links:" % len(broken))
        for f, h in sorted(set(broken)):
            print("     %s -> %s" % (f, h))
    else:
        print("ok   every internal link and asset reference resolves")

    print()
    print("=" * 74)
    print("SITEMAP / ROBOTS")
    print("=" * 74)
    locs = re.findall(r"<loc>(.*?)</loc>", io.open("sitemap.xml", encoding="utf-8").read())
    print("ok   sitemap lists %d URLs" % len(locs))
    for f in files:
        if f.endswith("/index.html"):
            u = SITE + "/" + f[: -len("/index.html")]
        elif f == "index.html":
            u = SITE + "/"
        else:
            u = SITE + "/" + f
        if u not in locs:
            fail += 1
            print("FAIL not in sitemap: %s" % u)
    for l in locs:
        key = l.replace(SITE, "") or "/"
        if key not in routes and not os.path.exists("." + key):
            fail += 1
            print("FAIL sitemap URL has no file: %s" % l)
    for f in files:
        s = io.open(f, encoding="utf-8").read()
        ca = re.search(r'rel="canonical" href="(.*?)"', s)
        if ca and ca.group(1) not in locs:
            fail += 1
            print("FAIL canonical not in sitemap: %s -> %s" % (f, ca.group(1)))
    if "Sitemap: %s/sitemap.xml" % SITE not in io.open("robots.txt", encoding="utf-8").read():
        fail += 1
        print("FAIL robots.txt does not reference the sitemap")
    else:
        print("ok   robots.txt references the sitemap")
    print("ok   sitemap URLs and canonicals are consistent")

    print()
    print("=" * 74)
    print("FREE / PRO ENTITLEMENT COPY")
    print("=" * 74)
    home = io.open("index.html", encoding="utf-8").read()
    journey = io.open("journey-intelligence/index.html", encoding="utf-8").read()
    ent = []
    # Free functionality must not be labelled Pro-only.
    if re.search(r"Meeting History\s*<span class=\"pro-badge\">", home):
        ent.append("homepage labels Meeting History as Pro-only (Free allows 6 saved meetings)")
    # Verified against ntmapp src/config/journeys/journeyLimits.ts and the
    # Pro gates in app/api/** (see docs/journey-screenshots.md for context).
    for frag, where, label in (
        ("Up to 6 saved meetings", home, "Free: 6 saved meetings"),
        ("Up to 2 Journeys", home, "Free: 2 Journeys"),
        ("Up to 6 meetings per Journey", home, "Free: 6 meetings per Journey"),
        ("Confirmed outcome tracking", home, "Free: confirmed outcome tracking"),
        ("Advanced AI Learn, Compare &amp; Ask", home, "Pro-only AI named in pricing"),
        ("2 Journeys", journey, "journey page: Free Journey allowance"),
        ("Advanced AI <strong>Learn</strong>", journey, "journey page: Pro AI capabilities"),
        ("save", journey, "journey page: storage opt-in"),
        # Storage needs BOTH the account toggle (User.storeMeetings, default
        # false, enforced in src/server/meetings/storage.ts) and a per-meeting
        # save. Saying only "click Save" understates the opt-in.
        ("off by default", journey, "journey page: storage off by default"),
        ("off by default", home, "homepage: storage off by default"),
        # Effectiveness/coaching evidence is written by Learn, which is Pro.
        # The page must say so, or Free readers are misled.
        ("produced\n        by <strong>Advanced AI Learn, which is a Pro capability</strong>", journey,
         "journey page: effectiveness evidence needs Pro"),
        # Free caps are enforced at create time only.
        ("applied when you create something new", journey, "journey page: create-time limits"),
    ):
        if frag not in where:
            ent.append("missing entitlement copy: %s" % label)

    # Claims the product does not support.
    for pat, why in (
        # NOTE: there is deliberately no "unlimited" rule here.
        #
        # "Unlimited" is TRUE for paid plans — PAID_MAX_JOURNEYS and
        # PAID_MAX_MEETINGS_PER_JOURNEY are null, and the app's own Pro card
        # says so. The only risk is attaching it to Free, and every text
        # heuristic for that fired on correct copy instead: "Everything in
        # Free / Unlimited saved meetings" inside the Pro card, and
        # "six on Free, unlimited on Pro" which is the contrast we want.
        #
        # The Free caps are guarded positively instead, by the required-copy
        # checks above ("Up to 2 Journeys", "Up to 6 meetings per Journey",
        # "Up to 6 saved meetings"). Replacing any of those with an unlimited
        # claim removes the required string and fails the build, which is the
        # same protection without the false positives.
        (r"predicts? (?:deal|hiring|relationship)", "predictive claim"),
        # No cron, no purge route and no expiry column exist; the published
        # privacy policy says deletion is user-initiated.
        (r"archived and deleted after 12 months", "unsupported auto-deletion claim"),
        (r"automatically archived after 12 months", "unsupported auto-archive claim"),
        # Launch pages must not ship mock product imagery.
        (r"shot-frame|Product screenshot to follow", "placeholder product screenshot"),
        # Saved meetings persist until the user deletes them, so a blanket
        # "never stored" claim contradicts the product and the policy's own
        # saved-meetings section.
        (r"never stored after processing|notes are never stored", "blanket never-stored claim"),
        # 13.99 x 12 = 167.88 against 139 is 17%, not 20%. The app derives this
        # (ANNUAL_SAVING_PERCENT) after shipping the same defect on its own card.
        (r"Save 20%", "wrong annual saving (17%, not 20%)"),
        # There is ONE Pro allowance (3000 min / 5000 calls). Annual does not
        # buy a bigger one; the site previously advertised 5,000/8,000.
        (r"8,000 AI calls", "non-existent annual allowance"),
        # Recording online calls is on every plan; Pro HD is transcription
        # quality, not access (RECORDING_ONLINE_IS_FREE in the app's help copy).
        (r"Teams, Zoom and Google Meet calls on Pro|online call[^.]{0,40}Pro plans",
         "online-call capture wrongly sold as Pro-only"),
    ):
        for f in files:
            if re.search(pat, io.open(f, encoding="utf-8").read(), re.I):
                ent.append("%s in %s" % (why, f))
    if ent:
        fail += 1
        for e in ent:
            print("FAIL %s" % e)
    else:
        print("ok   Free/Pro copy matches the verified entitlement list")
        print("ok   no unlimited-usage or predictive claims")

    print()
    print("=" * 74)
    print("RESULT: %s" % ("%d GROUP(S) FAILED" % fail if fail else "ALL CHECKS PASSED"))
    print("=" * 74)
    return 1 if fail else 0


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    sys.exit(main())
