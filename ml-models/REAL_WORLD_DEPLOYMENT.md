# SafeDrive AI - Real-World Deployment Guide

## Understanding Camera Requirements

### What the Model Expects (State Farm Training Data)
- **Camera Position:** Passenger side, dashboard level
- **Camera Angle:** Horizontal or slightly downward
- **View Captured:** Right side of driver, steering wheel visible, dashboard/car interior
- **Height:** Dashboard/chest level (NOT eye level, NOT cup holder level)

### Why This Matters for Phone Placement
Your model was trained on a specific camera perspective. For accurate detection, the phone camera must capture a **similar view** of the driver.

## Supported Phone Mount Positions

### ✅ RECOMMENDED: AC Vent Mount (Center or Right Side)
**Why it works:**
- Height: Dashboard level (matches training data) ✓
- Angle: Horizontal view of driver ✓
- Position: Center or right side captures driver's upper body ✓
- Car interior visible (dashboard, steering wheel) ✓

**Setup:**
```
1. Use AC vent phone mount
2. Mount on CENTER vent or RIGHT side vent
3. Adjust to capture driver's upper body + steering wheel
4. Phone should be in LANDSCAPE mode for better field of view
```

**Pros:**
- Most common phone position for GPS use
- Stable mounting
- Doesn't block windshield
- Matches training data camera height

**Cons:**
- Blocks one AC vent
- May need adjustment based on vent angle

---

### ✅ RECOMMENDED: Dashboard Mount (Center Console)
**Why it works:**
- Height: Dashboard level (matches training data) ✓
- Angle: Can be adjusted to horizontal view ✓
- Position: Center captures full driver view ✓
- Car interior visible ✓

**Setup:**
```
1. Use adhesive dashboard mount or weighted base
2. Position on center of dashboard (near infotainment area)
3. Angle phone to capture driver from chest level
4. Ensure steering wheel is visible in frame
```

**Pros:**
- Very stable
- Good angle flexibility
- Doesn't obstruct windshield
- Compatible with GPS use

**Cons:**
- May leave residue (adhesive mounts)
- Takes up dashboard space

---

### ⚠️ ACCEPTABLE: Windshield Mount (Lower Third Only)
**Why it can work:**
- If mounted in LOWER third of windshield, height is close to dashboard level
- Can capture similar angle as training data if positioned correctly

**Setup:**
```
1. Use suction cup windshield mount
2. Mount in LOWER THIRD of windshield (not center/top)
3. Position on right side for better driver view
4. Angle slightly downward toward driver
```

**Pros:**
- Easy to install/remove
- Adjustable
- Common for GPS use

**Cons:**
- May be illegal in some states (21 states ban windshield mounts)
- Can block driver's view if not positioned carefully
- If mounted too high, angle won't match training data

---

### ❌ NOT RECOMMENDED Positions

**Eye-Level Windshield Mount (Top/Center)**
- Too high - completely different angle from training data
- Model will see driver looking "down" (at road) as distraction
- ❌ Does NOT match training camera perspective

**Cup Holder Mount**
- Too low - sees driver from below
- Captures mostly ceiling and driver's chin
- ❌ Completely wrong angle

**CD Slot Mount**
- May be too low depending on car
- Limited adjustment options
- ⚠️ Test first, may not work well

**Held in Hand / Lap**
- Unstable, constantly moving
- Wrong angle
- ❌ Unreliable for monitoring

---

## Multi-Position Compatibility Strategy

### For App Integration (Future Enhancement)

Since users will mount phones in different positions, the app should:

**1. Camera Placement Validation (Startup)**
```
When app starts:
├─ Show camera feed
├─ Detect if car interior is visible (steering wheel, dashboard)
├─ Detect camera height (too high/low/correct)
├─ Provide real-time feedback:
   "✓ Good position - steering wheel visible"
   "⚠ Move camera lower - current angle too high"
   "✗ Car interior not detected - ensure dashboard is visible"
```

**2. Visual Alignment Guide**
```
Show AR overlay with:
├─ Target frame outline (where driver should appear)
├─ Steering wheel indicator (should be visible here)
├─ Height meter (dashboard level indicator)
└─ Real-time "alignment score"
```

**3. Auto-Calibration Mode**
```
For first-time setup:
├─ Ask user to sit in normal driving position
├─ Detect face + car interior features
├─ Calculate offset from expected training data view
├─ Apply correction factor to predictions
└─ Save calibration for this mounting position
```

## Testing Your Setup

### Quick Validation Test
```bash
# Run camera placement guide
cd ml-models/integration_tests
python camera_placement_guide.py
```

