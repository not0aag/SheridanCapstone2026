# Persistent Training Guide - Can Close MacBook Lid!

## 🚀 Start Training (Runs Even When Lid Closed)

```bash
cd /Users/harry/Sheridan/Sem-5/Capstone/SheridanCapstone2026/ml-models/week3_finetuning
./run_training_persistent.sh
```

**After running this command:**
- ✅ You can close your MacBook lid
- ✅ You can close the terminal
- ✅ Training will continue in background
- ✅ Mac will not sleep during training

## 📊 Check Training Status

```bash
cd /Users/harry/Sheridan/Sem-5/Capstone/SheridanCapstone2026/ml-models/week3_finetuning
./check_training_status.sh
```

## 📝 Monitor Live Progress

```bash
cd /Users/harry/Sheridan/Sem-5/Capstone/SheridanCapstone2026/ml-models/week3_finetuning
tail -f training_persistent.log
```

Press `Ctrl+C` to stop watching (training continues)

## ⏱️ Training Time

- **Estimated:** 5-6 hours total
- **Phase 1:** ~3 hours (30 epochs, frozen backbone)
- **Phase 2:** ~2-3 hours (20 epochs, fine-tuning)

## 🔍 What to Look For

In the log file, you'll see:
```
Epoch X/30 - loss: X.XXXX - accuracy: 0.XXXX - val_accuracy: 0.XXXX
```

**Good signs:**
- Accuracy increasing each epoch
- Loss decreasing each epoch
- Val_accuracy reaching 0.92+ (92%+)

## 🎯 Expected Results

- **After 10 epochs:** ~60-70% accuracy
- **After 20 epochs:** ~75-85% accuracy
- **After 30 epochs:** ~80-88% accuracy
- **After 50 epochs:** **88-95% accuracy** (TARGET: 92%+)

## ✅ When Training Completes

Look for in the log:
```
TRAINING COMPLETE!
Final Validation Accuracy: X.XX%
```

If **≥ 92%**: 🎉 TARGET ACHIEVED!
If **< 92%**: We have backup strategies

## 🛑 Stop Training (If Needed)

```bash
# Find process ID
pgrep -f "train_improved_model.py"

# Kill it
kill <process_id>
```

## 💡 Recommended Workflow

1. **Start training before going to bed:**
   ```bash
   ./run_training_persistent.sh
   ```

2. **Close MacBook lid and sleep** 😴

3. **Wake up 5-6 hours later**

4. **Check results:**
   ```bash
   ./check_training_status.sh
   ```

5. **If complete, evaluate model!**

## 📁 Output Files

After training completes:
- `models/best_model_improved.h5` - Best model (highest val_accuracy)
- `models/mobilenetv2_improved_final.h5` - Final model (last epoch)
- `logs/improved_run_TIMESTAMP/` - TensorBoard logs
- `training_persistent.log` - Complete training output

## 🔧 Troubleshooting

**Training stopped unexpectedly?**
- Check log: `tail -100 training_persistent.log`
- Look for error messages
- Restart: `./run_training_persistent.sh`

**Mac still sleeping?**
- Verify caffeinate is running: `ps aux | grep caffeinate`
- System Settings → Battery → Prevent automatic sleeping when display is off

**Out of memory?**
- Reduce batch size in `improved_config.py` (16 → 8)
- Close other applications

---

## 🎓 For Your Demo (December 4)

After training completes with 92%+ accuracy:
1. Convert to TFLite
2. Test with real-world demo
3. Show professors the improved accuracy!

**You're all set! Just run the training and let it work overnight!** 🚀
