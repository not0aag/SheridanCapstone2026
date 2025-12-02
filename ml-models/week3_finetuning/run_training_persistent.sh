#!/bin/bash

# SafeDrive AI - Persistent Training Script
# This will keep training even when MacBook lid is closed
# Using caffeinate to prevent sleep + nohup to persist after terminal closes

echo "=========================================="
echo "SafeDrive AI - Persistent Training"
echo "=========================================="
echo ""
echo "This training will:"
echo "  - Prevent Mac from sleeping (caffeinate)"
echo "  - Continue even if you close this terminal (nohup)"
echo "  - Take approximately 5-6 hours"
echo "  - Save all output to training_persistent.log"
echo ""
echo "You can:"
echo "  - Close your MacBook lid"
echo "  - Close this terminal"
echo "  - Let it run overnight"
echo ""
echo "To monitor progress:"
echo "  tail -f training_persistent.log"
echo ""
echo "Starting training in 3 seconds..."
sleep 3

# Activate virtual environment
source ../../safedrive_ml_env/bin/activate

# Run with caffeinate (prevents sleep) and nohup (persists after terminal closes)
nohup caffeinate -i python train_improved_model.py > training_persistent.log 2>&1 &

# Get the process ID
TRAINING_PID=$!

echo ""
echo "✅ Training started!"
echo ""
echo "Process ID: $TRAINING_PID"
echo "Log file: training_persistent.log"
echo ""
echo "To monitor:"
echo "  tail -f training_persistent.log"
echo ""
echo "To check if still running:"
echo "  ps aux | grep $TRAINING_PID"
echo ""
echo "To stop training (if needed):"
echo "  kill $TRAINING_PID"
echo ""
echo "=========================================="
echo "You can now close your MacBook lid safely!"
echo "=========================================="
