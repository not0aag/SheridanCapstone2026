#!/bin/bash

# Check training status script

echo "=========================================="
echo "SafeDrive AI - Training Status Check"
echo "=========================================="
echo ""

# Check if training process is running
if pgrep -f "train_improved_model.py" > /dev/null; then
    echo "✅ Training is RUNNING"
    echo ""
    
    # Get process info
    TRAINING_PID=$(pgrep -f "train_improved_model.py")
    echo "Process ID: $TRAINING_PID"
    echo "CPU/Memory usage:"
    ps aux | grep $TRAINING_PID | grep -v grep
    echo ""
    
    # Show last 20 lines of log
    echo "Latest training output:"
    echo "----------------------------------------"
    tail -20 training_persistent.log
    echo "----------------------------------------"
    echo ""
    echo "To see live updates:"
    echo "  tail -f training_persistent.log"
    
else
    echo "❌ Training is NOT running"
    echo ""
    
    # Check if log file exists
    if [ -f "training_persistent.log" ]; then
        echo "Log file exists. Last 30 lines:"
        echo "----------------------------------------"
        tail -30 training_persistent.log
        echo "----------------------------------------"
    else
        echo "No log file found. Training hasn't been started yet."
    fi
fi

echo ""
echo "=========================================="
