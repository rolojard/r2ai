#!/bin/bash

# Memory monitoring for R2D2 project
while true; do
    echo "=== Memory Status $(date) ==="
    free -h
    echo ""
    echo "Top Memory Consumers:"
    ps aux --sort=-%mem | head -10
    echo ""
    echo "Claude Processes:"
    pgrep -f claude | xargs -I {} ps -p {} -o pid,ppid,%cpu,%mem,cmd 2>/dev/null || echo "No Claude processes running"
    echo ""
    sleep 30
done
