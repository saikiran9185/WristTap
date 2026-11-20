# Kinematic body-model and constraint-aided IMU hand/arm tracking (no cameras / UWB / light)

Context for the reader: a user stands in place and touches a projected wall. Calibration is done by touching the 4 projection corners, and later touches are detected by a wrist piezo. The question is how far an IMU-only arm chain (upper arm + forearm, optionally hand and torso) can go without double integration, and how touches can be used to cancel drift.

Research note: about 17 tool calls were used. Several primary full texts could not be fetched: the Xsens MVN whitepaper PDF came back as compressed binary, PMC returned a captcha, MDPI returned 403, and the people.isy.liu.se DNS lookup failed. Where a number comes from a search snippet or a secondary summary, it is labelled that way.

## 1. IMU arm motion capture: forward kinematics, sensor-to-segment calibration, reported wrist/hand errors, commercial drift handling

### Takeaway
Hand position from the orientation of each segment combined with segment lengths (forward kinematics, FK) involves **no double integration**. Its error is bounded by orientation error × lever arm plus segment-length and calibration error. Upper-limb IMU studies against optical mocap report wrist position errors of **about 1–2 cm (SD) for short reaching tasks with 2+ IMUs**. With a single wrist IMU plus learned priors the error is **about 2.5–10 cm**. Joint-angle RMSEs are **about 2–12°** for commercial suits. Commercial suits (Xsens/Movella) handle drift with magnetometers plus a biomechanical model plus contact detection, but they admit drift remains when the body is not in contact with the world.

