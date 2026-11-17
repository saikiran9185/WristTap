// WristTap v2: a wearable you can open and close. Every part is parametric.
//
//   core_base + core_lid  : closed box on the FOREARM (just behind the wrist).
//                           Holds the breadboard, the ESP32 and MPU #1. The lid slides
//                           in from the elbow end and clicks shut. A power bank straps
//                           on top of the lid (two strap tunnels).
//   hand_base + hand_lid  : small closed shell on the BACK OF THE HAND for MPU #2.
//   pod_piezo (x4)        : slide onto the WRIST strap, disc touches the skin.
//   pod_fsr (x2)          : slide onto the FOREARM strap, inner forearm, FSR touches the skin.
//   fit_test              : 30 min print that checks every critical fit first.
//
// Axes (as worn): X = across the arm, Y = along the arm (+Y = towards the elbow for the
// core box, towards the fingers for the hand shell), Z = away from the skin, z = 0 = skin.
//
//   openscad -D 'part="core_base"' -o core_base.stl band.scad
// Print parts come out already turned the right way up (no supports needed).

include <config.scad>

part = "assembly";

// ── Shared sizes ────────────────────────────────────────────
slot_l  = strap_w + 2.5;            // strap tunnel / slot length (across the strap)
slot_t  = strap_t + 0.9;            // strap tunnel / slot height
wing    = slot_t + 2*2.2;
wing_h  = 3.6;
c_wall  = 2.4;                      // box walls
gd      = 1.2;                      // lid groove depth into the wall
lid_t   = 2.4;
lip     = 1.4;                      // wall above the lid groove
lid_gap = 0.3;                      // play around the lid in the groove

module rbox(size, r=2) {            // rounded box, centred in X/Y, from z=0
    r2 = max(0.01, min(r, size[0]/2-0.01, size[1]/2-0.01));
    hull() for (sx=[-1,1], sy=[-1,1])
        translate([sx*(size[0]/2-r2), sy*(size[1]/2-r2), 0]) cylinder(r=r2, h=size[2]);
}
module rbox_at(x0, x1, y0, y1, z0, z1, r=0.6) {   // rounded box from corner coordinates
    translate([(x0+x1)/2, (y0+y1)/2, z0]) rbox([x1-x0, y1-y0, z1-z0], r);
}

// ── Slide-lid box (used by the core box and the hand shell) ─
// Inner cavity X in [-iw/2, iw/2], Y in [0, il]. Floor from z=0 to zf.
// Lid sits in grooves at z = zg .. zg+lid_t+2*lid_gap, slides in from the +Y end.
// A ridge on the +Y end wall clicks into a window in a springy tongue of the lid.
function box_top(zg) = zg + lid_t + 2*lid_gap + lip;
latch_w = 8;                        // ridge length (X)
module slide_box_shell(iw, il, zf, zg, r=3) {
    ow = iw + 2*c_wall; ol = il + 2*c_wall; top = box_top(zg);
    difference() {
        translate([0, il/2, 0]) rbox([ow, ol, top], r);
        translate([0, il/2, zf]) rbox([iw, il, top], 1);                       // cavity
        // lid groove: both sides + the -Y end, open at the +Y end
        translate([0, (il + c_wall + 1 - gd)/2, zg]) rbox([iw + 2*gd, il + gd + c_wall + 1, lid_t + 2*lid_gap], 0.4);
        // +Y end wall cut down to the groove floor so the lid can slide over it
        translate([0, il + c_wall/2, zg + 25]) cube([iw + 2*gd, c_wall + 2, 50], center=true);
    }
    // latch ridge on top of the +Y end wall (triangle, 0.8 tall)
    translate([0, il + c_wall/2, zg]) rotate([0, 90, 0])
        linear_extrude(latch_w, center=true) polygon([[0, -1.0], [0, 1.0], [-0.8, 0]]);
}
// Lid as worn: from y = -gd+lid_gap (in the -Y groove) to past the +Y outer face (finger tab).
lid_tab = 4;
tongue_t = 1.4;                     // thinned springy tongue (PLA stays under ~0.6 % strain)
tongue_l = 20;
module slide_lid_final(iw, il, zg) {
    lw = iw + 2*gd - 2*lid_gap;
    y0 = -gd + lid_gap; y1 = il + c_wall + lid_tab;
    z0 = zg + lid_gap;
    ch_w = latch_w + 1.2;
    tw = latch_w + 6;
    win_y0 = il + c_wall/2 - 1.6; win_y1 = il + c_wall/2 + 1.6;
    translate([0, 0, z0]) difference() {
        union() {
            translate([0, (y0+y1)/2, 0]) rbox([lw, y1-y0, lid_t], 1);
            // finger lift on the tongue end + grip ridges on both sides of it
            translate([0, y1 - 1.4, 0]) rbox([tw - 2, 2.0, lid_t + 1.4], 0.8);
            for (s=[-1,1]) translate([s*(tw/2 + 1.2 + (lw/2 - tw/2 - 1.2)/2), y1 - 1.4, 0])
                rbox([lw/2 - tw/2 - 4, 2.0, lid_t + 1.0], 0.8);
        }
        translate([0, 0, -1]) rbox_at(-ch_w/2, ch_w/2, y0 - 1, win_y0 - 4.5, 0, 1 + 1.0, 0.3);
        translate([0, 0, -1]) rbox_at(-latch_w/2 - 0.6, latch_w/2 + 0.6, win_y0, win_y1, 0, lid_t + 4, 0.3);
        for (s=[-1,1]) translate([s*(tw/2 + 0.6), 0, -1]) rbox_at(-0.6, 0.6, win_y0 - tongue_l, y1 + 1, 0, lid_t + 4, 0.3);
        // thin the tongue from the top so it bends instead of snapping
        rbox_at(-tw/2, tw/2, win_y0 - tongue_l + 2, y1 - 2.6, tongue_t, lid_t + 5, 0.3);
    }
}

