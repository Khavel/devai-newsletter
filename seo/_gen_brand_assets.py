# -*- coding: utf-8 -*-
"""Generate Twitter avatar (800x800) + banner (1500x500) sets for the 3 brands.
Supersampled 2x for crisp text. Output -> seo/brand_assets/."""
import os, math
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "brand_assets")
os.makedirs(OUT, exist_ok=True)
SS = 2  # supersample factor

FB = r"C:\Windows\Fonts\seguibl.ttf"   # Segoe UI Black (headings)
FH = r"C:\Windows\Fonts\segoeuib.ttf"  # Segoe UI Bold
FS = r"C:\Windows\Fonts\seguisb.ttf"   # Segoe UI Semibold

def fnt(path, size):
    try: return ImageFont.truetype(path, size)
    except Exception: return ImageFont.load_default()

def vgrad(w, h, c1, c2):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    return img

def poly(cx, cy, r, n, rot=-90):
    return [(cx + r * math.cos(math.radians(rot + i * 360 / n)),
             cy + r * math.sin(math.radians(rot + i * 360 / n))) for i in range(n)]

def save(img, name):
    img = img.resize((img.width // SS, img.height // SS), Image.LANCZOS)
    p = os.path.join(OUT, name)
    img.save(p, "PNG")
    print("wrote", p, img.size)

# ---------------- AVATARS (800x800) ----------------
A = 800 * SS

def avatar_devai():
    img = vgrad(A, A, (79, 70, 229), (124, 58, 237))   # indigo -> violet
    d = ImageDraw.Draw(img)
    d.text((A/2, A*0.30), "</>", font=fnt(FB, int(A*0.16)), fill=(165, 180, 252), anchor="mm")
    d.text((A/2, A*0.52), "DevAI", font=fnt(FB, int(A*0.26)), fill="white", anchor="mm")
    d.text((A/2, A*0.72), "S E M A N A L", font=fnt(FS, int(A*0.072)), fill=(199, 210, 254), anchor="mm")
    save(img, "devai_avatar.png")

def avatar_proplab():
    img = Image.new("RGB", (A, A), (11, 15, 26))       # near-black
    d = ImageDraw.Draw(img)
    g = (34, 197, 94)
    d.line(poly(A/2, A*0.46, A*0.30, 7) + [poly(A/2, A*0.46, A*0.30, 7)[0]], fill=g, width=int(A*0.012), joint="curve")
    d.line(poly(A/2, A*0.46, A*0.19, 7) + [poly(A/2, A*0.46, A*0.19, 7)[0]], fill=(34, 197, 94, 120), width=int(A*0.006), joint="curve")
    d.text((A/2, A*0.46), "PL", font=fnt(FB, int(A*0.20)), fill="white", anchor="mm")
    d.text((A/2, A*0.82), "P R O P L A B", font=fnt(FS, int(A*0.075)), fill=g, anchor="mm")
    save(img, "proplab_avatar.png")

def avatar_futpicks():
    img = vgrad(A, A, (15, 81, 50), (21, 128, 61))     # deep green
    d = ImageDraw.Draw(img)
    cx, cy, r = A/2, A*0.305, A*0.16
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill="white")          # ball
    pent = poly(cx, cy, r*0.40, 5, rot=-90)
    d.polygon(pent, fill=(17, 24, 39))                         # center patch
    for px, py in pent:                                        # seams to edge
        ang = math.atan2(py - cy, px - cx)
        d.line([(px, py), (cx + r*math.cos(ang), cy + r*math.sin(ang))],
               fill=(17, 24, 39), width=int(A*0.007))
    d.text((A/2, A*0.585), "Fut", font=fnt(FB, int(A*0.18)), fill="white", anchor="mm")
    d.text((A/2, A*0.755), "Picks", font=fnt(FB, int(A*0.18)), fill=(187, 247, 208), anchor="mm")
    save(img, "futpicks_avatar.png")

# ---------------- BANNERS (1500x500) ----------------
BW, BH = 1500 * SS, 500 * SS

def banner(name, bg1, bg2, accent, title, sub, domain, motif):
    img = vgrad(BW, BH, bg1, bg2) if bg2 else Image.new("RGB", (BW, BH), bg1)
    d = ImageDraw.Draw(img)
    mx = int(BW * 0.06)
    d.text((mx, BH*0.34), title, font=fnt(FB, int(BH*0.20)), fill="white", anchor="lm")
    d.text((mx, BH*0.60), sub, font=fnt(FH, int(BH*0.072)), fill=(235, 235, 245), anchor="lm")
    d.text((mx, BH*0.76), domain, font=fnt(FB, int(BH*0.078)), fill=accent, anchor="lm")
    motif(d, accent)
    save(img, name)

def b_devai(d, accent):
    d.text((BW*0.85, BH*0.5), "</>", font=fnt(FB, int(BH*0.52)), fill=(120, 110, 220), anchor="mm")

def b_proplab(d, accent):
    cx, cy = BW*0.85, BH*0.5
    d.line(poly(cx, cy, BH*0.30, 7) + [poly(cx, cy, BH*0.30, 7)[0]], fill=accent, width=int(BH*0.012), joint="curve")
    for i, h in enumerate([0.22, 0.34, 0.18]):
        x = BW*0.965 + i*BH*0.05
        d.rectangle([x, cy - BH*h, x + BH*0.03, cy], fill=accent)

def b_futpicks(d, accent):
    d.ellipse([BW*0.80, BH*0.18, BW*0.80 + BH*0.6, BH*0.18 + BH*0.6], outline=accent, width=int(BH*0.014))

if __name__ == "__main__":
    avatar_devai(); avatar_proplab(); avatar_futpicks()
    banner("devai_banner.png", (79,70,229), (124,58,237), (199,210,254),
           "DevAI Semanal", "Trucos de IA para developers · cada semana", "devaisemanal.com", b_devai)
    banner("proplab_banner.png", (11,15,26), None, (34,197,94),
           "PropLab", "NBA & WNBA player props · 7-factor scoring model", "nbaproplab.com", b_proplab)
    banner("futpicks_banner.png", (15,81,50), (21,128,61), (74,222,128),
           "FutPicks", "Value football picks vs Pinnacle · Poisson + xG", "futpicks.com", b_futpicks)
    print("DONE")
