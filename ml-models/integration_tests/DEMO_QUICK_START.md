# 🚀 Demo Day Quick Start (2-Minute Setup)

## The Day Before Demo
```bash
# Test the demo script once
cd /Users/harry/Sheridan/Sem-5/Capstone/SheridanCapstone2026/ml-models/integration_tests
source ../../safedrive_ml_env/bin/activate
python demo_script.py

# Practice these 5 actions:
# 1. Look forward (hands on imaginary wheel)
# 2. Text on phone (look down)
# 3. Phone to ear
# 4. Drink from bottle
# 5. Reach behind you
```

## Demo Day Morning (30 min before)
```bash
# 1. Grant camera permission if needed
#    System Settings → Privacy & Security → Camera → Enable for Terminal

# 2. Start demo
cd /Users/harry/Sheridan/Sem-5/Capstone/SheridanCapstone2026/ml-models/integration_tests
source ../../safedrive_ml_env/bin/activate
python demo_script.py

# 3. Verify it works:
#    - Camera shows you
#    - "Driver Detected" appears
#    - FPS shows 40+
#    - Green "SAFE DRIVING" when you look forward

# 4. Press 'q' to quit, you're ready!
```

## During Demo (5 minutes total)

**Say this:** (30 sec)
> "I'm going to demonstrate SafeDrive AI's real-time distraction detection. Watch the status change as I simulate different driver behaviors."

**Do this:** (2 min)
1. Look forward → Shows "✓ SAFE DRIVING" (green)
2. Pick up phone, text → Shows "⚠ TEXTING" (red alert)
3. Phone to ear → Shows "⚠ PHONE CALL" (red alert)  
4. Drink water → Shows "⚠ DRINKING" (red alert)
5. Reach behind → Shows "⚠ REACHING BEHIND" (red alert)

**Say this:** (30 sec)
> "As you can see, the system detects distractions instantly. It runs at 40+ FPS on my laptop and 25+ FPS on Android. The model is only 2.4MB - perfect for mobile deployment."

**Invite interaction:** (1 min)
> "Would anyone like to try it? Just pick up your phone and you'll see the alert."

## 🎯 If Something Goes Wrong

| Problem | Solution |
|---------|----------|
| Camera won't open | Use backup video or skip to slides |
| Wrong detections | Say "This is why we're fine-tuning to 92%+" |
| Low FPS | Say "On mobile we optimize for battery efficiency" |
| Crashes | Restart script, or show static image test |

## 📱 Backup Plan (No Camera)
```bash
# Show the pipeline working with static test
python test_static_image.py
```

## ✅ You're Ready If:
- [ ] Script runs without errors
- [ ] Camera shows you
- [ ] At least 3 different actions detected
- [ ] FPS shows 25+

**That's it! You're demo-ready! 🎉**
