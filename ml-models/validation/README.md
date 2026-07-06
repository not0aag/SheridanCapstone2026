# Model validation

The Android app ships `app/src/main/assets/models/distraction_classifier.tflite` and its
doc comment (`DistractionInferenceEngine.kt`) claims "~91% val accuracy" — but that number
can't be traced to anything in this repo:

- The model file's checksum doesn't match any `.tflite` artifact under `ml-models/`
  (only `.gitkeep` placeholders remain in `week2_training/models` and `week3_finetuning/models`).
- `ml-models/week3_finetuning/CURRENT_STATUS.md` is frozen at "Epoch 1/30, ~23.5% accuracy"
  with no later update — the "week 3 fine-tuned model" the doc comment cites doesn't have
  a finished, committed run anywhere.
- The one fully-documented conversion, `ml-models/week2_training/tflite_models/model_metadata.json`,
  shows accuracy dropping from 84.88% (Keras) to 23.8% (TFLite) after conversion —
  `"validation_status": "WARNING"`, `"accuracy_difference_percent": 61.08` — caused by a
  preprocessing mismatch: that metadata documents `/255.0` ([0,1]) normalization, while
  `DistractionInferenceEngine.kt` actually feeds the model `(channel/127.5) - 1.0` ([-1,1]).

`validate_tflite.py` loads the actual shipped model and runs it through the *exact*
on-device preprocessing, so you can get a real number instead of the unverified claim.

## Setup

Reuses `ml-models/week2_training`'s existing pinned environment — no new dependency:

```
cd ml-models/week2_training
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
cd ../validation
```

## If you have labeled images (even 5-10 per class)

Arrange them one folder per class, folder name starting with the class index:

```
labeled_images/
  c0_safe/*.jpg
  c1_texting_right/*.jpg
  c2_phone_right/*.jpg
  c3_texting_left/*.jpg
  c4_phone_left/*.jpg
  c5_radio/*.jpg
  c6_drinking/*.jpg
  c7_reaching_behind/*.jpg
  c8_hair_makeup/*.jpg
  c9_talking_passenger/*.jpg
```

Then:

```
python validate_tflite.py --data-dir path/to/labeled_images
```

Prints per-miss detail, overall accuracy, and a confusion matrix.

## If you have zero labeled data right now

Point it at any folder of photos (even just yourself at your desk vs. holding a phone)
for a manual sanity check — no accuracy number, just predictions to eyeball:

```
python validate_tflite.py --sanity-dir path/to/any_photos
```

Use this to catch egregious breakage (e.g. the model always predicting one class,
or predictions that make no sense at all) before you've gathered a real labeled set.

Run this at least once before the demo — replace the unverified "~91%" claim in
`DistractionInferenceEngine.kt`'s doc comment with whatever this script actually measures.
