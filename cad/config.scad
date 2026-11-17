// WristTap wearable — MEASUREMENTS. Measure your parts with a ruler, change the
// numbers here, then run ./cad/build.sh. Every value is in millimetres.
// "(measure)" = please check this one on your own part before the full print.

/* [Fit] */
tol        = 0.3;    // extra gap around every part (raise to 0.4 if the fit test is tight)

/* [Strap] */
strap_w    = 25;     // velcro strap width
strap_t    = 2.6;    // strap thickness where the velcro overlaps (measure)

/* [Piezo disc] */
disc_d     = 27.0;   // brass disc diameter (27 mm discs)
disc_t     = 0.5;    // brass + ceramic thickness
ceramic_d  = 20.0;   // white/grey ceramic circle diameter (measure)

/* [MPU boards] */
mpu_l      = 21.2;   // board length, along the pin row (measure)
mpu_w      = 16.4;   // board width (measure)
mpu_pcb_t  = 1.6;
mpu_wires  = "jumpers"; // "jumpers" = female jumper plugs on the pins (today), "soldered" = wires soldered to the pads (thin pod)
plug_h     = 14.0;   // female jumper plug height under the board
wire_bend  = 3.0;    // room for the wire to bend sideways under the plug

/* [FSR strip] */
fsr_w      = 10.0;   // green FSR strip width (measure)
fsr_t      = 0.4;    // strip thickness

/* [ESP32 DevKit, 30 pin] */
esp_l      = 51.5;   // board length, USB end to antenna end (measure)
esp_w      = 28.3;   // board width (measure)
esp_pcb_t  = 1.6;
esp_pin_span = 38.1; // length of each pin row (15 pins x 2.54)
esp_lift   = 18.0;   // board underside above the bottom of the carrier: floor 2.4 + jumper plugs 14 + 1.6 spare

/* [Breadboard, 400 point half size] */
bb_l       = 82.5;   // (measure)
bb_w       = 54.5;   // (measure)
bb_h       = 8.5;

/* [Print] */
wall       = 2.0;
floor_t    = 2.4;
$fn        = 64;

/* [v2 band: closed shells, see band.scad] */
mpu_ra_out = 17.0;   // right-angle header: how far the jumper plugs stick out past the pin edge (measure)
mpu_ra_t   = 4.0;    // right-angle header: plug height above the MPU board top (measure)
fsr_pad_d  = 18.5;   // FSR 402 round pad diameter (measure)
fsr_tail_w = 8.0;    // FSR tail width (measure)
fsr_pad_t  = 0.45;
