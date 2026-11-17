# WristTap paper sled: A4 cut-and-fold sheet at true size. Run: python3 make_dieline.py
# Solid = cut, dashed = fold (mountain/valley not needed, every fold goes UP), grey = glue tab.
MM = 72/25.4
ops = []
def line(x1,y1,x2,y2,dash=False,w=0.6):
    ops.append(f"{'[4 3] 0 d' if dash else '[] 0 d'} {w} w {x1*MM:.2f} {(297-y1)*MM:.2f} m {x2*MM:.2f} {(297-y2)*MM:.2f} l S")
def poly(pts, fill=False):
    p = " ".join(f"{x*MM:.2f} {(297-y)*MM:.2f} {'m' if i==0 else 'l'}" for i,(x,y) in enumerate(pts))
    ops.append(("0.88 g " if fill else "") + "[] 0 d 0.6 w " + p + (" h B 0 g" if fill else " h S"))
def text(x,y,s,size=8):
    s = s.replace("(", "\\(").replace(")", "\\)")
    ops.append(f"BT /F1 {size} Tf {x*MM:.2f} {(297-y)*MM:.2f} Td ({s}) Tj ET")
def rect(x,y,w,h): poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])

def tray(ox, oy, L, W, h, tab=9, slits=()):
    """open box: base L x W, walls h. Long walls carry glue tabs that tuck inside the short walls."""
    bx, by = ox+h, oy+h
    # outline (cut)
    out = [(bx,oy),(bx+L,oy),(bx+L,by),                          # top wall
           (bx+L+2,by),(bx+L+tab,by+2),(bx+L+tab,by+h-2),(bx+L+2,by+h)]  # (no tab here: corner)
    # build cut path piece by piece instead: walls + tabs
    for (x,y,w,hh) in [(bx,oy,L,h),(bx,by+W,L,h),(ox,by,h,W),(bx+L,by,h,W)]: pass
    # top wall + tabs
    cut = [(ox+2,by),(ox+2,by)]  # placeholder
    P = []
    P += [(bx-tab+2,oy+2),(bx,oy),(bx+L,oy),(bx+L+tab-2,oy+2),(bx+L+tab-2,by-2),(bx+L,by)]      # top wall w/ tabs
    P += [(bx+L+h,by),(bx+L+h,by+W),(bx+L,by+W)]                                                 # right wall
    P += [(bx+L+tab-2,by+W+2),(bx+L+tab-2,by+W+h-2),(bx+L,by+W+h),(bx,by+W+h),(bx-tab+2,by+W+h-2),(bx-tab+2,by+W+2),(bx,by+W)]  # bottom wall w/ tabs
    P += [(ox,by+W),(ox,by),(bx,by),(bx-tab+2,by-2)]                                             # left wall
    poly(P)
    for t in [((bx-tab+2,oy+2),(bx,oy),(bx,by),(bx-tab+2,by-2)),((bx+L,oy),(bx+L+tab-2,oy+2),(bx+L+tab-2,by-2),(bx+L,by)),
              ((bx+L,by+W),(bx+L+tab-2,by+W+2),(bx+L+tab-2,by+W+h-2),(bx+L,by+W+h)),((bx,by+W),(bx-tab+2,by+W+2),(bx-tab+2,by+W+h-2),(bx,by+W+h))]:
        poly(list(t), fill=True)
    # folds
    for (x1,y1,x2,y2) in [(bx,by,bx+L,by),(bx,by+W,bx+L,by+W),(bx,by,bx,by+W),(bx+L,by,bx+L,by+W),
                          (bx,oy,bx,by),(bx+L,oy,bx+L,by),(bx,by+W,bx,by+W+h),(bx+L,by+W,bx+L,by+W+h)]:
        line(x1,y1,x2,y2,dash=True)
    for (sx, sy, sw, sh) in slits: rect(bx+sx, by+sy, sw, sh)
    return bx, by

# ---- 1. tray: 142 x 60 floor, 10 mm walls (same footprint as the 3D sled) ----
L, W, H = 142, 60, 10
bx, by = tray(14, 18, L, W, H, slits=[(x-14, 4, 28, 3) for x in (44, 113)] + [(x-14, W-7, 28, 3) for x in (44, 113)])
text(bx+4, by+W/2-2, "TRAY FLOOR  -  breadboard goes here (this end)", 8)
text(bx+96, by+W/2-2, "ESP32 end  ->  USB", 8)
text(bx+4, by+W/2+6, "Strap: up through slit A, across under the board, down through slit B", 7)
text(bx+30, by+10.5, "slit A", 6); text(bx+30, by+W-8.5, "slit B", 6)
text(14, 12, "1. TRAY  -  cut solid lines, cut the 4 slits, fold every dashed line UP, glue grey tabs inside the short walls", 8)

# ---- 2. ESP riser: 40 x 21 top, 18 mm tall (fits between the two rows of jumper plugs) ----
oy2 = 132
tray(14, oy2, 40, 21, 18, tab=10)
text(14, oy2-5, "2. ESP RISER  -  fold the same way, stand it UPSIDE DOWN (open side on the tray floor)", 8)
text(36, oy2+18+6, "top: ESP32 lies here", 7)
text(36, oy2+18+11, "pins + jumper plugs hang", 7); text(36, oy2+18+15, "down each side of it", 7)

# ---- 3. ESP end stops (2 pieces, fold into L, glue at both ESP ends) ----
ox3, oy3 = 120, 140
for k in range(2):
    x = ox3 + k*40
    rect(x, oy3, 32, 30); line(x, oy3+8, x+32, oy3+8, dash=True)
    text(x+2, oy3+5, "glue on floor", 6); text(x+2, oy3+20, f"end stop {k+1}", 7)
text(ox3, oy3-5, "3. END STOPS  -  fold, glue at each ESP end", 8)
text(ox3, oy3+38, "Stop 2 (USB end): cut a 13 mm notch for the cable", 7)

# ---- scale check + notes ----
y = 205
line(14, y, 64, y, w=1.2); line(14, y-2, 14, y+2, w=1.2); line(64, y-2, 64, y+2, w=1.2)
text(68, y+1.5, "<- must measure exactly 50 mm. Print at 100% / Actual size, NOT 'fit to page'.", 8)
notes = ["Use thin card: cereal box, 250-300 gsm. Score folds with an empty pen + ruler first.",
         "Glue: Fevicol / glue stick / double tape. Tape the breadboard's sticky back onto the floor.",
         "ESP32 sits on the riser, chip side up, pins pointing down. The riser lifts it 18 mm so",
         "the jumper plugs on its pins fit underneath. Wires leave sideways between the end stops.",
         "Same layout as the 3D printed sled (cad/sled.scad): test fit and strap position on paper first."]
for i, n in enumerate(notes): text(14, 216 + i*6, n, 8)
text(14, 290, "WristTap paper sled  -  A4, true size", 7)

content = "\n".join(ops).encode()
objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {210*MM:.2f} {297*MM:.2f}] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>".encode(),
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
out = b"%PDF-1.4\n"; offs = []
for i, o in enumerate(objs, 1):
    offs.append(len(out)); out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
x = len(out)
out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode() + b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
out += f"trailer << /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF".encode()
open("WristTap_paper_sled_A4.pdf", "wb").write(out)
print("ok")