// ── CORE BOX (forearm) ──────────────────────────────────────
bb_px  = bb_w + 0.8;  bb_py = bb_l + 0.8;     // breadboard pocket
ch_w   = 7.6;                                // side channel for MPU #1 (stands on edge)
fence_t = 1.2;
zone_gap = 3;
esp_py = esp_w + 0.8;
c_iw   = ch_w + fence_t + bb_px;             // inner width
c_il   = bb_py + zone_gap + esp_py;          // inner length
c_zf   = floor_t;
esp_under = 2.5 + plug_h + 4;                // header spacer + jumper plug + room for the wire to bend
esp_z  = c_zf + esp_under;                   // underside of the ESP32 board
esp_top = esp_z + esp_pcb_t + 3.2;           // top of the WROOM module
c_zg   = esp_top + 1.0;                      // lid groove floor
esp_yc = bb_py + zone_gap + esp_py/2;
esp_x1 = c_iw/2 - 1.0;                       // USB end of the ESP32 (1 mm from the wall)
esp_x0 = esp_x1 - esp_l;
bb_x0  = -c_iw/2 + ch_w + fence_t;           // breadboard pocket, -X edge
mpu1_y = bb_py + zone_gap - 2;               // MPU #1 board edge with the pins (plugs point to -Y)

