# Week 2: Distraction Detection Model

## Deliverables
- MobileNetV2 distraction classifier: 84.88% validation accuracy
- TFLite model: 2.40MB (90.7% size reduction)
- Delivered to Sukh for Android integration

## Files
- `train_mobilenetv2.py` - Training script
- `convert_to_tflite.py` - TFLite conversion
- `config.py` - Configuration
- `models/` - Trained models
  - `mobilenetv2_final.keras` (25.8MB)
  - `distraction_model.tflite` (2.40MB)

## Performance
- Validation Accuracy: 84.88%
- Target: 92%+ (Week 3 fine-tuning)
- Driver-based split (20 train/6 val)
