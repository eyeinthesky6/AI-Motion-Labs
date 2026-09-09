# M2 Quality Diagnostics

M2 starts with a **non-destructive quality layer**. It reads a validated MotionSpec asset and calculates diagnostics without changing the asset manifest or payload.

## Current signals

- pose coverage / missing-frame ratio;
- mean and 10th-percentile joint confidence;
- median frame interval;
- joint velocity median/p95/max;
- normalized bone-length variance;
- warnings for low coverage, low confidence, large temporal spikes and unstable bone lengths.

Run:

```bash
motionlab quality ./out/my-motion.motion
motionlab quality ./out/my-motion.motion --json
```

## Why these signals

### Coverage
A generator can only reuse a motion that was actually observed. Missing spans must be visible rather than silently interpolated.

### Confidence
Confidence gives a first-pass indication of joints likely to need inspection, especially hands, feet and occluded limbs.

### Velocity spikes
Single-frame jumps are often a sign of detector jitter, identity switches, occlusion recovery or timestamp problems. The report is a diagnostic, not a universal biomechanical threshold.

### Bone-length variance
A person's skeleton should not repeatedly stretch and shrink. Large normalized variation is a useful detector for jitter and bad observations before retargeting.

## Deliberately deferred

- biomechanical validity claims;
- learned quality scores;
- automatic repair/interpolation;
- foot-contact scoring;
- camera/root separation;
- visual overlay rendering.

Those require benchmark evidence first. M2 should make failure visible before attempting to hide it with cleanup.

## Acceptance target

A human should be able to inspect a generated asset and answer:

> **Did we actually capture the action well enough to reuse it?**

The next M2 step is a simple original-video + skeleton overlay and neutral-skeleton preview, followed by FFmpeg/ffprobe handling for VFR and unusual codecs.