### Cited Findings
- A 2021 Scientific Reports study tracked wrist position relative to the shoulder, using IMU-estimated upper-arm and forearm orientations fed into a kinematic arm model. Against Vicon during healthy-participant reaching, mean signed error was **0.09 ± 1.81 cm** for the IMU method and 0.48 ± 1.58 cm for HTC Vive. The work targeted stroke survivors. Numbers are from the search summary; the full text was blocked by a captcha. — [Sci Rep 2021, s41598-021-01805-2](https://www.nature.com/articles/s41598-021-01805-2); [PMC PDF mirror](https://rcastoragev2.blob.core.windows.net/70ec799215a036b7856259118f23de32/PMC8602299.pdf)
- A single wrist-IMU trajectory reconstruction (drinking task, Politecnico di Torino thesis) reported about 1 ± 0.5 cm per axis error over a 15 cm slide (about 6% of movement), and <2 cm MAE on most axes after optimisation. The thesis states that multi-IMU kinematic models reach about **1–2% of range of motion**. — [PoliTo thesis](https://webthesis.biblio.polito.it/34849/1/tesi.pdf)
- A systematic review/meta-analysis of IMU upper-extremity ROM validity found wrist joint-angle RMSE ranging from about **2.2° to 30°**. It advises caution especially for wrist radial/ulnar deviation. — [Cambridge meta-analysis](https://core-prod.cambridgecore.org/core/services/aop-cambridge-core/content/view/92EA831951DF80B7F9700715C573F267/S2631717624000069a.pdf/concurrent-validity-of-inertial-measurement-units-in-range-of-motion-measurements-of-upper-extremity-a-systematic-review-and-meta-analysis.pdf)
- Perception Neuron Studio vs OptiTrack, upper body (Wu et al. 2022, 7 participants): CMC 0.73–0.99, **RMSE 1.9–12.5°**, bias 0.2–27.8°. Faster movement gave larger bias. — [Sensors 22(18):6954](https://www.mdpi.com/1424-8220/22/18/6954); [PMC9506133](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9506133/)
- Sers et al. 2020 (Measurement) found Perception Neuron valid for upper-body ROM to within **5° RMSE** vs Vicon (as cited in the search summary). — [Leicester repository PDF](https://figshare.le.ac.uk/articles/journal_contribution/Validity_of_the_perception_neuron_inertial_motion_capture_system_for_upper_body_motion_analysis/10245029/1/files/18494483.pdf)
- No Rokoko validation study reporting hand position in cm was found (see Gaps).
- Smartwatch-only (single wrist IMU) arm pose estimation:
  - ArmPoser (arXiv 2609.08806): median elbow error **5.81 cm**, wrist **10.27 cm**.
  - IROS 2023 probabilistic method: mean wrist+elbow error **2.56 cm**.
  - SmartPoser, which adds phone UWB: wrist 13.3 cm, elbow 8.7 cm.
  - A secondary summary gives ArmTrak at 12.0 cm elbow / 13.3 cm wrist.
  - Protocols differ, so these are not directly comparable. — [ArmPoser](https://arxiv.org/pdf/2609.08806); [IROS23 preprint](https://arxiv.org/html/2306.13192v3); [SmartPoser](https://arxiv.org/abs/2509.03451)
- Sensor-to-segment calibration, three comparisons:
  - Bouvier et al. 2015 compared technical-axes, static-pose and functional calibrations. They found only small discrepancies and concluded that accuracy depends more on procedural rigour than on the choice of method. — [Sensors 15:18813 / PMC4570347](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4570347/)
  - A 2025 clinical-setting method that estimates joint positions reached a median RMS error of **5–8°**. It was significantly better than static-pose calibration (p < 0.001), and the authors note static pose is the most common method. — [PMC12250904](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12250904/)
  - Bonfiglio et al. 2025 compared N-pose, functional and manual calibrations for the humerothoracic joint. Differences were minor and not significant, and the authors recommend static N-pose for simplicity (per search summary). — [search summary; see PMC12250904 context](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12250904/)
- The Xsens MVN technical paper (Schepers, Giuberti, Bellusci, "Xsens MVN: Consistent Tracking of Human Motion Using Inertial Sensing") has sections on Scaling, Sensor-to-Segment Calibration and Axes definition, and a predefined scaling model is used. Its body text could not be extracted. — [MVN whitepaper PDF](https://blog.xsens.com/hubfs/Downloads/Whitepapers/MVN_Whitepaper.pdf)
- Xsens describes its engine as combining all trackers with "advanced biomechanical models", giving immunity to magnetic distortion. Xsens lists the limited accuracy of the biomechanical model across subjects as an error source. — [Xsens blog: consistent tracking](https://www.xsens.com/blog/consistent-tracking-of-human-motion-using-inertial-sensing)
- Movella says drift "is inherent to inertial mocap". It is more prominent in fast dynamic motion and **when the user is not touching the ground**, so contact matters. — [Movella blog: drift dilemma](https://movella.com/resources/blog/mocap-without-limits-how-xsens-solved-the-drift-dilemma)
- MVN detects contact points of the body with the external world, which constrains the kinematics. A Kalman filter corrects drift and joint-position uncertainty (secondary description in the Xsens-ROS bridge paper). Xsens recommends HTC Vive fusion for absolute position. — [arXiv 2306.17738](https://arxiv.org/pdf/2306.17738); [Movella blog](https://movella.com/resources/blog/mocap-without-limits-how-xsens-solved-the-drift-dilemma)

### Inferences
- With FK, hand position error ≈ Σ(segment length × orientation error) + length error, and it does **not** grow quadratically like double integration. For a shoulder-to-fingertip chain of about 0.65–0.75 m, 1° of heading error gives about 1.1–1.3 cm lateral error at the fingertip (small-angle L·θ). 5° gives about 6 cm. This is geometry, not a cited result.
- The 0.09 ± 1.81 cm Sci Rep figure is the closest analogue to WristTap: 2 arm IMUs, shoulder-relative, short trials. It suggests **about 2 cm (1σ) is realistic right after calibration**. Heading drift and shoulder motion add to that over time.
- Static N-pose calibration is "good enough" in the literature. For WristTap the 4-corner touch can act as a task-specific functional calibration (see section 4).

### Gaps
- Exact Xsens MVN hand-position accuracy in cm and its contact-detection algorithm (whitepaper text unreadable; algorithm closed-source).
- Rokoko and Noitom hand-position (cm) validations were not found.
- Full-text error breakdown of the Sci Rep 2021 study (stroke vs healthy, trial durations) was blocked.

## 2. Joint constraints (elbow hinge, ROM limits) for magnetometer-free heading

### Takeaway
The Seel/Laidig group shows that a **6-axis IMU pair across a hinge or 2-DoF joint can keep relative heading long-term stable without magnetometers**, using kinematic constraints. Reported errors are **<4°** total angle error on a mechanical joint, and **about 4.3° RMSE** for magnetometer-free knee flexion. This fixes *relative* heading (forearm vs upper arm). It does **not** fix the absolute heading of the whole chain relative to the wall, which still drifts with gyro bias unless another reference is used, such as a torso IMU, wall touches, or a magnetometer.

### Cited Findings
- Laidig et al. (2017) used an orientation-based constraint to estimate the relative heading of two bodies joined by a 1-DoF (hinge) joint. The real-time quaternion method was evaluated in simulation. — [cited within Lehmann et al. arXiv 2002.00639](https://arxiv.org/pdf/2002.00639)
- Laidig, Lehmann, Bégin, Seel (EMBC 2019) presented magnetometer-free real-time tracking of 2-DoF joints. It estimates relative heading by minimising a nonlinear cost and tracks correctly even as heading drifts past 360°. — [FAU CRIS 253665908](https://www.cris.fau.de/publications/253665908/)
- Lehmann, Laidig, Deimel, Seel (IFAC World Congress 2020) handled arbitrary joints using **range-of-motion constraints** and a window-based nonlinear cost. The relative orientation is long-term stable, with total angle error **<4°** in all experiments on a mechanical test joint. — [arXiv 2002.00639](https://arxiv.org/abs/2002.00639)
- Laidig, Weygers, Seel (Sensors 2022) presented self-calibrating magnetometer-free 2-DoF tracking. It estimates the joint axes and the heading offset simultaneously from arbitrary motion. This is relevant because the elbow is often modelled as 2-DoF (flexion + pronation/supination). — [FAU CRIS 287478627](https://cris.fau.de/publications/287478627); [preprint](https://preprints.org/manuscript/202211.0035/v1)
- Eckhoff et al. studied sparse magnetometer-free tracking on double-hinge chains and derived observability conditions. — [arXiv 2002.00902](https://ar5iv.labs.arxiv.org/html/2002.00902)
- Seel, Raisch, Schauer (Sensors 2014), "IMU-based joint angle measurement for gait analysis": joint **axis** and **position** identification from gyro/accelerometer data during arbitrary motion, then flexion/extension angle. A later study reports magnetometer-free knee flexion RMSE of about 4.34°, comparable to magnetometer-based methods (search snippet). — [FAU CRIS](https://cris.fau.de/publications/253675326); [DOAJ](https://doaj.org/article/91fbbe9bf8f349d7a8645cc1eb81fa1a)
- Kok, Hol, Schön (2014) introduced optimisation-based (MAP) magnetometer-free inertial motion capture with natural inclusion of biomechanical constraints. Reviews describe it as giving drift-free joint angles, but at a higher computational cost than filtering. Weygers et al. (IEEE Sensors J. 2020) report drift-free joint kinematics with a joint constraint (per search summaries). — [KokHS2014 PDF](https://people.isy.liu.se/rt/manko/publications/KokHS2014.pdf); [Weygers et al. TU Delft](https://pure.tudelft.nl/ws/portalfiles/portal/81850427/09044292.pdf)
- VQF (Laidig & Seel, Information Fusion 91, 2023) is a 6D/9D orientation filter with gyro-bias estimation that handles heading via a scalar heading offset. It averaged **2.9° RMSE** across public datasets, against 5.3–16.7° for eight literature methods. It is open-source (C++/Python). — [FAU CRIS](https://cris.fau.de/publications/281418367); [VQF docs](https://vqf.readthedocs.io/); [arXiv 2203.17024](https://arxiv.deeppaper.ai/papers/2203.17024v2)

### Inferences
- For WristTap, the useful split is:
  - **Inclination** (pitch/roll) of each segment is drift-free from gravity.
  - **Relative heading** between forearm and upper arm can be held by elbow-hinge/ROM constraints (Laidig/Lehmann).
  - **Common heading** of the whole arm vs the wall is the one unobservable DoF. It is the main candidate for correction by wall touches.
- Heading-drift rate depends on residual gyro bias after on-line bias estimation. As an assumption, not measured: residual bias of 0.01–0.05 °/s gives about 0.6–3°/min, which works out to roughly 0.7–4 cm/min of lateral fingertip drift at 0.7 m reach, before any touch correction.

### Gaps
- No upper-limb (elbow) specific accuracy numbers in cm from the Laidig magnetometer-free methods were found; reported results are angles on knees or mechanical joints.
- Seel 2014's own degree figures could not be confirmed (MDPI 403).

## 3. Contact-aided / constraint-aided inertial navigation; touch events as measurement updates; IMU + surface work

### Takeaway
The general framework is well established in legged robotics. A detected contact with a world-fixed point or surface gives a **pseudo-measurement**: zero velocity (a ZUPT analogue), a fixed contact position, or point-on-plane. In an EKF/InEKF this makes position and some rotation components observable. For pens and writing, **plane constraints** (detect the writing plane, project onto it, treat deviation as drift) reach **mm-level** stroke accuracy over short strokes. No published work was found that uses wrist-IMU touches on a wall as position fixes for an arm-chain model. That combination appears novel, though it is a direct transfer of these ideas.

### Cited Findings
- Contact with a world-fixed surface gives a noisy pseudo-observation that the contact point is stationary. This is used in legged robots (Hartley et al.) and VINS. — [arXiv 2408.12360](https://arxiv.org/pdf/2408.12360)
- Hartley et al. built a contact-aided invariant EKF with IMU + contact sensors on the Cassie biped. They show that absolute position and a rotation become observable through contact and that it outperforms a quaternion EKF. — [arXiv 1805.10410](https://arxiv.com/abs/1805.10410)
- Contact Inertial Odometry (Lew et al.) detects collisions from estimated external forces and generates pseudo-velocity measurements fused in an EKF. — [arXiv 1909.00079](https://arxiv.org/pdf/1909.00079v1)
- A review of information-aided navigation (Engelsman & Klein) classifies pseudo-measurement and constraint (model) aiding. — [arXiv 2301.01114](https://arxiv.org/pdf/2301.01114)
- Two IMU pen patents correct drift during writing:
  - One transforms data into the writing-plane frame before integration and treats deviation from expected writing directions as drift, which it subtracts. — [US10146338](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10146338)
  - The other corrects acceleration against expected values. — [US10126844](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10126844)
- A pen-tail IMU handwriting system (Bu et al.) and a related system use PCA to find the writing plane and separate on-plane strokes by distance from it. The reported average tracking error is **1.84 mm** for letters of about 2 × 1 cm (snippet-level). — [arXiv 2101.06022](https://bohrium.dp.tech/paper/arxiv/2101.06022); [CERIST record](https://biblio.cerist.dz/show/fr/00000000000000619604000000)
- A stylus-on-surface patent notes that surface bumps, friction vibration and repeated lift/touch inject IMU noise. It fuses optical data to mitigate this. — [US11397478](https://patents.google.com/patent/US11397478)
- Movella/Xsens: drift is worse without ground contact, and MVN uses detected external contacts to constrain kinematics. — [Movella blog](https://movella.com/resources/blog/mocap-without-limits-how-xsens-solved-the-drift-dilemma); [arXiv 2306.17738](https://arxiv.org/pdf/2306.17738)
- Pure double integration is the comparison baseline. A simple INS on an Xsens MTx had average position error **>150 m after 60 s**, and about 5 m with magnetometer fusion. A constant accelerometer bias produces position error that grows with t². — [Cambridge UCAM-CL-TR-696](https://www.cl.cam.ac.uk//techreports/UCAM-CL-TR-696.pdf); [SBG glossary](https://www.sbg-systems.com/glossary/position-drift/)

### Inferences
- A WristTap touch event (piezo spike) can supply three kinds of update:
  1. **Point-on-plane:** the FK fingertip must lie on the calibrated wall plane, a 1-D constraint along the wall normal.
  2. **Zero-velocity:** the hand is still during contact, which helps the filter decide when to apply updates and lets it estimate gyro bias during the contact dwell, because orientation is static.
  3. **Fixed-point:** if the touched target is known, for example the user is asked to tap a UI button at a known projector location, it gives a full 2-D in-plane position fix, which can correct the common heading offset and shoulder position.
- Unknown-location touches only constrain depth (the normal direction). The in-plane heading drift that matters most for a wall UI is only corrected by known-target touches. Plane distance does give a weak heading cue, because rotating the arm about the vertical axis changes the reach distance to the plane at a given elbow geometry.
- This is the hand analogue of foot-mounted ZUPT plus legged-robot contact InEKF. Hartley's InEKF is a ready formal template.

### Gaps
- No academic paper was found that uses smart-ring, watch or wrist-IMU touches on a wall or table as position updates for an arm kinematic model. A targeted search of CHI/UIST/IMWUT (e.g., ring-based surface touch) could still turn something up.
- No IMU-based wall-pointing accuracy studies were found. The large-display ray-casting literature is camera/mocap-based: Mayer et al. report about 60 cm mean ray-cast error at 2–3 m. That number concerns ray pointing, not touch. — [Mayer et al. LMU](https://www.medien.informatik.uni-muenchen.de/pubdb/publications/pub/mayer2015modelingdistant/mayer2015modelingdistant.pdf)

## 4. Calibrating the wall plane and arm lengths from touching known points (4 corners)

### Takeaway
No source describes this exact procedure, but it maps onto standard least-squares calibration. The literature supports joint-position/functional calibration being better than static poses (5–8° vs worse). Four corner touches give 4 × 3 = 12 scalar constraints on the FK fingertip positions. That is enough to solve for wall plane, shoulder offset, heading offset and one or two scale parameters, especially if more touches are added over time.

### Cited Findings
- Joint-position-based calibration outperformed static pose (median RMS 5–8°, p < 0.001). — [PMC12250904](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12250904/)
- Seel et al. identify joint **position** vectors (sensor-to-joint offsets) from IMU data during arbitrary motion via optimisation. This gives lever arms without a tape measure. — [Seel 2014 Sensors, FAU CRIS](https://cris.fau.de/publications/253675326)
- Pen systems detect the writing plane by PCA over the 3-D trajectory, a least-squares plane fit. — [CERIST record](https://biblio.cerist.dz/show/fr/00000000000000619604000000)
- Distant-pointing studies fit polynomial correction models to systematic offsets measured by pointing at known targets. This is the same idea as a data-driven residual correction. — [Mayer et al.](https://www.medien.informatik.uni-muenchen.de/pubdb/publications/pub/mayer2015modelingdistant/mayer2015modelingdistant.pdf)

### Inferences (proposed method, not from a source)
- Unknowns are:
  - shoulder position in the wall frame (3);
  - common heading offset (1);
  - upper-arm and forearm+hand lengths (2), or a single scale;
  - optionally a small tilt/heading misalignment per sensor.
- Data: at each corner touch, gravity-aligned segment orientations q_ua and q_fa from the IMUs, plus the known corner position in a wall frame with a known projection width/height in metres. Minimise Σ‖FK(q_i; θ) − c_i‖² with Gauss–Newton. Four corners give 12 equations for about 6–8 unknowns, so the system is overdetermined.
- If the projection size in metres is unknown, fit a plane plus homography: FK fingertip points → least-squares plane → 2-D in-plane coordinates → 4-point homography to projector pixels. This also absorbs scale errors in arm length.
- Add more known-point touches (e.g., centre, edge midpoints, or every tap on a known UI target) to keep re-estimating the heading offset and shoulder position on-line. A sliding-window least squares or EKF state handles this.

### Gaps
- No published accuracy results for "touch-the-corners" arm-chain calibration were found.

## 5. Torso/shoulder movement as an error source; adding a torso/chest IMU

### Takeaway
FK from shoulder-relative arm orientations assumes the shoulder is fixed in the wall frame. Any torso lean, rotation or step, and any scapular elevation/protraction during reach, moves the shoulder and translates directly into fingertip error. A chest IMU fixes torso *orientation* (lean and twist, and heading via a shared reference) but not torso *translation*. Commercial suits handle translation with full-body models plus foot contacts.

### Cited Findings
- Xsens MVN uses a full-body biomechanical model with contact detection (feet on ground) to constrain the root/pelvis position. Drift increases when contact is absent. — [Movella blog](https://movella.com/resources/blog/mocap-without-limits-how-xsens-solved-the-drift-dilemma); [arXiv 2306.17738](https://arxiv.org/pdf/2306.17738)
- The Sci Rep 2021 wrist-tracking work measured wrist position **relative to the shoulder**, meaning shoulder translation was out of scope for its 1.8 cm figure. — [Sci Rep 2021](https://www.nature.com/articles/s41598-021-01805-2)
- Bonfiglio et al. 2025 specifically modelled the **humerothoracic** joint with a thorax IMU, which shows that a thorax sensor is standard for shoulder kinematics (per search summary). — [context in PMC12250904](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12250904/)

### Inferences
- Torso twist of θ degrees about a vertical axis through the spine moves the shoulder by about r·θ, with r ≈ 0.18–0.20 m (half shoulder width). Each 5° of twist gives about 1.6 cm of shoulder shift. The arm's heading also changes by θ, which already costs about 6 cm at 0.7 m reach unless the chest IMU captures it. This geometric estimate is the strongest argument for a chest IMU.
- A chest IMU lets you express arm orientations relative to the thorax. Then only the thorax heading relative to the wall drifts, and a single parameter can be re-anchored on known-target touches.
- Small torso translations (sway, a half step) are invisible to IMUs without double integration. They must be absorbed by re-estimating the shoulder position on touch events, or limited by instructing the user to stand on a floor marker.

### Gaps
- No source quantified typical shoulder/scapular translation (cm) during standing reaches to a wall. Biomechanics literature on scapulohumeral rhythm would supply this but was not searched in depth.

## 6. Expected accuracy on a wall at about 0.5–1 m reach, and degradation over minutes

### Takeaway
Drawing the evidence together: **about 2 cm (1σ) right after calibration** is plausible with 2 arm IMUs. That is in line with 1.8 cm SD for shoulder-relative wrist position, and with about 1.2 cm per degree of heading error at 0.7 m. Without corrections, error grows **roughly linearly** with heading drift, at a few cm per minute with a 6-axis IMU after bias estimation. That contrasts with the quadratic, metres-in-seconds growth of double integration. With touch corrections at known targets every few seconds to tens of seconds, the error should stay bounded near the calibration-level error. That last part is an inference; no study confirms it.

### Cited Findings
- IMU kinematic-model wrist error vs Vicon: 0.09 ± 1.81 cm. — [Sci Rep 2021](https://www.nature.com/articles/s41598-021-01805-2)
- Multi-IMU kinematic models reach about 1–2% of range of motion (thesis literature summary). — [PoliTo thesis](https://webthesis.biblio.polito.it/34849/1/tesi.pdf)
- Best-in-class orientation filter averages 2.9° RMSE (VQF), against 5.3–16.7° for other filters. — [VQF](https://cris.fau.de/publications/281418367)
- Magnetometer-free joint tracking with constraints: <4° total angle error. — [arXiv 2002.00639](https://arxiv.org/abs/2002.00639)
- Commercial suit joint-angle RMSE: 1.9–12.5° (Perception Neuron Studio). — [Sensors 2022](https://www.mdpi.com/1424-8220/22/18/6954)
- Double-integration baseline: >150 m after 60 s with a MEMS IMU. — [Cambridge TR-696](https://www.cl.cam.ac.uk//techreports/UCAM-CL-TR-696.pdf)

### Inferences
- Error budget at 0.7 m reach (geometric, assumed values):

  | Source | Contribution |
  |---|---|
  | Orientation error of 3° (VQF-class) | ≈ 3.7 cm worst-case lateral; partially cancels across segments |
  | Arm-length error of 1 cm | ≤ 1 cm, absorbed by the corner calibration |
  | Torso twist, uncompensated | ~6 cm per 5° |
  | Heading drift | ~1–4 cm/min before touch updates (assumed residual bias 0.01–0.05 °/s) |

- Getting to **≤2 cm usable** accuracy likely needs four things:
  - corner calibration solving for heading offset, shoulder position and scale;
  - elbow-hinge constraint for relative heading;
  - a chest IMU, or a strict instruction to stand still;
  - frequent known-target touch updates and bias re-estimation during contact dwell.
- Projected UI targets should be sized **≥ about 5–8 cm** to remain robust between touch corrections. This is a design inference, not tested.

### Gaps
- No study reports wrist position error **as a function of time over minutes** for IMU-only upper-limb FK. Most validation trials are short (seconds).
- No IMU-only wall-touch or touch-corrected accuracy data exists in the sources found. WristTap would have to measure this itself, for example by touching known grid points every N seconds and logging the residuals.
