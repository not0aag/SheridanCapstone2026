# SafeDrive AI - Model Storage Strategy

## 📁 What Goes Where

### ✅ Committed to Git (Version Controlled)

**Source Code & Scripts:**
- `*.py` - All Python training/evaluation scripts
- `config.py` - Training configurations
- `requirements.txt` - Dependencies
- Shell scripts (`.sh` files)

**Documentation:**
- `README.md` files
- Integration guides
- Technical documentation

**Small Production Models:**
- `*.tflite` - TensorFlow Lite models (typically <5MB)
- `*.mlmodel` - Core ML models for iOS
- `metadata.json` - Model specifications

**Why:** Small, deployment-ready, benefits from version control

### ❌ NOT Committed to Git (Ignored via .gitignore)

**Large Training Models:**
- `*.h5` - Keras/TensorFlow SavedModel format (25-50MB each)
- `*.keras` - Keras model format
- Checkpoint files

**Why:** Too large for Git (bloats repository), can be regenerated

**Training Artifacts:**
- `logs/` - TensorBoard training logs
- `*.log` - Training output logs
- `__pycache__/` - Python cache files

**Why:** Machine-specific, regenerated each run

---

## 🗂️ Directory Structure

```
ml-models/
├── week2_training/
│   ├── *.py                    ✅ Git (source code)
│   ├── README.md               ✅ Git (docs)
│   ├── models/
│   │   ├── .gitkeep            ✅ Git (preserves folder)
│   │   ├── *.h5                ❌ NOT in Git (large models)
│   │   └── *.keras             ❌ NOT in Git (large models)
│   └── tflite_models/
│       ├── *.tflite            ✅ Git (small, production)
│       └── *.json              ✅ Git (metadata)
│
├── week3_finetuning/
│   ├── *.py                    ✅ Git (source code)
│   ├── models/
│   │   ├── .gitkeep            ✅ Git (preserves folder)
│   │   └── *.h5                ❌ NOT in Git (large models)
│   └── logs/
│       ├── .gitkeep            ✅ Git (preserves folder)
│       └── */                  ❌ NOT in Git (training logs)
│
└── integration_tests/
    └── *.py                    ✅ Git (test scripts)
```

---

## 💾 Where to Store Large Models

### Option 1: Local Storage Only (Current)
**Location:** `/Users/harry/Sheridan/Sem-5/Capstone/SheridanCapstone2026/ml-models/`

**Pros:**
- ✅ Free
- ✅ Fast access
- ✅ Private

**Cons:**
- ❌ Not shared with team
- ❌ Lost if machine fails
- ❌ Can't access from other devices

**Best for:** Solo development, quick iterations

### Option 2: Google Drive (Recommended for Teams)
**Location:** `Google Drive/SafeDrive AI/Models/`

**Setup:**
```bash
# After training completes
cp ml-models/week3_finetuning/models/best_model_improved.h5 \
   ~/Google\ Drive/SafeDrive\ AI/Models/
```

**Pros:**
- ✅ Shared with team
- ✅ Backed up automatically
- ✅ Access from anywhere
- ✅ Free (15GB)

**Cons:**
- ⚠️ Requires internet for sync

**Best for:** Team collaboration, backups

### Option 3: AWS S3 / Cloud Storage
**Best for:** Production deployment, serving models to mobile apps

---

## 🔄 How to Reproduce Models

Anyone can regenerate your models using the Git repository:

```bash
# Clone repo
git clone https://github.com/not0aag/SheridanCapstone2026.git
cd SheridanCapstone2026/ml-models/week3_finetuning

# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run training (5-6 hours)
python train_improved_model.py

# Models generated in models/ directory
ls models/
# Output: best_model_improved.h5, mobilenetv2_improved_final.h5
```

**This is why we don't need large models in Git!**

---

## 📊 Current Model Sizes

| Model | Format | Size | Git Status |
|-------|--------|------|------------|
| Week 2 - MobileNetV2 | .h5 | 26 MB | ❌ Not in Git |
| Week 2 - TFLite | .tflite | 2.4 MB | ✅ In Git |
| Week 3 - Improved (when complete) | .h5 | ~26 MB | ❌ Not in Git |
| Week 3 - TFLite (when converted) | .tflite | ~2.4 MB | ✅ Will be in Git |

---

## 🎯 Best Practices

### When Training:
1. ✅ Models save to `models/` directory (gitignored)
2. ✅ Source code auto-commits (version controlled)
3. ✅ Training logs stay local (gitignored)

### When Sharing:
1. ✅ Push source code to Git
2. ✅ Share large models via Google Drive (if needed)
3. ✅ Team can reproduce by running training scripts

### When Deploying:
1. ✅ Convert to TFLite (small, optimized)
2. ✅ Commit TFLite to Git (2-3MB is fine)
3. ✅ Integrate into mobile app

---

## ✨ Summary

**Git Repository Contains:**
- Source code to train models ✅
- Small production models (TFLite) ✅
- Documentation ✅

**Local Machine Contains:**
- Large training models (.h5) 📁
- Training logs 📁
- Training outputs 📁

**Google Drive (Optional):**
- Backups of best models ☁️
- Shared team models ☁️

**This keeps your Git repo fast and clean while preserving reproducibility!**

---

## 🔍 Quick Reference

```bash
# Check what's ignored
cat .gitignore | grep "ml-models"

# See Git-tracked ML files
git ls-files ml-models/

# Check size of committed files
git ls-files ml-models/ | xargs du -sh

# Remove accidentally committed large file
git rm --cached path/to/large/file.h5
git commit -m "chore: remove large model from git"
```

---

**Last Updated:** December 2, 2025  
**Policy:** Keep Git lean, models reproducible, production artifacts version-controlled