module core_base() {
    ow = c_iw + 2*c_wall;
    difference() {
        union() {
            slide_box_shell(c_iw, c_il, c_zf, c_zg, 4);
            // fence between the MPU channel and the breadboard
            rbox_at(-c_iw/2 + ch_w, -c_iw/2 + ch_w + fence_t, 0, c_il, 0, c_zf + 10, 0.3);
            // ESP32 rests: antenna end (6 mm) and USB end (2.5 mm), middle only (clear of the plug rows)
            rbox_at(esp_x0 - 0.4, esp_x0 + 6, esp_yc - 7, esp_yc + 7, 0, esp_z, 0.6);
            rbox_at(esp_x1 - 2.5, esp_x1 + 1.05, esp_yc - 7, esp_yc + 7, 0, esp_z, 0.4);
            // little end stops so the ESP32 can't slide along X
            rbox_at(esp_x0 - 1.6, esp_x0 - 0.4, esp_yc - 7, esp_yc + 7, 0, esp_z + 2.5, 0.4);
            // MPU #1: a floor lip keeps its bottom edge against the wall
            rbox_at(-c_iw/2, -c_iw/2 + ch_w, mpu1_y - 1, mpu1_y + mpu_w + 1, 0, c_zf + 0.8, 0.3);
            // strap wings (strap goes UNDER the box, through these slots, around the forearm)
            for (yc=[24, c_il - 24], s=[-1,1])
                translate([s*(ow/2 + wing/2 - 1), yc, 0]) difference() {
                    rbox([wing + 2, slot_l + 6, wing_h], 2);
                    translate([s*0.5, 0, -1]) rbox([slot_t, slot_l, wing_h + 2], 0.8);
                }
            // zip-tie lug outside the wrist end (tie the wire bundle down = no tug on the breadboard)
            translate([0, -c_wall - 3, 0]) rbox([46, 7, 4], 1.5);
        }
        // wire entry notch, wrist end (closed on top by the lid)
        translate([(bb_x0 + c_iw/2)/2 - 2, -c_wall - 1, c_zf + 12]) rbox([44, 2*c_wall + 2, 60], 3);
        // USB hole for the power-bank cable, +X wall
        translate([c_iw/2 + c_wall/2, esp_yc, esp_z + esp_pcb_t + 1.4 - 4.5]) rbox([c_wall + 4, 12.5, 9], 1.5);
        // zip-tie slots in the lug
        for (dx=[-15, 0, 15]) translate([dx, -c_wall - 3, -1]) rbox([3.8, 2.2, 10], 0.5);
        // label
        translate([0, c_il/2, -0.01]) mirror([1,0,0]) linear_extrude(0.6) text("WRISTTAP  v2", size=5, halign="center", valign="center");
    }
}

// power bank strap tunnels on the lid (strap runs across the arm, wraps over the power bank)
pb_tun_y = [27, c_il - 42];
module core_lid() {
    z0 = c_zg + lid_gap + lid_t;
    difference() {
        union() {
            slide_lid_final(c_iw, c_il, c_zg);
            for (yc = pb_tun_y) translate([0, yc, z0 - 0.01]) difference() {
                rbox([20, slot_l + 2*2, slot_t + 1.8], 1.5);
                translate([0, 0, -1]) cube([30, slot_l, 2*(slot_t + 1)], center=true);
            }
        }
        // arrow + text so you know which end goes to the wrist
        translate([0, 1.2, z0 - 0.6]) linear_extrude(1) {
            text("WRIST", size=5, halign="center", valign="bottom");
            translate([-14, 5]) polygon([[-3, 0], [3, 0], [0, -4.5]]);
            translate([14, 5]) polygon([[-3, 0], [3, 0], [0, -4.5]]);
        }
    }
}

// ── HAND SHELL (MPU #2, back of the hand) ───────────────────
h_iw = mpu_l + 0.8;                          // pin row runs across the hand (X)
h_il = mpu_w + 0.8 + mpu_ra_out + 1;         // board + plugs pointing to -Y (wrist)
h_zf = 1.6;
h_zg = h_zf + 0.8 + mpu_pcb_t + mpu_ra_t + 0.8;
h_ow = h_iw + 2*c_wall;
module hand_base() {
    difference() {
        union() {
            slide_box_shell(h_iw, h_il, h_zf, h_zg, 3);
            // strap wings at both X ends
            for (s=[-1,1]) translate([s*(h_ow/2 + wing/2 - 1), h_il/2, 0]) difference() {
                rbox([wing + 2, slot_l + 6, wing_h], 2);
                translate([s*0.5, 0, -1]) rbox([slot_t, slot_l, wing_h + 2], 0.8);
            }
        }
        // ribbon exit, wrist end (-Y)
        translate([0, -c_wall - 1, h_zf + 0.8]) rbox([h_iw - 2, 2*c_wall + 2, 30], 1);
    }
    // two rails the board sits on (clears solder joints on the underside)
    for (s=[-1,1]) rbox_at(s*(h_iw/2) - (s > 0 ? 3 : 0), s*(h_iw/2) + (s < 0 ? 3 : 0),
                           h_il - mpu_w - 0.4, h_il, h_zf - 0.01, h_zf + 0.8, 0.3);
}
module hand_lid() { slide_lid_final(h_iw, h_il, h_zg); }

