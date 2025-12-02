# Week 3: Model Fine-Tuning (84.88% → 92%+ Target)

## Problem Identified
Real-world testing revealed the Week 2 model (84.88% validation accuracy) has significant accuracy issues:
- Consistently misclassifies "safe driving" as "reaching behind"
- Poor generalization to new camera angles/lighting
- Trained on State Farm dataset but struggles with real-world scenarios

## Improvements Implemented

### 1. Advanced Data Augmentation
**Previous:**
- Basic rotation, flip, brightness, contrast
- Limited variation

**New:**
- Rotation, flip, brightness, contrast, saturation, hue
- Random zoom/crop (simulates camera distance)
- Wider brightness range (0.7-1.3 vs 0.8-1.2)
- Color channel shifts
- **Total: 8 augmentation techniques** vs 4 previously

### 2. Mixup Augmentation
**New technique:** Blend two images and labels during training
- Proven to improve generalization by 2-5%
- Prevents overfitting to specific examples
- Alpha = 0.2 (20% mixing ratio)

### 3. Label Smoothing
**New:** Prevents overconfident predictions
- Smoothing factor: 0.1
- Improves calibration and generalization

### 4. Stronger Regularization
**Dropout:** 0.2 → 0.3 (50% increase)
**L2 Weight Decay:** 0.0001 (NEW)
- Prevents overfitting to training data

### 5. More Training
**Epochs:** 30 → 50 (67% increase)
- Phase 1: 20 → 30 epochs (frozen backbone)
- Phase 2: 10 → 20 epochs (fine-tuning)

### 6. Better Learning Rate Schedule
**Previous:** Fixed LR with ReduceLROnPlateau
**New:** Cosine annealing with warm restarts
- Helps escape local minima
- Better convergence

### 7. Smaller Batch Size
**Previous:** 32
**New:** 16
- Better gradient estimates
- Improved generalization

## Expected Results

### Conservative Estimate: 88-90%
- 3-5% improvement from augmentation
- Solid improvement, may need more iterations

### Optimistic Estimate: 92-95%
- All techniques working synergistically
- Achieves target accuracy

### If Below 88%:
Additional strategies to try:
1. **EfficientNet-B0** (larger model, better accuracy)
2. **Ensemble methods** (combine multiple models)
3. **More data** (augment dataset with synthetic images)
4. **Architecture search** (try different models)

## Training Time Estimate

**MacBook Pro M4 (Metal acceleration):**
- Previous training: ~3 hours (30 epochs)
- New training: ~5-6 hours (50 epochs, more augmentation)

## How to Run

```bash
cd /Users/harry/Sheridan/Sem-5/Capstone/SheridanCapstone2026/ml-models/week3_finetuning

# Activate environment
source ../../safedrive_ml_env/bin/activate

# Start training
python train_improved_model.py
```

## Monitoring Training

```bash
# In another terminal, start TensorBoard
tensorboard --logdir=./logs

# Open browser to http://localhost:6006
```

## Research References

1. **Mixup:** Zhang et al. (2017) - "mixup: Beyond Empirical Risk Minimization"
2. **Label Smoothing:** Szegedy et al. (2016) - "Rethinking the Inception Architecture"
3. **Transfer Learning Best Practices:** Kornblith et al. (2019)
4. **Data Augmentation:** Cubuk et al. (2019) - "AutoAugment"

## Success Criteria

- ✅ **Minimum:** 92% validation accuracy
- ✅ **Ideal:** 94-95% validation accuracy
- ✅ **Real-world test:** Correctly classifies majority of scenarios in live demo

If target achieved → Convert to TFLite and test in production
If target not achieved → Iterate with additional techniques
