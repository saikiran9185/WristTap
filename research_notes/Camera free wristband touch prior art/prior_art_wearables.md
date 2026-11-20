# Camera-free wearable touch / gesture / pointing: prior art for WristTap

Compiled 15 Nov 2026. Scope: whole systems and products, not filter math. WristTap = ESP32 wristband, IMUs on wrist + upper arm, 4 piezo discs on wrist skin, 2 FSRs. Goal: tell a Mac/projector WHERE the user touches a projected wall (in the dark), WHEN, and WHAT gesture the hand makes.

Framing used throughout. Every system below answers some of three questions:
- **WHEN**: was there a contact or tap event? Detection, latency.
- **WHERE**: absolute position on a surface or screen, or on the body.
- **WHAT**: which gesture, pose or finger.

No wearable-only system found answers WHERE on a large wall in absolute coordinates.

---

## Q1. HCI research: closest systems, how they sense, accuracy

### Takeaway
Wrist and arm sensing is strong at WHEN (F1 0.95 to 0.99, about 10 ms latency with a ring IMU) and at WHAT (about 87 to 97% on 5 to 10 gestures, usually measured on the same user). For WHERE it works only in two cases: (a) a small set of discrete on-body locations (Skinput, ViBand), or (b) a small patch near the hand, where Acustico gets about 5 to 8 mm RMSE using wrist acoustic TDOA. No paper found localises touches across a wall-sized surface from the wrist alone.

### Cited Findings

