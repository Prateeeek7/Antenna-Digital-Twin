#!/bin/bash
# Monitor script for 1000-sample Meep FDTD training

LOG_FILE="/tmp/meep_training_1000samples.log"
echo "=== Meep FDTD Training Monitor (1000 samples) ==="
echo ""

# Check if process is running
PID=$(pgrep -f 'train_surrogate_model.py.*1000')
if [ -z "$PID" ]; then
    echo "❌ Training process not found"
    exit 1
else
    echo "✅ Training running (PID: $PID)"
fi

echo ""

# Check log file
if [ -f "$LOG_FILE" ]; then
    echo "📊 Latest Progress:"
    tail -5 "$LOG_FILE" | grep -E "Progress|Completed|simulation|Training|Error" || tail -3 "$LOG_FILE"
    echo ""
    
    # Extract progress
    completed=$(grep -o "Progress: [0-9]*/1000" "$LOG_FILE" | tail -1 | grep -o "[0-9]*" | head -1)
    if [ ! -z "$completed" ]; then
        percent=$(echo "scale=1; $completed * 100 / 1000" | bc 2>/dev/null || echo "0")
        remaining=$((1000 - completed))
        echo "📈 Progress: $completed / 1000 completed ($percent%)"
        echo "⏳ Remaining: $remaining simulations"
    fi
else
    echo "⚠️  Log file not found"
fi

echo ""

# Count results
RESULTS_DIR="/Users/pratikkumar/Desktop/Antenna Digital Twin/backend/data/em_results"
if [ -d "$RESULTS_DIR" ]; then
    count=$(find "$RESULTS_DIR" -name "results.json" 2>/dev/null | wc -l | tr -d ' ')
    echo "📁 Results files: $count"
    
    # Check for any errors
    error_count=$(find "$RESULTS_DIR" -name "*.log" -exec grep -l "Error\|Failed\|Exception" {} \; 2>/dev/null | wc -l | tr -d ' ')
    if [ "$error_count" -gt 0 ]; then
        echo "⚠️  Found $error_count log files with errors"
    fi
fi

echo ""

# Active simulation processes
sim_count=$(ps aux | grep -E "simulation.py" | grep -v grep | wc -l | tr -d ' ')
echo "🔄 Active simulations: $sim_count"

echo ""
echo "💡 Monitor live: tail -f $LOG_FILE"








