// WristTap wearable housing — every part, parametric.
// Axes (as worn): X = along the strap (around the wrist), Y = along the arm
// (+Y points to the elbow), Z = away from the skin. z = 0 is the skin.
//
// Render one part:   openscad -D 'part="pod_top"' -o pod_top.stl wristtap.scad
// Parts: fit_test, pod_top, pod_piezo, pod_combo, hand_plate, carrier, assembly
// Print parts come out already turned the right way up for printing (no supports).

include <config.scad>

part = "assembly";

// ── Derived sizes ───────────────────────────────────────────
slot_l   = strap_w + 2.5;            // strap slot length
slot_t   = strap_t + 0.9;            // strap slot thickness
wing     = slot_t + 2*2.2;           // wing width with the slot in it
wing_h   = 3.6;                      // wing thickness

disc_pocket = disc_d + 2*tol;        // disc seat
disc_depth  = disc_t + 0.3;          // seat depth (disc sits about flush, 0.3 for tape)
relief_d    = ceramic_d + 1.5;       // hollow behind the ceramic: room for solder + lets the disc flex
relief_h    = 2.2;
skin_side_h = disc_depth + relief_h + 1.2;   // solid layer above the relief

mpu_seat_l  = mpu_l + 2*tol;
mpu_seat_w  = mpu_w + 2*tol;
mpu_under   = mpu_wires == "jumpers" ? plug_h + wire_bend : 2.5;   // space under the board
mpu_box_h   = mpu_under + mpu_pcb_t + 0.6;                         // cavity height incl. board
ledge       = 1.4;                   // board rests on this ledge (3 sides; pin side is open)

fsr_ch_w    = fsr_w + 1.0;
fsr_ch_d    = fsr_t + 0.2;

pod_y       = max(disc_pocket, slot_l) + 2*wall;   // pod size across the strap
pod_x       = disc_pocket + 2*wall;                // pod size along the strap

// ── Helpers ─────────────────────────────────────────────────
module rbox(size, r=2) {             // rounded box, centred in X/Y, from z=0
    r2 = min(r, size[0]/2-0.01, size[1]/2-0.01);
    hull() for (sx=[-1,1], sy=[-1,1])
        translate([sx*(size[0]/2-r2), sy*(size[1]/2-r2), 0]) cylinder(r=r2, h=size[2]);
}

// Strap wings at both X ends: the strap comes up through one slot, over the
// top of the pod (pressing it onto the skin and holding the boards in) and
// down through the other slot.
module wings(body_x, h=wing_h) {
    difference() {
        rbox([body_x + 2*wing, pod_y, h], 2.5);
        for (s=[-1,1]) translate([s*(body_x/2 + wing/2), 0, -1])
            rbox([slot_t, slot_l, h+2], 0.8);
    }
}

// Disc seat cut from the skin side (z = 0). Wires leave through a groove
// towards +Y (wire_dir = 1) or -Y (wire_dir = -1).
module disc_cut(wire_dir=1) {
    translate([0,0,-1]) cylinder(d=disc_pocket, h=disc_depth+1);
    cylinder(d=relief_d, h=disc_depth+relief_h);
    // groove for the red + black wires (both solder joints sit in it)
    translate([0, wire_dir*pod_y/4, -1]) rbox([6.5, pod_y/2+2, disc_depth+relief_h+1], 1);
    // finger notch to pry the disc out
    translate([0, -wire_dir*disc_pocket/2, -1]) cylinder(d=6, h=disc_depth+1);
}

// MPU cavity, opening on top (z = top). Pin row on the +Y side, open notch there
// so the plugs and wires come out towards the elbow.
module mpu_cut(top) {
    // board seat
    translate([0,0,top-mpu_pcb_t-0.6]) rbox([mpu_seat_l, mpu_seat_w, 10], 0.6);
    // space under the board (ledge on -Y, -X, +X)
    translate([0, ledge/2, top-mpu_box_h]) rbox([mpu_seat_l-2*ledge, mpu_seat_w-ledge, mpu_box_h+1], 0.6);
    // pin side: full board length for the row of 8 plugs (no ledge here)
    translate([0, mpu_seat_w/2-2.5, top-mpu_box_h]) rbox([mpu_seat_l, 5, mpu_box_h+1], 0.4);
    // wire notch through the +Y wall, full height of the cavity
    translate([0, mpu_seat_w/2+wall, top-mpu_box_h]) rbox([mpu_seat_l-3, 3*wall, mpu_box_h+1], 0.6);
}

