from flask import Flask, render_template_string, request, redirect, url_for, session
import base64
import hashlib
import hmac
import io
import json
import uuid
import urllib.error
import urllib.request
from urllib.parse import urlencode

import qrcode
import qrcode.constants
from qrcode.image import svg as qr_svg

app = Flask(__name__)
app.secret_key = "nexora_secret_2025"

RAZORPAY_KEY_ID     = "rzp_test_XXXXXXXXXXXXXXXXXX"
RAZORPAY_KEY_SECRET = "YOUR_SECRET_HERE"

UPI_VPA          = "nexora@upi"
UPI_PAYEE_NAME   = "NexoraEduTech"


def _razorpay_keys_ok() -> bool:
    kid, sec = RAZORPAY_KEY_ID.strip(), RAZORPAY_KEY_SECRET.strip()
    return bool(kid) and "XXXXX" not in kid and sec and "YOUR_SECRET" not in sec


def create_razorpay_order(amount_paise: int, receipt: str) -> dict:
    if not _razorpay_keys_ok():
        raise RuntimeError("Razorpay keys not configured")
    url = "https://api.razorpay.com/v1/orders"
    auth = base64.b64encode(f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode()).decode()
    body = json.dumps(
        {"amount": amount_paise, "currency": "INR", "receipt": receipt[:40]}
    ).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def verify_razorpay_signature(rzp_order_id: str, rzp_payment_id: str, signature: str) -> bool:
    if not signature or not _razorpay_keys_ok():
        return False
    msg = f"{rzp_order_id}|{rzp_payment_id}".encode()
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(), msg, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def build_upi_uri(amount: str, service: str, tier: str, order_id: str) -> str:
    note = f"{service} – {tier} · {order_id}"
    if len(note) > 80:
        note = note[:77] + "…"
    params = {
        "pa": UPI_VPA,
        "pn": UPI_PAYEE_NAME,
        "am": f"{float(amount):.2f}",
        "cu": "INR",
        "tn": note,
    }
    return "upi://pay?" + urlencode(params)


def qr_svg_data_uri(payload: str) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qr_svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"

