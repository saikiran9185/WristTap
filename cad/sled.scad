// WristTap SLED: one open tray for the half breadboard + ESP32. Fast print, little plastic.
// Open top: you can pull any wire or change the layout without opening anything.
//
//   [ ESP32 on a rib frame ][ half breadboard pocket ]   ← straps go across the arm through the 4 slots
//
// To change it: edit the numbers below, then in OpenSCAD press F6 and File > Export > STL.
// Every value is in millimetres. "(measure)" = check on your own part.

/* [Half breadboard, 400 point] */
bb_l    = 83.0;   // length, row 1 to row 30 end (measure)
bb_w    = 55.0;   // width (measure)
bb_wall = 6.0;    // how high the pocket walls hold the board

/* [ESP32 DevKit, 30 pin] */
esp_l   = 51.5;   // USB end to antenna end (measure)
esp_w   = 28.3;   // (measure)
row_gap = 25.4;   // distance between the two pin rows
plug_h  = 14.0;   // female jumper plug length under the board (measure)
bend    = 4.0;    // room for the jumper wire to bend sideways under the plug
usb_w   = 13.0;   // opening for the USB plug

/* [Strap] */
strap_w = 25.0;   // velcro strap width
strap_t = 2.6;    // strap thickness (measure)

/* [Print] */
tol     = 0.4;    // gap around each part (0.5 if tight, 0.3 if loose)
wall    = 1.6;    // 4 lines of a 0.4 nozzle
floor_t = 1.6;
rib     = 1.6;

/* [Sensors] */
mpu_l   = 21.2;   // MPU board, along the pin row (measure)
mpu_w   = 16.4;   // MPU board width (measure)
mpu_ra_out = 17;  // right-angle jumper plugs stick out this far past the pin edge
disc_d  = 27.0;   // piezo brass disc
ceramic_d = 20.0; // ceramic circle + solder blobs on the back
fsr_pad_d = 18.5; // FSR 402 round pad
fsr_tail_w = 8.0; // FSR tail width
engrave = 0.6;    // label depth
font    = "Liberation Sans:style=Bold";

part = "sled";    // sled | pod_p0..pod_p3 | pod_f0 | pod_f1 | hand | view

/* [Hidden] */
$fn = 40;
pw = bb_w + 2*tol;                 // pocket inner width
W  = pw + 2*wall;                  // tray width (across the arm)
Lb = bb_l + 2*tol;                 // breadboard pocket length
Le = esp_l + 2*tol;                // ESP bay length
xb = wall;                         // breadboard pocket start
xm = xb + Lb;                      // middle wall
xe = xm + wall;                    // ESP bay start
L  = xe + Le + wall;               // tray length (along the arm)
rib_h = plug_h + bend;             // ESP board sits on top of the ribs
pcb_z = floor_t + rib_h;
end_h = pcb_z + 3;                 // end walls hold the ESP board 3 mm up its edge
rib_w = row_gap - 2.6 - 2*0.6;     // inner rib frame fits between the two plug rows
slot_l = strap_w + 2.5;
slot_t = strap_t + 1.0;
wing   = slot_t + 2*2.4;           // wing sticks out this far each side
wing_h = 4.0;

module rbox(s, r=2) { hull() for (x=[r, s[0]-r], y=[r, s[1]-r]) translate([x, y, 0]) cylinder(r=r, h=s[2]); }

module strap_wings(xc) {
    for (s=[0,1]) translate([xc - (slot_l+5)/2, s ? W - 1 : -wing + 1, 0])
        difference() {
            rbox([slot_l + 5, wing, wing_h], 2);
            translate([2.5, s ? wing - 2.4 - slot_t - 1 + 1 : 2.4, -1]) cube([slot_l, slot_t, wing_h + 2]);
        }
}

module sled() {
    difference() {
        union() {
            rbox([L, W, floor_t], 3);                                                          // floor
            // breadboard pocket walls
            difference() { rbox([xm + wall, W, floor_t + bb_wall], 3); translate([xb, wall, -1]) cube([Lb, pw, 50]); }
            // ESP end walls (middle wall is shared)
            translate([xm, W/2 - (esp_w + 2*tol)/2 - wall, 0]) cube([wall, esp_w + 2*tol + 2*wall, end_h]);   // tall only behind the ESP, wires pass over the rest
            translate([L - wall, W/2 - (esp_w + 2*tol)/2 - wall, 0]) cube([wall, esp_w + 2*tol + 2*wall, end_h]);
            // ESP side guides: short corner posts, wires leave freely between them
            for (x=[xe, L - wall - 6], s=[-1,1])
                translate([x, W/2 + s*(esp_w/2 + tol) + (s<0 ? -wall : 0), 0]) cube([6, wall, end_h]);
            // rib frame the ESP board rests on (between the two rows of jumper plugs)
            translate([xe + 6, W/2 - rib_w/2, 0]) difference() {
                cube([Le - 12, rib_w, pcb_z]);
                translate([rib, rib, floor_t]) cube([Le - 12 - 2*rib, rib_w - 2*rib, 50]);
            }
            strap_wings(xb + Lb/2);
            strap_wings(xe + Le/2);
            // MPU #1 bay at the WRIST end (the breadboard end): board lies flat, pins + plugs point sideways
            translate([-ext, 0, 0]) rbox([ext + 3, W, floor_t], 3);
            translate([mx0 - wall, my0 - wall, 0]) difference() {
                cube([mpu_l + 2*tol + 2*wall, mpu_w + 2*tol + wall, floor_t + 3]);
                translate([wall, wall, floor_t]) cube([mpu_l + 2*tol, mpu_w + 2*tol + 5, 10]);   // open on the pin side
            }
        }
        // ---- engraved labels: which part goes where ----
        lab(xb + 3, wall + 1.7, "HALF BREADBOARD 83 x 55", 3.4);
        lab(xb + 3, W - wall - 5.3, "ROW 30", 3.4);
        lab(xm - 17, W - wall - 5.3, "ROW 1", 3.4);
        lab(xe + 2, 2.5, "ESP32 51 x 28", 3.6);
        lab(xe + 2, W - 7, "USB >  ELBOW", 3.6);
        lab(-ext + 3, 8, "MPU #1", 4);
        lab(-ext + 3, 2.5, "21 x 16  WRIST", 2.8);
        lab(mx0 + 2, my0 + 3, "PINS ^", 3.2);
        // save plastic: big window under the breadboard (it rests on the 7 mm rim)
        translate([xb + 7, wall + 7, -1]) rbox([Lb - 14, pw - 14, floor_t + 2], 4);
        // window under the ESP, inside the rib frame
        translate([xe + 6 + rib + 2, W/2 - rib_w/2 + rib + 2, -1]) rbox([Le - 12 - 2*rib - 4, rib_w - 2*rib - 4, floor_t + 2], 2);
        // USB opening in the far end wall
        translate([L - wall - 1, W/2 - usb_w/2, pcb_z - 1]) cube([wall + 2, usb_w, 50]);
        // finger notch on the middle wall above the breadboard, to lift the board out
        translate([xm - 1, W/2 - 8, floor_t + bb_wall]) cube([wall + 2, 16, 50]);
    }
}