// ── PODS ────────────────────────────────────────────────────
pw = 1.8;                                    // pod wall
disc_pocket = disc_d + 2*tol;
disc_depth  = disc_t + 0.3;
relief_d    = ceramic_d + 1.5;
relief_h    = 2.2;
skin_h      = disc_depth + relief_h + 1.2;
pod_y       = max(disc_pocket + 2*pw, slot_l + 2*1.8);
tun_h       = slot_t + 1.8;                  // tunnel height incl. roof

module strap_tunnel(px, z) {                 // strap runs along X through it
    translate([0, 0, z - 0.01]) difference() {
        rbox([px, pod_y, tun_h], 2.5);
        translate([0, 0, -1]) cube([px + 2, slot_l, 2*(slot_t + 1)], center=true);
    }
}
pp_x = disc_pocket + 2*pw;
module pod_piezo() {
    difference() {
        union() { rbox([pp_x, pod_y, skin_h], 3); strap_tunnel(pp_x, skin_h); }
        translate([0,0,-1]) cylinder(d=disc_pocket, h=disc_depth+1);
        cylinder(d=relief_d, h=disc_depth+relief_h);
        // wire groove along the strap (+X), both solder joints sit in it
        translate([pp_x/4, 0, -1]) rbox([pp_x/2 + 2, 6.5, disc_depth + relief_h + 1], 1);
        // finger notch to pry the disc out
        translate([-disc_pocket/2, 0, -1]) cylinder(d=6, h=disc_depth+1);
    }
}
pf_x = fsr_pad_d + 0.8 + 2*pw;
pf_h = 2.6;
module pod_fsr() {
    seat_d = fsr_pad_d + 0.8;
    difference() {
        union() { rbox([pf_x, pod_y, pf_h], 3); strap_tunnel(pf_x, pf_h); }
        // pad seat 1.0 deep with a 10 mm press bump left standing in the middle
        difference() {
            translate([0,0,-1]) cylinder(d=seat_d, h=1.0 + 1);
            translate([0,0,0.3]) cylinder(d=10, h=2);
        }
        // tail channel along the strap (+X)
        translate([pf_x/4 + 1, 0, -1]) rbox([pf_x/2 + 2, fsr_tail_w + 1, 1.0 + 1], 0.5);
    }
}

// ── FIT TEST ────────────────────────────────────────────────
module fit_test() {
    difference() {
        union() {
            rbox([118, 70, 1.2], 3);
            translate([-38, 14, 0]) cylinder(d=disc_pocket + 2*pw, h=disc_depth + 1.2);           // disc seat
            translate([-6, 18, 0]) rbox([fsr_pad_d + 0.8 + 2*pw, fsr_pad_d + 0.8 + 2*pw, 2.2], 2);  // FSR seat
            translate([26, 18, 0]) rbox([mpu_l + 0.8 + 2*pw, mpu_w + 0.8 + 2*pw, 4], 1.5);          // MPU seat
            translate([48, -12, 0]) rbox([slot_t + 4, slot_l + 4, 4], 1.5);                         // strap slot
            for (s=[-1,1]) translate([-20 + s*(esp_l + 0.8 + 2.4)/2, -20, 0]) rbox([2.4, 14, 6], 0.6); // ESP32 length posts
        }
        translate([-38, 14, 1.2]) cylinder(d=disc_pocket, h=10);
        translate([-6, 18, 1.2]) cylinder(d=fsr_pad_d + 0.8, h=10);
        translate([26, 18, 1.2]) rbox([mpu_l + 0.8, mpu_w + 0.8, 10], 0.6);
        translate([48, -12, -1]) rbox([slot_t, slot_l, 10], 0.8);
        translate([-38, -4, 0.8]) linear_extrude(1) text("disc", size=4, halign="center");
        translate([-6, 3, 0.8]) linear_extrude(1) text("FSR", size=4, halign="center");
        translate([26, 4, 0.8]) linear_extrude(1) text("MPU", size=4, halign="center");
        translate([-20, -32, 0.8]) linear_extrude(1) text("ESP32 length", size=3.5, halign="center");
    }
}
// breadboard gauge: a corner frame you drop the breadboard into (checks the core pocket)
module bb_gauge() {
    difference() {
        rbox([bb_px + 4, 24, 4], 2);
        translate([0, 2, 1.2]) rbox([bb_px, 24, 10], 0.6);
    }
}