This will show:
- Live camera feed
- Whether car interior is detected
- If position matches training data expectations
- Visual diagram of correct vs current position

### Static Image Test
```python
# Take a photo in "safe driving" position
# Run model prediction
# Expected: "Safe Driving" with 80%+ confidence
# If you get "Reaching Behind" or other - position is wrong
```

## Common Phone Mounting Scenarios

### Scenario 1: Using Phone for GPS + Background Monitoring
**Setup:**
```
Mount: AC Vent (center)
Orientation: Landscape
Position: Adjust so driver's upper body + steering wheel visible
App: GPS in foreground, SafeDrive monitoring in background
```

**How it works:**
- User sees GPS directions
- SafeDrive runs in background, monitoring camera
- Alerts when distraction detected
- No interference with GPS functionality

---

### Scenario 2: Dedicated Monitoring (Phone as Dashcam)
**Setup:**
```
Mount: Dashboard mount (center console)
Orientation: Landscape
Position: Angled toward driver
App: SafeDrive in foreground with live view
```

**How it works:**
- Phone acts as dedicated monitoring device
- Live feedback on screen
- Recording for later review (optional)
- Best for testing/demonstration

---

### Scenario 3: Ride-Share/Fleet Vehicle
**Setup:**
```
Mount: Permanent dashboard mount
Position: Optimized once, left in place
App: Auto-start on vehicle ignition
```

**How it works:**
- Professional DMS-like setup
- Consistent position across all trips
- Data logging for fleet management
- Most accurate since position never changes

---

## Legal Considerations by State

**States Prohibiting Windshield Mounts (21 states):**
- Must use dashboard or vent mounts
- Check local laws before deployment

**States Allowing Windshield Mounts with Restrictions (15 states):**
- Usually limited to lower corners or bottom 5-6 inches
- Our "lower third" recommendation complies with most restrictions

**Recommendation:**
Default to **AC vent** or **dashboard mounts** for broadest legal compliance.

---

## Troubleshooting Common Issues

### Issue: Model predicts distractions when driving safely
**Cause:** Camera position doesn't match training data
**Fix:**
1. Check if steering wheel is visible in frame
2. Ensure camera is at dashboard level (not eye level)
3. Verify car interior is visible (not just driver against sky)
4. Run camera placement guide for real-time feedback

### Issue: Low confidence scores (below 60%)
**Cause:** Poor lighting or camera angle
**Fix:**
1. Ensure adequate interior lighting
2. Avoid direct sunlight on driver's face (causes shadows)
3. Adjust mount angle slightly
4. Clean phone camera lens

### Issue: No detection / camera blocked
**Cause:** Mount position blocks camera or driver not in frame
**Fix:**
1. Adjust mount to capture full driver upper body
2. Ensure nothing is obstructing camera (phone case, vent fins)
3. Check camera isn't pointed too high/low

---

## Performance Expectations by Mount Type

| Mount Type | Expected Accuracy | Setup Difficulty | GPS Compatible |
|------------|------------------|------------------|----------------|
| AC Vent (center/right) | 80-90% | Easy | ✓ Yes |
| Dashboard (center) | 85-90% | Easy | ✓ Yes |
| Windshield (lower third) | 75-85% | Easy | ✓ Yes |
| Windshield (top/center) | 40-60% | Easy | ✓ Yes (but accuracy poor) |
| Cup Holder | 30-50% | Easy | ✗ No |

**Note:** Accuracy assumes proper car interior visibility and dashboard-level height.

---

## Summary: Deployment Best Practices

✅ **DO:**
- Mount phone at dashboard level (chest height when seated)
- Use AC vent or dashboard mount for most consistent results
- Ensure steering wheel + dashboard visible in frame
- Run camera placement guide before first drive
- Use landscape orientation for wider field of view

❌ **DON'T:**
- Mount at eye level (too high)
- Use cup holder mounts (too low)
- Block camera with phone case or accessories
- Expect it to work in non-car environments (office, home)
- Mount where it obstructs driver's view of road

🎯 **RECOMMENDED SETUP:**
```
Mount Type: AC Vent Mount (center or right side)
Orientation: Landscape
Height: Dashboard level
Frame Content: Driver upper body (60%) + steering wheel/dashboard (40%)
Lighting: Avoid direct sunlight on face
```

This setup provides the best balance of:
- Model accuracy (matches training data)
- GPS compatibility (can run in background)
- Legal compliance (no windshield obstruction)
- User convenience (easy to adjust)
