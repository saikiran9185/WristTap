# Classical (non-deep-learning) methods to reduce IMU drift: error sources, calibration, fusion filters, multi-IMU arrays, ZUPT

Context: wrist + upper-arm IMUs (MPU6050/MPU6500-class 6-axis MEMS, maybe BNO085 9-axis) used to estimate hand position for touching a projected wall, with no camera, lidar or light sensors. Researched 15 Nov 2026. Most foundational sources are older (2007 to 2017) but still the standard references. Numbers marked "(computed)" are my own arithmetic from cited specs, not figures quoted by a source.

## 1. Error sources in MEMS IMUs, Allan variance, typical values, and why position drifts much faster than orientation

### Takeaway
For an MPU6500-class part, white noise is not the main problem. Unremoved bias is: the initial gyro zero-rate offset is up to ±5 °/s, and the bias moves with temperature by about ±0.24 °/s per °C. Gyro bias makes orientation error grow linearly with time. Once orientation is wrong, part of gravity leaks into the "linear" acceleration, so position error from a gyro bias grows like t³, and from an accelerometer bias like t². In practice, free-integrated position from a consumer IMU is useless after a few seconds unless something resets it.

### Cited Findings
**MPU-6500 datasheet (PS-MPU-6500A-01, rev 1.0, 2013; TDK now lists rev 1.3 from 2020 and marks the part "not recommended for new designs"):**
- Gyro: initial zero-rate output (ZRO) tolerance is ±5 °/s at 25 °C (production tested). ZRO variation over −40 to +85 °C is ±0.24 °/s/°C (characterization, not guaranteed). Rate noise spectral density is 0.01 °/s/√Hz, with total RMS noise 0.1 °/s-rms at 92 Hz DLPF. Sensitivity scale-factor tolerance is ±3%, scale-factor variation over temperature ±4%, nonlinearity ±0.1%, cross-axis sensitivity ±2% — [MPU-6500 Product Specification rev 1.0](https://ocw.cs.pub.ro/courses/_media/pm/prj2017/amocanu/mpu_6500_rev1.0_1_.pdf)
- Accelerometer: initial zero-g tolerance is ±60 mg on X/Y (Z ±80 mg in the full table). Zero-g change over temperature is ±0.64 mg/°C on X/Y and ±1 mg/°C on Z. Sensitivity tolerance ±3%, sensitivity change ±0.026 %/°C, nonlinearity ±0.5%, cross-axis ±2%, noise PSD 300 µg/√Hz — [MPU-6500 Product Specification rev 1.0](https://ocw.cs.pub.ro/courses/_media/pm/prj2017/amocanu/mpu_6500_rev1.0_1_.pdf)
- TDK's product page gives ±5 dps ZRO, 0.01 dps/√Hz gyro noise and 300 µg/√Hz accel noise. A trade-press summary gives 250 µg/√Hz for the accelerometer instead — [TDK MPU-6500 page](https://invensense.tdk.com/?p=554); [Fierce Electronics](https://www.fierceelectronics.com/embedded/motion-tracking-device-from-invensense)
- InvenSense does not publish a bias-instability figure for the MPU-6050. Measured Allan-variance results are the only source — [InvenSense forum, MPU6050 bias instability](https://adm.invensense.tdk.com/mpu6050-bias-instability-drift)
- A peer-reviewed Allan-variance study of MPU-6050 gyros sampled at 70 Hz found no Markov noise and no rate random walk, and found X and Z noisier than Y. Full numbers sit behind a 403; I could only read the abstract — [Sensors 2020, 20(17), 4841](https://www.mdpi.com/1424-8220/20/17/4841)
- An unverified blog figure for the MPU6050 gives ARW about 0.3 °/√h and bias instability about 10 °/h, against a tactical ADIS16490 at 0.006 °/√h and 0.8 °/h. I could not confirm these against a primary source — [wiredwisdom blog](https://wiredwisdom.netlify.app/posts/embedded-day-07/)

**Woodman, "An introduction to inertial navigation", Cambridge tech report UCAM-CL-TR-696 (2007; older but still the standard tutorial):**
- Grade comparison. MEMS Honeywell GG5300: ARW 0.2 °/√h, bias stability <70 °/h. Laser GG1320AN: 0.0035 °/√h, 0.0035 °/h — [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)
- Allan deviation reading rules. White noise (ARW/VRW) is the −0.5 slope, read at τ = 1 s. Bias instability is the flat minimum. Conversion: ARW (°/√h) = (1/60) × noise density (°/h/√Hz) — [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)
- Measured Xsens MTx gyros (12 h static log, 100 Hz): bias instability 32 to 43 °/h (0.009 to 0.012 °/s), ARW 4.6 to 4.8 °/√h — [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)
- Error growth laws:
  - Constant gyro bias: angle error grows linearly.
  - Gyro white noise: angle random walk, σ ∝ √t.
  - Constant accel bias: position error ½·b·t².
  - Accel white noise: second-order random walk in position, σ ∝ t^{3/2}.
  - Accel flicker/bias wander: velocity ∝ t^{3/2}, position ∝ t^{5/2}.
  
  Source: [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)
- "The critical error path": a tilt error ε projects g·sin(ε) onto the horizontal axes. A tilt error of only 0.05° gives a 0.0086 m/s² residual, which becomes **7.7 m horizontal position error after 30 s** — [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)
- Stationary MTx, 500 runs of 60 s with pure strapdown integration: **average position error over 150 m after 60 s**. Gyro noise dominates position drift after about 0.3 s, and accelerometer-caused drift becomes insignificant after a few seconds. Magnetometer fusion cut the 60 s error from over 150 m to about 5 m — [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)
- Kok, Hol and Schön: inertial-only estimates "are accurate on a short time scale, but suffer from integration drift over longer time scales". The standard fix is to combine them with other sensors or with models — [Kok, Hol, Schön 2017, Foundations and Trends in Signal Processing / arXiv 1704.06053](https://arxiv.org/abs/1704.06053)

### Inferences
- (computed) MPU6500 gyro noise of 0.01 °/s/√Hz is about 0.6 °/√h ARW. That is roughly 0.08° of random angle error after 1 minute, which is negligible next to bias.
- (computed) Gyro bias effects:
  - An uncalibrated ZRO of up to 5 °/s is up to 300 °/min of yaw drift.
  - Even 0.1 °/s of residual bias is 6 °/min.
  - The ±0.24 °/s/°C temperature coefficient means a wrist-worn sensor warming 2 to 3 °C from skin contact could shift bias by about 0.5 to 0.7 °/s, which is 30 to 40 °/min. Temperature compensation or continuous bias re-estimation is therefore mandatory. The coefficient is a characterization value, so real parts are probably better, but this is the order of magnitude to plan for.
- (computed) Accelerometer bias b to position error via ½·b·t²:
  - 1 mg residual (0.0098 m/s²): 0.5 cm at 1 s, 4.4 cm at 3 s, 49 cm at 10 s.
  - The uncalibrated ±60 mg: about 29 cm after just 1 s.
  - A 0.5° tilt error (0.086 m/s² leaked gravity): about 4.3 cm at 1 s and 17 cm at 2 s.
- (computed) Accel white noise at 300 µg/√Hz gives σ_pos ≈ q·t^{3/2}/√3: about 0.2 cm at 1 s and about 5 cm at 10 s. Bias and tilt errors dominate, not noise.
- Implication for WristTap: double-integrated hand position can only be trusted over short bursts, under roughly 1 s, between resets. Absolute hand position should come mainly from orientation × limb-length kinematics (upper arm + forearm), not from double integration.

### Gaps
- I could not open the Sensors 2020 MPU-6050 Allan table (HTTP 403). Peer-reviewed numeric ARW and bias instability for the MPU6050/6500 are unconfirmed here; the blog's 0.3 °/√h and 10 °/h are unverified.
- I did not obtain BNO085 gyro and accel noise or bias-stability figures from the CEVA datasheet (doc 1000-4044).
- I did not fetch better-part comparisons such as BMI270, ICM-42688-P or ICM-45686 datasheets. The ICM-40609-D datasheet lists ±10 mdps/°C gyro offset tempco, about 24x better than the MPU-6500 value, but that is a different part — [ICM-40609-D datasheet](https://invensense.tdk.com/wp-content/uploads/2022/07/DS-000330-ICM-40609-D-v1.2.pdf)

## 2. Calibration that removes systematic error

### Takeaway
Calibration removes the large constant terms: a multi-position static calibration takes out accelerometer bias, scale and misalignment, and a gyro bias measured at rest takes out the initial offset. What remains is bias instability plus temperature-driven bias change. Static multi-position calibration needs no equipment, and 12 orientations are enough.

### Cited Findings
- Tedaldi, Pretto and Menegatti (ICRA 2014) estimate accelerometer and gyro biases, scale factors and misalignments with no external equipment. The IMU is placed in 37 to 50 static positions held 1 to 4 s each, with automatic static-interval detection and gyro integration between poses. On a factory-calibrated Xsens MTi the results were comparable to the factory certificate. Open-source implementation: imu_tk — [Webering et al. 2022 summary of Tedaldi method](https://arxiv.org/abs/2207.04801v1); [imu_tk mirror](https://gitee.com/ysfvest/imu_tk)
- Webering et al. (2022) improved the method for low-noise and wireless IMUs: **N = 12 orientations are sufficient**, more orientations give only marginal improvement, and calibration time fell from about 5 min to under 2 min — [arXiv 2207.04801](https://arxiv.org/abs/2207.04801v1)
- Gyro constant bias "can be estimated by taking a long term average of the gyro's output whilst it is not undergoing any rotation". Accelerometer bias at rest is complicated by gravity, so orientation must be known — [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)
- Woodman's simulation versus real-device gap: an unmodelled gyro bias error of 0.03 °/√s, plus calibration and temperature effects, explained the extra real-device drift — [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)
- The MPU-6500's accelerometer zero-g tempco (±0.64 mg/°C) and gyro ZRO tempco (±0.24 °/s/°C) show that one-off room-temperature calibration leaves temperature-dependent residuals — [MPU-6500 PS rev 1.0](https://ocw.cs.pub.ro/courses/_media/pm/prj2017/amocanu/mpu_6500_rev1.0_1_.pdf)

### Inferences
- Recommended pipeline for WristTap:
  1. One-time 12-position accelerometer calibration per sensor (imu_tk style).
  2. Gyro bias averaged over 2 to 5 s at every power-up and whenever still.
  3. A temperature table (bias vs on-die temperature, logged while warming) or online bias tracking.
- (computed) After good calibration, residual accel bias of about 1 to 5 mg is plausible. That still gives 0.5 to 2.5 cm after 1 s of double integration, which is why position resets (section 6) remain necessary.

### Gaps
- I found no source quantifying residual drift (°/min, cm after N s) specifically after calibration of an MPU6050/6500. The Tedaldi paper's error tables were not retrieved.
- I found no published temperature-compensation curve for the MPU6500.

## 3. Fusion filters (complementary, Mahony, Madgwick, EKF/ESKF/MEKF, invariant EKF), yaw observability, heading drift rates

### Takeaway
All these filters use the accelerometer's gravity vector to correct roll and pitch, so tilt is bounded to a few degrees. Without a magnetometer, nothing observes yaw: 6-axis yaw drifts at whatever the residual gyro z-bias is. Reported rates are about 0.1 to 2 °/min for consumer parts. No filter is a clear winner; tuning matters more than filter family. Modern filters such as VQF add rest detection plus gyro bias estimation, which is what actually slows yaw drift.

### Cited Findings
- Madgwick gradient-descent filter, 2011 IEEE ICORR abstract: accuracy matching a Kalman-based algorithm, with **< 0.8° static RMS and < 1.7° dynamic RMS error**. The 2010 internal report states < 0.6° static and < 0.8° dynamic against a commercial filter, with optical verification — [Madgwick 2010 internal report](https://courses.cs.washington.edu/courses/cse466/14au/labs/l4/madgwick_internal_report.pdf); [ahrs docs on Madgwick](https://ahrs.readthedocs.io/en/latest/filters/madgwick.html)
- Rankings conflict across studies:
  - Quadcopter data: tuned Mahony beat Madgwick and EKF on Euler RMSE — [Ludwig & Burnham ICUAS 2018](https://web.cs.ndsu.nodak.edu/~siludwig/Publish/papers/ICUAS2018.pdf)
  - Foot-mounted data: Madgwick (β = 0.033) beat Mahony (kp = 0.13, ki = 0.3) on heading — [Ludwig et al. SPIE 2018](https://proceedings.spiedigitallibrary.org/conference-proceedings-of-spie/10598/105982L/Comparison-of-attitude-and-heading-reference-systems-using-foot-mounted/10.1117/12.2296568.full)
  - KUKA robot ground truth: EKF outperformed the others at higher compute cost — [Cavallo et al., via search summary, IFAC 2014](https://skoge.folk.ntnu.no/prost/proceedings/ifac2014/media/files/1173.pdf)
  - 3-axis gimbal: pure gyro integration had the highest roll/pitch RMSE, and Madgwick and Mahony were similar — [FAU thesis, Henrich 2020](https://www.mad.tf.fau.de/files/2020/02/BT_LeaHenrich_Final.pdf)
- VQF (Laidig & Seel, Information Fusion 2023; current state of the art among classical filters): includes rest detection, gyro bias estimation during rest and during motion, and magnetic disturbance rejection. Across many public datasets it reached **average RMSE 2.9° vs 5.3° to 16.7° for eight literature filters**, with gains also in gyro bias estimation. It outputs a separate 6D quaternion. MIT-licensed code at github.com/dlaidig/vqf — [VQF publication record](https://cris.fau.de/publications/284485551); [VQF docs](https://vqf.readthedocs.io/)
- Yaw is unobservable without a magnetic reference. NXP states that a 6-axis accel+gyro algorithm will drift in yaw, and a 9-axis one is needed to anchor heading — [NXP community](https://community.nxp.com/t5/Sensors/Gyro-drifting/m-p/435989)
- BNO085 "Game Rotation Vector" is 6-axis with no magnetometer: yaw is relative, set to zero at power-up, and drifts. Users report that AR/VR-stabilised modes help in some cases and not others. No datasheet drift rate was found — [SparkFun forum](https://community.sparkfun.com/t/bno080-ar-vr-stabilization-game-rotation-vector/38249); [Arduino forum](https://forum.arduino.cc/t/bno085-calibration-process/904696)
- Anecdotal heading drift rates (individual setups, not controlled benchmarks):
  - MPU-6050 6-DoF fusion: about **1.8 °/min** yaw — [Parallax forum PDF](https://forums.parallax.com/uploads/attachments/41167/106673.pdf)
  - ST ISM330BX stationary: about **2 °/min** at 3.84 kHz ODR, about **0.5 °/min** at 30 Hz, and about **0.1 °/min** on ST's demo board — [ST community](https://community.st.com/mems-sensors-48/ism330bx-sflp-drift-154042)
  - Raspberry Pi attitude sensor without magnetometer: elevation drift about 1 arcmin/h, but **azimuth drift almost 150° in 10 h** (about 0.25 °/min) — [arXiv 1412.6444](https://arxiv.org/pdf/1412.6444)

### Inferences
- Complementary, Mahony and Madgwick filters correct tilt only, using gravity. Mahony's integral term and Madgwick's gyro-bias extension estimate gyro bias only on the axes that gravity makes observable, so z-bias in the world frame (yaw) stays unobserved without a magnetometer.
- EKF, ESKF and MEKF add explicit bias states and covariances, which helps when extra updates exist (ZUPT, zero angular rate, kinematic constraints). The invariant EKF improves consistency, but it does not make yaw observable by itself.
- For WristTap: expect roughly 0.2 to 2 °/min yaw drift on each IMU after bias calibration. (computed) For a 0.6 m effective arm reach, 1° of yaw is about 1 cm of lateral hand error on the wall. Periodic heading re-referencing is needed, for example a "touch the calibration corner" gesture or using the wall plane as a constraint.

### Gaps
- I found no controlled, peer-reviewed °/min heading-drift figure for the MPU6050/6500 or the BNO085 Game Rotation Vector.
- I did not retrieve a quantitative invariant-EKF vs MEKF comparison for consumer IMUs.
- VQF 6D-specific heading error numbers were not retrieved (they are in the arXiv 2203.17024 tables).

## 4. Online gyro bias estimation, magnetometer-free heading, magnetometer pitfalls indoors

### Takeaway
The most effective classical yaw-drift reducer without a magnetometer is to re-estimate gyro bias whenever the sensor is detected at rest (a zero-angular-rate update), as VQF does. Magnetometers indoors are unreliable because building steel, radiators and wiring distort the field, but 9-axis fusion can still bound long-term drift if disturbances are detected and rejected.

### Cited Findings
- VQF performs rest detection and estimates gyro bias both during rest and during motion. This is listed as a core feature and was benchmarked as improving bias estimates over the literature methods — [VQF docs](https://vqf.readthedocs.io/); [VQF Information Fusion 2023](https://cris.fau.de/publications/284485551)
- Gyro bias can be estimated by averaging output while not rotating — [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)
- Indoors, the no-disturbance magnetometer assumption "is often violated" because of steel in buildings and objects like radiators — [Kok et al. 2013, Linköping](https://people.isy.liu.se/rt/manko/publications/KokWSG2013.pdf)
- Indoor magnetic fields can be distorted enough that heading cannot be computed directly from magnetic data — [Sensors 2020, PMC7146404](https://pmc.ncbi.nlm.nih.gov/articles/PMC7146404)
- Direction errors were measured in an office building and a grocery store, and an error model was proposed — [Liu & Pahlavan, WPI](https://cwins.wpi.edu/publications/conference%20paper/Guanxiong.pdf)
- Counterpoint: a magnetometer's long-term heading drift was small compared with gyro-derived heading, despite short-term fluctuations in complex buildings — [NeurIT, arXiv 2404.08939](https://arxiv.org/pdf/2404.08939)
- Out-of-plane magnetic variation was found at more than half of indoor measurement locations — [IEEE TIM 2021](https://unpaywall.org/10.1109%2FTIM.2021.3059317)
- Woodman: magnetometer-aided MTx reduced 60 s position error from over 150 m to about 5 m, which shows how much heading/attitude anchoring matters — [Woodman 2007](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf)

### Inferences
- WristTap near a projector and laptop, with possibly steel furniture or wall studs, is a high-disturbance case. If a BNO085 is used, prefer the Game Rotation Vector (6-axis) for short-term smoothness and use the magnetometer at most as a slow, gated heading reference (VQF-style disturbance rejection).
- Other magnetometer-free heading options for a two-IMU arm chain:
  - Treat the elbow as a hinge, so the relative yaw between forearm and upper-arm IMUs is constrained.
  - Use the known wall-normal direction at each touch.
  - Re-zero heading at a known pose ("arm pointing at the wall centre").

### Gaps
- I found no quantitative indoor heading error (degrees) for a typical room. The one figure found was an MSE of 12.74° for a Hall-effect magnetometer method, which is not directly comparable — [TUM thesis](https://mediatum.ub.tum.de/doc/1538362/document.pdf)
- Elbow-hinge, joint-axis-constraint heading methods (e.g. Seel/Laidig work on magnetometer-free joint angles) were not researched in this pass.

## 5. Multi-IMU arrays (averaging, virtual IMU, √N)

### Takeaway
Averaging N co-located IMUs with independent errors cuts noise variance by N, so standard deviation drops by √N. Real arrays report bias-instability improvements of about 3 to 5x for 8 sensors. Constant biases are not removed by averaging unless each sensor is calibrated, and correlated errors such as temperature-driven ones reduce the gain.

### Cited Findings
- Skog, Nilsson and Händel's open-source multi-IMU (MIMU) platform, which grew out of OpenShoe: averaging N IMUs with independent errors gives var(ū) = (1/N)·var(single). Adapted weights and constellation design can do better than plain averaging — [MIMU platform paper](https://typeset.io/pdf/an-open-source-multi-inertial-measurement-unit-mimu-platform-2p72z8xlkx.pdf); [OpenShoe](https://openshoe.org)
- Maximum-likelihood fusion of array measurements, with a Cramér-Rao bound: Skog, Nilsson, Händel and Nehorai, "Inertial Sensor Arrays, Maximum Likelihood, and Cramér–Rao Bound", IEEE Trans. Signal Processing 64(16):4218–4227, 2016 — [OpenShoe publications](https://www.openshoe.org/?p=905)
- Bose, Gupta and Händel studied the noise performance vs number of IMUs and the clock-related power consumption of multi-IMU platforms, to find an operating point. The Osmium MIMU4444 board has 32 IMUs — [SlideShare, multi-IMU PDR evolution](https://www.slideshare.net/slideshow/evolution-of-a-shoemounted-multiimu-pedestrian-dead-reckoning-pdr-sensor/77946393); [Massive sensor arrays](https://www.slideshare.net/slideshow/massive-sensors-array-for-precision-sensing/56818134)
- Gyro array patent: combined bias stability of **2.11 °/h vs 10.2 °/h for a single element, a 4.83x reduction**, against the √8 = 2.83x expected for uncorrelated errors. The larger factor was attributed to the combining method handling correlated errors. Note: I am inferring from the search snippet that the array has 8 gyros, and the exact patent is one of two listed results — [US patent 9772186](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9772186); [US patent 8887566](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8887566)
- Array calibration: peripheral-free calibration of redundant consumer MEMS IMU arrays — [Micromachines 13(8):1214](https://mdpi.com/2072-666X/13/8/1214)

### Inferences
- (computed) Four MPU6500s averaged would cut white noise 2x. Bias instability gains of about 2 to 4x are plausible, so yaw drift of about 1 °/min might drop to about 0.3 to 0.5 °/min. This only holds after per-sensor bias calibration, since uncalibrated constant biases average to a nonzero mean bias.
- A virtual IMU on a rigid wrist board is cheap: MPU6500s cost little and share one I²C/SPI bus. Larger arrays (8 to 32) bring power, clock-sync and bus-bandwidth costs (Bose et al.).

### Gaps
- I did not retrieve the 32-IMU Allan variance numbers (Osmium MIMU4444 subsets of 1 to 32).
- I could not attribute a reported "69.8% bias-instability reduction, 70.3% ARW reduction (array of up to 18 MEMS IMUs)" to a confirmed paper, so it is excluded.

## 6. Zero-velocity updates (ZUPT) and still-detection outside foot-mounted navigation

### Takeaway
ZUPT is the most effective classical position-drift corrector, but it needs regular, reliably detected zero-velocity moments. The foot provides these at every step; the hand does not. For a wall-touch interface, though, the moment of touch, and the pause before and after it, are natural still moments. Near-zero velocity at contact, plus wall-plane position constraints, act as ZUPT-like pseudo-measurements. Wrist-IMU studies report position errors below 10% of range of motion with a single IMU.

### Cited Findings
- Stroke-rehab upper-limb IMU tracking: zero-velocity events for upper-limb segments are harder to predict than in gait, but ZUPT was "the most effective method to correct the drift" compared with wavelet analysis and high-pass filtering — [Kent study](https://kar.kent.ac.uk/99941/1/article.pdf)
- Wrist-IMU work used the DynAMoS statistical detector to find static periods for ZUPT. It reports **errors below 10% of the range of motion for a single IMU, versus 1–2% for multi-IMU kinematic-model approaches**. ML classifiers outperformed threshold-based still-detection, but traditional drift correction remained competitive for position — [PMC9823748](https://pmc.ncbi.nlm.nih.gov/articles/PMC9823748); [PoliTo thesis](https://webthesis.biblio.polito.it/34849/1/tesi.pdf)
- For a hand-moved device, ZUPT accuracy is limited. Using stationary intervals before and after a motion to estimate gravity and bias improves it — [Chandel et al., PerCom Workshops 2020](https://staff.itee.uq.edu.au/jaga/proceedings/percomworkshops2020/papers/p292-chandel.pdf)
- Hand-held inertial metrology patents apply ZUPT at survey points where the device is deliberately held still — [US patent 9557157](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9557157)
- OpenShoe is the reference open-source foot-mounted ZUPT-aided INS (EKF with zero-velocity pseudo-measurements) — [OpenShoe](https://openshoe.org)

### Inferences
- Suggested WristTap design:
  - Run an ESKF with gyro and accel bias states.
  - Apply ZUPT and zero-angular-rate updates when a still-detector fires (accel magnitude near g, low gyro variance over about 100 ms).
  - Apply a contact update when the piezo detects a tap: velocity normal to the wall ≈ 0, and hand position lies on the wall plane.
  - Between touches, constrain hand position through the arm kinematic chain (upper-arm IMU + forearm/wrist IMU + measured segment lengths), so position error is bounded by orientation error × limb length instead of growing as t² to t³. This mirrors the 1–2% (multi-IMU kinematic) vs <10% (single IMU) gap reported above.
- (computed) With ZUPT every 1 to 2 s, a 1 mg residual accel bias contributes only about 0.5 to 2 cm per segment. A 0.5° tilt error contributes about 4 to 17 cm, so tilt accuracy (good fusion) matters more than accel bias.

### Gaps
- I found no published quantitative cm-level accuracy for IMU-only hand positioning on a wall or touch surface.
- No study combining ZUPT with tap or contact events (piezo) for upper-limb tracking was found in this pass.