**Bio-acoustic and vibration sensing (closest to WristTap's piezos)**
- **Skinput (Harrison, Tan, Morris; CHI 2010, CACM 2011).** An armband of vibration sensors works out where a finger taps on the arm and hand. Paired with a pico projector, it turns the skin into a display. — [CACM / MSR PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/11/p111-harrison.pdf); [CACM](https://cacm.acm.org/?p=37895)
  - Accuracy: up to 95.5% for 5 locations with the armband below the elbow. Secondary summaries give about 87.6 to 88% overall, 88.3% with the band above the elbow, and about 81.5% for 10 forearm locations. Accuracy drops as BMI rises, and jogging gave 4 false positives in 6 minutes. — [LaptopMag](https://www.laptopmag.com/articles/new-bio-acoustic-sensing-technology-turns-your-body-into-a-ui); secondary figures from [slide summary](https://fr.slideshare.net/Nehapevekar/skinput-technology). The secondary numbers are not checked against the paper's tables.
  - Lesson for WristTap: discrete classification of on-body sites works; continuous position does not.
- **ViBand (Laput, Xiao, Harrison; UIST 2016, Best Paper).** A custom kernel raises a commodity smartwatch accelerometer to 4 kHz, up from the roughly 100 Hz API limit. At that rate the watch can classify taps on forearm, palm and back of hand, identify grasped and motorised objects, and receive data through the body. The authors claim it is accurate, robust to noise, consistent across users and independent of environment. — [Robert Xiao project page](https://www.robertxiao.ca/research/viband/); [Chris Harrison](https://chrisharrison.net/index.php/Research/Viband); [paper PDF](https://modernmobile.cs.washington.edu/docs/viband.pdf); [CMU news](https://www.cmu.edu/news/stories/archives/2016/october/smartwatch-capability.html)
  - Lesson: about 4 kHz sampling of wrist vibration is enough for rich bio-acoustic classification. Piezo discs sampled through the ESP32 ADC at several kHz are in the same regime.
- **Acustico (Gong, Gupta, Benko; Facebook Reality Labs + Dartmouth; UIST 2020).** A passive acoustic wrist device with 4 sensors: 2 accelerometers and 2 microphones. It uses time-difference-of-arrival (TDOA) of surface-borne and airborne vibration to detect AND 2D-localise taps on uninstrumented surfaces. Tap detection F1 = 0.9987 across environmental noise. Localisation RMSE = 7.6 mm (X) and 4.6 mm (Y), with 20 participants. — [ACM DL](https://dl.acm.org/doi/10.1145/3379337.3415901); [Meta Research page](https://research.facebook.com/publications/acustico-surface-tap-detection-and-localization-using-wrist-based-acoustic-tdoa-sensing/); [Hackster summary](https://www.hackster.io/news/tapping-into-vibrations-9a684dfb2a65)
  - Limitation per Hackster: it was not tested for cases where the hand is not resting on the surface. As I understand it, localisation is of the fingertip relative to the wrist, within a small area near the hand, not in world or wall coordinates.
  - **This is the single closest prior art to WristTap's piezo array.** WristTap's 4 piezos could use TDOA in the same way, but that gives finger-relative-to-wrist position only.
- **VibAware (Kim et al., CHI 2023).** An active acoustic transmitter on the wrist plus an accelerometer on a ring, for microgesture and touch sensing. — cited in [TouchFusion related work](https://arxiv.org/html/2602.15011)
- **FingerPing (Zhang et al., Georgia Tech, CHI 2018).** A thumb ring injects 20 Hz to 6 kHz chirps into the body. 4 receivers on wrist and thumb tell apart up to 22 hand poses: the thumb touching each of 12 phalanges, plus 10 ASL poses. — [ResearchGate](https://www.researchgate.net/publication/324669169_FingerPing_Recognizing_Fine-grained_Hand_Poses_using_Active_Acoustic_On-body_Sensing); [ScienceDaily](https://www.sciencedaily.com/releases/2018/05/180514151908.htm)
  - Lesson: active acoustic sensing (driving a piezo as a transmitter) can read hand pose. WristTap's piezos could double as an active sensor. See Inferences.

**IMU-only wrist and finger sensing**
- **Serendipity (Wen, Ramos Rojas, Dey; CHI 2016).** An off-the-shelf smartwatch accelerometer plus gyroscope recognises 5 fine finger gestures (pinch, tap, rub, etc.): mean F1 87% (SD 7.9%), near-perfect when trained per user. — [ResearchGate](https://www.researchgate.net/publication/301931139_Serendipity_Finger_Gesture_Recognition_using_an_Off-the-Shelf_Smartwatch)
- **Thumb-to-finger with COTS watch accelerometer (Tsunoda et al., MUM 2024).** 80.1% on 17 gestures, 90.2% on 11, 98.2% on 5. — [ACM DL](https://dl.acm.org/doi/full/10.1145/3701571.3701600); [PDF](https://www.iplab.cs.tsukuba.ac.jp/paper/international/tsunoda_MUM2024.pdf)
  - Lesson: the gesture vocabulary should stay at about 5 to 8 classes for accuracy above 95%.
- **Finger-worn IMU touch contact (Gu, Yu et al.; UIST 2019).** An IMU ring on the proximal phalanx of the index finger raises contact-sensing F1 from 84.74% to 98.61%, with about 10 ms latency. The paper explicitly argues that cameras struggle to see the exact moment of contact, and proposes fusing the ring with optical sensing. — [PDF](https://xiaoying-wei.github.io/TappingRing.pdf); [dblp](https://dblp.uni-trier.de/rec/conf/uist/GuYLLXWS19.html)
- **TapID (Meier, Streli, Fender, Holz; 2021) and TapType (Streli et al., CHI 2022).** Wristbands with inertial sensors only, for taps and text entry on any surface. They already appear in WristTap's internal research. — cited in [TouchFusion](https://arxiv.org/html/2602.15011)
- **HaloTouch (CHI 2025, Robert Xiao's group).** Recent work on low-latency touch detection that builds on Gu et al.'s ring IMU. — [PDF](https://robertxiao.ca/pubs/2025_CHI_HaloTouch.pdf). Details were not extracted this session.
- **WristWhirl (Gong, Yang et al.; Dartmouth, UIST 2016).** The wrist acts as a joystick. 12 IR proximity sensors plus a piezo in the strap, driven by an Arduino Due. Directional marks took about 0.5 s and free-form shapes about 1.5 s. — [ACM DL](https://dl.acm.org/doi/abs/10.1145/2984511.2984563); [ScienceDaily](https://www.sciencedaily.com/releases/2016/10/161014150848.htm)

**Impedance, EMG and multimodal wristbands**
- **Tomo (Zhang & Harrison; UIST 2015).** Wearable electrical impedance tomography. Wrist placement scored 97% and 87% on two gesture sets, arm placement 93% and 81%, all per user and per session. Later EITPose work found Tomo-style cross-user accuracy of only about 38.8 to 51.7%. — [ACM DL](https://dl.acm.org/doi/10.1145/2807442.2807480); [PDF](https://chrisharrison.net/projects/tomo/tomo.pdf); [EITPose CHI 2024](https://dl.acm.org/doi/10.1145/3613904.3642663)
  - Lesson: "97%" in a wrist-gesture paper is often per user. Cross-user accuracy can collapse, so plan for per-user calibration.
- **EITPose (CHI 2024).** Wearable EIT for continuous hand pose estimation. — [ACM DL](https://dl.acm.org/doi/10.1145/3613904.3642663)
- **Z-Band (IMWUT, about 2025).** Wrist-based electrical impedance sensing for "on-world" touch. Touch detection above 95% when stationary. — [ACM DL](https://dl.acm.org/doi/abs/10.1145/3770637?af=R)
- **TouchFusion (Whitmire, Benko et al., Meta; arXiv 16 Feb 2026).** A research wristband that fuses 8-channel sEMG at 2 kHz, 1 MHz bioimpedance, 4 IR proximity sensors, single-pixel and 8x8 ToF, and IMU plus magnetometer. It detects world and body touch, taps, swipes and holds, and tracks fingertip motion like a trackpad.
  - World-touch AUC-ROC 0.994. Body touch 0.969.
  - Online tap success: median 0.95. Touch-state success: median 0.97 (mean 0.83).
  - 1D Fitts throughput only about 1.1 to 1.2 bits/s.
  - Wrist dead-reckoning velocity error about 15 to 18 cm/s, RMSE about 23 to 26 cm/s. Fingertip velocity error 3.5 cm/s.
  - It tracks relative motion and velocity, not absolute position.
  - — [arXiv](https://arxiv.org/html/2602.15011)
  - Lesson: even Meta's kitchen-sink wristband does relative trackpad-style tracking at low throughput and does not claim absolute world position. That is strong evidence that WristTap's WHERE needs an external reference.
- **WristPP (arXiv 2603.00606, 2026).** A wrist-worn system that estimates hand pose and pressure. Relevant to WristTap's FSRs. — [arXiv](https://arxiv.org/pdf/2603.00606). Numbers not extracted.
- **SonarWatch (arXiv 2408.12689, 2024).** Ultrasound plus motion field sensing for smartwatches. — [arXiv](https://arxiv.org/pdf/2408.12689)
- **Wrist NIR + IMU (Stanford, IEEE RA-L 2022).** Surface-touch and grasp detection, 97% mean accuracy. — [PDF](https://hci.stanford.edu/publications/2022/cofer_gestureDetection.pdf)

**Hybrid (excluded because it uses a camera, but shows the pattern)**
- **SurfaceXR (arXiv 2603.19529, 2026).** Fuses smartwatch IMUs with egocentric camera hand pose for surface interactions. The IMU supplies WHEN and the camera supplies WHERE. — [arXiv](https://arxiv.org/pdf/2603.19529). Full text could not be fetched because the file was over the size limit.
- **OmniTouch (Harrison, Benko, Wilson; UIST 2011).** A shoulder-worn depth camera plus pico projector that turns any surface into a touch display. It is excluded because it is camera-based, but it is the canonical "projected UI on any surface" wearable. No source was fetched this session, so see Gaps.

### Inferences
- The field's consistent pattern: wearables do WHEN and WHAT, and something external (camera, depth sensor, sensor bar, UWB) does WHERE. SurfaceXR and Gu et al. both state this division of labour explicitly.
- Acustico shows that 4 vibration sensors on the wrist with TDOA can localise to sub-centimetre accuracy, but only relative to the wrist. WristTap's 4 piezos could reproduce this to tell which finger tapped, or to give a small offset of the fingertip from the wrist. It cannot give the wrist's position on the wall.
- Skinput and ViBand show that discrete classification of tap sites is robust while continuous position is not. WristTap could offer a coarse "zone" mode, such as a 3x3 grid on the wall, if the wrist's absolute pose can be estimated at all.
- FingerPing suggests the 4 piezos could be driven as transmitter plus receivers (active sensing) for hand-pose recognition, in addition to passive tap pickup.

### Gaps
- Accuracy numbers for EchoFlex, SensIR, Taprint, TouchPose, ThumbTrak and MouseRing (Shen et al., 2024) were not found or verified this session. Search results never returned EchoFlex or Taprint. They may exist under different names, so verify before citing.
- ViBand's paper-level numbers (location count and % accuracy) were not extracted because the PDF was not parsed.
- Acustico's localisation area or grid size and the fingertip-versus-wrist reference frame should be checked in the full PDF. A local copy of the PDF was downloaded but could not be parsed because no PDF text tool is installed.
- OmniTouch accuracy was not fetched. From memory it is roughly finger-click detection on arbitrary surfaces with a depth camera, but it is unverified here.
- No 2022 to 2026 CHI, UIST or IMWUT paper was found that does wall-scale absolute touch localisation from a wrist wearable alone.

---

## Q2. Commercial products: what each can and cannot do about absolute position

### Takeaway
Every shipping wrist or hand wearable is either a discrete gesture classifier (Meta Neural Band, Apple Double Tap, Mudra, Doublepoint) or a relative motion pointer (Tap Strap mouse mode, Genki Wave, gyro air mice). None provides absolute position on a wall or screen without an external reference.

### Cited Findings
- **Meta Neural Band (sEMG; ships with Meta Ray-Ban Display, Sept 2025). Research basis: Kaifosh & Reardon et al., Nature 645:702-711 (2025).**
  - Closed-loop performance: 0.66 target acquisitions/s on a continuous navigation task, 0.88 gesture detections/s on discrete gestures, handwriting at 20.9 WPM.
  - Offline accuracy above 90% for held-out participants (Meta's own statement).
  - Personalisation improves handwriting by up to 16%.
  - — [Nature via RePEc](https://ideas.repec.org/a/nat/nature/v645y2025i8081d10.1038_s41586-025-09255-w.html); [Meta blog](https://www.meta.com/blog/reality-labs-surface-emg-research-nature-publication-ar-glasses-orion/)
  - Neural handwriting rolled out as Early Access around Aug 2026. Meta advises printing, a steady pace and resting the wrist on a hard surface. — [Ubergizmo](https://www.ubergizmo.com/2026/08/ray-ban-display-meta-rolls-out-neural-handwriting-for-silent-ai-interactions/); [Android Central](https://androidcentral.com/gaming/virtual-reality/early-access-metas-neural-band-just-got-cooler-with-neural-handwriting-for-ray-ban-display)
  - Absolute position: none. Navigation is gesture-driven, plus pointing via the glasses' UI.
- **Mudra Link / Mudra Band (Wearable Devices Ltd; CES 2025).** 3 "Surface Nerve Conductance" sensors plus a 6DoF IMU. Works as mouse, D-pad or keyboard, and claims to read pinch pressure (not independently verified). Runs on Windows, macOS, iOS and Android. Price $199 to $349 depending on version and source (sources conflict). — [UploadVR](https://uploadvr.com/mudra-link-is-a-200-meta-neural-wristband-alternative-for-any-device); [Wareable](https://www.wareable.com/news/mudra-link-neural-wristband-gesture-control-ces-2025-announcement); [Hackster](https://www.hackster.io/news/wearable-devices-unveils-the-mudra-link-a-neural-interface-gesture-wristband-bcaa833ac8ef); [Tom's Guide](https://www.tomsguide.com/computing/smart-glasses/i-tried-this-brain-sensing-wristband-at-ces-2025-and-it-feels-like-the-future)
  - Absolute position: none. Its cursor is IMU-relative, like an air mouse.
- **Apple Watch Double Tap (Series 9 / Ultra 2, Oct 2023) and AssistiveTouch.** Thumb-index double pinch. Runs on the S9 Neural Engine and fuses accelerometer, gyroscope and optical heart sensor data. Apple tuned it on hundreds of users to avoid accidental triggers, and it is disabled during workouts. — [Trusted Reviews](https://www.trustedreviews.com/explainer/what-is-apple-watch-double-tap-magic-new-gesture-explained-4367413); [MacRumors](https://www.macrumors.com/2023/10/26/new-apple-watch-double-tap-gesture)
  - Absolute position: none. It is a one-bit discrete event.
  - Lesson: the optical PPG sensor reads tendon and blood-volume changes as a gesture cue. WristTap's FSRs against the skin play a similar role.
- **Doublepoint WowMouse (Wear OS from 2023, Apple Watch from CES 2025).** A watch-only app for tap gestures and pointer control. Vendor-reported tap accuracy is 97% stationary, 95% walking and 94% running, with no calibration. One independent hands-on test registered only 3 of 10 TV flicks on one watch and 8 of 10 on a Galaxy Watch 7. — [Digital Trends](https://digitaltrends.com/mobile/wowmouse-app-apple-watch-doublepoint-gesture-click-mac-smart-home-control); [Beebom](https://beebom.com/wowmouse-update-control-tv-with-flick-of-wrist/amp/); [UploadVR](https://www.uploadvr.com/android-watch-app-wowmouse-simulates-mouse-input-for-ar-vr/)
  - Absolute position: none. The pointer is relative and IMU-driven.
- **Tap Strap 2 / TapXR (Tap Systems).** Finger-tap chording keyboard plus mouse.
  - Wired found mouse mode kept reading the table up to about 2 inches away, so it did not switch off when the hand was lifted.
  - Users report that air-mouse mode is hard because the same wrist motion both moves the pointer and clicks (the "Midas / click-jitter" problem). Tap accuracy drops without a stable surface.
  - Apple World Today rated it 3.5/5: "intriguing but gimmicky".
  - — [Wired review mirror](https://wirednews.pages.dev/review/tap-strap-2); [Apple World Today 2019](https://appleworld.today/2019/10/tap-strap-2-airmouse-improves-on-the-first-version-but-is-still-tricky-to-master/)
  - Absolute position: none.
- **Genki Wave ring (2018 onward).** 9DoF IMU plus nRF52832, sends MIDI over BLE. 6 gestures (tilt, pan, roll, vibrato, tap, click) and 3 buttons. About $299 to $349. — [Nordic](https://nordicsemi.com/News/2020/10/Genki-Instruments-Wave-uses-nRF52832); [Engadget](https://www.engadget.com/2018-03-09-wave-ring-wearable-midi-controller.html)
  - Absolute position: none. Its orientation output is continuous but relative, mapped to parameters.
- **Wii Remote (2006), the contrast case.** Absolute pointing comes from a PixArt IR camera in the remote viewing 2 IR LED clusters on the sensor bar. Camera resolution is 128x96, giving 1024x768 with sub-pixel analysis. In a UMD study, IMU-only "relative" mode and camera "absolute" mode were treated as distinct modes. — [WiiBrew Sensor Bar](https://wiibrew.org/wiki/Sensor_Bar); [WiiBrew pointing](https://www.wiibrew.org/wiki/Wiimote/Pointing); [UMD study](https://core.ac.uk/download/56107538.pdf)

### Inferences
- These products have converged on discrete gestures plus a relative cursor. Even Meta's roughly $800 system with a Nature paper behind it does not attempt absolute world pointing from the wrist.
- Tap Strap's lift-off and Midas problems are WristTap's main risks to avoid. WristTap's FSRs and piezo onset give an explicit contact signal that can gate when the pointer is "live". That is better than Tap Strap's optical proximity, which kept sensing the table about 2 inches away.
- Apple and Doublepoint numbers are vendor-reported and per gesture, with no published target-acquisition metrics.

### Gaps
- Not verified this session: Myo armband (Thalmic Labs, 2014 to 2018, 8-channel EMG plus IMU, discontinued), Litho finger controller (about 2019, IMU plus capacitive touchpad, AR pointing), Google Soli (60 GHz radar, Pixel 4 Motion Sense 2019, discontinued in Pixel), Xsens and Rokoko gloves (IMU mocap: finger pose, drifting global position; Rokoko Smartgloves reportedly add EMF for absolute position), Logitech Spotlight and Gyration air mice. These are background knowledge only and need citations before use. The Logitech Spotlight search returned nothing useful.
- No controlled accuracy studies were found for Tap Strap, Mudra or WowMouse pointing (Fitts throughput, target size).

---

## Q3. Has anyone achieved camera-free absolute pointing on a large wall or projection using only a wearable? Closest systems?

### Takeaway
No system was found that did this. The closest systems are:
- (1) Watchpoint (2016): smartwatch freehand pointing on a large display, using an IMU arm model.
- (2) SmartPoser (2025): adds UWB ranging to fix the IMU's lack of absolute reference.
- (3) Gyro air mice and IMU-only Wii mode, which are relative.

ArmPoser explicitly states it cannot recover absolute global heading.

### Cited Findings
- **Watchpoint (MobileHCI 2016).** Freehand pointing and clicking with a commodity smartwatch on nearby large displays. It was statistically comparable to baseline systems in speed and error rate, with lower error on small targets. — [ACM DL](https://dl.acm.org/doi/10.1145/2909132.2909263); [ResearchGate](https://www.researchgate.net/publication/303542611_Watchpoint_Freehand_Pointing_with_a_Smartwatch_in_a_Ubiquitous_Display_Environment) (the ResearchGate full text returned 403). The baseline and exact error numbers were not extracted.
- **"I am a Smartwatch and I can Track my User's Arm" (Shen et al., MobiSys 2016).** Arm-pose estimation from the watch IMU alone. — [ResearchGate](https://www.researchgate.net/publication/304358728_I_am_a_Smartwatch_and_I_can_Track_my_User's_Arm)
- **ArmPoser (2026).** Calibration-free arm pose from one smartwatch IMU. Its stated limitation: it estimates arm motion relative to the body but **does not recover absolute global heading**. — [arXiv](https://arxiv.org/pdf/2609.08806); [DOI](https://doi.org/10.1145/3822518.3830068)
- **SmartPoser (arXiv 2509.03451, 2025).** Fuses UWB ranging between phone and watch with IMU data. The UWB distances are absolute and drift less than inertial-only estimates. — [arXiv](https://arxiv.org/pdf/2509.03451)
- **Watch-Pointer (2026).** Wrist-IMU-driven pointer, but on the watch screen itself. — [ACM DL](https://dl.acm.org/doi/10.1145/3822518.3839304)
- Prior laser-pointer research found that distant absolute pointing has very low accuracy for small targets even when the device is tracked perfectly, because of hand tremor amplified over distance. — [Laser Pointer Interaction (Olsen & Nielsen, CHI 2001)](https://www.researchgate.net/publication/2930230_Laser_Pointer_Interaction)
- Wii Remote: without the sensor bar (IR camera reference) you get only relative inertial pointing. — [UMD study](https://core.ac.uk/download/56107538.pdf); [WiiBrew](https://www.wiibrew.org/wiki/Wiimote/Pointing)

### Inferences
- What WristTap is attempting has no published precedent: absolute wall-touch position from wrist plus upper-arm IMUs, with no camera. That makes it novel, but also high risk. The most likely failure is yaw (heading) drift, which ArmPoser names explicitly. Magnetometers indoors near a projector and steel are unreliable.
- Realistic camera-free fixes, borrowed from the systems above:
  - (a) Per-session calibration taps on known wall points (corners or projected targets), then a 2-link arm model from the shoulder. This works like the Wii's sensor-bar mapping, but with touches as the reference.
  - (b) Zero-velocity updates: re-anchor on every touch, because the hand is stationary on a known plane at touch time.
  - (c) Adding a cheap absolute reference that is not a camera, as SmartPoser does with UWB anchors near the projector. Another option is a single IR photodiode on the band that reads a projected pattern (structured-light timing), which works in the dark.
  - (d) Snapping to UI targets: projected UI with large targets, like a Skinput or ViBand discrete zone grid, instead of free continuous position.
- Since touching the wall puts the hand on a flat plane, the touch point is the intersection of the arm ray with the wall plane. Errors from upper-arm and forearm orientation scale with arm length, about 0.6 to 0.7 m. A 2-degree yaw error therefore moves the touch point about 2 to 2.5 cm, which is fine for large projected buttons but not for fine targets. This is a back-of-envelope estimate, not a cited figure.
- Note also that shoulder translation (the user stepping or leaning) is unobservable from wrist and upper-arm IMUs alone. A fixed standing position or a re-calibration tap is needed.

### Gaps
- Watchpoint's absolute/relative method and error numbers could not be read (403).
- No published cm-level accuracy was found for IMU-only arm-ray pointing at a wall.

---

## Q4. What accuracy and target sizes have these achieved? What WristTap can borrow or must avoid

### Takeaway
Benchmarks to beat or match:
- WHEN: F1 at least 0.98, latency about 10 ms or less (Gu 2019; Acustico F1 0.9987).
- WHAT: at least 95% on 5 gestures (Serendipity 87% F1; MUM 2024 98.2% on 5).
- WHERE on the body: 95.5% on 5 sites (Skinput).
- WHERE near the hand: about 5 to 8 mm RMSE (Acustico, wrist-relative).
- Continuous tracking: 1 to 1.2 bits/s Fitts throughput for wrist-only (TouchFusion), far below a mouse.
- No wall-scale absolute benchmark exists.

### Cited Findings (summary table)

| System | Year | Sensors | WHEN | WHERE | WHAT | Source |
|---|---|---|---|---|---|---|
| Skinput | 2010 | Vibration armband + pico projector | yes | 5 on-body sites, up to 95.5% | - | [MSR](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/11/p111-harrison.pdf) |
| ViBand | 2016 | Watch accel @4 kHz | yes | on-hand sites (count not extracted) | gestures, objects | [Xiao](https://www.robertxiao.ca/research/viband/) |
| Serendipity | 2016 | Watch accel + gyro | - | - | 5 gestures F1 87% | [RG](https://www.researchgate.net/publication/301931139_Serendipity_Finger_Gesture_Recognition_using_an_Off-the-Shelf_Smartwatch) |
| Tomo | 2015 | Wrist EIT | - | - | 97% / 87% per user; cross-user about 39 to 52% | [ACM](https://dl.acm.org/doi/10.1145/2807442.2807480) |
| WristWhirl | 2016 | 12 IR + piezo strap | - | wrist-joystick, relative | marks about 0.5 s | [ACM](https://dl.acm.org/doi/abs/10.1145/2984511.2984563) |
| FingerPing | 2018 | Active acoustic, thumb ring + 4 Rx | - | thumb on 12 phalanges | 22 poses | [RG](https://www.researchgate.net/publication/324669169_FingerPing_Recognizing_Fine-grained_Hand_Poses_using_Active_Acoustic_On-body_Sensing) |
| Gu ring IMU | 2019 | Index ring IMU | F1 98.61%, 10 ms | - | - | [PDF](https://xiaoying-wei.github.io/TappingRing.pdf) |
| Acustico | 2020 | 2 accel + 2 mic, wrist | F1 0.9987 | RMSE 7.6/4.6 mm (wrist-relative) | - | [ACM](https://dl.acm.org/doi/10.1145/3379337.3415901) |
| Z-Band | about 2025 | Wrist impedance | above 95% | - | - | [ACM](https://dl.acm.org/doi/abs/10.1145/3770637?af=R) |
| Meta sEMG / Neural Band | 2025 | 16-ch sEMG (product) | 0.88 det/s | - | above 90% offline; 20.9 WPM | [Nature](https://ideas.repec.org/a/nat/nature/v645y2025i8081d10.1038_s41586-025-09255-w.html) |
| TouchFusion | 2026 | sEMG+bioZ+IR+ToF+IMU | AUC 0.994; tap 0.95 | relative only; 1.1 to 1.2 bits/s | taps, swipes | [arXiv](https://arxiv.org/html/2602.15011) |
| WowMouse | 2023-25 | Watch IMU | 94 to 97% (vendor) | relative cursor | taps | [DT](https://digitaltrends.com/mobile/wowmouse-app-apple-watch-doublepoint-gesture-click-mac-smart-home-control) |
| Wii Remote | 2006 | IR camera + sensor bar | - | absolute, 1024x768 effective | - | [WiiBrew](https://www.wiibrew.org/wiki/Wiimote/Pointing) |

(The "16-ch" figure for the Neural Band is from background knowledge and was not verified this session.)

### Inferences: borrow
1. **Acustico-style TDOA on the 4 piezos.** Use it for finger identity and a small fingertip offset, and as a very high-confidence WHEN signal.
2. **ViBand-level sampling.** Sample the piezos at kHz rates, and classify the tap type (fingertip, knuckle, palm slap, nail) from spectral features. Skinput and ViBand show these are separable.
3. **Re-anchor the arm model on every touch.** Contact is a moment of zero velocity on a known plane (Gu, Acustico and TouchFusion all rely on a strong contact signal). Use the FSRs plus piezo onset for gating.
4. **Calibration taps on projected targets.** This plays the role of the Wii sensor bar. Expect to re-calibrate yaw every session and whenever the user moves.
5. **Small gesture vocabulary** of 5 to 8 classes, with per-user fine-tuning (Tomo's cross-user collapse, and Meta's 16% gain from personalisation).
6. **Discrete target layouts** in the projected UI, such as large buttons or zones. This is the honest choice until cm-level accuracy is measured.

### Inferences: avoid
- **Tap Strap's Midas and lift-off problems.** Do not let the same motion both move and click, and gate on true contact.
- **Reporting only per-user, per-session accuracy** (the Tomo trap). Report cross-session and cross-user numbers.
- **Relying on the magnetometer for heading** indoors near projectors and steel.
- **Claiming absolute wall position without an external reference.** No prior system does this, and ArmPoser explicitly notes heading is unobservable. Frame WristTap's WHERE as "calibrated, re-anchored arm-model estimate" and measure the error in cm across the wall.

### Gaps
- No standard metric exists for wall-scale wearable touch localisation. WristTap should define one, for example mean and 95th-percentile cm error on a grid of projected targets at several wall regions, plus drift over 5 minutes without re-calibration.
- Target-size data for gyro air mice and smartwatch pointing (Watchpoint) was not extracted.
