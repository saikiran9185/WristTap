// WristTap: where every printed part sits on the arm and hand (left arm, palm down).
// Picture only, nothing here is printed. Render: openscad -D 'view="top"' body_view.scad
include <sled.scad>
part = "body";

/* body (simple shapes, about an adult arm) */
ax_z   = -30;                 // arm centre line height (sled floor is z = 0, on top of the arm)
cy     = W/2;                 // arm centre line, across
wrist_x = -ext - 34;          // wrist crease
elbow_x = L + 60;
function ry(x) = x < wrist_x ? 28 : 28 + (x - wrist_x)/(elbow_x - wrist_x)*8;    // half width
function rz(x) = x < wrist_x ? 19 : 19 + (x - wrist_x)/(elbow_x - wrist_x)*9;    // half height

skin = "#e8b892";
module forearm() color(skin)
    hull() for (x=[wrist_x, elbow_x]) translate([x, cy, ax_z]) rotate([0,90,0]) scale([rz(x), ry(x), 1]) cylinder(r=1, h=1, $fn=64);
module hand() color(skin) {
    hull() {
        translate([wrist_x, cy, ax_z]) rotate([0,90,0]) scale([19, 28, 1]) cylinder(r=1, h=1, $fn=48);
        translate([wrist_x - 85, cy, ax_z - 2]) rotate([0,90,0]) scale([12, 42, 1]) cylinder(r=1, h=1, $fn=48);
    }
    for (k=[0:3]) translate([wrist_x - 85, cy - 30 + k*20, ax_z - 2]) rotate([0,-90,0]) cylinder(d=17, h=[62,72,76,70][k], $fn=24);
    // thumb (thumb side = -Y on a left arm, palm down)
    hull() { translate([wrist_x - 30, cy - 36, ax_z - 6]) sphere(10); translate([wrist_x - 85, cy - 62, ax_z - 8]) sphere(8); }
}

// put a strap pod on the skin: angle a around the arm (90 = top, -90 = palm side), tunnel follows the strap
module on_ring(x, a, lift = 0.3) {
    c = cos(a); s = sin(a);
    px = x; py = cy + (ry(x) + lift)*c; pz = ax_z + (rz(x) + lift)*s;
    multmatrix([[0,1,0,px],[-s,0,c,py],[c,0,s,pz],[0,0,0,1]]) translate([-pod/2, -pod/2, 0]) children();
}
module strap(x, grow = 0, w = strap_w) color("#2a2a2a")
    translate([x - w/2, cy, ax_z]) rotate([0,90,0]) difference() {
        scale([rz(x) + 3.6 + grow, ry(x) + 3.6 + grow, 1]) cylinder(r=1, h=w, $fn=72);
        translate([0,0,-1]) scale([rz(x) + 0.2 + grow, ry(x) + 0.2 + grow, 1]) cylinder(r=1, h=w + 2, $fn=72);
    }

// ---- parts with their components ----
wrist_strap_x = wrist_x + 16;
PZ_A   = [180, -90, 0, 90];         // P0 pinky bone (+Y side), P1 inner wrist, P2 thumb bone (-Y side), P3 top of wrist
PZ_COL = ["#e4572e", "#f3a712", "#29bf12", "#00a5cf"];
F_A    = [-112, -68];
fsr_x  = xe + Le/2;                 // FSRs ride on the elbow-end tray strap, inner forearm
hand_x = wrist_x - 48;

module piezo_disc() color("#c8a464") translate([pod/2, pod/2, 0]) cylinder(d=disc_d, h=0.5);
module fsr_pad()   color("#333") translate([pod/2, pod/2, 0]) cylinder(d=fsr_pad_d, h=0.4);

module everything() {
    forearm(); hand();
    // tray + its parts
    color("#f2b134") sled();
    dummies();
    color("#2b6cb0") translate([mx0 + tol, my0 + tol, floor_t]) cube([mpu_l, mpu_w, 1.6]);                       // MPU #1
    color("dimgray") translate([mx0 + 2, my0 + mpu_w, floor_t + 1.6]) cube([mpu_l - 4, mpu_ra_out, 2.5]);         // its plugs
    for (x=[xb + Lb/2, xe + Le/2]) strap(x, 2);
    // wrist strap + 4 piezo pods
    strap(wrist_strap_x);
    for (k=[0:3]) on_ring(wrist_strap_x, PZ_A[k]) { color(PZ_COL[k]) strap_pod(str("P", k), PZ_NAME[k]) piezo_pocket(); piezo_disc(); }
    // 2 FSR pods under the elbow-end strap
    for (k=[0:1]) on_ring(fsr_x, F_A[k], 2.3) { color("#8e44ad") strap_pod(str("F", k), "INNER FOREARM", 2.2) fsr_pocket(); fsr_pad(); }
    // MPU #2 on the back of the hand, strap around the palm
    translate([hand_x + 15.5, cy - 15.5, ax_z + 13.4]) rotate([0,0,90]) translate([-15.5, -15.5, 0]) {
        color("#6b4fb8") hand_holder();
        color("#2b6cb0") translate([3 + wall + tol, 2 + wall + tol, 1.6 + slot_t + floor_t]) cube([mpu_l, mpu_w, 1.6]);
    }
    color("#2a2a2a") translate([hand_x - strap_w/2 + 15.5, cy, ax_z - 2]) rotate([0,90,0]) difference() {
        scale([16.5, 45, 1]) cylinder(r=1, h=strap_w, $fn=72);
        translate([0,0,-1]) scale([13.2, 42.2, 1]) cylinder(r=1, h=strap_w + 2, $fn=72);
    }
}
if (part == "body") everything();