# ════════════════════════════════════════════
#  VIDEO LIBRARY
# ════════════════════════════════════════════
VIDEO_LIBRARY = {
    "Online Learning Program": {
        "Basic": [
            {"id":"v1","title":"Introduction to Online Learning","duration":"12:30","thumb":"https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
            {"id":"v2","title":"Digital Tools for Students","duration":"18:45","thumb":"https://images.unsplash.com/photo-1587620962725-abab7fe55159?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
            {"id":"v3","title":"Effective Note-Taking Strategies","duration":"22:10","thumb":"https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
        ],
        "Standard": [
            {"id":"v4","title":"Live Session: Advanced Concepts","duration":"45:00","thumb":"https://images.unsplash.com/photo-1523580494863-6f3031224c94?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
            {"id":"v5","title":"Mentorship Q&A Session","duration":"30:20","thumb":"https://images.unsplash.com/photo-1556761175-b413da4baf72?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
        ],
        "Premium": [
            {"id":"v6","title":"Master Class: Future of EdTech","duration":"60:00","thumb":"https://images.unsplash.com/photo-1552664730-d307ca884978?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
            {"id":"v7","title":"1-on-1 Career Guidance Recording","duration":"55:30","thumb":"https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
        ],
    },
    "Professional Training Program": {
        "Basic": [
            {"id":"t1","title":"Python for Professionals","duration":"35:00","thumb":"https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
            {"id":"t2","title":"Data Analysis Fundamentals","duration":"28:15","thumb":"https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
        ],
        "Standard": [
            {"id":"t3","title":"Real-World Project Walkthrough","duration":"50:00","thumb":"https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
            {"id":"t4","title":"Resume & Interview Prep","duration":"40:00","thumb":"https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
        ],
        "Premium": [
            {"id":"t5","title":"Advanced ML & AI Projects","duration":"75:00","thumb":"https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
            {"id":"t6","title":"Cloud Deployment Masterclass","duration":"65:00","thumb":"https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
        ],
    },
    "EdTech Consulting Service": {
        "Basic": [
            {"id":"c1","title":"Digital Strategy 101","duration":"20:00","thumb":"https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
        ],
        "Standard": [
            {"id":"c2","title":"Institution Transformation Case Studies","duration":"45:00","thumb":"https://images.unsplash.com/photo-1552664730-d307ca884978?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
        ],
        "Premium": [
            {"id":"c3","title":"Executive EdTech Roadmap Workshop","duration":"90:00","thumb":"https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=400","embed":"https://www.youtube.com/embed/dQw4w9WgXcQ"},
        ],
    },
}

TIER_ORDER = ["Basic", "Standard", "Premium"]

def get_accessible_videos(service_title, tier):
    videos = []
    for t in TIER_ORDER:
        videos += VIDEO_LIBRARY.get(service_title, {}).get(t, [])
        if t == tier:
            break
    return videos


def list_checkout_courses():
    out = []
    seen = set()
    for program_name, by_tier in VIDEO_LIBRARY.items():
        for tier in TIER_ORDER:
            for vid in by_tier.get(tier, []):
                label = f"{program_name} — {vid['title']}"
                if label in seen:
                    continue
                seen.add(label)
                out.append(label)
    for title in (
        "Python Programming",
        "Data Science",
        "Web Development",
        "Machine Learning",
    ):
        label = f"Open Catalogue — {title}"
        if label not in seen:
            seen.add(label)
            out.append(label)
    return out

services_data = {
    "online": {
        "title":    "Online Learning Program",
        "price":    "4999",
        "standard": "7999",
        "premium":  "12999",
        "points":   [
            "Flexibility to learn anytime",
            "Affordable compared to traditional education",
            "Global recognition of certificates",
            "Expert-led live & recorded sessions"
        ],
        "hero_image": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=1400",
        "gallery": [
            "https://images.unsplash.com/photo-1596495577886-d920f1fb7238?w=500",
            "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=500",
            "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=500",
        ],
    },
    "training": {
        "title":    "Professional Training Program",
        "price":    "9999",
        "standard": "14999",
        "premium":  "19999",
        "points":   [
            "Bridges skill gaps for job-readiness",
            "Boosts career advancement",
            "Hands-on project experience",
            "Industry-certified mentors"
        ],
        "hero_image": "https://images.unsplash.com/photo-1531482615713-2afd69097998?w=1400",
        "gallery": [
            "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=500",
            "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=500",
            "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=500",
        ],
    },
    "consulting": {
        "title":    "EdTech Consulting Service",
        "price":    "14999",
        "standard": "19999",
        "premium":  "24999",
        "points":   [
            "Strategic digital transformation guidance",
            "Institution-wide innovation roadmap",
            "Competitive advantage in education sector",
            "Dedicated expert consultant"
        ],
        "hero_image": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=1400",
        "gallery": [
            "https://images.unsplash.com/photo-1556761175-4b46a572b786?w=500",
            "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=500",
            "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=500",
        ],
    },
}

# ════════════════════════════════════════════
#  SHARED HEAD / NAV SNIPPET
# ════════════════════════════════════════════
SHARED_HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --blue-deep: #000428;
    --blue-mid:  #004e92;
    --accent:    #00c6ff;
    --gold:      #ffd700;
    --danger:    #ff512f;
    --danger2:   #dd2476;
    --white:     #ffffff;
    --glass:     rgba(255,255,255,0.08);
    --glass2:    rgba(255,255,255,0.14);
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    font-family: 'DM Sans', sans-serif;
    background: linear-gradient(135deg, var(--blue-deep), var(--blue-mid));
    min-height: 100vh;
    color: var(--white);
  }
  h1,h2,h3,h4 { font-family: 'Syne', sans-serif; }

  /* ── NAV ── */
  .nav {
    position: sticky; top: 0; z-index: 100;
    background: rgba(0,4,40,0.75);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }
  .nav-inner {
    max-width: 1200px; margin: 0 auto;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 20px; height: 60px;
  }
  .nav-logo {
    font-family: 'Syne', sans-serif; font-weight: 800;
    font-size: 1.25em; color: var(--accent); text-decoration: none;
    white-space: nowrap;
  }
  .nav-links {
    display: flex; gap: 6px; align-items: center; list-style: none;
  }
  .nav-links a {
    color: rgba(255,255,255,0.82); text-decoration: none;
    padding: 7px 14px; border-radius: 8px; font-size: .9em; font-weight: 500;
    transition: background .2s, color .2s;
    white-space: nowrap;
  }
  .nav-links a:hover { background: var(--glass2); color: var(--white); }

  /* hamburger */
  .hamburger {
    display: none; flex-direction: column; gap: 5px;
    cursor: pointer; padding: 6px; background: none; border: none;
  }
  .hamburger span {
    display: block; width: 24px; height: 2px;
    background: var(--white); border-radius: 2px;
    transition: transform .3s, opacity .3s;
  }
  .hamburger.open span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
  .hamburger.open span:nth-child(2) { opacity: 0; }
  .hamburger.open span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

  @media (max-width: 640px) {
    .hamburger { display: flex; }
    .nav-links {
      display: none; flex-direction: column;
      position: absolute; top: 60px; left: 0; right: 0;
      background: rgba(0,4,40,0.97);
      border-bottom: 1px solid rgba(255,255,255,0.1);
      padding: 12px 16px 16px; gap: 4px;
    }
    .nav-links.open { display: flex; }
    .nav-links a { padding: 10px 14px; font-size: 1em; }
  }

  /* ── BUTTONS ── */
  .btn-grad {
    display: inline-block;
    background: linear-gradient(45deg, var(--danger), var(--danger2));
    color: var(--white); text-decoration: none; border: none;
    padding: 12px 26px; border-radius: 50px; font-size: 1em; font-weight: 700;
    cursor: pointer; transition: opacity .2s, transform .15s;
    font-family: 'DM Sans', sans-serif;
  }
  .btn-grad:hover { opacity: .9; transform: translateY(-2px); }

  .btn-blue {
    display: inline-block;
    background: linear-gradient(45deg, #00b4d8, #0077b6);
    color: var(--white); text-decoration: none; border: none;
    padding: 14px 36px; border-radius: 14px; font-size: 1.05em; font-weight: 800;
    cursor: pointer; transition: opacity .2s, transform .15s;
    font-family: 'DM Sans', sans-serif;
  }
  .btn-blue:hover { opacity: .9; transform: translateY(-2px); }

  /* ── FOOTER ── */
  .footer {
    text-align: center; padding: 20px 16px;
    font-size: .82em; color: rgba(255,255,255,0.5);
    border-top: 1px solid rgba(255,255,255,0.07);
    margin-top: 40px;
  }
  .footer a { color: var(--accent); text-decoration: none; }
</style>
<script>
  document.addEventListener('DOMContentLoaded', function(){
    var btn = document.getElementById('hamburger');
    var menu = document.getElementById('navLinks');
    if(btn && menu){
      btn.addEventListener('click', function(){
        btn.classList.toggle('open');
        menu.classList.toggle('open');
      });
    }
  });
</script>
"""

NAV_HTML = """
<nav class="nav">
  <div class="nav-inner">
    <a href="/" class="nav-logo">🎓 Nexora</a>
    <button class="hamburger" id="hamburger" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
    <ul class="nav-links" id="navLinks">
      <li><a href="/">Home</a></li>
      <li><a href="/services">Services</a></li>
      <li><a href="/courses">Courses</a></li>
      <li><a href="/faculty">Faculty</a></li>
    </ul>
  </div>
</nav>
"""

# ════════════════════════════════════════════
#  HOME PAGE
# ════════════════════════════════════════════
home_page = """
<!DOCTYPE html>
<html lang="en">
<head>
""" + SHARED_HEAD + """
<title>Nexora EduTech</title>
<style>
  .hero-wrap {
    position: relative; min-height: calc(100vh - 60px);
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    text-align: center; padding: 60px 20px 80px;
    background: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1400') no-repeat center center/cover;
  }
  .hero-wrap::before {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(to bottom, rgba(0,4,40,.6), rgba(0,4,40,.82));
  }
  .hero-content { position: relative; z-index: 1; max-width: 800px; }
  .hero-content h1 {
    font-size: clamp(2.2em, 7vw, 4.5em);
    line-height: 1.1; margin-bottom: 18px;
    text-shadow: 0 2px 20px rgba(0,0,0,.5);
  }
  .hero-content h1 span { color: var(--accent); }
  .hero-content p {
    font-size: clamp(1em, 2.5vw, 1.35em);
    opacity: .88; max-width: 600px; margin: 0 auto 36px; line-height: 1.65;
  }
  .hero-btns {
    display: flex; flex-wrap: wrap; gap: 14px; justify-content: center;
  }
  .hero-btns a {
    min-width: 160px; text-align: center;
    padding: 14px 28px; font-size: 1em;
  }
  @media (max-width: 480px) {
    .hero-btns a { width: 100%; max-width: 320px; }
  }
</style>
</head>
<body>
""" + NAV_HTML + """
<div class="hero-wrap">
  <div class="hero-content">
    <h1>WELCOME TO <span>Nexora</span></h1>
    <p>Empowering education with technology, innovation, and premium digital experiences.</p>
    <div class="hero-btns">
      <a href="/services" class="btn-grad">Explore Services 🚀</a>
      <a href="/faculty"  class="btn-grad">Meet Faculty 👨‍🏫</a>
      <a href="/courses"  class="btn-grad">Courses Offered 📔</a>
    </div>
  </div>
</div>
<footer class="footer">
  📞 +91 1234567890 &nbsp;|&nbsp; ✉ <a href="mailto:support@nexoraedutech.com">support@nexoraedutech.com</a><br>
  &copy; 2025 Nexora EduTech. All rights reserved.
</footer>
</body>
</html>
"""

# ════════════════════════════════════════════
#  SERVICES PAGE
# ════════════════════════════════════════════
services_page = """
<!DOCTYPE html>
<html lang="en">
<head>
""" + SHARED_HEAD + """
<title>Our Services – Nexora EduTech</title>
<style>
  .page-hero {
    height: clamp(160px, 30vw, 260px);
    background: url('https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=1400') no-repeat center center/cover;
    position: relative; display: flex; justify-content: center; align-items: center;
  }
  .page-hero::after { content:''; position:absolute; inset:0; background:rgba(0,4,40,.6); }
  .page-hero h1 {
    position: relative; z-index: 1;
    font-size: clamp(1.8em, 5vw, 3em); text-shadow: 0 2px 10px rgba(0,0,0,.5);
  }
  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr));
    gap: 24px; max-width: 1100px; margin: 48px auto; padding: 0 20px;
  }
  .s-card {
    background: var(--glass); border-radius: 18px; overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 8px 24px rgba(0,0,0,.4);
    transition: transform .25s, box-shadow .25s;
  }
  .s-card:hover { transform: translateY(-6px); box-shadow: 0 16px 40px rgba(0,0,0,.55); }
  .s-card img { width: 100%; height: 200px; object-fit: cover; display: block; }
  .s-card-body { padding: 22px; }
  .s-card-body h2 { color: var(--accent); font-size: 1.3em; margin-bottom: 10px; }
  .s-card-body p { color: rgba(255,255,255,.78); font-size: .95em; line-height: 1.6; margin-bottom: 18px; }
</style>
</head>
<body>
""" + NAV_HTML + """
<div class="page-hero"><h1>Our Services</h1></div>
<div class="cards-grid">
  <div class="s-card">
    <img src="https://images.unsplash.com/photo-1596495577886-d920f1fb7238?w=600" alt="Online Learning">
    <div class="s-card-body">
      <h2>Online Learning</h2>
      <p>Flexible, affordable, and accessible education with live &amp; recorded classes.</p>
      <a href="/services/online" class="btn-grad">View Details</a>
    </div>
  </div>
  <div class="s-card">
    <img src="https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600" alt="Training Programs">
    <div class="s-card-body">
      <h2>Training Programs</h2>
      <p>Job-oriented training with real projects, mentorship, and career support.</p>
      <a href="/services/training" class="btn-grad">View Details</a>
    </div>
  </div>
  <div class="s-card">
    <img src="https://images.unsplash.com/photo-1556761175-4b46a572b786?w=600" alt="EdTech Consulting">
    <div class="s-card-body">
      <h2>EdTech Consulting</h2>
      <p>Transform your institution with expert digital strategy and innovation.</p>
      <a href="/services/consulting" class="btn-grad">View Details</a>
    </div>
  </div>
</div>
<footer class="footer">&copy; 2025 Nexora EduTech. All rights reserved.</footer>
</body>
</html>
"""

# ════════════════════════════════════════════
#  SERVICE DETAIL TEMPLATE
# ════════════════════════════════════════════
detail_template = """
<!DOCTYPE html>
<html lang="en">
<head>
""" + SHARED_HEAD + """
<title>{{title}} – Nexora EduTech</title>
<style>
  .detail-hero {
    height: clamp(220px, 40vw, 420px);
    background: url('{{hero_image}}') no-repeat center center/cover;
    position: relative; display: flex; align-items: flex-end; justify-content: center;
  }
  .detail-hero::after { content:''; position:absolute; inset:0; background:linear-gradient(to bottom,rgba(0,0,0,.1),rgba(0,4,40,.88)); }
  .detail-hero h1 {
    position:relative; z-index:1;
    font-size: clamp(1.6em, 4vw, 2.8em);
    padding-bottom: clamp(16px, 3vw, 28px);
    text-shadow: 0 2px 10px rgba(0,0,0,.8); text-align:center; padding-inline: 16px;
  }
  .section {
    width: min(92%, 1000px); margin: 28px auto;
    background: var(--glass); padding: clamp(20px, 4vw, 36px);
    border-radius: 20px; box-shadow: 0 4px 16px rgba(0,0,0,.3);
    border: 1px solid rgba(255,255,255,0.07);
  }
  .section h2 { color: var(--gold); font-size: 1.35em; margin-bottom: 18px; }
  .points-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 200px), 1fr));
    gap: 12px; margin-bottom: 28px;
  }
  .point {
    background: rgba(255,255,255,0.08); border-radius: 10px; padding: 13px 15px;
    font-size: .95em; border-left: 3px solid var(--accent); line-height: 1.5;
  }
  .gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 220px), 1fr));
    gap: 12px;
  }
  .gallery img {
    width:100%; height: 180px; object-fit:cover; border-radius:12px;
    box-shadow: 0 4px 12px rgba(0,0,0,.4); transition: transform .25s, box-shadow .25s;
    display: block;
  }
  .gallery img:hover { transform: scale(1.03); box-shadow: 0 8px 20px rgba(0,0,0,.5); }

  /* Pricing tiers */
  .tiers {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr));
    gap: 20px; margin-top: 10px;
  }
  .tier {
    background: white; color: #333; border-radius: 16px;
    padding: clamp(20px, 4vw, 28px); text-align:center;
    border: 2px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,.12);
    transition: transform .2s, box-shadow .2s;
  }
  .tier:hover { transform: translateY(-5px); box-shadow: 0 12px 28px rgba(0,0,0,.18); }
  .tier h3 { color: #734b6d; margin-top:0; font-size:1.15em; margin-bottom: 8px; }
  .tier p { font-size: .88em; color: #666; margin: 8px 0; line-height: 1.5; }
  .tier .price { font-size: 2em; font-weight: 800; color: #004e92; margin: 14px 0 4px; }
  .pay-btn {
    width: 100%; padding: 13px 0;
    background: linear-gradient(45deg, var(--danger), var(--danger2));
    color: white; border: none; border-radius: 30px; font-size: .98em; font-weight: 700;
    cursor: pointer; margin-top: 14px; transition: opacity .2s, transform .2s;
    font-family: 'DM Sans', sans-serif;
  }
  .pay-btn:hover { opacity: .88; transform: scale(1.02); }
</style>
</head>
<body>
""" + NAV_HTML + """
<div class="detail-hero"><h1>{{title}}</h1></div>

<div class="section">
  <h2>✨ Highlights</h2>
  <div class="points-grid">
    {% for p in points %}<div class="point">✔ {{p}}</div>{% endfor %}
  </div>
  <h2>📸 Gallery</h2>
  <div class="gallery">
    {% for img in gallery %}<img src="{{img}}" alt="Service image" loading="lazy">{% endfor %}
  </div>
</div>

<div class="section">
  <h2>💳 Choose Your Plan</h2>
  <div class="tiers">
    <div class="tier">
      <h3>⭐ Basic</h3>
      <p>Access to core features and recorded sessions.</p>
      <div class="price">₹{{price}}</div>
      <form method="post" action="/checkout">
        <input type="hidden" name="service" value="{{title}}">
        <input type="hidden" name="tier"    value="Basic">
        <input type="hidden" name="amount"  value="{{price}}">
        <button class="pay-btn">Enroll – Basic</button>
      </form>
    </div>
    <div class="tier">
      <h3>🥈 Standard</h3>
      <p>Includes mentorship, live projects, and certificates.</p>
      <div class="price">₹{{standard}}</div>
      <form method="post" action="/checkout">
        <input type="hidden" name="service" value="{{title}}">
        <input type="hidden" name="tier"    value="Standard">
        <input type="hidden" name="amount"  value="{{standard}}">
        <button class="pay-btn">Enroll – Standard</button>
      </form>
    </div>
    <div class="tier">
      <h3>👑 Premium</h3>
      <p>Lifetime access, advanced resources, and priority support.</p>
      <div class="price">₹{{premium}}</div>
      <form method="post" action="/checkout">
        <input type="hidden" name="service" value="{{title}}">
        <input type="hidden" name="tier"    value="Premium">
        <input type="hidden" name="amount"  value="{{premium}}">
        <button class="pay-btn">Enroll – Premium</button>
      </form>
    </div>
  </div>
</div>

<footer class="footer">&copy; 2025 Nexora EduTech. All rights reserved.</footer>
</body>
</html>
"""

# ════════════════════════════════════════════
#  CHECKOUT DETAILS (Step 1)
# ════════════════════════════════════════════
checkout_details_template = """
<!DOCTYPE html>
<html lang="en">
<head>
""" + SHARED_HEAD + """
<title>Complete Enrolment – Nexora EduTech</title>
<style>
  body {
    display: flex; flex-direction: column;
    justify-content: flex-start; align-items: center;
    padding: 20px 16px 40px;
  }
  .card {
    background: white; border-radius: 24px;
    max-width: 560px; width: 100%;
    box-shadow: 0 24px 64px rgba(0,0,0,.45); overflow: hidden;
    margin-top: 20px;
  }
  .card-top {
    background: linear-gradient(135deg, var(--blue-deep), #0077b6);
    padding: clamp(18px, 4vw, 26px) clamp(20px, 5vw, 32px);
    text-align: center; color: white;
  }
  .card-top .logo { font-size: 1.2em; font-weight: 800; font-family:'Syne',sans-serif; }
  .card-top .subtitle { font-size: .82em; opacity: .8; margin-top: 4px; }
  .card-body { padding: clamp(20px, 5vw, 32px); }
  .summary {
    background: #f0f7ff; border-radius: 12px;
    padding: 14px 18px; margin-bottom: 22px; font-size: .88em;
  }
  .summary-row {
    display: flex; justify-content: space-between;
    margin: 4px 0; color: #333; flex-wrap: wrap; gap: 4px;
  }
  .summary-row strong { color: #0077b6; }
  .form-title {
    font-size: .95em; font-weight: 800; color: #1a1a2e;
    margin-bottom: 14px; text-transform: uppercase; letter-spacing: .6px;
    border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;
    font-family: 'Syne', sans-serif;
  }
  .form-title.mt { margin-top: 20px; }
  .form-group { margin-bottom: 14px; }
  .form-group label {
    display: block; font-size: .78em; font-weight: 700; color: #666;
    margin-bottom: 5px; text-transform: uppercase; letter-spacing: .4px;
  }
  .form-group input,
  .form-group select,
  .form-group textarea {
    width: 100%; padding: 11px 14px; border: 2px solid #e2e8f0; border-radius: 10px;
    font-size: .95em; font-family: 'DM Sans', sans-serif; color: #222;
    transition: border-color .2s, box-shadow .2s; background: white;
    -webkit-appearance: none; appearance: none;
  }
  .form-group textarea { min-height: 72px; resize: vertical; }
  .form-group input:focus,
  .form-group select:focus,
  .form-group textarea:focus {
    outline: none; border-color: #0077b6;
    box-shadow: 0 0 0 3px rgba(0,119,182,.12);
  }
  .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  @media (max-width: 400px) { .row2 { grid-template-columns: 1fr; } }
  .pay-btn {
    width: 100%; padding: 15px;
    background: linear-gradient(45deg, var(--danger), var(--danger2));
    color: white; border: none; border-radius: 12px;
    font-size: 1.02em; font-weight: 800; cursor: pointer;
    transition: opacity .2s, transform .15s; margin-top: 6px;
    font-family: 'DM Sans', sans-serif;
  }
  .pay-btn:hover { opacity: .92; transform: translateY(-1px); }
  .secure { text-align:center; margin-top:12px; font-size:.75em; color:#aaa; }
  .secure span { color: #2ecc71; font-weight: 700; }
  .err { color: #e74c3c; font-size: .85em; margin-bottom: 12px; padding: 10px 14px; background:#fff5f5; border-radius:8px; }
</style>
</head>
<body>
""" + NAV_HTML + """
<div class="card">
  <div class="card-top">
    <div class="logo">🎓 Nexora EduTech</div>
    <div class="subtitle">Step 1 of 2 · Your details</div>
  </div>
  <div class="card-body">
    <div class="summary">
      <div class="summary-row"><span>Order</span><strong>#{{order_id}}</strong></div>
      <div class="summary-row"><span>Service</span><strong>{{service}}</strong></div>
      <div class="summary-row"><span>Plan</span><strong>{{tier}}</strong></div>
      <div class="summary-row"><span>Due</span><strong>₹{{amount}}</strong></div>
    </div>
    {% if err %}<div class="err">{{ err }}</div>{% endif %}

    <div class="form-title">📋 Your Details</div>
    <form method="post" action="/checkout/details">
      <div class="form-group">
        <label>Full Name *</label>
        <input type="text" name="student_name" placeholder="e.g. Priya Sharma" required autocomplete="name" value="{{ saved_name }}">
      </div>
      <div class="row2">
        <div class="form-group">
          <label>Email *</label>
          <input type="email" name="student_email" placeholder="you@example.com" required autocomplete="email" value="{{ saved_email }}">
        </div>
        <div class="form-group">
          <label>Phone *</label>
          <input type="tel" name="student_phone" placeholder="10-digit mobile" maxlength="10" required autocomplete="tel" value="{{ saved_phone }}">
        </div>
      </div>

      <div class="form-title mt">📚 Course &amp; Schedule</div>
      <div class="form-group">
        <label>Select course *</label>
        <select name="student_course_track" required>
          <option value="">— Choose a course —</option>
          {% for c in course_choices %}
          <option value="{{ c }}" {% if saved_course == c %}selected{% endif %}>{{ c }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="form-group">
        <label>Batch timing preference</label>
        <select name="student_batch_pref">
          <option value="">— Select if applicable —</option>
          <option value="Morning (6am–12pm)" {% if saved_batch == 'Morning (6am–12pm)' %}selected{% endif %}>Morning (6am–12pm)</option>
          <option value="Afternoon (12pm–5pm)" {% if saved_batch == 'Afternoon (12pm–5pm)' %}selected{% endif %}>Afternoon (12pm–5pm)</option>
          <option value="Evening (5pm–10pm)" {% if saved_batch == 'Evening (5pm–10pm)' %}selected{% endif %}>Evening (5pm–10pm)</option>
          <option value="Weekend only" {% if saved_batch == 'Weekend only' %}selected{% endif %}>Weekend only</option>
          <option value="Flexible / self-paced" {% if saved_batch == 'Flexible / self-paced' %}selected{% endif %}>Flexible / self-paced</option>
        </select>
      </div>
      <div class="form-group">
        <label>Notes for our team (optional)</label>
        <textarea name="student_course_notes" placeholder="Learning goals, prior experience, accessibility needs…">{{ saved_notes }}</textarea>
      </div>

      <button class="pay-btn" type="submit">Continue to UPI payment →</button>
    </form>
    <div class="secure"><span>✔</span> Payment QR is shown only on the next step</div>
  </div>
</div>
</body>
</html>
"""

# ════════════════════════════════════════════
#  CHECKOUT PAY (Step 2)
# ════════════════════════════════════════════
checkout_pay_template = """
<!DOCTYPE html>
<html lang="en">
<head>
""" + SHARED_HEAD + """
<title>Pay – Nexora EduTech</title>
<style>
  body {
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    padding: 30px 16px;
  }
  .wrap {
    background: white; border-radius: 24px;
    max-width: 400px; width: 100%;
    padding: clamp(28px, 6vw, 44px) clamp(20px, 5vw, 32px);
    text-align: center; box-shadow: 0 24px 64px rgba(0,0,0,.45);
    margin-top: 20px;
  }
  .amount { font-size: clamp(1.8em, 6vw, 2.4em); font-weight: 800; color: #004e92; margin-bottom: 6px; font-family:'Syne',sans-serif; }
  .course { font-size: .98em; font-weight: 600; color: #333; line-height:1.5; margin-bottom:24px; padding:0 4px; }
  .qr-box {
    display: inline-block; padding: 12px; background: #f8fbff;
    border-radius: 16px; border: 1px solid #d6e8ff;
  }
  .qr-box img { width: min(240px, 72vw); height: auto; display: block; }
  .scan-tip { margin-top: 16px; font-size: .82em; color: #888; }
</style>
</head>
<body>
""" + NAV_HTML + """
<div class="wrap">
  <div class="amount">₹{{amount}}</div>
  <div class="course">{{course_selected}}</div>
  {% if payment_qr %}
  <div class="qr-box">
    <img src="{{payment_qr}}" alt="UPI Payment QR code">
  </div>
  <p class="scan-tip">📱 Scan with any UPI app to pay</p>
  {% endif %}
</div>
</body>
</html>
"""

# ════════════════════════════════════════════
#  PAYMENT SUCCESS
# ════════════════════════════════════════════
success_template = """
<!DOCTYPE html>
<html lang="en">
<head>
""" + SHARED_HEAD + """
<title>Payment Successful – Nexora EduTech</title>
<style>
  body { display:flex; flex-direction:column; justify-content:center; align-items:center; padding:24px 16px; }
  .card {
    background: white; border-radius: 24px;
    max-width: 520px; width: 100%;
    padding: clamp(28px, 6vw, 44px) clamp(20px, 5vw, 40px);
    box-shadow: 0 24px 64px rgba(0,0,0,.45); text-align: center;
    margin-top: 20px;
  }
  .check { font-size: clamp(3em, 10vw, 4.5em); margin-bottom: 8px; animation: pop .5s cubic-bezier(.36,.07,.19,.97); }
  @keyframes pop { 0%{transform:scale(0)} 70%{transform:scale(1.2)} 100%{transform:scale(1)} }
  h1 { color: #1a1a2e; font-size: clamp(1.4em, 4vw, 1.9em); margin-bottom: 8px; }
  .welcome { color: #0077b6; font-size: clamp(1em, 3vw, 1.15em); font-weight: 800; margin-bottom: 22px; }
  .info-box { background: #f0f7ff; border-radius: 14px; padding: clamp(14px,4vw,20px); text-align: left; margin-bottom: 24px; }
  .info-row {
    display: flex; justify-content: space-between; align-items: flex-start;
    padding: 7px 0; border-bottom: 1px solid #dde8f5;
    font-size: clamp(.8em, 2.5vw, .92em); color: #444; gap: 10px; flex-wrap: wrap;
  }
  .info-row:last-child { border-bottom: none; }
  .info-row strong { color: #004e92; text-align:right; flex:1; word-break:break-all; }
</style>
</head>
<body>
""" + NAV_HTML + """
<div class="card">
  <div class="check">✅</div>
  <h1>Payment Successful!</h1>
  <div class="welcome">Welcome aboard, {{student_name}}! 🎉</div>
  <div class="info-box">
    <div class="info-row"><span>Name</span><strong>{{student_name}}</strong></div>
    <div class="info-row"><span>Email</span><strong>{{student_email}}</strong></div>
    <div class="info-row"><span>Phone</span><strong>{{student_phone}}</strong></div>
    <div class="info-row"><span>Service</span><strong>{{service}}</strong></div>
    <div class="info-row"><span>Plan</span><strong>{{tier}}</strong></div>
    <div class="info-row"><span>Amount Paid</span><strong>₹{{amount}}</strong></div>
    {% if course_track %}<div class="info-row"><span>Course focus</span><strong>{{course_track}}</strong></div>{% endif %}
    {% if batch_pref %}<div class="info-row"><span>Batch preference</span><strong>{{batch_pref}}</strong></div>{% endif %}
    {% if course_notes %}<div class="info-row"><span>Notes</span><strong>{{course_notes}}</strong></div>{% endif %}
    <div class="info-row"><span>Payment ID</span><strong>{{payment_id}}</strong></div>
    <div class="info-row"><span>Order ID</span><strong>{{order_id}}</strong></div>
  </div>
  <a href="/videos" class="btn-blue">▶ Start Learning Now</a>
</div>
</body>
</html>
"""

# ════════════════════════════════════════════
#  VIDEO PORTAL
# ════════════════════════════════════════════
videos_template = """
<!DOCTYPE html>
<html lang="en">
<head>
""" + SHARED_HEAD + """
<title>My Videos – Nexora EduTech</title>
<style>
  .topbar {
    background: rgba(0,0,0,.45); padding: 14px clamp(16px, 4vw, 32px);
    display: flex; justify-content: space-between; align-items: center;
    backdrop-filter: blur(10px); flex-wrap: wrap; gap: 8px;
  }
  .topbar .logo { font-family:'Syne',sans-serif; font-size:1.2em; font-weight:800; color:var(--accent); }
  .welcome-name { color: var(--gold); font-weight:700; }
  .badge-tier {
    background: linear-gradient(45deg,var(--danger),var(--danger2));
    padding: 3px 11px; border-radius: 30px; font-size:.8em; font-weight:700; margin-left:6px;
  }
  .portal-hero { padding: clamp(28px,5vw,44px) 20px 16px; text-align:center; }
  .portal-hero h1 { font-size: clamp(1.6em, 4vw, 2.2em); margin-bottom:8px; }
  .portal-hero p { color:#a0c4ff; font-size:clamp(.9em,2.5vw,1em); }

  /* Video player */
  .player-section { max-width: 860px; margin: 0 auto 32px; padding: 0 clamp(12px, 3vw, 20px); }
  .player-wrap { background:rgba(0,0,0,.5); border-radius:18px; overflow:hidden; box-shadow:0 12px 40px rgba(0,0,0,.5); }
  .player-ratio { position:relative; padding-bottom:56.25%; height:0; overflow:hidden; }
  .player-ratio iframe { position:absolute; top:0; left:0; width:100%; height:100%; border:none; display:block; }
  .player-info { padding: clamp(12px,3vw,18px) clamp(14px,3vw,22px); }
  .player-info h2 { font-size:clamp(1em,2.5vw,1.25em); color:var(--gold); margin-bottom:4px; }
  .player-info span { color:#a0c4ff; font-size:.88em; }

  /* Grid */
  .grid-title { text-align:center; font-size:clamp(1.1em,3vw,1.35em); font-weight:800; margin:8px 0 18px; color:var(--gold); }
  .vid-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr));
    gap: 16px; max-width:1100px; margin:0 auto clamp(40px,8vw,60px); padding:0 clamp(12px,3vw,20px);
  }
  .vid-card {
    background: var(--glass); border-radius:14px; overflow:hidden;
    cursor:pointer; transition:transform .2s, box-shadow .2s;
    border:2px solid transparent;
  }
  .vid-card:hover { transform:translateY(-4px); box-shadow:0 8px 24px rgba(0,0,0,.4); }
  .vid-card.active { border-color: var(--gold); }
  .vid-card img { width:100%; height:140px; object-fit:cover; display:block; }
  .vid-card .meta { padding: clamp(10px,2vw,13px); }
  .vid-card .meta h3 { font-size:.9em; margin-bottom:6px; color:#e0f0ff; line-height:1.4; }
  .duration-badge {
    display:inline-block; background:rgba(0,0,0,.55); color:#fff;
    font-size:.72em; padding:3px 9px; border-radius:5px;
  }
</style>
</head>
<body>

<div class="topbar">
  <div class="logo">🎓 Nexora EduTech</div>
  <div>
    <span class="welcome-name">👋 {{student_name}}</span>
    <span> · {{service}}</span>
    <span class="badge-tier">{{tier}}</span>
  </div>
</div>

<div class="portal-hero">
  <h1>My Learning Portal</h1>
  <p>Welcome back, <strong>{{student_name}}</strong>! You have <strong>{{count}}</strong> videos on your <strong>{{tier}}</strong> plan.</p>
</div>

<div class="player-section">
  <div class="player-wrap">
    <div class="player-ratio">
      <iframe id="mainPlayer" src="{{first_embed}}" allowfullscreen
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe>
    </div>
    <div class="player-info">
      <h2 id="nowTitle">{{first_title}}</h2>
      <span id="nowDuration">⏱ {{first_duration}}</span>
    </div>
  </div>
</div>

<div class="grid-title">📚 All Videos</div>
<div class="vid-grid">
  {% for v in videos %}
  <div class="vid-card {% if loop.first %}active{% endif %}" id="card-{{v.id}}"
       onclick="playVideo('{{v.id}}','{{v.embed}}','{{v.title}}','{{v.duration}}')">
    <img src="{{v.thumb}}" alt="{{v.title}}" loading="lazy">
    <div class="meta">
      <h3>{{v.title}}</h3>
      <div class="duration-badge">⏱ {{v.duration}}</div>
    </div>
  </div>
  {% endfor %}
</div>

<script>
function playVideo(id, embed, title, duration) {
  document.getElementById('mainPlayer').src = embed;
  document.getElementById('nowTitle').textContent = title;
  document.getElementById('nowDuration').textContent = '⏱ ' + duration;
  document.querySelectorAll('.vid-card').forEach(c => c.classList.remove('active'));
  document.getElementById('card-' + id).classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
</script>
</body>
</html>
"""

# ════════════════════════════════════════════
#  FACULTY PAGE
# ════════════════════════════════════════════
faculty_page = """
<!DOCTYPE html>
<html lang="en">
<head>
""" + SHARED_HEAD + """
<title>Our Faculty – Nexora EduTech</title>
<style>
  .page-title { text-align:center; padding: clamp(32px,6vw,56px) 20px 8px; font-size:clamp(1.8em,5vw,2.6em); }
  .fac-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 220px), 1fr));
    gap: 20px; max-width: 960px; margin: 28px auto 60px; padding: 0 20px;
  }
  .fac-card {
    background: var(--glass); border-radius: 16px;
    padding: clamp(20px,4vw,28px) 20px; text-align: center;
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 6px 18px rgba(0,0,0,.35);
    transition: transform .2s, box-shadow .2s;
  }
  .fac-card:hover { transform: translateY(-4px); box-shadow: 0 10px 28px rgba(0,0,0,.45); }
  .fac-card .avatar {
    width: 72px; height: 72px; border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--blue-mid));
    display: flex; align-items: center; justify-content: center;
    font-size: 2em; margin: 0 auto 14px;
  }
  .fac-card h2 { font-size: 1.05em; margin-bottom: 6px; }
  .fac-card p { color: rgba(255,255,255,.7); font-size: .88em; line-height:1.5; }
</style>
</head>
<body>
""" + NAV_HTML + """
<h1 class="page-title">Meet Our Faculty</h1>
<div class="fac-grid">
  <div class="fac-card"><div class="avatar">🤖</div><h2>Dr. Arun K</h2><p>AI &amp; Machine Learning Expert</p></div>
  <div class="fac-card"><div class="avatar">☁️</div><h2>Prof. Rajesh Kumar</h2><p>Cloud Computing Specialist</p></div>
  <div class="fac-card"><div class="avatar">🧠</div><h2>Dr. Meera Iyer</h2><p>Education Psychology Expert</p></div>
  <div class="fac-card"><div class="avatar">🚀</div><h2>Prof. Arvind Menon</h2><p>EdTech Strategy Innovator</p></div>
</div>
<footer class="footer">&copy; 2025 Nexora EduTech. All rights reserved.</footer>
</body>
</html>
"""

# ════════════════════════════════════════════
#  COURSES PAGE
# ════════════════════════════════════════════
courses_page = """
<!DOCTYPE html>
<html lang="en">
<head>
""" + SHARED_HEAD + """
<title>Courses – Nexora EduTech</title>
<style>
  .page-title { text-align:center; padding: clamp(32px,6vw,56px) 20px 8px; font-size:clamp(1.8em,5vw,2.6em); }
  .courses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr));
    gap: 22px; max-width: 1100px; margin: 28px auto 60px; padding: 0 20px;
  }
  .c-card {
    background: var(--glass); border-radius: 16px; overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 6px 18px rgba(0,0,0,.35);
    transition: transform .22s, box-shadow .22s;
  }
  .c-card:hover { transform: translateY(-5px); box-shadow: 0 12px 30px rgba(0,0,0,.5); }
  .c-card img { width:100%; height: clamp(160px, 25vw, 190px); object-fit:cover; display:block; }
  .c-card-body { padding: 16px 18px; }
  .c-card-body h3 { font-size: 1.05em; color: var(--accent); }
</style>
</head>
<body>
""" + NAV_HTML + """
<h1 class="page-title">🎓 Courses We Offer</h1>
<div class="courses-grid">
  <div class="c-card">
    <img src="https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=500" alt="Python" loading="lazy">
    <div class="c-card-body"><h3>Python Programming</h3></div>
  </div>
  <div class="c-card">
    <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500" alt="Data Science" loading="lazy">
    <div class="c-card-body"><h3>Data Science</h3></div>
  </div>
  <div class="c-card">
    <img src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=500" alt="Web Development" loading="lazy">
    <div class="c-card-body"><h3>Web Development</h3></div>
  </div>
  <div class="c-card">
    <img src="https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=500" alt="Machine Learning" loading="lazy">
    <div class="c-card-body"><h3>Machine Learning</h3></div>
  </div>
</div>
<footer class="footer">&copy; 2025 Nexora EduTech. All rights reserved.</footer>
</body>
</html>
"""

# ════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════

@app.route("/")
def home():
    return render_template_string(home_page)

@app.route("/services")
def services():
    return render_template_string(services_page)

@app.route("/services/<name>")
def service_detail(name):
    if name not in services_data:
        return "Service not found", 404
    d = services_data[name]
    return render_template_string(detail_template,
        title      = d["title"],
        points     = d["points"],
        hero_image = d["hero_image"],
        gallery    = d["gallery"],
        price      = int(d["price"]),
        standard   = int(d["standard"]),
        premium    = int(d["premium"]))

@app.route("/checkout", methods=["POST"])
def checkout():
    service  = request.form.get("service")
    tier     = request.form.get("tier")
    amount   = request.form.get("amount")
    order_id = "VE-" + uuid.uuid4().hex[:8].upper()
    session["pending_checkout"] = {
        "order_id": order_id,
        "service": service or "",
        "tier": tier or "",
        "amount": amount or "",
    }
    session.pop("checkout_student", None)
    session.pop("checkout_details_done", None)
    session.pop("rzp_order_id", None)
    return redirect(url_for("checkout_details"))


def _render_checkout_details(pending, err=None, **saved):
    defaults = dict(
        saved_name="", saved_email="", saved_phone="",
        saved_course="", saved_batch="", saved_notes="",
    )
    defaults.update(saved)
    return render_template_string(
        checkout_details_template,
        service=pending["service"],
        tier=pending["tier"],
        amount=pending["amount"],
        order_id=pending["order_id"],
        course_choices=list_checkout_courses(),
        err=err,
        **defaults,
    )


@app.route("/checkout/details", methods=["GET", "POST"])
def checkout_details():
    pending = session.get("pending_checkout")
    if not pending:
        return redirect(url_for("services"))

    if request.method == "GET":
        prev = session.get("checkout_student") or {}
        return _render_checkout_details(
            pending, err=None,
            saved_name=prev.get("student_name", ""),
            saved_email=prev.get("student_email", ""),
            saved_phone=prev.get("student_phone", ""),
            saved_course=prev.get("student_course_track", ""),
            saved_batch=prev.get("student_batch_pref", ""),
            saved_notes=prev.get("student_course_notes", ""),
        )

    name   = request.form.get("student_name", "").strip()
    email  = request.form.get("student_email", "").strip()
    phone  = request.form.get("student_phone", "").strip()
    course = request.form.get("student_course_track", "").strip()
    batch  = request.form.get("student_batch_pref", "").strip()
    notes  = request.form.get("student_course_notes", "").strip()

    errs = []
    if not name:              errs.append("Please enter your full name.")
    if not email or "@" not in email: errs.append("Enter a valid email.")
    if not phone or not phone.isdigit() or len(phone) != 10: errs.append("Enter a valid 10-digit mobile number.")
    if not course:            errs.append("Please select a course.")
    if errs:
        return _render_checkout_details(
            pending, err=" ".join(errs),
            saved_name=name, saved_email=email, saved_phone=phone,
            saved_course=course, saved_batch=batch, saved_notes=notes,
        )

    session["checkout_student"] = {
        "student_name": name, "student_email": email, "student_phone": phone,
        "student_course_track": course, "student_batch_pref": batch, "student_course_notes": notes,
    }
    session["checkout_details_done"] = pending["order_id"]
    return redirect(url_for("checkout_pay"))


@app.route("/checkout/pay")
def checkout_pay():
    pending = session.get("pending_checkout")
    if not pending:
        return redirect(url_for("services"))
    if session.get("checkout_details_done") != pending.get("order_id"):
        return redirect(url_for("services"))
    if not session.get("checkout_student"):
        return redirect(url_for("checkout_details"))

    oid        = pending["order_id"]
    stu        = session["checkout_student"]
    upi_uri    = build_upi_uri(pending["amount"], pending["service"], pending["tier"], oid)
    payment_qr = qr_svg_data_uri(upi_uri)
    session.pop("rzp_order_id", None)

    return render_template_string(
        checkout_pay_template,
        amount=pending["amount"],
        course_selected=stu.get("student_course_track", ""),
        payment_qr=payment_qr,
    )


@app.route("/payment-success", methods=["POST"])
def payment_success():
    pending    = session.get("pending_checkout")
    done       = session.get("checkout_details_done")
    posted_oid = request.form.get("internal_order_id", "")
    student    = session.get("checkout_student")
    if (
        not pending or not student
        or done != pending.get("order_id")
        or posted_oid != pending.get("order_id")
    ):
        return redirect(url_for("services"))

    rzp_pay_id = request.form.get("razorpay_payment_id", "").strip()
    rzp_oid    = request.form.get("razorpay_order_id", "").strip()
    rzp_sig    = request.form.get("razorpay_signature", "").strip()

    if not (rzp_pay_id and rzp_oid and rzp_sig):
        return redirect(url_for("checkout_pay"))
    if rzp_oid != session.get("rzp_order_id"):
        return redirect(url_for("services"))
    if not verify_razorpay_signature(rzp_oid, rzp_pay_id, rzp_sig):
        return redirect(url_for("checkout_pay"))

    payment_id = rzp_pay_id
    order_id   = posted_oid
    service    = pending["service"]
    tier       = pending["tier"]
    amount     = pending["amount"]

    student_name  = student.get("student_name", "Student")
    student_email = student.get("student_email", "")
    student_phone = student.get("student_phone", "")
    course_track  = (student.get("student_course_track") or "").strip()
    batch_pref    = (student.get("student_batch_pref") or "").strip()
    course_notes  = (student.get("student_course_notes") or "").strip()

    session["subscription"] = {
        "service": service, "tier": tier, "amount": amount,
        "name": student_name, "email": student_email, "phone": student_phone,
        "course_track": course_track, "batch_pref": batch_pref, "course_notes": course_notes,
    }
    session.pop("pending_checkout", None)
    session.pop("checkout_details_done", None)
    session.pop("checkout_student", None)
    session.pop("rzp_order_id", None)

    return render_template_string(
        success_template,
        service=service, tier=tier, amount=amount,
        payment_id=payment_id, order_id=order_id,
        student_name=student_name, student_email=student_email, student_phone=student_phone,
        course_track=course_track, batch_pref=batch_pref, course_notes=course_notes,
    )


@app.route("/videos")
def videos():
    sub = session.get("subscription")
    if not sub:
        return redirect(url_for("services"))

    service_title = sub["service"]
    tier          = sub["tier"]
    student_name  = sub.get("name", "Student")
    video_list    = get_accessible_videos(service_title, tier)

    if not video_list:
        return "<h2 style='color:white;text-align:center;margin-top:80px'>No videos found for your plan.</h2>"

    first = video_list[0]
    return render_template_string(videos_template,
        service=service_title, tier=tier, student_name=student_name,
        videos=video_list, count=len(video_list),
        first_embed=first["embed"], first_title=first["title"], first_duration=first["duration"])


@app.route("/faculty")
def faculty():
    return render_template_string(faculty_page)


@app.route("/courses")
def courses():
    return render_template_string(courses_page)


if __name__ == "__main__":
    app.run(debug=True)