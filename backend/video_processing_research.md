# Video Processing Libraries Research

## Overview
Research on video processing libraries for SafeDrive AI backend video handling.

---

## 1. FFmpeg

### What it is:
- Industry-standard multimedia framework
- Command-line tool for video/audio processing
- Supports virtually all video formats

### Key Features:
- Video compression and encoding (H.264, H.265, VP9)
- Format conversion (MP4, AVI, MOV, WebM)
- Video trimming and splitting
- Resolution scaling
- Frame extraction
- Audio extraction/manipulation

### Use Cases for SafeDrive AI:
- Compress 1080p videos from mobile to reduce storage costs
- Convert videos to H.264 format for web compatibility
- Extract 30-second clips (pre/post incident)
- Reduce file size while maintaining quality

### Python Integration:
- Library: `ffmpeg-python`
- Installation: `pip install ffmpeg-python`
- Requires FFmpeg binary installed on system

### Example Code:
```python
import ffmpeg

# Compress video to H.264
(
    ffmpeg
    .input('input.mp4')
    .output('output.mp4', vcodec='libx264', crf=23)
    .run()
)

# Extract 30-second clip
(
    ffmpeg
    .input('input.mp4', ss=30, t=30)  # Start at 30s, duration 30s
    .output('clip.mp4')
    .run()
)
```

### Pros:
- ✅ Industry standard, battle-tested
- ✅ Extremely fast
- ✅ Supports all formats
- ✅ High-quality compression

### Cons:
- ❌ Requires system binary installation
- ❌ Complex command syntax
- ❌ Steep learning curve

---

## 2. OpenCV (Open Computer Vision)

### What it is:
- Computer vision and image processing library
- Originally designed for real-time computer vision
- Includes video I/O capabilities

### Key Features:
- Read/write video files
- Frame-by-frame processing
- Image manipulation (resize, rotate, crop)
- Face detection and tracking
- Motion detection
- Video stabilization

### Use Cases for SafeDrive AI:
- Extract frames for ML analysis
- Video stabilization (gyroscope-based)
- Add overlays (timestamps, GPS coordinates)
- Quality analysis
- Frame rate conversion

### Python Integration:
- Library: `opencv-python`
- Installation: `pip install opencv-python`
- Pure Python, no external dependencies

### Example Code:
```python
import cv2

# Read video
cap = cv2.VideoCapture('input.mp4')

# Get video properties
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Process frames
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Add timestamp overlay
    cv2.putText(frame, 'SafeDrive AI', (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
cap.release()
```

### Pros:
- ✅ Frame-by-frame control
- ✅ Good for adding overlays/annotations
- ✅ Built-in image processing
- ✅ No external dependencies

### Cons:
- ❌ Slower than FFmpeg for encoding
- ❌ Limited codec support
- ❌ Not ideal for large-scale compression

---

## 3. MoviePy

### What it is:
- Python library for video editing
- Built on top of FFmpeg
- High-level, user-friendly API

### Key Features:
- Video concatenation
- Text/image overlays
- Video effects and transitions
- Audio manipulation
- GIF creation
- Simple trimming and cutting

### Use Cases for SafeDrive AI:
- Quick video editing tasks
- Prototype video processing
- Simple concatenation (multiple clips)
- Adding text overlays

### Python Integration:
- Library: `moviepy`
- Installation: `pip install moviepy`
- Requires FFmpeg binary

### Example Code:
```python
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# Load video
clip = VideoFileClip('input.mp4')

# Trim to 30 seconds
trimmed = clip.subclip(0, 30)

# Add text overlay
txt = TextClip('Incident Detected', fontsize=50, color='red')
txt = txt.set_position('center').set_duration(5)

# Composite
final = CompositeVideoClip([trimmed, txt])
final.write_videofile('output.mp4')
```

### Pros:
- ✅ Very easy to use
- ✅ Great for prototyping
- ✅ Good documentation
- ✅ Pythonic API

### Cons:
- ❌ Slower than direct FFmpeg
- ❌ Overhead for simple tasks
- ❌ Still requires FFmpeg binary

---

## Recommendation for SafeDrive AI

### Primary Tool: **FFmpeg** (via ffmpeg-python)
**Use for:**
- Video compression (H.264 encoding)
- Format conversion
- Extracting incident clips (30s pre/post)
- Production video processing pipeline

**Why:**
- Fastest performance
- Industry-standard compression
- Best quality-to-size ratio
- Required for production at scale

### Secondary Tool: **OpenCV**
**Use for:**
- Adding timestamp/GPS overlays
- Video stabilization (if needed)
- Quality analysis
- Frame extraction for ML

**Why:**
- Frame-by-frame control
- Good for metadata overlays
- No FFmpeg dependency needed

### Not Recommended: **MoviePy**
**Reason:**
- Adds unnecessary overhead
- Slower than direct FFmpeg
- Overkill for our use cases
- Better suited for creative video editing

---

## Implementation Plan

### Phase 1: Video Upload & Storage
1. Receive video from mobile app
2. Store temporarily on EC2
3. Upload to S3 (raw)

### Phase 2: Processing Pipeline
1. Use FFmpeg to compress (H.264, CRF 23)
2. Extract 30-second incident clips
3. Use OpenCV to add metadata overlay (timestamp, GPS)
4. Upload processed video to S3
5. Delete temporary files
6. Store S3 key in PostgreSQL

### Phase 3: Optimization
1. Batch processing for multiple videos
2. Parallel processing with multiprocessing
3. S3 lifecycle policies (hot → cold → glacier)

---

## Required System Setup

### Install FFmpeg Binary:

**Ubuntu/Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- Download from: https://ffmpeg.org/download.html
- Add to PATH

### Verify Installation:
```bash
ffmpeg -version
```

---

## Performance Benchmarks (Estimated)

| Task | FFmpeg | OpenCV | MoviePy |
|------|--------|--------|---------|
| Compress 1GB video | ~2 min | ~10 min | ~5 min |
| Extract 30s clip | ~5 sec | ~30 sec | ~15 sec |
| Add overlay | ~30 sec | ~10 sec | ~45 sec |
| CPU Usage | Low-Med | Medium | Med-High |

---

## Next Steps (Week 2)

1. Install FFmpeg on development machine
2. Test compression with sample videos
3. Implement basic compression POC
4. Measure actual performance
5. Design production pipeline
6. Set up S3 integration

---

## References

- FFmpeg: https://ffmpeg.org/
- ffmpeg-python: https://github.com/kkroening/ffmpeg-python
- OpenCV: https://opencv.org/
- MoviePy: https://zulko.github.io/moviepy/
