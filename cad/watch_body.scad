// WristTap WATCH on the arm (left arm, palm down). Picture only.
include <watch.scad>
part = "wbody";

cy = BY/2;  ax_z = -21.5;
wrist_x = bc - 16;  elbow_x = BX + 110;
function ry(x) = x < wrist_x ? 28 : 28 + (x - wrist_x)/(elbow_x - wrist_x)*7;
function rz(x) = x < wrist_x ? 19 : 19 + (x - wrist_x)/(elbow_x - wrist_x)*3;
skin = "#e8b892";

module forearm() color(skin)
    hull() for (x=[wrist_x, elbow_x]) translate([x, cy, ax_z]) rotate([0,90,0]) scale([rz(x), ry(x), 1]) cylinder(r=1, h=1, $fn=64);
module hand() color(skin) {
    hull() {
        translate([wrist_x, cy, ax_z]) rotate([0,90,0]) scale([19, 28, 1]) cylinder(r=1, h=1, $fn=48);
        translate([wrist_x - 85, cy, ax_z - 2]) rotate([0,90,0]) scale([12, 42, 1]) cylinder(r=1, h=1, $fn=48);
    }
    for (k=[0:3]) translate([wrist_x - 85, cy - 30 + k*20, ax_z - 2]) rotate([0,-90,0]) cylinder(d=17, h=[62,72,76,70][k], $fn=24);
    hull() { translate([wrist_x - 30, cy - 36, ax_z - 6]) sphere(10); translate([wrist_x - 85, cy - 62, ax_z - 8]) sphere(8); }
}
// pad on the skin at angle a (90 = top, -90 = palm side, 0 = little-finger side, 180 = thumb side)
module on_skin(x, a, lift = 1.2) {
    c = cos(a); s = sin(a);
    multmatrix([[0,1,0,x],[-s,0,c,cy + (ry(x) + lift)*c],[c,0,s,ax_z + (rz(x) + lift)*s],[0,0,0,1]]) children();
}
// curved band piece around the arm from angle a0 to a1, x0..x0+w
module band_seg(x0, w, a0, a1, t = band_t) {
    x = x0 + w/2;
    intersection() {
        translate([x0, cy, ax_z]) rotate([0,90,0]) difference() {
            scale([rz(x) + t, ry(x) + t, 1]) cylinder(r=1, h=w, $fn=96);
            translate([0,0,-1]) scale([rz(x), ry(x), 1]) cylinder(r=1, h=w + 2, $fn=96);
        }
        translate([x0 - 1, 0, 0]) rotate([90,0,90]) linear_extrude(w + 2)
            polygon(concat([[cy, ax_z]], [for (t=[a0:5:a1]) [cy + 90*cos(t), ax_z + 90*sin(t)]], [[cy + 90*cos(a1), ax_z + 90*sin(a1)]]));
    }
}

band_col = "#f2b134";
module worn() {
    forearm(); hand();
    // block + its parts
    color(band_col) block();
    color("#1f2b3a") translate([ex0 + tol, BY/2 - esp_w/2, pcb_z]) cube([esp_l, esp_w, 1.6]);
    color("ivory") translate([wall + tol, wall + tol, ledge_z + ledge_t]) cube([bb_l, bb_w, 8.5]);
    color("#2b6cb0") translate([wall + 3 + wall + tol, BY/2 - 14 + wall + tol, floor_t]) cube([mpu_l, mpu_w, 1.6]);
    color(band_col) translate([bc, BY/2 - bw/2, -1]) rbox([-bc + 4, bw, floor_t + 1], 3);          // spine
    // the band, wrapped (one piece in the print)
    color(band_col) band_seg(bc - bw/2, bw, -270, 90);
    color(band_col) band_seg(bc - bw/2, bw + 30, -130, -50);                                        // paddle under the inner wrist
    for (p = [[90, "P3", "#00a5cf"], [0, "P0", "#e4572e"], [180, "P2", "#29bf12"], [-90, "P1", "#f3a712"]])
        on_skin(bc, p[0]) { color(p[2]) disc_pad(0, 0, p[1]); color("#c8a464") cylinder(d=disc_d, h=0.5); }
    for (k=[0:1]) on_skin(bc + 29, -90 + (k ? -1 : 1)*26) { color("#8e44ad") fsr_pad_m(0, 0, str("F", k), 1); color("#333") cylinder(d=fsr_pad_d, h=0.4); }
    // MPU #2 on the back of the hand
    hand_x = wrist_x - 48;
    translate([hand_x + 15.5, cy - 15.5, ax_z + 13.4]) rotate([0,0,90]) translate([-15.5, -15.5, 0]) {
        color("#6b4fb8") hand_holder();
        color("#2b6cb0") translate([3 + wall + tol, 2 + wall + tol, 1.6 + slot_t + floor_t]) cube([mpu_l, mpu_w, 1.6]);
    }
    color("#2a2a2a") translate([hand_x - strap_w/2 + 15.5, cy, ax_z - 2]) rotate([0,90,0]) difference() {
        scale([16.5, 45, 1]) cylinder(r=1, h=strap_w, $fn=72);
        translate([0,0,-1]) scale([13.2, 42.2, 1]) cylinder(r=1, h=strap_w + 2, $fn=72);
    }
}
if (part == "wbody") worn();