// ── Parts (modelled as worn) ────────────────────────────────
module pod_piezo_worn() {
    h = skin_side_h + 0.4;
    difference() {
        union() { rbox([pod_x, pod_y, h], 3); wings(pod_x, h); }   // wings full height: flat on both faces
        disc_cut(1);
    }
}

module pod_combo_worn() {            // piezo + FSR strip
    yd = -(fsr_ch_w + wall)/2;       // disc moves to -Y, FSR channel on +Y
    yf = disc_pocket/2 + wall/2;
    py = pod_y + fsr_ch_w + wall;
    h  = skin_side_h + 0.4;
    difference() {
        union() {
            translate([0,yd,0]) rbox([pod_x, pod_y, h], 3);
            translate([0,yf+yd,0]) rbox([pod_x, fsr_ch_w+2*wall, h], 3);
            translate([0,yd,0]) wings(pod_x, h);
        }
        translate([0,yd,0]) disc_cut(-1);
        // FSR channel across the whole skin side (the strip runs around the wrist)
        translate([0, yf+yd, -1]) rbox([200, fsr_ch_w, fsr_ch_d+1], 0.3);
    }
}

module pod_top_worn() {              // MPU #1 on top + piezo 0 underneath
    h = skin_side_h + mpu_box_h;
    difference() {
        // wings on the OUTER face: the pod prints upside down with the wings flat on the bed
        union() { rbox([pod_x, pod_y, h], 4); translate([0,0,h-wing_h]) wings(pod_x); }
        disc_cut(-1);
        mpu_cut(h);
    }
}

module hand_plate_worn() {           // MPU #2 on the back of the hand
    px = mpu_seat_l + 2*wall + 4;
    h  = 1.6 + mpu_box_h;
    difference() {
        union() { rbox([px, pod_y, h], 4); wings(px); }
        mpu_cut(h);
    }
}

// Forearm carrier: breadboard tray + raised ESP32 cradle. Sits on the
// forearm, strap 2 goes under it through the side slots.
bb_pl = bb_l + 2*tol;  bb_pw = bb_w + 2*tol;
esp_gap  = esp_l + 2*tol;
end_t    = 2.6;
car_bb_x = -(esp_gap + 2*end_t + 4)/2;        // breadboard centre
car_es_x = (bb_pl + 2*wall + 4)/2;            // ESP32 centre
car_l    = bb_pl + 2*wall + 4 + esp_gap + 2*end_t;
car_w    = bb_pw + 2*wall;

module carrier() {
    tray_h = floor_t + 5;
    top_end = esp_lift + esp_pcb_t + 2.5;
    difference() {
        union() {
            // floor plate
            translate([(car_bb_x+car_es_x)/2 - (car_bb_x+car_es_x)/2, 0, 0])
            hull() {
                translate([car_bb_x,0,0]) rbox([bb_pl+2*wall, car_w, floor_t], 4);
                translate([car_es_x,0,0]) rbox([esp_gap+2*end_t, car_w, floor_t], 4);
            }
            // breadboard tray walls
            translate([car_bb_x,0,0]) rbox([bb_pl+2*wall, car_w, tray_h], 4);
            // ESP32 end walls (pin-free ends of the board) + ledges
            for (s=[-1,1]) translate([car_es_x + s*(esp_gap/2 + end_t/2), 0, 0])
                rbox([end_t, 18, top_end], 0.8);
            // ledges: antenna end (-X) 6 mm, USB end (+X) 2.5 mm, middle 14 mm only (clear of the plugs)
            translate([car_es_x - esp_gap/2 + 3, 0, 0]) rbox([6, 14, esp_lift], 0.6);
            translate([car_es_x + esp_gap/2 - 1.25, 0, 0]) rbox([2.5, 14, esp_lift], 0.4);
            // strap wings, one pair under each half
            for (cx=[car_bb_x, car_es_x], s=[-1,1])
                translate([cx, s*(car_w/2 + wing/2 - 1), 0])
                difference() {
                    rbox([slot_l + 6, wing + 2, wing_h], 2);
                    translate([0, s*0.5, -1]) rbox([slot_l, slot_t, wing_h+2], 0.8);
                }
        }
        // breadboard pocket
        translate([car_bb_x,0,floor_t]) rbox([bb_pl, bb_pw, 20], 1);
        // USB plug cut-out in the +X end wall
        translate([car_es_x + esp_gap/2 + end_t/2, 0, esp_lift - 4]) rbox([end_t+2, 12.5, 20], 1);
        // zip-tie slots either side of the ESP32 (tie it down across the board)
        for (dx=[-12,12], s=[-1,1]) translate([car_es_x+dx, s*(esp_w/2+tol+5), -1]) rbox([3.6, 2.0, 10], 0.5);
        // zip-tie slots along the breadboard edges for the wire bundles
        for (dx=[-30,0,30], s=[-1,1]) translate([car_bb_x+dx, s*(bb_pw/2+wall+0.0), -1]) rbox([3.6, 2.0, 10], 0.5);
        // weight-saving windows under the breadboard (kept away from the slots)
        for (dx=[-22,22]) translate([car_bb_x+dx, 0, -1]) rbox([30, 30, floor_t+0.5], 4);
    }
}

