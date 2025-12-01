# Week 2: Distraction Detection Model

## Results
- **Validation Accuracy:** 84.88% (driver-based split)
- **Target:** 92%+ (Week 3 fine-tuning)
- **Keras Model:** 25.8MB
- **TFLite Model:** 2.4MB (90.7% reduction)
- **Training Time:** ~3 hours (M4 Pro + Metal)

## Files
```
week2_training/
├── *.py                  # Training & conversion scripts
├── models/
│   └── mobilenetv2_final.h5       # Final Keras model (25.8MB)
└── tflite_models/
    ├── mobilenetv2_distraction_classifier.tflite  # (2.4MB)
    ├── model_metadata.json                        # Model specs
    └── INTEGRATION_GUIDE.md                       # For Sukh
```

## Usage
```bash
# Train model
python train_mobilenetv2.py

# Convert to TFLite  
python convert_to_tflite.py

# Evaluate
python evaluate_model.py
```

## Status
- ✅ Model trained (84.88% accuracy)
- ✅ TFLite converted (2.4MB)
- ✅ Delivered to Sukh for Android integration
- ⏳ Week 3: Fine-tune to 92%+