ext = mpu_l + 2*tol + 2*wall + 4;          // MPU #1 bay length
mx0 = -ext + 2 + wall;                     // MPU #1 pocket inner corner
my0 = W/2 - 6 - (mpu_w + 2*tol)/2;

module lab(x, y, t, size, z = floor_t) {
    translate([x, y, z - engrave]) linear_extrude(engrave + 1) text(t, size = size, font = font);
}

// ---------- strap pods: slide onto a 25 mm strap, the part sits in the bottom (skin side) ----------
pod = 31;  base_t = 3.0;  roof = 2.0;
module strap_pod(tag, sub, h_base = base_t) {
    H = h_base + slot_t + roof;
    difference() {
        rbox([pod, pod, H], 4);
        translate([-1, (pod - slot_l)/2, h_base]) cube([pod + 2, slot_l, slot_t]);            // strap tunnel (along X)
        children();                                                                          // the part's pocket
        translate([pod/2, pod/2 + 3, H - engrave]) linear_extrude(2) text(tag, size = 8, font = font, halign = "center");
        translate([pod/2, 5, H - engrave]) linear_extrude(2) text(sub, size = 3, font = font, halign = "center");
    }
}
module piezo_pocket() {
    translate([pod/2, pod/2, -1]) cylinder(d = disc_d + 0.6, h = 1 + 0.8);                   // brass disc, flush with the bottom
    translate([pod/2, pod/2, -1]) cylinder(d = ceramic_d + 1, h = 1 + 2.2);                  // room for ceramic + solder blobs
    translate([pod/2, pod/2 - 2, -1]) cube([pod, 4, 1 + 1.6]);                               // wire groove to the edge, along the strap
}
module fsr_pocket() {
    translate([pod/2, pod/2, -1]) cylinder(d = fsr_pad_d + 0.6, h = 1 + 0.7);
    translate([pod/2, pod/2 - (fsr_tail_w + 0.6)/2, -1]) cube([pod, fsr_tail_w + 0.6, 1 + 0.7]);
}
PZ_NAME = ["PINKY BONE", "INNER WRIST", "THUMB BONE", "WRIST TOP"];

// ---------- MPU #2 hand holder: strap around the palm runs under it ----------
module hand_holder() {
    hb = 1.6;  hx = mpu_l + 2*tol + 2*wall;  hy = pod;
    H = hb + slot_t + floor_t;
    difference() {
        union() {
            rbox([hx + 6, hy, H], 3);
            translate([3, 2, H - 0.01]) difference() {                                       // pocket walls, open on the pin side (+Y)
                cube([hx, mpu_w + 2*tol + wall, 3]);
                translate([wall, wall, -1]) cube([mpu_l + 2*tol, mpu_w + 2*tol + 5, 10]);
            }
        }
        translate([-1, (hy - slot_l)/2, hb]) cube([hx + 8, slot_l, slot_t]);                   // strap tunnel
        translate([3 + wall + 2, 2 + wall + 4, H - engrave]) linear_extrude(2) text("MPU #2", size = 3.6, font = font);
        translate([3 + wall + 2, 2 + wall + 10, H - engrave]) linear_extrude(2) text("HAND  PINS ^", size = 2.6, font = font);
    }
}

module dummies() {
    color("ivory") translate([xb + tol, wall + tol, floor_t]) cube([bb_l, bb_w, 8.5]);
    color("#1f2b3a") translate([xe + tol, W/2 - esp_w/2, pcb_z]) cube([esp_l, esp_w, 1.6]);
    color("dimgray") for (s=[-1,1]) translate([xe + tol + 6.7, W/2 + s*row_gap/2 - 1.25, pcb_z - plug_h]) cube([38.1, 2.5, plug_h]);
}

if (part == "sled") sled();
for (k = [0:3]) if (part == str("pod_p", k)) strap_pod(str("P", k), PZ_NAME[k]) piezo_pocket();
if (part == "pod_f0") strap_pod("F0", "INNER FOREARM", 2.2) fsr_pocket();
if (part == "pod_f1") strap_pod("F1", "INNER FOREARM", 2.2) fsr_pocket();
if (part == "hand") hand_holder();
if (part == "view") { color("#f2b134") sled(); dummies(); }
echo(str("SLED size: ", L, " x ", W + 2*wing - 2, " x ", end_h, " mm"));
