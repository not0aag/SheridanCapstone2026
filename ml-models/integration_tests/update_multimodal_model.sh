#!/bin/bash

# Script to update the multimodal system with newly trained model
# Usage: ./update_multimodal_model.sh [extreme_aug|class_weights]

MODEL_TYPE=$1

if [ "$MODEL_TYPE" == "extreme_aug" ]; then
    echo "Updating multimodal system to use extreme augmentation model..."
    MODEL_PATH="../week3_finetuning/tflite_models/extreme_aug_model.tflite"
elif [ "$MODEL_TYPE" == "class_weights" ]; then
    echo "Updating multimodal system to use class weights model..."
    MODEL_PATH="../week3_finetuning/tflite_models/best_model_class_weights.tflite"
else
    echo "Usage: ./update_multimodal_model.sh [extreme_aug|class_weights]"
    exit 1
fi

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Error: Model not found at $MODEL_PATH"
    echo "Training may not be complete yet."
    exit 1
fi

# Update multimodal_distraction_detector.py
sed -i '' "s|MODEL_PATH = \".*\"|MODEL_PATH = \"$MODEL_PATH\"|" multimodal_distraction_detector.py

echo "✓ Multimodal system updated!"
echo "New model: $MODEL_PATH"
echo ""
echo "Test it:"
echo "  python multimodal_distraction_detector.py"