// ── Dummy parts (virtual fit checks + pictures) ─────────────
module dummy_bb() { translate([bb_x0 + 0.4, 0.4, c_zf + 0.05]) cube([bb_w, bb_l, bb_h]); }
module dummy_esp() {
    translate([esp_x0, esp_yc - esp_w/2, esp_z + 0.05]) cube([esp_l, esp_w, esp_pcb_t]);
    translate([esp_x0 + 1, esp_yc - 9, esp_z + esp_pcb_t]) cube([18, 18, 3.2]);          // WROOM module (antenna end)
    translate([esp_x1 - 0.5, esp_yc - 4, esp_z + esp_pcb_t]) cube([2, 8, 2.8]);           // micro-USB socket
    for (s=[-1,1]) translate([esp_x1 - 3 - esp_pin_span, esp_yc + s*(esp_w/2 - 1.27) - 1.25, esp_z - 2.5 - plug_h])
        cube([esp_pin_span, 2.5, 2.5 + plug_h - 0.05]);                                    // spacer + plugs
}
// MPU with right-angle header, local: board X in [-l/2, l/2], Y in [0, w], pin edge at Y=0, plugs to -Y
module dummy_mpu_ra() {
    translate([-mpu_l/2, 0, 0]) cube([mpu_l, mpu_w, mpu_pcb_t]);
    translate([-mpu_l/2 + 3, 4, mpu_pcb_t]) cube([mpu_l - 6, 8, 1.2]);                    // chip + parts
    translate([-10.15, -mpu_ra_out, 0]) cube([20.3, mpu_ra_out + 2.6, mpu_pcb_t + mpu_ra_t]);
}
module dummy_mpu1() {    // standing on edge against the -X wall, chip facing +X, plugs to -Y
    translate([-c_iw/2 + 0.05, mpu1_y, c_zf + 0.8 + mpu_l/2 + 0.05]) rotate([0, 90, 0]) dummy_mpu_ra();
}
module dummy_mpu2() { translate([0, h_il - mpu_w - 0.4, h_zf + 0.8 + 0.05]) dummy_mpu_ra(); }
module dummy_lid_core() { core_lid(); }

// ── Assembly picture ────────────────────────────────────────
wrist_rx = 30; wrist_rz = 23;               // ~16.5 cm wrist
module place_on_wrist(angle, y=0) {
    px = wrist_rx*sin(angle); pz = wrist_rz*cos(angle);
    n  = atan2(wrist_rx*sin(angle)/wrist_rx^2, wrist_rz*cos(angle)/wrist_rz^2);
    translate([px, y, pz]) rotate([0, n, 0]) translate([0,0,0.2]) children();
}
module arm() {
    color("#e8c39e") {
        hull() {
            translate([0, 0, 0]) rotate([90,0,0]) scale([wrist_rx, wrist_rz, 1]) cylinder(r=1, h=1, $fn=48);
            translate([0,-200,4]) rotate([90,0,0]) scale([wrist_rx*1.4, wrist_rz*1.45, 1]) cylinder(r=1, h=1, $fn=48);
        }
        hull() {
            translate([0,10,0]) rotate([-90,0,0]) scale([wrist_rx*1.1, wrist_rz*0.9, 1]) cylinder(r=1, h=1, $fn=48);
            translate([0,90,-2]) rotate([-90,0,0]) scale([wrist_rx*1.5, 13, 1]) cylinder(r=1, h=1, $fn=48);
        }
    }
}
module core_assembled(show_lid=true) {
    color("#3d4a5c") core_base();
    color("#f4f4f4") dummy_bb();
    color("#222") dummy_esp();
    color("#2b6cb0") dummy_mpu1();
    if (show_lid) color("#8fa3bf", 0.85) core_lid();
}
module assembly() {
    arm();
    // core box on the forearm, wrist end 22 mm behind the wrist, box +Y towards the elbow
    translate([0, -22, wrist_rz + 3]) mirror([0,1,0]) {
        core_assembled();
        color("#555") translate([0, c_il/2 - 4, c_zg + lid_gap + lid_t + slot_t + 1.8]) rbox([26, 95, 24], 4);   // power bank
    }
    // 4 piezo pods on the wrist strap
    for (a = [0, 90, 180, 270]) color("#d69e2e") place_on_wrist(a, 4) pod_piezo();
    // 2 FSR pods on the forearm strap (inner forearm, under the box strap)
    for (a = [160, 200]) color("#c05621") translate([0, -45, 2]) scale([1.18, 1, 1.2]) place_on_wrist(a, 0) pod_fsr();
    // hand shell on the back of the hand
    color("#805ad5") translate([0, 38, 14]) hand_base();
    color("#b794f4", 0.85) translate([0, 38, 14]) hand_lid();
}
module core_open() {          // exploded: lid pulled out towards the elbow, so you can see inside
    color("#3d4a5c") core_base();
    color("#f4f4f4") dummy_bb();
    color("#222") dummy_esp();
    color("#2b6cb0") dummy_mpu1();
    color("#8fa3bf", 0.8) translate([0, c_il*0.75, 14]) core_lid();
}

