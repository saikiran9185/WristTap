# Camera-free, lidar-free localization options for the WristTap band (absolute 3D hand position + touch point on a projected wall, dark room)

Scope: technologies that could pair with an ESP32 wristband to give (a) absolute 3D wrist position in a room and/or (b) the touch point on a projected wall, with no camera or lidar, working in the dark. As of 15 Nov 2026. All cm figures are from the cited sources; where sources disagree, both are given. Prices in INR are from Indian listings where found, otherwise USD/AUD/GBP converted only roughly (1 USD ~ Rs 85-88, an assumption, not sourced).

## Q1. IMU-only with body model and touch resets (brief recap)

### Takeaway
IMUs give no absolute position. A two-IMU arm model plus a touch reset (ZUPT plus wall-plane constraint) is good right after calibration, but heading drift grows, and published smartwatch arm-tracking sits around 7-12 cm wrist error. It is the cheapest option and fully "band only, dark-OK", but on its own it is not absolute.

### Cited Findings
- WearMoCap (smartwatch + phone arm pose tracking, 2025): wrist RMSE 6.79 cm in upper-arm mode, other modes about 10-12 cm — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11738771/) (via the earlier WristTap IMU notes, search snippet, not full text)
- Learned inertial odometry (RoNIN/TLIO/AirIO) still drifts by a few percent of distance travelled (e.g. AirIO 3.56%, TLIO 6.46% drift on Nymeria), so it does not give stable cm wall coordinates — [TLIO arXiv](https://arxiv.org/abs/2007.01867) (summarised in earlier notes `../IMU drift fixes for hand tracking/deep_learning_methods.md`)
- Ultra Diffusion Poser (ETH, 2026) adds UWB inter-sensor distances to 6 IMUs precisely because "IMUs give no absolute measurement, so drift is hard to correct" — [arXiv 2606.02153](https://arxiv.org/pdf/2606.02153)

### Inferences
- The "~2 cm right after calibration" figure from earlier WristTap research holds only for a short time window. The yaw (heading) drift of a 6-axis IMU is what moves the projected point sideways on the wall.
- Every touch is a free reset (zero velocity + known plane), which bounds depth error. But the lateral (x,y on the wall) error after a long hover needs an absolute reference. That is why the options below matter.

### Gaps
- No published number for "wall-touch x,y error vs time since last reset" for a two-IMU arm chain. WristTap would have to measure it.

## Q2. UWB (DW1000 / DW3000 / DWM3000, Qorvo; ESP32 UWB boards; Apple U1/U2-style)

### Takeaway
UWB is the strongest "band-only, RF, dark-OK" absolute fix. Expect about 10 cm (good cases 10-15 cm) 3D with DIY ESP32 + DW3000 TWR and 4-6 anchors at about 10 Hz (up to about 100 Hz with fast drivers). That is too coarse for a touch point on its own, but ideal for correcting IMU drift (IMU for cm-level short-term shape, UWB for no-drift absolute). Indian cost is about Rs 2,000-5,000 per node, so a tag plus 4 anchors costs about Rs 10k-25k.

### Cited Findings
- Accuracy: Qorvo's nominal DW3000 ranging accuracy is about ±10 cm in line of sight with calibration. The 15.65 ps timer resolution does not mean mm accuracy, because antenna delay, multipath and clock stability dominate — [NiceRF DW3000 guide](https://www.nicerf.com/news/dw3000-uwb-indoor-positioning-twr-anchors-calibration.html)
- Peer-reviewed ESP32 + DWM3000 system: up to 10 cm accuracy using TWR between one tag and five anchors — [arXiv 2403.10194](https://arxiv.org/html/2403.10194v1)
- DIY ESP32 + DWM3000 RTLS build reports updates about every 100 ms and "consistently 10-15 cm in good conditions" — [Instructables / CircuitDigest](https://circuitdigest.com/microcontrollers-projects/diy-indoor-uwb-positioning-system-using-esp32-and-qorvo-dwm3000); code: [GitHub ESP32-DWM3000-UWB-Indoor-RTLS-Tracker](https://github.com/Circuit-Digest/ESP32-DWM3000-UWB-Indoor-RTLS-Tracker)
- Update rate: users report 100 Hz (10 ms) ranging is possible, depending heavily on driver speed. 10 Hz is typical for hobby builds — [Qorvo forum: UWB sensor refresh rate](https://forum.qorvo.com/t/uwb-sensor-refresh-rate/14966)
- DW3000 supports up to 6.8 Mbps, which shortens frames and allows faster measurements — [NiceRF](https://www.nicerf.com/news/dw3000-uwb-indoor-positioning-twr-anchors-calibration.html)
- TWR vs TDoA: TDoA needs networked anchors on a perfectly synchronised clock, usually a cabled 10 MHz distribution (wireless sync is possible but hard). Most ESP32 projects use TWR — [Qorvo forum: ESP32 + DW1000/DW3000](https://forum.qorvo.com/t/esp32-dw1000-or-dw3000-uwb/13968); [Qorvo forum: wireless anchor sync for custom TDoA](https://forum.qorvo.com/t/dw3000-dwm3001cdk-best-approach-for-wireless-anchor-clock-sync-custom-tdoa/25981); DIY downlink-TDoA thread: [Qorvo forum](https://forum.qorvo.com/t/diy-uwb-precise-positioning-with-downlink-tdoa/25550)
- India prices: bare Qorvo DWM3000TR13 about Rs 3,268 incl. GST + duty at Tanotis — [Tanotis](https://www.tanotis.com/products/qorvo-dwm3000tr13-transceiver-module-gpio-spi-8-25-ghz-6-8-mbps-55-ma-2-5-to-3-6v); about Rs 2,148 at DigiKey India — [DigiKey IN](https://www.digikey.in/en/products/detail/qorvo/DWM3000TR13/24367320); Qorvo store $28.34 — [Qorvo store](https://store.qorvo.com/products/detail/dwm3000-qorvo/681949/)
- Makerfabs ESP32 UWB DW3000 board about Rs 5,135 at Fabtolab — [Fabtolab](https://fabtolab.com/makerfabs-esp32-umb-dw3000-ultra-wideband); Ai-Thinker BU04 (DW3000 + STM32) about Rs 1,890 + GST at Robosap — [Robosap](https://robosap.in/product-category/wireless/wireless-modules/); Robu only lists an out-of-stock DWM1000 Crowtail — [Robu](https://stgaws.robu.in/product/elecrow-crowtail-dwm1000-uwbultra-wide-band-indoor-positioning-module)

### Inferences
- With TWR and N anchors, each tag fix needs N exchanges, so 4 anchors at 100 Hz ranging gives about 25 Hz position. Combine it with the IMU at 200+ Hz in an EKF.
- Body blocking (the wrist band is against the body, so the body sits between tag and anchors) is the main real-world error source. Mount anchors high in the 4 room corners, or 2 on the projection wall plus 2 behind the user.
- An Apple U1/U2-style phone could act as an anchor only through Apple's NearbyInteraction / accessory protocol with Qorvo's Apple-compatible firmware (DWM3001CDK). That is more complex than pure ESP32 anchors.
- UWB 10 cm is about the size of a projected button at 2-3 m wall width, so it is not enough for the touch point itself. Fuse with IMU, or use wall-side acoustic tap localization (Q5) for the touch point.

### Gaps
- No measured ESP32 + DW3000 TDoA accuracy or rate figure found.
- Apple U1/U2 accuracy figures were not researched in depth. Commonly quoted "cm-level" claims have no primary source here.
- Z (height) accuracy is usually worse than x,y when anchors are coplanar. No DW3000-specific number was found.

## Q3. Ultrasonic / acoustic ToF and TDoA (Marvelmind, Cricket, DIY mics/speakers, laptop-speaker chirps)

### Takeaway
Ultrasound is the most accurate RF-free, light-free room option: Marvelmind claims ±2 cm (differential) at up to 25 Hz. MIT Cricket gives 1-5 cm range and about 10 cm position. Research FMCW-chirp systems on phone or laptop speakers reach mm-level (MilliSonic 2.6 mm median 3D with a 4-mic array). Drawbacks: line of sight to beacons, occlusion by the body, and the fact that "dark room" is fine but "quiet room" is not guaranteed (audible chirps annoy people; near-ultrasound 18-22 kHz is borderline audible to young people).

### Cited Findings
- Marvelmind Super-MP-3D: up to ±2 cm precision (differential), absolute accuracy 1-3% of distance to beacons (reducible by calibration). Update rate 0.05-25 Hz, shared between mobile beacons in the non-inverse architecture (25 Hz for 1 mobile, 12.5 Hz for 2) — [RobotShop](https://ca.robotshop.com/products/marvelmind-starter-set-super-mp-3d-915-868mhz-useu); [Unmanned Tech UK](https://www.unmannedtechshop.co.uk/products/marvelmind-starter-set-super-mp-3d)
- Marvelmind price: starter sets about $700-$900 (Super-MP-3D $761 US, CAD $916; AUD 700-770 for the HW set; £635 UK, sold out); single Super-Beacon (22 kHz) about $124 — [Core Electronics](https://core-electronics.com.au/marvelmind-indoor-navigation-system-starter-set-hw-915868mhz-supporting-ultrasonic-and-tof.html); [RobotShop beacon](https://www.robotshop.com/products/marvelmind-super-beacon-22khz)
- MIT Cricket (RF + ultrasound, time difference between RF and ultrasonic pulse): project claims 1-3 cm ranging/positioning precision — [Cricket project](https://people.csail.mit.edu/hari/nmsweb/projects/cricket/). The thesis is more conservative: 5 cm distance, 10 cm position, 3 degrees orientation — [Priyantha thesis](https://people.csail.mit.edu/rudolph/Teaching/Articles/bodhi-thesis.pdf). Lecture slides: distance 1-5 cm, position 10-15 cm, error grows with distance and angle — [6.S062 slides](https://6s062.github.io/6MOB/2018/materials/cricket.pdf)
- CAT (FMCW acoustic distance between speaker and mic, fused with IMU) reaches mm-level tracking; MilliSonic, a successor, reports 0.7 mm median 1D and 2.6 mm median 3D accuracy for smartphones with a 4-microphone array — [MilliSonic arXiv 1901.06601](https://arxiv.org/pdf/1901.06601)
- Vernier (acoustic motion tracking on mobile devices): median error < 4 mm at 7 m — [Vernier PDF](https://innovationcenter.msu.edu/wp-content/uploads/2021/07/Vernier-Accurate-and-Fast-Acoustic-Motion-Tracking-Using-Mobile-Devices.pdf)
- Conventional FMCW processing loses accuracy when multipath components are close together — [MilliSonic](https://arxiv.org/pdf/1901.06601)
- FaceOri: ultrasonic ranging on earphones to track head position/orientation (a wearable-side ultrasonic example) — [arXiv 2203.10553](https://arxiv.org/pdf/2203.10553)

### Inferences
- DIY WristTap version: Mac/laptop speakers (or 2-4 cheap tweeters around the projection) emit 18-22 kHz FMCW chirps. An I2S MEMS mic on the band (e.g. ICS-43434 or INMP441, which work to about 20+ kHz at 48 kHz sampling) records them, and the ESP32 or Mac does the cross-correlation. The radio (ESP-NOW/BLE) carries the sync. This is a Cricket/CAT-style system with almost no infrastructure cost (about Rs 300-1,500 for mics/tweeters).
- Laptop built-in speakers are only about 30 cm apart, so the geometry is poor for room-scale 3D. You need 3-4 spread-out speakers for a good fix (geometric dilution).
- The ultrasonic route satisfies "no light, no camera" and is the best cm-per-rupee option, but it needs line of sight from the band mic to the speakers. A wrist mic facing the wall works if the speakers sit at the wall/projector.

### Gaps
- No primary source on how well an ESP32 + I2S mic captures 18-22 kHz chirps (mic response, aliasing). Builders would need to test it.
- No figures were found on how much body or sleeve occlusion degrades accuracy.

## Q4. Magnetic field tracking (Polhemus-style AC/DC EM, DIY coil + magnetometer, Finexus, uTrack)

### Takeaway
Commercial EM trackers (Polhemus Liberty) are sub-mm, 240 Hz, about 3.5 ms latency, dark-proof and occlusion-proof, but have a short range (about 1-2 m class) and are expensive and distorted by metal. Finexus and uTrack give mm-level finger tracking but only relative to the hand (a few cm range), not in the room. DIY room-scale coil + magnetometer measured results are about 15-30 cm, with cm only in theory. Not a good fit for room-scale WristTap. Good for finger pose relative to the band.

### Cited Findings
- Polhemus Liberty: 240 updates/s on all sensors at once; latency 3.5 ms (filters off), about 7 ms with dynamic filters — [Liberty datasheet via IITM](https://home.iitm.ac.in/skm/manuals/LIBERTY.pdf); Polhemus comparison tables list 0.03 in RMS (0.76-0.8 mm) static accuracy, but the extracted table could not be tied cleanly to Liberty — [Polhemus G4](https://polhemus.com/all-trackers/g4); [Polhemus Fastrak](https://polhemus.com/all-trackers/fastrak)
- Finexus (UW + Oculus Research, CHI 2016): 4 magnetometers track electromagnets on fingertips at 0.95 mm (fixed orientation) and 1.33 mm (random orientation) mean error vs optical ground truth — [UW Ubicomp Lab](https://ubicomplab.cs.washington.edu/publications/finexus); [PDF](https://ubicomplab.cs.washington.edu/pdfs/finexus.pdf)
- Independent student replication of Finexus: about 2.6 mm mean error, but only inside a 40 x 40 mm region — [UW CSE490V report](https://courses.cs.washington.edu/courses/cse490v/20wi/public/report_06.pdf)
- uTrack: 2 magnetometers on the back of the fingers + permanent magnet on the thumb, 4.84 mm average 3D accuracy (thumb relative to fingers) — [UW uTrack](https://ubicomplab.cs.washington.edu/publications/utrack)
- Room-scale: Cramér-Rao bound analysis shows cm accuracy is theoretically achievable in a 10 x 10 x 3 m room with 12 flat wall coils at 10 mW (theory, not measured) — [arXiv 1708.05677](https://arxiv.org/pdf/1708.05677)
- Measured DC-field multi-anchor coil system: max error 14.7 cm over 3.0 x 1.5 m — [IEEE 8938782 record](https://bvbvf1.bib-bvb.de/vufind/PrimoRecord/cdi_ieee_primary_8938782). Induced-field + random forest (2026): sub-20 cm 2D, sub-30 cm 3D — [arXiv 2602.00817](https://arxiv.org/html/2602.00817v1)
- Wearable magnetic receiver dissertation: 60-70 cm mean error depending on environment; 8 cm only when fused with LIDAR — [Pirkl dissertation](https://kluedo.ub.rptu.de/files/4558/dissertation_pirkl_endversion.pdf)

### Inferences
- Field strength falls as 1/r^3, so a DIY coil (e.g. a 3-axis coil driven by the Mac or ESP32 near the wall) + the band's magnetometer works well at less than 1 m. Near the wall it could refine the touch point if the coil sits behind the projection surface, but steel studs, rebar and laptops distort the field.
- "Auracle" is an ear-worn eating-detection device (acoustic), not a magnetic tracker. No magnetic system by that name was found.

### Gaps
- Polhemus range spec and Indian price not confirmed (typically quoted for US research labs only).
- No DIY ESP32 room-scale AC-coil tracker with measured cm results was found.

## Q5. Acoustic localization of the tap ON the wall or surface (piezos in the corners, TDoA in a solid)

### Takeaway
This directly gives the touch point, independent of where the band is. MIT's Responsive Window got σ = 2.5 cm on 2 x 2 m tempered glass with 4 corner piezos and about 65 ms latency. Generic table TDoA systems reach about 3 cm. Toffee (device-side) only gives bearing (4.3° mean error). Works in total darkness, costs under Rs 1,000 in piezos, but needs a hard continuous surface (glass, board, MDF panel). A painted plaster/brick wall is much harder (damping, dispersion). The band's IMU can supply the exact tap moment, which turns the problem into easier ToA-with-known-start.

### Cited Findings
- MIT Responsive Window (Paradiso, Leo et al., CHI 2002 / IEEE Sensors 2002): 4 contact piezo pickups near the corners, DSP extracts amplitude, frequency content and differential arrival times; σ = 2.5 cm on 1/4-in tempered glass and σ = 3-4 cm on 1 cm shatterproof glass over areas up to 2 x 2 m; coordinates within about 65 ms (DSP dominates); lower accuracy outside the square framed by the sensors; bending waves are highly dispersive, which smears the rising edge; analytic dispersion compensation would improve precision — [MIT Media Lab publication](https://www.media.mit.edu/publications/passive-acoustic-knock-tracking-for-interactive-windows-2); [Sensor Review 2005](https://d2pnhgckm19p0r.cloudfront.net/insight/content/doi/10.1108/02602280510585727/full/html); thesis [Che King Leo](https://resenv.media.mit.edu/pubs/theses/CheKingThesis.pdf)
- Earlier Paradiso systems: a simple 8-bit PIC timed the leading edge of each sensor and a least-squares fit gave coordinates; the method was first used on Ishii's PingPongPlus table — [Ars Electronica 2001, Paradiso](https://webarchive.ars.electronica.art/takeover/update/showtopiclong.asp%3FID=146.html)
- PingPongPlus: microphone array under a ping-pong table locating ball impacts by arrival times — [NIME 2014 paper](https://www.nime.org/proceedings/2014/nime2014_436.pdf)
- TAI-CHI (EU project): TDoA with 3+ sensors tested on steel whiteboard and hardwood board; the project's main breakthrough was time-reversal (location template matching), which works on any object without special materials; plate thickness determines resolution — [Cardiff thesis (Ji)](https://orca.cardiff.ac.uk/54576/1/U584936.pdf); [phys.org](https://phys.org/news116778958.html); [Elsevier chapter](https://www.oreilly.com/library/view/intelligent-production-machines/9780080447308/ch81.html)
- A different sound-based TDoA system on a 1 x 2 m table: about 3 cm average accuracy/precision; MoBat (2015) tried piezos in a chipboard table first and found the SNR insufficient — [MoBat, TUM](https://www.campar.in.tum.de/pub/kreskowski2015mobat/kreskowski2015mobat.pdf)
- Toffee (Xiao, Harrison et al., MobileHCI 2014): acoustic TDoA from the device's own sensors through the table, resolving tap bearing with 4.3° mean error on a laptop prototype — [Robert Xiao: Toffee](https://www.robertxiao.ca/research/toffee/); [Chris Harrison](https://chrisharrison.net/index.php/Research/Toffee)
- Hobby piezo TDoA project — [hackaday.io TapTDOA](https://hackaday.io/project/159821-taptdoa)

### Inferences
- Sampling-rate requirement (my calculation, not sourced): bending-wave speed in glass/MDF is roughly 300-1,500 m/s depending on frequency and thickness. For 1 cm resolution at about 1,000 m/s you need about 10 µs timing, i.e. 100 kHz+ per channel; 2.5 cm needs about 40 kHz. The ESP32's built-in ADC in DMA mode can reach about this rate on a few channels, but simultaneous sampling is better done with comparator edge-capture (the PIC-style approach) or a multi-channel audio codec / USB audio interface at 96-192 kHz on the Mac.
- Hybrid idea for WristTap: the band's IMU detects the tap impulse time (t0) and sends it over ESP-NOW (radio latency is about 1 ms, which is about 1 m of wave travel, so not good enough for absolute ToA). Better: use wall TDoA for x,y and the band only to confirm who tapped and with which gesture.
- A projected-on wall made of plaster is a poor medium. A cheap fix is a 4 x 3 ft MDF, acrylic or glass panel with 4 piezo discs (Rs 20-50 each) as the projection screen.

### Gaps
- No primary source found for the "Knocker" paper (it identifies objects by knocking with a phone, not localization). It was not verified as relevant.
- No accuracy figures found for plaster or brick walls.
- PingPongPlus's sampling rate was not found.

## Q6. Electric field, capacitive, RF backscatter, Wi-Fi CSI, mmWave hand tracking

### Takeaway
These all need infrastructure on the room side (radar units, Wi-Fi transceivers, electrodes), and most do not need the band at all. Device-free RF body tracking (WiTrack) is 10-21 cm. Wi-Fi CSI on ESP32 is good for gesture classification, not cm position. ESP32 Wi-Fi FTM is metres. mmWave radar can localize touches on a surface to about 1.6 cm (90th percentile) with 4 radars, which is the only one in this group competitive for wall touch. Dark-OK, no camera, but the radars are infrastructure.

### Cited Findings
- WiTrack (Adib et al., NSDI 2014, FMCW radio reflections): body centre localized to 10-13 cm in x/y and 21 cm in z on average; pointing direction 11.2° median; works through walls — [WiTrack NSDI'14 PDF](https://courses.grainger.illinois.edu/CS598WSI/fa2024/Papers\WiTrack_NSDI14.pdf); [project page](https://witrack.csail.mit.edu/)
- ESP32 Wi-Fi FTM (802.11mc) ranging: 75% of ranges within 5 m with 4 anchors in a 12 x 6 m room; multipath/NLOS bias heavy-tailed — [Emergent Mind summary](https://www.emergentmind.com/topics/commodity-esp32-wifi-sensors)
- ESP32 CSI hand gestures: 97.2% in-session / 92.1% cross-session classification accuracy (not position) — [Preprints 202602.0018](https://www.preprints.org/manuscript/202602.0018)
- Google Soli (60 GHz): sub-mm motion tracking claim at >10,000 fps, but the 7 GHz bandwidth limit gives about 2 cm range resolution — [Soli paper PDF](https://modernmobile.cs.washington.edu/docs/soli.pdf)
- mmWave FMCW touch localization with 4 radars (Amazon Science): 1.6 cm at 90th percentile; finger and hand closer than about 3 cm in range merge into one target. A passive 60 GHz tracker reached 0.8 cm (pen), 5 cm (pencil), 15 cm (marker) at 90th percentile — [Amazon Science PDF](https://cdn.amazon.science/25/4f/ffc25e4b4171bdda21f99581c2e6/sub-resolution-mmwave-fmcw-radar-based-touch-localization-using-deep-learning.pdf) (figures from search snippet; PDF text could not be extracted locally)

### Inferences
- A TI IWR6843 eval board costs roughly $100-200 abroad (not verified for India), and 4 of them plus deep-learning calibration are beyond a design-student budget and timeline.
- Electric-field / capacitive sensing on a whole wall (e.g. conductive paint electrodes) is a possible touch surface, but it is infrastructure and was not researched in depth here.

### Gaps
- RF-Capture hand accuracy not found. No ESP32 CSI paper reporting metric cm hand position was found.
- No sourced Indian price for TI mmWave boards.

## Q7. Light-based but camera-free (projector-coded light + photodiode; Lighthouse / TS4231), for comparison

### Takeaway
The projector itself can localize a photodiode on the band to its exact projector pixel with Gray-code patterns (Johnny Lee, UIST 2004). It is extremely cheap (one photodiode, Rs 20-50) and gives pixel-perfect wall coordinates, but it needs the projector to flash patterns (visible flicker unless the patterns are high-speed or IR) and only works while the band is inside the projector beam. SteamVR Lighthouse + TS4231 gives about 2-6 mm 3D. Both are "light", which the user prefers to avoid, but neither is a camera and both work in a dark room (they work best in the dark).

### Cited Findings
- Lee, Dietz, Maynes-Aminzade, Raskar, Hudson, "Automatic Projector Calibration with Embedded Light Sensors", UIST 2004: light sensors in the surface, Gray-coded binary patterns find each sensor's pixel location; number of patterns depends on projector resolution, not number of sensors — [MERL TR2004-036](https://merl.com/publications/docs/TR2004-036.pdf); [researchr](https://researchr.org/publication/LeeDMRH04)
- 1024 x 768 needs only about 20 patterns to identify every pixel uniquely — [blog summary 2010](https://automodellingandvideomapping.blogspot.com/2010/05/automatic-projector-calibration.html); fibre-optic sensors to USB light sensors give the exact pixel position — [Hackaday 2007](https://hackaday.com/2007/11/15/automatic-projector-calibration)
- Lighthouse: first-generation system about 1.9 mm RMS accuracy (study cited by VRARwiki) — [VRARwiki](https://vrarwiki.com/wiki/Lighthouse_tracking); FOSDEM 2025 open-source LH2 mocap for robotics: 6 mm accuracy, 0.15 mm precision — [FOSDEM 2025 slides](https://fosdem.org/2025/events/attachments/fosdem-2025-5013-repurposing-valve-s-steamvr-2-0-technology-to-develop-an-open-source-low-cost-motion-capture-system-for-robotics/slides/237613/fosdem_20_66dDa8e.pdf)
- L-Cube: open-source ground-truth localization with LH2 base stations + TS4231 + ESP32-S3 — [EWSN 2024 demos](https://www.ewsn.org/file-repository/ewsn2024/ewsn2024demos-final8.pdf); hobby TS4231 + ESP8266 log shows setup problems (no light events after configuring) — [hackaday.io 153224](https://hackaday.io/project/153224-ts4231-esp8266-lighthouse-tracking); [LighthouseESP GitHub](https://github.com/nullstalgia/LighthouseESP)

### Inferences
- For WristTap's "where on the projected wall" question, projector-coded light is the most direct: the photodiode on the band, near the fingertip, tells you the projector pixel under the hand. It could run as a brief pattern burst only at touch time (IMU detects tap, then Mac flashes about 20 frames, which takes about 0.33 s at 60 Hz). The latency is high but the cost is zero, and it self-calibrates the projector mapping.
- Lighthouse base stations (about $150-200 each abroad, used) are the most accurate DIY 3D option but are light sweeps and cost more.

### Gaps
- Indian availability and price of TS4231 and SteamVR base stations not found.
- No ESP32 TS4231 accuracy measurement found.

## Summary comparison (assembled from the cited findings above; ranking is my inference)

| Option | Gives | Accuracy (cited) | Rate / latency | Infrastructure | Rough cost (India) | Band-only? No cam/lidar? Dark? | DIY difficulty (1 easy - 5 hard) |
|---|---|---|---|---|---|---|---|
| IMU + arm model + touch reset | relative 3D, resets on touch | ~2 cm just after reset; 6.8-12 cm wrist RMSE (WearMoCap) | 100-1000 Hz, <10 ms | none | Rs 500-2,000 | Yes / Yes / Yes | 2 |
| UWB DW3000 TWR (4-6 anchors) | absolute 3D | ~10 cm (10-15 cm DIY) | 10 Hz typical, up to ~100 Hz ranging | 4+ powered anchors | Rs 10k-25k (5 nodes) | Tag on band + anchors / Yes / Yes | 3 |
| UWB TDoA | absolute 3D | ~10 cm | higher, scales to many tags | cabled-clock anchors | higher | Yes / Yes / Yes | 5 |
| Marvelmind ultrasonic | absolute 3D | ±2 cm diff., 1-3% of distance abs. | up to 25 Hz | 4+ beacons | ~$700-900 imported (~Rs 60-80k, est.) | Beacon on band / Yes / Yes | 2 (buy) |
| DIY ultrasonic/FMCW chirps (speakers + band mic) | absolute 3D | Cricket 10 cm pos.; CAT/MilliSonic mm-level in research | 10-50 Hz | 3-4 speakers | Rs 500-2,000 | Mic on band / Yes / Yes (needs LOS, quiet-ish) | 4 |
| Commercial EM (Polhemus) | absolute 6DoF | ~0.8 mm | 240 Hz, 3.5 ms | source coil, short range | very high | Sensor wired / Yes / Yes | 1 (buy) / unaffordable |
| DIY magnetic coils room-scale | absolute 3D | 15-30 cm measured | ? | coils | Rs 1-3k | Yes / Yes / Yes | 4 |
| Finexus / uTrack | finger pose relative to hand | 1-5 mm | real time | none (on hand) | Rs 1-2k | Yes / Yes / Yes | 3 |
| Wall piezo TDoA | touch x,y only | σ 2.5-4 cm on glass; ~3 cm table | ~65 ms | 4 piezos on a hard panel | Rs 200-1,500 | Wall-side / Yes / Yes | 3 |
| mmWave radar (4 units) | touch x,y | 1.6 cm @90% | ? | 4 radars | high | No / Yes / Yes | 5 |
| Wi-Fi CSI / FTM | gesture class / metres | 10-21 cm (WiTrack radar); FTM ~metres | - | APs / radios | low-high | No / Yes / Yes | 4-5 |
| Projector Gray code + photodiode | wall pixel x,y | ~1 projector pixel | ~20 frames per fix | the projector itself | Rs 50 | Yes / Yes (light) / Yes | 2 |
| Lighthouse + TS4231 | absolute 3D | ~2-6 mm | 30-120 Hz class | 1-2 base stations | high (imported) | Yes / Yes (IR light) / Yes | 4 |

### Inferred recommendation path for a design student in India
1. Now: IMU + arm model + touch-reset (already in progress).
2. Cheapest absolute fix for touch point: projector Gray-code photodiode burst at touch time (if light is acceptable), or a 4-piezo hard projection panel (no light).
3. Absolute 3D hover: DW3000 UWB (4 anchors + band tag) fused with the IMU, aiming at about 5 cm after fusion (not yet demonstrated in a source). Or DIY ultrasonic chirps from 3-4 speakers to an I2S mic on the band for better accuracy at lower cost, if near-ultrasound is acceptable in the room.
