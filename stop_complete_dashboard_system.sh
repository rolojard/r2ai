#!/bin/bash
# Stop Complete R2D2 Dashboard System

echo "🛑 Stopping Complete R2D2 Dashboard System..."
echo "=============================================="
echo ""

cd /home/rolo/r2ai

echo "Step 1: Stopping Dashboard Server..."
./stop_dashboard.sh
echo ""

echo "Step 2: Stopping Vision System..."
./stop_vision_system.sh
echo ""

echo "✅ Complete dashboard system stopped"