// ── Checks ──────────────────────────────────────────────────
echo(str("CHECK core box outside = ", c_iw + 2*c_wall, " x ", c_il + 2*c_wall, " x ", box_top(c_zg) + slot_t + 1.8, " mm (with tunnels)"));
echo(str("CHECK hand shell outside = ", h_iw + 2*c_wall, " x ", h_il + 2*c_wall, " x ", box_top(h_zg), " mm"));
echo(str("CHECK piezo pod = ", pp_x, " x ", pod_y, " x ", skin_h + tun_h, " mm; 4 pods = ", 4*pp_x, " mm of a ~165 mm wrist"));
echo(str("CHECK fsr pod = ", pf_x, " x ", pod_y, " x ", pf_h + tun_h));

// ── Output (print orientation) ──────────────────────────────
module flip_lid(zg) { translate([0,0,-(zg + lid_gap)]) children(); }
if      (part == "core_base") core_base();
else if (part == "core_lid")  flip_lid(c_zg) core_lid();
else if (part == "hand_base") hand_base();
else if (part == "hand_lid")  flip_lid(h_zg) hand_lid();
else if (part == "pod_piezo") pod_piezo();
else if (part == "pod_fsr")   pod_fsr();
else if (part == "fit_test")  fit_test();
else if (part == "bb_gauge")  bb_gauge();
else if (part == "assembly")  assembly();
else if (part == "core_open") core_open();
else if (part == "core_inside") core_assembled(false);
else if (part == "hand_open") { color("#805ad5") hand_base(); color("#2b6cb0") dummy_mpu2(); color("#b794f4",0.8) translate([0, h_il*0.8, 8]) hand_lid(); }
// virtual fit checks: each must be EMPTY
else if (part == "chk_core")     intersection() { core_base(); union() { dummy_bb(); dummy_esp(); dummy_mpu1(); } }
else if (part == "chk_core_lid") intersection() { core_lid(); union() { core_base_no_ridge(); dummy_esp(); dummy_mpu1(); } }
else if (part == "chk_hand")     intersection() { hand_base(); dummy_mpu2(); }
else if (part == "chk_hand_lid") intersection() { hand_lid(); union() { hand_base_no_ridge(); dummy_mpu2(); } }
// the ridge sits inside the lid window when closed; check everything else
module core_base_no_ridge() { difference() { core_base(); translate([0, c_il + c_wall/2, c_zg - 0.01]) cube([latch_w + 0.4, c_wall + 0.4, 2], center=true); } }
module hand_base_no_ridge() { difference() { hand_base(); translate([0, h_il + c_wall/2, h_zg - 0.01]) cube([latch_w + 0.4, c_wall + 0.4, 2], center=true); } }