// Fit test: every critical fit at true size, prints in about 20 minutes.
module fit_test() {
    difference() {
        union() {
            rbox([100, 78, 1.2], 3);
            // disc seat (as a ring, skin side up)
            translate([-30, 18, 0]) cylinder(d=disc_pocket+2*wall, h=disc_depth+relief_h+1.2);
            // MPU seat frame
            translate([10, 22, 0]) rbox([mpu_seat_l+2*wall, mpu_seat_w+2*wall, 5], 1.5);
            // strap slot frame
            translate([38, 0, 0]) rbox([slot_t+4.4, slot_l+4.4, 3.6], 1.5);
            // FSR channel bar
            translate([-5, -8, 0]) rbox([60, fsr_ch_w+4, 2.2], 1);
            // ESP32 length gauge: two posts, the board should drop between them
            for (s=[-1,1]) translate([-12 + s*(esp_gap/2 + 1.3), -28, 0]) rbox([2.6, 14, 6], 0.6);
        }
        // disc seat, cut from the top of the ring
        translate([-30, 18, disc_depth+relief_h+1.2]) mirror([0,0,1]) disc_cut_flat();
        translate([10, 22, 1.2]) rbox([mpu_seat_l, mpu_seat_w, 10], 0.6);
        translate([38, 0, -1]) rbox([slot_t, slot_l, 10], 0.8);
        translate([-5, -8, 2.2-fsr_ch_d]) rbox([62, fsr_ch_w, 5], 0.3);
        // labels
        translate([-30, -2, 0.8]) linear_extrude(1) text("disc", size=4, halign="center");
        translate([10, 7, 0.8]) linear_extrude(1) text("MPU", size=4, halign="center");
        translate([-5, -20, 0.8]) linear_extrude(1) text("ESP32 length", size=3.5, halign="center");
    }
}
module disc_cut_flat() {             // disc seat without the wire groove, for the fit test
    translate([0,0,-1]) cylinder(d=disc_pocket, h=disc_depth+1);
    cylinder(d=relief_d, h=disc_depth+relief_h);
}

// ── Dummy parts (for the virtual fit check and the assembly picture) ──
module dummy_disc()  { translate([0,0,0.05]) cylinder(d=disc_d, h=disc_t); }
module dummy_mpu(top) {               // board + the 8 jumper plugs under the pin row
    translate([-mpu_l/2, -mpu_w/2, top-mpu_pcb_t-0.6+0.05]) cube([mpu_l, mpu_w, mpu_pcb_t]);
    if (mpu_wires == "jumpers")
        translate([-20.3/2, mpu_w/2-2.6, top-mpu_pcb_t-0.6-plug_h]) cube([20.3, 2.5, plug_h]);
}
module dummy_esp() {
    z = esp_lift + 0.05;
    translate([car_es_x-esp_l/2, -esp_w/2, z]) cube([esp_l, esp_w, esp_pcb_t]);              // board
    translate([car_es_x-esp_l/2+1, -9, z+esp_pcb_t]) cube([18, 18, 3.2]);                    // WROOM module (antenna end)
    for (s=[-1,1]) translate([car_es_x+esp_l/2-3-esp_pin_span, s*(esp_w/2-1.27)-1.25, z-plug_h]) cube([esp_pin_span, 2.5, plug_h]); // plugs
}
module dummy_bb() { translate([car_bb_x-bb_l/2, -bb_w/2, floor_t+0.05]) cube([bb_l, bb_w, bb_h]); }
module dummy_strap_pod(body_x, h) {    // strap path over a pod: through both slots and over the top
    for (s=[-1,1]) translate([s*(body_x/2+wing/2)-strap_t/2, -strap_w/2, -0.5]) cube([strap_t, strap_w, h+0.5]);
}

