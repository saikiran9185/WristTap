# Wrist-worn gesture, touch and press-force sensing: prior art for WristTap

Written 15 Nov 2026. WristTap is an ESP32 band with 2 IMUs, 4 piezo discs on the skin and 2 FSRs under the strap. The Mac does the processing, and the goal is camera-free touch vs hover, press strength and gesture class.

How solid each source is: most numbers come from the primary paper (ViBand PDF, TouchFusion arXiv HTML, EI-Lite abstract page, the Nature 2025 article text). Some come only from search-result summaries of abstracts. Those are marked "(abstract/summary)" and should be checked before anyone quotes them.

## 1. Force myography (FMG) / FSR bands: gestures, grip force, drift and strap tightness

### Takeaway
FSR bands at the wrist reach about 80–97% on 5–48 gestures, but only with 8–16 FSRs and per-user, within-session training. Accuracy drops across sessions and re-wears, and that drift is FMG's best-known weakness. WristTap's 2 FSRs are far below the sensor counts in the literature. They can realistically give a "press / grip effort" signal and help with a few coarse gestures. They are not enough for fine gesture classification on their own.

### Cited Findings
- 16-FSR prototype band, tested alongside commercial sEMG on 48 gestures: ~96.7% in cross-validation and 89.4% cross-trial. The cross-trial figure is the more honest one. (abstract/summary) — [PubMed 28161107](https://www.pubmed.gov/28161107/)
- An 8-FSR band matched a commercial sEMG system at both wrist and forearm positions (Medical Engineering & Physics vol. 41, 2017). (abstract/summary) — [Peeref](https://peeref.com/works/4198651); [Frontiers Bioeng 2017](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2017.00042/pdf)
- Literature review (2025 chapter): ~93% for 6 hand movements with 8 FSRs; 90% for ASL digits with 8 FSRs; 87.7% for 6 grasps with a 10-FSR band plus Leap Motion; 89.65% for a 4-FSR wristband, but tested on only 1 volunteer. (summary) — [Springer 2025](https://link.springer.com/chapter/10.1007/978-3-032-03488-5_10)
- Echo-state network on a wristband FSR array: 5 gestures at 87.3% across 6 participants. (summary) — [Glasgow eprint](https://eprints.gla.ac.uk/197560/1/197560.pdf)
- 8-FSR band with 15 participants and 10 activities-of-daily-living gestures (Sagastume et al., Frontiers in Electronics 2024). — [Frontiers 2024](https://www.frontiersin.org/journals/electronics/articles/10.3389/felec.2024.1503424/pdf)
- Sampling frequency, channel count and placement all affect FMG accuracy. 8 channels were sufficient in that study, and for *static* gestures the FMG sampling rate can be as low as ~5 Hz. (Sensors 2021, "Investigation on the Sampling Frequency and Channel Number for FMG-based hand gesture recognition"; summary) — [MDPI Sensors 21(11):3872](https://mdpi.com/1424-8220/21/11/3872); [catalog record](https://vufind.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c446t-d4accc91a2a86ce155bea25c2d6c9a942dc956ed9df420c1c3998669890eb17e3)
- WristFlex (Dementyev & Paradiso, MIT, UIST 2014): FSRs around the wrist that read tendon movement and distinguish subtle finger *pinch* gestures with ">80%" accuracy. Sensor power is 60.7 µW. Accelerometer orientation data can extend the number of gestures. — [MIT Media Lab](https://www.media.mit.edu/publications/wristflex-low-power-gesture-input-with-wrist-worn-pressure-sensors/); [DSpace](https://dspace.mit.edu/handle/1721.1/103642)
- FMG regression of force rather than class: Sakr, Jiang & Menon (2019) estimated isometric hand force and torque from **60 FSRs in 4 bands** on the arm. They used GRNN/SVR/random forest against a 6-DoF load cell, with 9 participants. — [Frontiers Robotics & AI 2019](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2019.00120/full)
- FMG grasp regression (Chegani & Menon 2018): training has to include more than one wrist position, because wrist movement changes the FMG signal and hurts continuous prediction. — [PMC6199756](https://pmc.ncbi.nlm.nih.gov/articles/PMC6199756)
- FMG suffers "stochastic signal variation within the same class of gestures along time", which leads to low inter-session accuracy (a domain shift). — [Sensors 21:1504, ETH](https://research-collection.ethz.ch/bitstream/20.500.11850/472323/3/sensors-21-01504-v2.pdf)
- A prosthesis study with FMG sensors on a Velcro strap found that limb position and load both affect classification, so adaptive control is likely to be needed. — [JMIR Rehab 2017](https://rehab.jmir.org/2017/1/e5)

### Inferences
- With 2 FSRs over the flexor tendons, WristTap gets roughly a 2-D signal: overall flexor effort plus a coarse left/right split. Expect it to work well for "pressing hard vs light vs not pressing" and for a whole-hand grip. Expect it to work poorly for telling individual fingers apart. The 4-FSR, single-user 89.65% result is the closest analogue, and it is weak evidence.
- Strap tension sets the FSR baseline (preload). The FSR reading should be treated as relative to a baseline captured on wear-on, not as an absolute force value.
- FMG is low-bandwidth. 50–100 Hz per FSR is plenty, and the ESP32's 500 Hz ADC is more than enough for the FSRs.

### Gaps
- I found no study that quantifies how strap tightness or cuff pressure affects FMG accuracy. This is a known gap.
- I found no FMG study that uses only 2 FSRs at the wrist.

## 2. Bio-acoustic / piezo / MMG wrist sensing for taps and finger identification; required sample rates

### Takeaway
Tap and contact vibrations travel through the arm mainly between ~20 Hz and 1 kHz, with resonances near 170 Hz and 750 Hz. ViBand sampled at 4 kHz and classified 17 gestures at 94.3% with per-user training. A 500 Hz ADC (Nyquist 250 Hz) captures the low band, including the ~170 Hz peak, and slower MMG muscle sounds (3–100 Hz). It misses the 250 Hz–1 kHz content that makes tap textures (flick vs scratch vs snap) distinct. For WristTap, 500 Hz is probably enough to detect *that* a tap or touch onset happened and how energetic it was. Pushing the piezo channels to 1–2 kHz or more is the cheap upgrade worth doing.

### Cited Findings
- ViBand (Laput, Xiao, Harrison, CMU, UIST 2016): custom kernel raised an LG G Watch accelerometer from the ~100 Hz API limit to **4 kHz**, enough to sense vibrations up to 2 kHz. — [ViBand paper PDF](https://modernmobile.cs.washington.edu/docs/viband.pdf); [project page](https://www.robertxiao.ca/research/viband/)
- ViBand arm resonance sweep (0–2 kHz transducer): "vibration frequencies between 20 Hz and 1 kHz transmit particularly well through the arm, with salient peaks at ~170 Hz and ~750 Hz." — [ViBand PDF](https://modernmobile.cs.washington.edu/docs/viband.pdf)
- ViBand pipeline: per-axis FFT power spectra (Hamming window, DC removed), max across the 3 axes, average of the last w=20 spectra, then statistical features (mean, sum, min, max, 1st derivative, median, SD, range, band ratios, top 5 peaks) into an SMO SVM with a polynomial kernel. Band ratios, peaks, mean and SD gave 90% of the discriminative power. — [ViBand PDF](https://modernmobile.cs.washington.edu/docs/viband.pdf)
- ViBand gesture study: 17 participants (18 recruited) and 3 gesture sets totalling 17 gestures (one-handed, two-handed, on-body touch: flicks, claps, snaps, scratches, taps on palm, back of hand and forearm). **Per-user models trained on 15 examples per gesture.** Mean accuracy was 94.3% (SD 4.1%). Re-wearing the watch caused only a slight, non-significant drop, and there was no BMI effect. — [ViBand PDF](https://modernmobile.cs.washington.edu/docs/viband.pdf)
- ViBand false positives: after training with large negative ("null") background data, 77 minutes of walking, jogging, jumping jacks, reading and hand-washing across 17 users produced **6 false positives total**, with 0 for 12 of 17 users. — [ViBand PDF](https://modernmobile.cs.washington.edu/docs/viband.pdf)
- Skinput (Harrison, Tan, Morris, CHI 2010): an armband of tuned cantilevered piezo films, with 186 acoustic features. Across 20 participants it reached ~88% overall, 96% for forearm locations with sensors below the elbow, and 97% for finger flicks. It needs per-user training on each location, accuracy is lower for "fleshier" users, and the authors note that distinguishing a true tap from hover is "extraordinarily difficult" for optical approaches. (some figures from summaries) — [Skinput PDF, Microsoft Research](https://microsoft.com/en-us/research/wp-content/uploads/2010/04/SkinputHarrison.pdf); [ScienceDaily](https://www.sciencedaily.com/releases/2010/04/100406125547.htm)
- A wrist-worn piezoelectric sensor array for gesture input exists as a journal paper (title only retrieved). — [record](https://bvbvf1.bib-bvb.de/vufind/PrimoRecord/cdi_proquest_journals_2024517907)
- The usable MMG (muscle mechanical vibration) band is ~3–100 Hz. An open MMG hand-gesture dataset recorded 6-axis IMU at **200 Hz** with a 30–90 Hz bandpass for 11 hand/wrist gestures. Other MMG studies used 1 kHz, or upsampled to 2 kHz. One finger-gesture MMG paper used 50–900 Hz. — [PMC12175236 dataset](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12175236/); [search summary sources](https://pmc.ncbi.nlm.nih.gov/articles/PMC5299557)
- An accelerometer-based wrist approach outperformed sEMG on a 40-movement task across 20 subjects. (summary; primary not opened) — [Frontiers Neurology 2017](https://www.frontiersin.org/journals/neurology/articles/10.3389/fneur.2017.00573/pdf)

### Inferences
- **Can 500 Hz suffice?** For tap *onset* detection and energy (touch event, rough tap strength): probably yes. A tap transient has broadband energy, and the 20–250 Hz part, including the 170 Hz resonance, is captured. For *finger identification and gesture texture*: marginal. ViBand-class discrimination relies on spectra up to 1–2 kHz. Recommendations:
  1. Sample the piezos at ≥2 kHz in bursts, or with a rolling buffer that is shipped to the Mac only around onsets. The ESP32's I2S-ADC/DMA mode can reach tens of kHz.
  2. If staying at 500 Hz, put an analog anti-alias low-pass at ~200–250 Hz on each piezo. Otherwise the 250 Hz–1 kHz energy aliases into the band and corrupts features.
- Piezo discs touching skin respond to **change** (they are high-pass by physics). They show tap onsets and releases, not sustained touch. Hold state ("still pressing") has to come from the FSRs (sustained tendon load) or from the IMU's quietness after the tap.
- Copy ViBand's large negative-class training (walking, typing, washing). It is the single biggest false-positive reducer and costs nothing in hardware.
- WristTap's IMUs: if they are MPU6500-class, the accelerometer supports up to ~4 kHz output data rate (spec-sheet knowledge, not verified here). Running one IMU at 1–4 kHz over SPI would give ViBand-style sensing directly, without the piezos.

### Gaps
- I found no published head-to-head of the same tap-classification task at 500 Hz vs 4 kHz. ViBand compares only 100 Hz vs 4 kHz, qualitatively.
- I did not find per-finger identification accuracy from wrist piezo alone (which finger tapped). "Taprint" and similar papers did not show up.

## 3. Surface EMG wristbands (Meta Nature 2025, Myo) for comparison

### Takeaway
Meta's sEMG-RD band (16 bipolar channels, 2 kHz) used thousands of training participants to reach *generic* (no-calibration) models: >90% offline accuracy on held-out users for 9 discrete gestures, 0.88 gesture detections/s closed-loop, and 20.9 WPM handwriting. EMG captures intent with almost no visible movement, and its amplitude follows muscle force, including isometric presses. FMG and piezo signals need actual tendon motion or vibration. A hobby build cannot reproduce the generic-model data scale. WristTap should plan on per-user calibration.

### Cited Findings
- Kaifosh, Reardon & CTRL-labs at Reality Labs, "A generic non-invasive neuromotor interface for human-computer interaction", Nature 645:702–711. Online 23 Jul 2025, Sept 2025 issue. Closed-loop medians: 0.66 target acquisitions/s (continuous navigation), 0.88 gesture detections/s (discrete gestures), 20.9 WPM handwriting. Personalization improved handwriting by 16%. — [CSHL repository](https://repository.cshl.edu/id/eprint/42049/); [Nature reader copy](https://hn.jakechampion.name/reader/https://www.nature.com/articles/s41586-025-09255-w)
- Hardware: 48 electrode pins forming **16 bipolar channels**, sampled at **2 kHz**, streamed over Bluetooth. Participants per task ranged from 162 to 6,627. The public release has >100 h of sEMG from 300 participants. — [Nature reader copy](https://hn.jakechampion.name/reader/https://www.nature.com/articles/s41586-025-09255-w); [The Register](https://www.theregister.com/2025/07/23/meta_wristband_ui_control/); [Meta open-source blog](https://ai.meta.com/blog/open-sourcing-surface-electromyography-datasets-neurips-2024/)
- The 9 discrete gestures are index and middle finger press and release (4), thumb tap, and thumb swipes left/right/up/down. Offline accuracy was >90% on held-out participants. — [Nature reader copy](https://hn.jakechampion.name/reader/https://www.nature.com/articles/s41586-025-09255-w)
- Models: wrist task uses MPF features into an LSTM; discrete gestures use a 1D conv into LSTM layers; handwriting uses MPF features into a Conformer. Performance followed a power law in data and parameters, and personalization gains shrank as the generic training pool grew. Handwriting personalization: 20 min of user data gave a 16% median gain on a 6,400-participant generic model. Personalizing to one user hurt performance for other users. Training data included repeated band removal and repositioning, and deeper layers became insensitive to band placement. — [Nature reader copy](https://hn.jakechampion.name/reader/https://www.nature.com/articles/s41586-025-09255-w)
- EMG is unaffected by occlusion or lighting and detects gestures with minimal movement, including single motor-unit activity in low-movement conditions. The authors suggest it could sense the *force* of intended gestures, which cameras cannot see. — [Nature reader copy](https://hn.jakechampion.name/reader/https://www.nature.com/articles/s41586-025-09255-w)
- The preprint (2024) had reported 0.9 detections/s and 17.0 adjusted WPM. The final paper's numbers differ, so cite the Nature version. — [preprint PDF](https://storage.prod.researchhub.com/uploads/papers/2024/03/01/2024.02.23.581779.full.pdf)
- Related Meta dataset emg2pose (NeurIPS 2024 D&B) regresses full hand pose from wrist sEMG, using motion-capture labels. — [arXiv 2412.02725](https://arxiv.org/html/2412.02725v1)
- Myo-era comparison: an 8-FSR band matched a commercial sEMG system for gesture classification. — [Peeref (Med Eng Phys 41)](https://peeref.com/works/4198651)

### Inferences
- What EMG gives that WristTap's sensors don't: (a) isometric force with no movement, e.g. pressing a finger on a table harder without moving it; (b) individual-finger selectivity from 16 spatial channels; (c) intent onset that comes *before* movement. With 2 FSRs and 4 piezos, isometric press force can be approximated from FSR tendon load, because flexor tendons bulge under load. Finger selectivity will be weak.
- Meta's generic model needed thousands of users. For a single-user prototype, per-user training with 10–20 examples per class is the realistic target, as ViBand did with 15 per gesture.

### Gaps
- I did not retrieve exact generic false-negative rates or latency numbers for the discrete-gesture model (the article text was truncated).
- I did not retrieve specific Myo accuracy figures.

## 4. Touch vs hover detection and contact/press force estimation from the wrist

### Takeaway
Touch vs hover is hard for single-modality wrist sensing. The best recent system, Meta's TouchFusion (Feb 2026, 100 participants), fuses sEMG, bioimpedance, IR proximity, ToF and IMU to get world-touch AUC-ROC 0.994 and body-touch 0.969 with *generic* models. Direct wrist estimation of pinch or fingertip force has been shown (EI-Lite, UIST 2025: pinch force within ~0.55 N), but it is rare. For WristTap the workable recipe is: piezo/IMU transient = touch onset; FSR tendon load staying above baseline = still touching / pressing; FSR magnitude = press strength; a falling FSR load plus a release transient = lift-off.

### Cited Findings
- **TouchFusion** (Meta, arXiv 2602.15011, 16 Feb 2026). Sensors: 8-ch sEMG at 2 kHz; 4-ch bioimpedance at 2 kHz (1 MHz, 1 mA); 4-ch IR proximity at 100 Hz measuring *wrist deflection*; single-pixel ToF at 40 Hz; 8×8 ToF at 15 Hz; 6-axis IMU at **890 Hz**; magnetometer at 110 Hz. — [arXiv HTML](https://arxiv.org/html/2602.15011v1)
- TouchFusion results (window-level, 10-fold cross-user CV): world touch AUC-PR 0.960 / AUC-ROC 0.994; body touch AUC-PR 0.794 / AUC-ROC 0.969. Online (15 participants): median touch-state success 0.97 (mean 0.83, SD 0.28), median tap success 0.95. Most failures were *missed onsets*. Debounce was 160 ms (world) and 56 ms (body). All models were generic, with no per-user calibration, and personalization was left as future work. — [arXiv HTML](https://arxiv.org/html/2602.15011v1)
- TouchFusion models: world touch is a CNN-LSTM on sEMG + IR + IMU, with null/onset/offset classes, a **1 s window and 8.5 ms stride**. Body touch is conv + LSTM on 2-ch complex bioimpedance, with a 250 ms window and 6 ms stride. Fingertip velocity tracking uses IMU + IR + sEMG covariance features with a 200 ms window (R² 0.904). The authors say the models "relied heavily on proximity and inertial signals". No quantitative ablation and no force estimation are reported. — [arXiv HTML](https://arxiv.org/html/2602.15011v1)
- TouchFusion's single-pixel ToF cannot tell hovering over a surface from other occlusions, and the paper has no dedicated touch-vs-hover classifier. — [arXiv HTML](https://arxiv.org/html/2602.15011v1)
- **EI-Lite** (Google, UIST 2025): wrist-worn electrical impedance sensing. 6 micro-gestures + idle at 96.33%, and index-finger pinch force regression with MSE 0.3071 / "mean-force variance" 0.55 N across 15 participants. Includes an electrode-placement ablation (13 participants). — [Google Research](https://research.google/pubs/ei-lite-electrical-impedance-sensing-for-micro-gesture-recognition-and-pinch-force-estimation/)
- SenSkin (UIST 2013): IR reflective sensors in an armband estimate 3-D force applied to the skin. — [SenSkin PDF](https://star.rcast.u-tokyo.ac.jp/old/content/files/pdf/conference/full_paper/12.%20SenSkin.pdf)
- ElectroRing (Meta, CHI 2021): an active electrical ring for subtle pinch and palm-touch detection. It is a ring, not a band, but it shows that contact closure is easier to sense electrically than mechanically. — [ElectroRing PDF](https://research.facebook.com/file/485442549795198/ElectroRing--Subtle-Pinch-and-Touch-Detection-with-a-Ring.pdf)
- Skinput authors: telling a true tap from hover is "extraordinarily difficult" for camera/optical approaches. This motivates acoustic contact sensing. — [Skinput PDF](https://microsoft.com/en-us/research/wp-content/uploads/2010/04/SkinputHarrison.pdf)
- Force estimation from wrist sEMG: R² 0.78 for 2-DoF force, but poor for 3-DoF together. FMG with 60 FSRs regressed isometric hand force and torque. — [Frontiers Robotics & AI 2019](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2019.00120/full)
- Castellini et al. (2012): fingertip force regression from forearm signals was then "realized only in" one prior work, so the area is sparse. — [DLR PDF](https://elib.dlr.de/79296/1/inProc.2012.Castellini.sEMG_for_single_fingers.pdf)

### Inferences
- **Touch vs hover for WristTap:** hover produces no impact transient and little flexor load change. Touch produces a piezo/IMU transient, which is reliable for taps and less so for very gentle touches. A press produces a sustained FSR rise. So the touch/hover boundary is clean for taps and firm presses and fuzzy for feather-light touches. TouchFusion's main failure mode, missed onsets, would likely be worse here.
- **Press strength:** calibrate per user against a cheap ground truth, such as pressing on a kitchen scale or a spare FSR pad under the fingertip for a few minutes. Fit a monotonic regression (isotonic or a small MLP) from FSR delta-over-baseline, plus piezo transient energy, to newtons. EI-Lite's ~0.5 N error is a reasonable best-case target, and 3–5 strength levels is a realistic UX.
- Wrist posture changes FSR readings (Chegani & Menon). Include IMU-derived wrist orientation as a model input and collect calibration in several wrist poses.

### Gaps
- I found no paper that estimates fingertip force from 1–4 wrist FSRs specifically.
- No dedicated wrist-sensor touch-vs-hover benchmark with accuracy numbers was found.
- TouchFusion's late portion (offset 100k+) was not read and might contain ablations.

## 5. ML pipelines, per-user data, cross-session robustness, and camera labels used only for training

### Takeaway
Two pipelines both work at this scale. (a) Hand-crafted spectral and statistical features into an SVM or random forest (ViBand: 15 examples/gesture/user, 94%). This is the right first step for WristTap. (b) A small 1D-CNN + LSTM on raw multichannel windows (TouchFusion, Meta discrete gestures), which pays off once there is hours of data. Windows of 200 ms–1 s with ~5–12 ms stride are typical. Camera-derived labels (MediaPipe's 21 landmarks) used only at training time are an established pattern for camera-free wearables.

### Cited Findings
- Feature + SVM: ViBand's pipeline (FFT spectra averaged over 20 frames; band ratios, peaks, mean, SD into a poly-kernel SVM) trained in-session with 15 samples per gesture. — [ViBand PDF](https://modernmobile.cs.washington.edu/docs/viband.pdf)
- Deep: TouchFusion CNN-LSTM (1 s window, 8.5 ms stride) and conv-LSTM (250 ms, 6 ms stride). Meta discrete gestures: 1D conv + LSTM. Handwriting: Conformer. — [TouchFusion](https://arxiv.org/html/2602.15011v1); [Nature reader copy](https://hn.jakechampion.name/reader/https://www.nature.com/articles/s41586-025-09255-w)
- Meta's open model card (braindecode) uses rotation-invariant MLP features averaged over circular channel rotations (robust to band rotation), cross-channel covariance and MPF features, SpecAugment masking, and a 15-block Conformer with a CTC head. — [HF MetaNeuromotorHand](https://huggingface.co/braindecode/MetaNeuromotorHand/blob/main/README.md)
- Cross-session mitigation for EMG with donning/doffing and electrode shift: offline plus on-device updates reached 88.66% vs 78.48% without offline training. — [GIST PDF](https://scholar.gist.ac.kr/bitstream/local/32268/2/47731.pdf)
- HD-sEMG finger-force models from session 1 applied to later sessions after re-donning: RMSE rose only 2.6 ± 2.1% MVF (session 2) and 3 ± 2.6% MVF (session 3). — [Penn State](https://pure.psu.edu/en/publications/reliability-of-individual-finger-force-prediction-from-electromyo/)
- Donning/doffing shifts sensor position and is "largely responsible for the usability degradation" of trained myoelectric classifiers. — [Preprints 202002.0415](https://www.preprints.org/manuscript/202002.0415/v1/download)
- Camera labels at training only: WatchHand (2026) uses smartwatch speaker + mic acoustic sensing with MediaPipe Hands' 21 landmarks as ground truth, predicting 20 landmarks relative to the wrist. EtherPose (wrist RF antenna) used MediaPipe + webcam ground truth. mmEgoHand used MediaPipe Hand Landmark labels with manual filtering. — [WatchHand summary](https://api.emergentmind.com/topics/watchhand); [EtherPose (Hackster)](https://www.hackster.io/news/radio-killed-the-video-stream-98b0b768474d); [mmEgoHand arXiv](https://arxiv.org/html/2501.13805v2)
- Semi-supervised finger-IMU tracking (ssLOTR) needed only 15% of the labelled data of a fully supervised model. — [par.nsf.gov](https://par.nsf.gov/servlets/purl/10395306)
- Meta's emg2pose used motion-capture hand pose as labels for wrist sEMG regression. — [arXiv 2412.02725](https://arxiv.org/html/2412.02725v1)

### Inferences
- Recommended WristTap pipeline on the Mac:
  1. **Event stage:** an onset detector on piezo/IMU high-pass energy (threshold over an adaptive noise floor), firing within ~10–30 ms.
  2. **Classification stage:** features from a ~200–300 ms window around the onset (piezo band energies and ratios, IMU spectra and orientation deltas, FSR delta and slope) into an SVM or random forest. Train per user with 15–30 examples per class plus lots of "null" data.
  3. **State stage:** an HMM or simple state machine for hover → touch → press → release, using FSR as the sustained-state signal.
  4. Upgrade to a small 1D-CNN-LSTM once there are more than ~1–2 h of labelled data.
- **Camera as teacher:** record MediaPipe landmarks (webcam) in sync with band data during training sessions. Derive labels such as pinch/contact (thumb–index distance below a threshold), finger flexion angles and gesture class. MediaPipe cannot see contact *force* or true contact with a surface, and fingertip occlusion is common. Pair it with an FSR pad or scale for force labels, and a contact mic or touchpad for touch-truth labels.
- Latency budget: Meta and TouchFusion run 6–12 ms strides. Onset detection plus a 200 ms classification window yields ~200–250 ms gesture latency. Touch onset alone can be reported within ~30 ms, then refined.
- Cross-session: run a 10–20 s "rest + 3 reference presses" baseline routine on each wear-on to re-normalize FSR and piezo gains. Expect some accuracy loss after re-wear, though ViBand saw no significant drop.

### Gaps
- No published paper uses the exact WristTap sensor mix (IMU + piezo + 2 FSR), so accuracy for that combination is unknown.
- I found no direct paper training a wrist IMU/piezo model on MediaPipe labels. The closest examples are acoustic (WatchHand) and RF (EtherPose).

## 6. Sensor placement and mounting on a 3D-printed bangle

### Takeaway
The literature places FSRs over the volar (palm-side) wrist tendons and expects consistent preload. Piezo/vibration sensors need firm, consistent skin coupling, and ViBand asked users to wear the watch "comfortable but firm". Skinput found sensors below the elbow (on the forearm, closer to the hand) more accurate than above. Design for repeatable preload and wrist-pose-aware calibration.

### Cited Findings
- ViBand participants wore the watch in a "comfortable but firm" manner. Accuracy was robust to re-wearing. — [ViBand PDF](https://modernmobile.cs.washington.edu/docs/viband.pdf)
- Skinput: 96% accuracy with sensors below the elbow vs 88% above. Accuracy was lower in fleshier users. — [Skinput PDF](https://microsoft.com/en-us/research/wp-content/uploads/2010/04/SkinputHarrison.pdf)
- WristFlex places FSRs around the wrist to read tendon movement, and it fits a watch or bracelet form factor. — [MIT Media Lab](https://www.media.mit.edu/publications/wristflex-low-power-gesture-input-with-wrist-worn-pressure-sensors/)
- An 8-FSR band performed comparably at both wrist and forearm positions. — [Peeref](https://peeref.com/works/4198651)
- FMG accuracy depends on sensor placement and channel count. — [MDPI Sensors 21:3872](https://mdpi.com/1424-8220/21/11/3872)
- TouchFusion's IR proximity sensors measure *wrist deflection*, i.e. tendon and skin surface motion, and its models relied heavily on proximity and inertial signals. — [arXiv HTML](https://arxiv.org/html/2602.15011v1)
- For classifiers, wrist and limb position plus load change FMG signals. — [JMIR Rehab 2017](https://rehab.jmir.org/2017/1/e5); [PMC6199756](https://pmc.ncbi.nlm.nih.gov/articles/PMC6199756)

### Inferences (engineering judgement, not from a single source)
- **FSRs:** put both on the volar side over the flexor tendons (flexor digitorum superficialis / palmaris longus region), ~2–4 cm proximal to the wrist crease, where tendons move under the skin when fingers flex. Back each FSR with a small rigid puck (2–3 mm, hemispherical or domed) so force concentrates on the active area. Put a thin layer of firm foam (e.g. 1–2 mm EVA or Poron) *behind* the FSR, between it and the strap, to set a soft, repeatable preload. Avoid soft foam in front of the sensor, which absorbs the signal.
- **Piezos:** mount them in the rigid bangle shell pressing against the skin, with a small contact nub, ideally on bony or tendon-adjacent spots (radial and ulnar sides, dorsal wrist). Decouple them mechanically from the strap and each other with a compliant mount, so each disc hears its local skin rather than the whole shell ringing.
- **IMUs:** one rigid in the bangle body on the dorsal side (the hand/wrist motion reference). A second on a different segment, such as the back of the hand (dorsum) or a finger ring, adds far more information than two IMUs on the same rigid bangle. The literature shows finger-segment IMUs enable hand-kinematics tracking.
- **Strap:** use a non-stretch strap with indexed holes or a ratchet so tension repeats between wears. Record the hole or tension index with each session's calibration.
- Run each wear-on calibration in 2–3 wrist poses (neutral, flexed, extended) to address the posture sensitivity reported for FMG.

### Gaps
- No source quantified optimal contact pressure (kPa) or foam durometer for wrist FSR or piezo coupling.
- No source compared FSR placement on the volar vs dorsal wrist for a 2-sensor band.
