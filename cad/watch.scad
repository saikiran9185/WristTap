// WristTap WATCH: one small band. Printed flat in ONE piece:
//   compact block (ESP32 below, half breadboard on top, MPU #1 inside) + one wrist band with
//   P0..P3 discs around the wrist and F0/F1 on a paddle under the inner wrist.
// MPU #2 (hand) prints on the same plate as a loose piece: it must move with the hand.
// Edit sizes in sled.scad (parts) or below (band). F6, then File > Export > STL.
include <sled.scad>
part = "watch";            // watch | watch_plate (+ hand holder) | watch_view (with dummy parts)

/* [Block] */
esp_room = 5;              // space above the ESP32 board before the breadboard shelf
ledge    = 2.4;            // breadboard rests on this ledge (45° underneath, prints without support)
ledge_t  = 1.6;
bb_hold  = 5;              // pocket wall above the ledge

BX = Lb + 2*wall;          // block outer length (along the arm)
BY = W;                    // block outer width
ledge_z = pcb_z + 1.6 + esp_room;
top_z   = ledge_z + ledge_t + bb_hold;
ex0     = BX - wall - Le;  // ESP bay start (USB at the elbow end, x = BX)

/* [Band] */
bc  = -20;                 // wrist band centre line (just in front of the block)
qw  = wrist_c/4;           // top -> side of the wrist
yT  = BY/2;                // top of the wrist (P3)

module ledge_ring() {
    difference() {
        translate([wall, wall, ledge_z - ledge]) cube([Lb, pw, ledge + ledge_t]);
        hull() {
            translate([wall, wall, ledge_z - ledge - 0.01]) cube([Lb, pw, 0.01]);
            translate([wall + ledge, wall + ledge, ledge_z]) cube([Lb - 2*ledge, pw - 2*ledge, ledge_t + 1]);
        }
    }
}

module block() {
    difference() {
        union() {
            difference() { rbox([BX, BY, top_z], 3); translate([wall, wall, floor_t]) cube([Lb, pw, top_z]); }
            ledge_ring();
            // ESP32 rib frame + two stops on its wrist side
            translate([ex0 + 6, BY/2 - rib_w/2, 0]) difference() {
                cube([Le - 12, rib_w, pcb_z]);
                translate([rib, rib, floor_t]) cube([Le - 12 - 2*rib, rib_w - 2*rib, 50]);
            }
            for (s=[-1,1]) translate([ex0 - wall, BY/2 + s*(esp_w/2 + tol - 3) - 3, 0]) cube([wall, 6, pcb_z + 3]);
            // MPU #1 pocket on the floor at the wrist end, pins + plugs point to +Y
            translate([wall + 3, BY/2 - 14, 0]) difference() {
                cube([mpu_l + 2*tol + 2*wall, mpu_w + 2*tol + wall, floor_t + 2.5]);
                translate([wall, wall, floor_t]) cube([mpu_l + 2*tol, mpu_w + 5, 10]);
            }
        }
        // wire windows in both long walls (wires from the ESP + MPU go up to the breadboard)
        for (x=[6, 34, 62], y=[-1, BY - wall - 1]) translate([x, y, floor_t + 4]) cube([BX - 68 > 20 ? 22 : 18, wall + 2, ledge_z - ledge - floor_t - 6]);
        // USB opening (elbow end)
        translate([BX - wall - 1, BY/2 - usb_w/2, pcb_z - 1]) cube([wall + 2, usb_w, 8]);
        // window under the ESP inside the rib frame
        translate([ex0 + 6 + rib + 2, BY/2 - rib_w/2 + rib + 2, -1]) rbox([Le - 12 - 2*rib - 4, rib_w - 2*rib - 4, floor_t + 2], 2);
        // labels
        lab(ex0 + 2, wall + 1.2, "ESP32  USB >", 3.2);
        lab(wall + 3, wall + 1.2, "MPU #1", 3.2);
        // finger notches to lift the breadboard out
        for (y=[-1, BY - wall - 1]) translate([BX/2 - 8, y, top_z - 3]) cube([16, wall + 2, 5]);
    }
}

module watch_band() {
    // spine: block -> band
    translate([bc, BY/2 - bw/2, 0]) rbox([-bc + 4, bw, floor_t], 3);
    yP = yT + 2*qw;                         // under the wrist (inner wrist), on the +Y side
    yEnd = yP + 25;                         // +Y end
    yNeg = yT - (wrist_c - (yEnd - yT)) - 8; // -Y end: overlaps the +Y end by 8 mm under the wrist, like a watch strap
    band_y(bc, yNeg, yEnd);
    end_tab(bc, yNeg); end_tab(bc, yEnd);
    disc_pad(bc, yT,       "P3");           // top of wrist
    disc_pad(bc, yT + qw,  "P0");           // little-finger bone
    disc_pad(bc, yT - qw,  "P2");           // thumb bone
    // paddle under the inner wrist: P1 + F0/F1 just above it towards the elbow
    translate([bc - bw/2, yP - 25, 0]) rbox([bw + 30, 50, band_t], 3);
    disc_pad(bc, yP, "P1");
    fsr_pad_m(bc + 29, yP - 12.5, "F0", -1);
    fsr_pad_m(bc + 29, yP + 12.5, "F1", 1);
}

module watch() { block(); watch_band(); }

if (part == "watch") watch();
if (part == "watch_plate") { watch(); translate([BX + 12, -30, 0]) hand_holder(); }
if (part == "watch_view") {
    color("#f2b134") watch();
    color("#1f2b3a") translate([ex0 + tol, BY/2 - esp_w/2, pcb_z]) cube([esp_l, esp_w, 1.6]);
    color("ivory") translate([wall + tol, wall + tol, ledge_z + ledge_t]) cube([bb_l, bb_w, 8.5]);
    color("#2b6cb0") translate([wall + 3 + wall + tol, BY/2 - 14 + wall + tol, floor_t]) cube([mpu_l, mpu_w, 1.6]);
}
echo(str("BLOCK ", BX, " x ", BY, " x ", top_z, " mm  (breadboard top at ", ledge_z + ledge_t + 8.5, ")"));