// ── Assembly picture: parts on a simple arm ─────────────────
wrist_rx = 30; wrist_rz = 22;        // wrist cross-section (ellipse), roughly 165 mm round
module place_on_wrist(angle) {       // angle 0 = top of the wrist, measured around the ellipse
    px = wrist_rx*sin(angle); pz = wrist_rz*cos(angle);
    n  = atan2(wrist_rx*sin(angle)/wrist_rx^2, wrist_rz*cos(angle)/wrist_rz^2);   // surface normal angle
    translate([px, 0, pz]) rotate([0, n, 0]) translate([0,0,0.2]) children();
}
module assembly() {
    color("#e8c39e") {
        // forearm + wrist + hand (very rough)
        rotate([-90,0,0]) scale([wrist_rx, wrist_rz, 1]) cylinder(r=1, h=1, $fn=48);
        hull() {
            translate([0,-10,0]) rotate([90,0,0]) scale([wrist_rx, wrist_rz, 1]) cylinder(r=1, h=1);
            translate([0,-140,0]) rotate([90,0,0]) scale([wrist_rx*1.35, wrist_rz*1.4, 1]) cylinder(r=1, h=1);
        }
        hull() {
            translate([0,10,0]) rotate([-90,0,0]) scale([wrist_rx*1.1, wrist_rz*0.9, 1]) cylinder(r=1, h=1);
            translate([0,85,0]) rotate([-90,0,0]) scale([wrist_rx*1.4, 12, 1]) cylinder(r=1, h=1);
        }
    }
    color("#2b6cb0") place_on_wrist(0) pod_top_worn();
    color("#38a169") place_on_wrist(70) pod_piezo_worn();
    color("#d69e2e") place_on_wrist(150) pod_combo_worn();
    color("#d69e2e") place_on_wrist(-150) pod_combo_worn();
    color("#805ad5") translate([0, 50, 12.5]) hand_plate_worn();
    color("#4a5568") translate([0, -85, wrist_rz*1.3+0.5]) rotate([0,0,90]) carrier();
    color("#222") translate([0, -85, wrist_rz*1.3+0.5]) rotate([0,0,90]) dummy_esp();
    color("#f7f7f7") translate([0, -85, wrist_rz*1.3+0.5]) rotate([0,0,90]) dummy_bb();
}

// ── Design checks (printed at render time) ──────────────────
echo(str("CHECK pod_top height = ", skin_side_h + mpu_box_h, " mm (", mpu_wires, ")"));
echo(str("CHECK piezo pod height = ", skin_side_h + 0.4, " mm"));
echo(str("CHECK carrier = ", car_l, " x ", car_w + 2*wing, " mm"));
echo(str("CHECK strap slot = ", slot_l, " x ", slot_t, " mm"));
echo(str("CHECK thinnest wall over disc relief = ", 1.2, " mm (>= 3 layers at 0.16 mm)"));
assert(slot_t >= strap_t + 0.6, "strap slot too thin for the strap");
assert(pod_y >= slot_l + 2*1.5, "pod too narrow for the strap slot");

// ── Output: print orientation ───────────────────────────────
if (part == "pod_piezo")  mirror([0,0,1]) translate([0,0,-(skin_side_h+0.4)]) pod_piezo_worn();     // skin side up
else if (part == "pod_combo") mirror([0,0,1]) translate([0,0,-(skin_side_h+0.4)]) pod_combo_worn();
else if (part == "pod_top")   mirror([0,0,1]) translate([0,0,-(skin_side_h+mpu_box_h)]) pod_top_worn(); // MPU opening on the bed, disc seat up
else if (part == "hand_plate") hand_plate_worn();
else if (part == "carrier")    carrier();
else if (part == "fit_test")   fit_test();
else if (part == "assembly")   assembly();
// virtual fit checks: each must render EMPTY (no overlap between part and component)
else if (part == "chk_pod_top")   intersection() { pod_top_worn(); union() { dummy_disc(); dummy_mpu(skin_side_h+mpu_box_h); dummy_strap_pod(pod_x, skin_side_h+mpu_box_h); } }
else if (part == "chk_pod_piezo") intersection() { pod_piezo_worn(); union() { dummy_disc(); dummy_strap_pod(pod_x, skin_side_h+0.4); } }
else if (part == "chk_pod_combo") intersection() { pod_combo_worn(); union() { translate([0,-(fsr_ch_w+wall)/2,0]) dummy_disc(); translate([-100, disc_pocket/2+wall/2-(fsr_ch_w+wall)/2-fsr_w/2, 0.05]) cube([200, fsr_w, fsr_t]); translate([0,-(fsr_ch_w+wall)/2,0]) dummy_strap_pod(pod_x, skin_side_h+0.4); } }
else if (part == "chk_hand")      intersection() { hand_plate_worn(); union() { dummy_mpu(1.6+mpu_box_h); dummy_strap_pod(mpu_seat_l+2*wall+4, 1.6+mpu_box_h); } }
else if (part == "chk_carrier")   intersection() { carrier(); union() { dummy_esp(); dummy_bb(); } }
