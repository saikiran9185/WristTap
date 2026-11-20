# Deep-learning and data-driven methods for IMU drift reduction and sparse-IMU arm/hand pose (for a camera-free wristband + optional upper-arm band)

Notes compiled 15 Nov 2026. Each paper is dated. Numbers are as reported by the authors on their own benchmarks unless stated; numbers from different datasets are NOT directly comparable. Some arXiv IDs (2603.x to 2611.x) are 2026 preprints. Where only search snippets (not full text) were seen, this is flagged.

## 1. Sparse-IMU full/upper-body and single-watch arm pose: what accuracy is achievable?

### Takeaway
Learned single-wrist-IMU arm tracking now reaches about 9-10 cm median wrist position error without calibration (ArmPoser, SUI 2026) and about 7.7 cm with a short calibration in a seated/standing VR setting (HOOV, CHI 2023). About 2.3 cm is reported only under tight lab constraints: torso held still, known forward direction, arm lengths known, barometer calibration (Weigend et al., IROS 2023). For touching a projected wall, 7-10 cm is too coarse for small targets but fine for large tiles. A second IMU on the upper arm plus a known body pose (standing facing the wall) is the main lever for getting closer to the 2-5 cm range.

### Cited Findings

**Single smartwatch / wrist IMU arm pose (most relevant)**
- **ArmPoser** (arXiv 2609.08806, submitted 8 Sep 2026; ACM SUI '26, Bari, Oct 2026; Dev, Xu, Hoffmann, Loh, Gao, Ahuja; Northwestern/UChicago/MBZUAI). Single smartwatch IMU, calibration-free. Uses gravity-aligned orientation + linear acceleration at 30 Hz from Apple Watch SE 2 and Pixel Watch 3 — [arXiv](https://arxiv.org/html/2609.08806)
  - Model: three stacked LSTM modules (2 layers, hidden 256, dropout 0.4), adapted from MobilePoser. Stages: joint position regressor, then a bidirectional joint rotation estimator (6D rotations), plus a velocity estimator used only as a training regularizer. A separate BiLSTM classifies how the watch is worn (forearm side, crown direction) at ~91.8% accuracy with a 10 s window and ~98.7% with ~2 min — [arXiv](https://arxiv.org/html/2609.08806)
  - Median errors (cm), elbow / wrist: TotalCapture 6.75 / 11.67; DIP-IMU 6.03 / 9.89; IMUPoser dataset 4.89 / 10.24; own ArmPoser dataset 5.56 / 9.28. Mean angular error 25.6° — [arXiv](https://arxiv.org/html/2609.08806)
  - Wrist-elbow average (cm) on TotalCapture / DIP / IMUPoser / ArmPoser: IMUPoser (calibrated) 10.59 / 8.68 / 8.10 / 9.95; MobilePoser (calibrated) 9.59 / 8.53 / 7.88 / 9.63; ArmPoser (no calibration) 9.20 / 7.96 / 7.58 / 7.65 — [arXiv](https://arxiv.org/html/2609.08806)
  - Training data: synthetic IMU generated from AMASS mocap, augmented with strap/mounting perturbation up to ±40° and random yaw. Fine-tuned on DIP-IMU and IMUPoser. The new dataset has 10 participants, 30 activities and ~160 min per platform. Its ground truth came from EasyMocap with 6 calibrated RGB cameras at 60 Hz, so cameras were used for labels only — [arXiv](https://arxiv.org/html/2609.08806)
  - Compute: trained on one RTX 3090 (60 epochs pretraining + 15 fine-tuning). Inference uses 125 past + 5 future frames, so latency is about 170 ms. The live prototype streams the Apple Watch to a **MacBook Air M3** and runs at 30 Hz. Code and data are announced at github.com/SPICExLAB/ArmPoser — [arXiv](https://arxiv.org/html/2609.08806)
  - Baselines as quoted in the paper: ArmTrak (Shen et al., MobiSys 2016) wrist 13.3 / elbow 12.0 cm; SmartPoser wrist 13.3 / elbow 8.7 cm; TIC (Zuo et al. 2025) adapted to one wrist IMU, wrist 13.04 / elbow 7.31 cm on the ArmPoser data — [arXiv](https://arxiv.org/html/2609.08806)
- **"Anytime, Anywhere: Human Arm Pose from Smartwatch Data"** (Weigend, Sonawani, Drolet, Ben Amor, ASU; arXiv 2306.13192, IROS 2023). Samsung Galaxy Watch 5 only, streaming gyro, gravity, linear acceleration, rotation-vector quaternion and barometric pressure at ~50 Hz over UDP — [arXiv](https://arxiv.org/html/2306.13192)
  - Best model is an LSTM (sequence length 6, 128 units) with 6D-rotation targets: median wrist error **2.33 cm**, elbow 1.61 cm; RMSE wrist 3.71 ± 2.49 cm. MC dropout gives uncertainty and multimodal arm-pose hypotheses — [arXiv](https://arxiv.org/html/2306.13192)
  - Conditions behind that number: 3 s barometer calibration at chest height, 3 s arm-forward calibration ("forward direction must be constant and known"), known arm lengths, and chest/hip kept still. Recalibration is needed if the body moves. Ground truth from a 12-camera OptiTrack system; 6 participants, ~381k watch samples — [arXiv](https://arxiv.org/html/2306.13192)
  - Compute: 150 MC-dropout passes at ~40 Hz on a Xeon + RTX 2080 Ti. Code at github.com/wearable-motion-capture — [arXiv](https://arxiv.org/html/2306.13192)
  - The paper quotes a two-IMU baseline at wrist 6.9 ± 2.7 cm and elbow 5.2 ± 2.6 cm RMSE. It also contains an apparent typo claiming a ">44 cm reduction" — [arXiv](https://arxiv.org/html/2306.13192)
- **WearMoCap** (smartwatch pose tracking for robot control, PMC 2025, same ASU group). With the upper-arm mode the wrist RMSE was 6.79 cm. Other modes averaged roughly 10-12 cm (search snippet, not full text) — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11738771/)
- **HOOV** (Streli, Armani, Cheng, Holz, ETH Zürich; CHI 2023; arXiv 2303.07016). One wrist IMU estimates 3D hand position after the hand leaves the headset's camera view. The headset gives the starting point, so this is learned short-horizon dead reckoning. Mean error 7.7 cm (MAE 7.77 cm, median 7.00 cm), orientation error 6.50°, validated against OptiTrack — [arXiv](https://arxiv.org/pdf/2303.07016)
- **SmartPoser** (DeVrio et al., UIST 2023; arXiv 2509.03451). Phone + watch IMU + UWB ranging: median wrist error 13.3 cm, elbow 8.7 cm, average 11.0 cm — [ACM](https://dl.acm.org/doi/fullHtml/10.1145/3586183.3606821), [arXiv](https://arxiv.org/abs/2509.03451)
- Other single-watch baselines quoted in later papers: ArmTrak 13.3 cm median wrist; a particle-filter approach 8.8 cm in a static setting; an RNN approach 15.4 cm wrist (search-snippet level) — [ArmPoser arXiv](https://arxiv.org/html/2609.08806), [Weigend arXiv](https://arxiv.org/html/2306.13192)

**Sparse-IMU full-body lineage (DIP, TransPose, PIP, TIP, IMUPoser, MobilePoser, diffusion)**
- Error table on DIP-IMU from MobilePoser (UIST 2024; arXiv 2504.12492). The metric is in cm and labelled MPJVE in the snippet:
  - SIP 7.7, TransPose 7.1, PIP 5.9 (these use 6 Xsens IMUs)
  - IMUPoser 12.1 cm at 25 FPS, jitter 1.9 (1-3 consumer devices)
  - MobilePoser 10.6 cm at 60 FPS, jitter 0.97 (1-3 consumer devices). It also estimates global translation, and a physics optimizer follows the network
  - [arXiv](https://arxiv.org/html/2504.12492v1)
- Northwestern press coverage of MobilePoser says the average error is "8 to 10 cm" and contrasts that with Kinect at 4-5 cm — [Northwestern](https://www.mccormick.northwestern.edu/news/articles/2024/10/new-app-performs-real-time-full-body-motion-capture-with-a-mobile-device/)
- IMUPoser (Mollyn, Arakawa, Goel, Harrison, Ahuja; CHI 2023; arXiv 2304.12518) uses whatever subset of phone/watch/earbud IMUs is present. Dataset: 10 participants on consumer devices. Reported real-time error 12.08 cm — [arXiv](https://arxiv.org/abs/2304.12518v1), [project](https://karan-ahuja.com/imuposer.html)
- PIP (Physical Inertial Poser, arXiv 2203.08528, 2022) combines an RNN with a dual PD controller and physics optimization. It has the lowest cumulative error among its comparisons, but translation assumes flat ground — [arXiv](https://arxiv.org/pdf/2203.08528)
- TIP (Transformer Inertial Poser, SIGGRAPH Asia 2022) predicts stationary body points to correct gradual drift of translation and joints together. Code at github.com/jyf588/transformer-inertial-poser. A later comparison notes higher translation jitter — [GitHub](https://www.github.com/jyf588/transformer-inertial-poser)
- PNP (Physical Non-inertial Poser, arXiv 2404.19619, 2024) models non-inertial effects and claims the lowest global position drift among prior works. A 2024 comparison says physics-optimizer methods (PIP, PNP, GlobalPose) drift less on TotalCapture than some diffusion methods — [arXiv](https://arxiv.org/pdf/2404.19619)
- **Diffusion successors:**
  - DiffusionPoser (CVPR 2024) handles arbitrary sparse IMU configurations, but its gains over prior work were modest and the code is not public — [CVPR supp](https://openaccess.thecvf.com/content/CVPR2024/supplemental/Van_Wouwe_DiffusionPoser_Real-time_Human_CVPR_2024_supplemental.pdf)
  - **Ultra Diffusion Poser** (ETH, arXiv 2606.02153, 2026) uses 6 IMUs plus UWB inter-sensor distances as geometric constraints during diffusion sampling. The authors stress that IMUs give no absolute measurement, so drift is hard to correct, and that synthetic training data under-represents real sensor noise — [arXiv](https://arxiv.org/pdf/2606.02153)
  - Garment Inertial Poser (arXiv 2506.15290, 2025) handles loose IMUs in clothing — [arXiv](https://arxiv.org/pdf/2506.15290v2)
  - Stereo-Inertial Poser (arXiv 2603.02130, Mar 2026) uses 6 IMUs + one stereo camera and reports drift-free global translation — [arXiv](https://arxiv.org/html/2603.02130v1)
  - Group Inertial Poser (arXiv 2510.21654, 2025) does multi-person tracking with IMU + UWB — [arXiv](https://arxiv.org/pdf/2510.21654)
- A 2025 paper (arXiv 2505.09393) notes that pose becomes under-constrained as the number of IMUs falls, which is the core difficulty for watch-only setups (snippet) — [arXiv](https://arxiv.org/pdf/2505.09393)

### Inferences
- For WristTap the best-matched off-the-shelf recipe is ArmPoser or MobilePoser: AMASS-synthesized IMU pretraining, then fine-tuning on a small set of real recordings. It already runs live on a MacBook Air M3 from a streamed watch, so an ESP32 streaming orientation + linear acceleration over Wi-Fi/BLE at 30-60 Hz to a Mac is the same architecture.
- The wall-touch scenario resembles the constrained Weigend setup: the user stands roughly still facing a known wall direction, and arm lengths can be measured once. That suggests 2-5 cm wrist accuracy may be reachable with a short "point at wall" calibration plus an upper-arm IMU. The torso-motion assumption is a real limitation.
- A second IMU on the upper arm turns the problem into near-exact forward kinematics: shoulder → elbow → wrist from two orientations and two segment lengths. The remaining errors are then shoulder translation and strap slip, which suits a small learned correction rather than full dead reckoning.
- The ~170 ms latency of bidirectional or future-frame models matters for touch feedback. A causal (unidirectional) variant trades some accuracy for lower latency.

### Gaps
- Exact DIP (2018) and TransPose (2021) per-joint numbers were not re-verified from primary text here, beyond the MobilePoser comparison table.
- Shen et al. MobiSys 2016 ("I am a smartwatch and I can track my user's arm") was not fetched directly. Its 13.3 cm median wrist error comes from ArmPoser's citation.
- No paper found named "WristPose", "ArmTrack" (other than ArmTrak) or "LimbMotion". LimbMotion (Zhou et al., wearable + acoustic) was not located in this pass.
- Per-device breakdowns for IMUPoser (watch-only error) were not retrieved.
- No 2025-2026 paper was found evaluating hand position specifically against a vertical wall/plane.

## 2. Learned inertial odometry (drift numbers)

### Takeaway
Learned inertial odometry (RoNIN 2019, TLIO 2020, AirIO 2025, and 2025-2026 successors) still drifts by metres over minutes, for example 3.5-6.5% of distance travelled on the Nymeria wearable dataset. It suits walking-scale navigation, not centimetre hand position. Its useful ideas for WristTap are learned velocity/displacement priors fused in an EKF with learned uncertainty, and body-frame inputs with attitude encoding.

### Cited Findings
- **TLIO** (Liu et al., arXiv 2007.01867, 2020) feeds a network's displacement + covariance into an EKF. It reports 27% lower yaw drift and 33% lower position drift than the best RoNIN velocity-concatenation baseline on its test set — [arXiv](https://arxiv.org/abs/2007.01867)
- **AirIO** (Qiu, Xu, Chen, Zhao, Geng, Scherer, CMU; arXiv 2501.15659, Jan 2025, rev. Jun 2025; RA-L 2025 per search snippet) — [arXiv](https://arxiv.org/abs/2501.15659)
  - Keeps IMU data in the body frame and encodes attitude explicitly. It pairs with AirIMU (learned IMU correction + uncertainty) and an uncertainty-aware EKF — [arXiv](https://arxiv.org/abs/2501.15659)
  - Accuracy: +66.7% average across 3 datasets from the body-frame representation, a further +23.8% from attitude encoding, and +73.9% ATE on Blackbird. A snippet reports ATE cuts of 52.9% vs RoNIN and 54.4% vs TLIO — [arXiv](https://arxiv.org/abs/2501.15659), [AirIO supp](https://air-io.github.io/supplements/supplements.pdf)
- On the **Nymeria** dataset (a CVPR 2026 MARIO supplement):
  - AirIO: ATE 6.85 m, drift 3.56%
  - TLIO: ATE 10.19 m, drift 6.46%
  - Adding a pose-prior module lowers both. "PoseN"/"PoseA" denote a PoseNet trained on Nymeria / AMASS
  - [CVPR 2026 supp](https://openaccess.thecvf.com/content/CVPR2026F/supplemental/Li_MARIO_Motion-Augmented_Real-Time_CVPRF_2026_supplemental.pdf)
- **MARIO** (arXiv 2606.02996, CVPR Findings 2026) fuses multiple body-worn IMUs with human-motion priors for odometry, compared against AirIO, TLIO, EqNIO and RoNIN-LSTM — [arXiv](https://arxiv.org/html/2606.02996)
- Other 2025-2026 learned inertial odometry papers (existence confirmed; numbers not extracted):
  - TinyIO, lightweight reparameterized network — [arXiv 2507.15293](https://arxiv.org/pdf/2507.15293)
  - GNIO, gated — [arXiv 2603.15281](https://arxiv.org/pdf/2603.15281)
  - DINS-IO, differentiable INS consistency — [arXiv 2607.20232](https://arxiv.org/pdf/2607.20232)
  - Differentiable Filtering for IO, reports lower translational drift on noisy smartphone data than RoNIN/TLIO — [arXiv 2611.13517](https://arxiv.org/pdf/2611.13517)
  - Plug-and-play learned IMU bias factor for VIO — [arXiv 2503.12527](https://arxiv.org/pdf/2503.12527)
  - Learned IMU bias prediction for invariant VIO — [arXiv 2505.06748](https://ar5iv.labs.arxiv.org/html/2505.06748)
- A 2025 bias-prediction paper notes that AirIMU assumes ground-truth positions at deployment and does not claim real-time operation — [arXiv 2505.06748](https://ar5iv.labs.arxiv.org/html/2505.06748)

### Inferences
- Even the best learned inertial odometry drifts by roughly a few percent of distance, and it relies on gait periodicity (pedestrian) or vehicle dynamics. Free arm motion has neither, so double-integrating wrist acceleration with a learned correction will not give stable wall coordinates on its own.
- The transferable pattern is to have a network predict a short-window displacement or velocity with covariance, then fuse it in an EKF with strong constraints. For WristTap those constraints are arm kinematics, a fixed shoulder, and "the hand is on the wall plane at touch".

### Gaps
- RoNIN (2019), IONet (2018), RINS-W (2019) and AI-IMU dead reckoning (2019) were not re-fetched, so their numbers are not reported here. AI-IMU is car odometry and RINS-W is wheeled/pedestrian zero-velocity detection; both are mostly irrelevant to arm motion.
- No learned odometry paper specifically for free arm/hand motion (rather than whole-body trajectory) was found, apart from HOOV (section 1).

## 3. Learned gyro denoising / bias correction / physics-informed IMU models

### Takeaway
Brossard et al. (RA-L 2020) showed that a small dilated-CNN gyro corrector can beat visual-inertial odometry on attitude alone. AirIMU (2023-2025) extends this to learned correction plus uncertainty for preintegration. These help orientation drift, the dominant error source for a two-IMU kinematic arm model, and are cheap enough to run on a Mac.

### Cited Findings
- **Brossard, Bonnabel, Barrau, "Denoising IMU Gyroscopes with Deep Learning for Open-Loop Attitude Estimation"** (arXiv 2002.10718, IEEE RA-L 2020) — [arXiv](https://arxiv.org/pdf/2002.10718)
  - A dilated convolutional network (no RNN) corrects low-cost gyro readings, which are then integrated for orientation
  - On EuRoC and TUM-VI it beat top VIO systems on attitude without using vision
  - Code: github.com/mbrossar/denoise-imu-gyro
- AirIMU is AirIO's companion data-driven IMU correction + uncertainty model — [AirIO arXiv](https://arxiv.org/abs/2501.15659). Its own numbers were not retrieved.
- Learned bias factors for VIO (arXiv 2503.12527, 2025; arXiv 2505.06748, 2025) show active 2025 work on learned bias estimation — [arXiv 2503.12527](https://arxiv.org/pdf/2503.12527), [arXiv 2505.06748](https://ar5iv.labs.arxiv.org/html/2505.06748)

### Inferences
- For an ESP32 + MPU6500, the cheapest wins come before any learning: temperature-dependent bias calibration, a stationary-bias update while the arm rests, and a magnetometer or known-wall-heading yaw reset.
- A Brossard-style corrector needs ground-truth orientation for training (mocap, or a phone/camera-tracked rig). It is small enough to train on a laptop.

### Gaps
- No 2023-2026 direct follow-up to Brossard with comparable numbers was found in this pass, and no physics-informed neural network (PINN) IMU paper with arm-tracking numbers was located.
- AirIMU's standalone gyro-correction results were not retrieved.

## 4. Wrist-only touch detection and pointing on arbitrary surfaces

### Takeaway
Detecting *that* a tap happened is easy and very accurate from wrist IMUs at high sample rates: TapID reached F1 ≈ 0.997 with two IMUs on the strap. *Where* the tap lands is the hard part, and recent systems get it from a second modality (headset hand tracking). For WristTap, IMU-based tap-event detection is solved enough. Position must come from the arm model, possibly corrected at each touch.

### Cited Findings
- **TapID** (Meier, Streli, Fender, Holz, ETH; IEEE VR 2021) — [ETH PDF](https://research-collection.ethz.ch/bitstream/handle/20.500.11850/488237/vr2021-TapID.pdf?sequence=3)
  - Two IMUs in a flexible wristband, one on each side of the wrist
  - Tap-event detection F1 = 0.997 seated at a table
  - Finger identification F1 = 0.93 within-user, 0.91 cross-user with refinement taps, 0.87 without
  - Code: github.com/eth-siplab/TapID
- A third-party summary notes TapID was tethered to a PC and used a GPU — [summary](https://xrresearched.substack.com/p/tapid-rapid-touch-interaction-in)
- **SurfaceXR** (Xu, Chen, Gonzalez, Colaço, Hoffmann, Gonzalez-Franco, Ahuja; arXiv 2603.19529, Mar 2026; IEEE VR 2026 / TVCG) — [arXiv abs](https://arxiv.org/abs/2603.19529)
  - Fuses smartwatch IMU with headset egocentric hand tracking. 21-participant study of touch tracking and 8-class gestures
  - Per a search snippet: IMU-only single-tap 80.7%; fused 92.0% single-tap and 97.0% double-tap. The authors attribute part of the gap to TapID to their lower 200 Hz sampling — [arXiv PDF](https://arxiv.org/pdf/2603.19529)
- **ViBand** (Laput, Xiao, Harrison, CMU; UIST 2016) raises a smartwatch accelerometer from ~100 Hz to 4 kHz via a custom kernel. It then detects bio-acoustic events: taps on the forearm, palm and back of the hand, flicks, and object vibrations — [project](https://www.robertxiao.ca/research/viband/)
- Related wrist-accelerometer gesture work:
  - A 2024 thumb-to-finger study on COTS smartwatch accelerometers: 80.1% for 17 gestures, 94.7% for 4 gestures (leave-one-participant-out) — [Tsukuba](https://www.iplab.cs.tsukuba.ac.jp/en/paper/652fa814e3d7893ff73ec236/)
  - Apple holds "IMU for touch detection" patents (US 11073898, 11360550, 11803233) — [USPTO](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11073898)

### Inferences
- Running the MPU6500 accelerometer at ≥1 kHz in a burst window (it supports up to 4 kHz accel output), or using a piezo (WristTap's planned step 5), should give near-TapID tap detection on a hard wall.
- The touch event is also a free drift-correction signal: at contact the hand lies on the known wall plane with zero velocity. That is a zero-velocity update (ZUPT) plus a plane constraint, which can reset depth error and bias every touch.

### Gaps
- Serendipity (Wen et al., CHI 2016, finger gestures from a smartwatch) numbers were not retrieved.
- ViBand's exact accuracy numbers were not retrieved (the primary PDF was not fetched).
- No paper found doing IMU-only *localization* of touches on a projected wall.

## 5. Training data for a student; using camera labels only at training time

### Takeaway
Yes. Training with camera/mocap labels and deploying camera-free is the standard recipe in this whole literature:
- ArmPoser labelled its dataset with 6 RGB cameras (EasyMocap)
- Weigend et al. and HOOV used OptiTrack
- DIP, TransPose, PIP, IMUPoser and MobilePoser pretrain on IMU signals synthesized from AMASS mocap
- IMUTube synthesizes IMU data from ordinary video

A student can pretrain on AMASS-synthesized wrist (and upper-arm) IMU data, then fine-tune on 30-120 min of their own ESP32 recordings labelled by a webcam/phone pose estimator, or by the projected-touch locations themselves.

### Cited Findings
- ArmPoser: AMASS-synthesized IMU pretraining with mounting/yaw augmentation, fine-tuned on DIP-IMU + IMUPoser. Its new real dataset (10 people × ~160 min per platform) was labelled by EasyMocap from 6 RGB cameras. The runtime is camera-free — [arXiv](https://arxiv.org/html/2609.08806)
- Weigend et al.: 6 participants, ~381k watch samples labelled by 12-camera OptiTrack; runtime is watch-only — [arXiv](https://arxiv.org/html/2306.13192)
- HOOV: trained/validated against OptiTrack; runtime uses wrist IMU — [arXiv](https://arxiv.org/pdf/2303.07016)
- MobilePoser and the IMUPoser lineage train mostly on synthetic IMU derived from mocap (AMASS) and evaluate on DIP-IMU/TotalCapture/IMUPoser real data — [MobilePoser arXiv](https://arxiv.org/html/2504.12492v1)
- **IMUTube** (Kwon et al., IMWUT 2020; arXiv 2006.05675) — [arXiv](https://arxiv.org/abs/2006.05675), [GT licensing](https://licensing.research.gatech.edu/technology/imutube-converting-videos-human-activity-virtual-imu-data-streams)
  - Pipeline: video → 3D pose tracking → virtual IMU at chosen body sites → distribution matching to the target sensor
  - Virtual data was sometimes comparable to real-only training, and virtual + a little real beat real-only
  - Works best for simple activities whose key motion is mostly 2D
- Caveat: synthetic data under-represents real sensor noise (noted by Ultra Diffusion Poser) — [arXiv](https://arxiv.org/pdf/2606.02153)
- Datasets referenced across these papers:
  - AMASS (mocap)
  - DIP-IMU (10 participants, 17 Xsens IMUs, 64 sequences)
  - TotalCapture (13 Xsens + Vicon)
  - IMUPoser dataset (10 participants, consumer devices)
  - ArmPoser dataset (announced public)
  - Nymeria (egocentric wearable)
  - [ArmPoser arXiv](https://arxiv.org/html/2609.08806), [CVPR 2026 supp](https://openaccess.thecvf.com/content/CVPR2026F/supplemental/Li_MARIO_Motion-Augmented_Real-Time_CVPRF_2026_supplemental.pdf)

### Inferences (practical plan for WristTap)
- **Data:** synthesize wrist + upper-arm IMU streams from AMASS arm motion (as ArmPoser/MobilePoser do), then record your own sessions. Use the ESP32 IMUs plus a Mac webcam or phone running a pose estimator (MediaPipe, or multi-view EasyMocap if two phones are available) to label wrist/elbow 3D. The projector itself gives exact labels when the user touches known projected targets. Expect tens of minutes to a couple of hours of real data, based on ArmPoser's ~160 min per platform and Weigend's 6 participants.
- **Compute:** LSTM models with ~256 hidden units train in hours on a single consumer GPU (RTX 3090 in ArmPoser). On an Apple Silicon Mac, PyTorch MPS is plausible for training small LSTMs and easily fast enough for 30-60 Hz inference, since ArmPoser runs live on a MacBook Air M3. The user's Mac has 8 GB RAM, so keep models small and batch sizes modest.
- **Runtime:** ESP32 streams quaternion + linear acceleration (fused on-chip, or raw for host-side fusion) over Wi-Fi UDP at 50-100 Hz, as in Weigend's UDP watch stream. The Mac runs the network, an EKF with arm-kinematic constraints, and ZUPT/plane resets at detected touches.

### Gaps
- No paper found that uses a projector/touch-target self-labelling loop for IMU arm models. This is an inference, not a cited method.
- MediaPipe-labelled (monocular, noisy-depth) training for IMU arm pose was not benchmarked in any paper found. Its 3D label noise may limit accuracy compared with multi-camera EasyMocap or OptiTrack.
- No measurements were found of MPU6500-class (vs. Xsens/Apple Watch) sensor noise impact on these models.
