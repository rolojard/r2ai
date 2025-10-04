# Dashboard Performance Optimization Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        R2-D2 Vision Dashboard                             │
│                      Performance-Optimized System                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          Browser Frontend                                 │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     Performance Monitor                            │  │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐    │  │
│  │  │ FPS  │  │Variance│ │Latency│ │Queue │ │Dropped│ │Target│    │  │
│  │  │ 15.2 │  │  7.3%  │ │ 28ms │ │  1   │ │  12  │ │ 15.0 │    │  │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘    │  │
│  │           [Green]    [Green]    [Green]   [Green]   [Green]      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                   Adaptive Frame Rate Controller                  │  │
│  │                                                                     │  │
│  │  Monitors: Frame Variance                                         │  │
│  │  ├─ High Variance (>15%) → Reduce FPS by 10%                     │  │
│  │  ├─ Low Variance (<7.5%) → Increase FPS by 10%                   │  │
│  │  └─ Target Range: 5-30 FPS                                        │  │
│  │                                                                     │  │
│  │  Frame Timestamps [Circular Buffer - 30 frames]                   │  │
│  │  ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐│  │
│  │  │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ ││  │
│  │  └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘│  │
│  │         ↓                                                          │  │
│  │  Calculate: FPS, Variance, Adjust Target                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                   WebSocket Message Queue                         │  │
│  │                                                                     │  │
│  │  Incoming Messages [Max 10]                                       │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐                              │  │
│  │  │Message │→ │Message │→ │Message │ → requestAnimationFrame()    │  │
│  │  │  + ts  │  │  + ts  │  │  + ts  │    Processing                │  │
│  │  └────────┘  └────────┘  └────────┘                              │  │
│  │       ↓            ↓            ↓                                  │  │
│  │  [Latency Tracking: process_time - receive_time]                 │  │
│  │                                                                     │  │
│  │  Overflow Protection: Drop oldest if queue > 10                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              WebSocket Connection Manager                          │  │
│  │                                                                     │  │
│  │  Connection State Machine:                                         │  │
│  │  ┌──────────┐    open    ┌──────────┐   heartbeat   ┌─────────┐ │  │
│  │  │Connecting│──────────→ │Connected │──────────────→│ Healthy │ │  │
│  │  └──────────┘            └──────────┘               └─────────┘ │  │
│  │       ↑                        │                          │       │  │
│  │       │                      close                     missed     │  │
│  │       │                        ↓                      heartbeat   │  │
│  │  ┌──────────┐  backoff   ┌──────────┐                   ↓       │  │
│  │  │Reconnect │←───────────│Disconn.  │←──────────────────┘       │  │
│  │  │ Timer    │            └──────────┘                            │  │
│  │  └──────────┘                                                     │  │
│  │                                                                     │  │
│  │  Exponential Backoff Schedule:                                    │  │
│  │  Attempt 1: 1s → 2: 2s → 3: 4s → 4: 8s → 5: 16s → 6+: 30s       │  │
│  │                                                                     │  │
│  │  Heartbeat Monitor:                                               │  │
│  │  ├─ Send ping every 5 seconds                                     │  │
│  │  ├─ Track last heartbeat timestamp                                │  │
│  │  ├─ Detect stale connection (>10s no response)                    │  │
│  │  └─ Force reconnect after 3 missed heartbeats                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    VisionManager Enhanced                          │  │
│  │                                                                     │  │
│  │  Frame Processing Pipeline:                                        │  │
│  │  ┌──────────────┐                                                  │  │
│  │  │ Frame Arrives│                                                  │  │
│  │  └──────┬───────┘                                                  │  │
│  │         ↓                                                           │  │
│  │  ┌─────────────────┐     YES                                       │  │
│  │  │Time since last  │─────────→ Skip (Drop Frame)                  │  │
│  │  │< Target Interval│           Increment Drop Counter             │  │
│  │  └────────┬────────┘                                               │  │
│  │         NO↓                                                         │  │
│  │  ┌─────────────────┐                                               │  │
│  │  │Pending Update?  │─────YES──→ Skip (Drop Frame)                 │  │
│  │  └────────┬────────┘                                               │  │
│  │         NO↓                                                         │  │
│  │  ┌─────────────────┐                                               │  │
│  │  │Record Timestamp │→ Add to circular buffer                       │  │
│  │  └────────┬────────┘                                               │  │
│  │           ↓                                                         │  │
│  │  ┌─────────────────┐                                               │  │
│  │  │Update Video Feed│→ requestAnimationFrame                        │  │
│  │  └────────┬────────┘                                               │  │
│  │           ↓                                                         │  │
│  │  ┌─────────────────┐                                               │  │
│  │  │Update Statistics│→ PerformanceMonitor.update()                 │  │
│  │  └─────────────────┘                                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
                                    ↕
                              WebSocket (ws://localhost:8766)
                                    ↕
┌───────────────────────────────────────────────────────────────────────┐
│                       Backend Server (Node.js)                          │
│                        dashboard-server.js                              │
│                                                                         │
│  - HTTP Server (Port 8765) - Dashboard HTML                            │
│  - WebSocket Server (Port 8766) - Real-time data                       │
│  - No modifications required for optimizations                          │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Performance Optimization Flow

### Frame Rate Adaptation Cycle

```
┌────────────────────────────────────────────────────────────┐
│                  Continuous Monitoring Loop                 │
└────────────────────────────────────────────────────────────┘
                            │
                            ↓
        ┌───────────────────────────────────┐
        │  Calculate Frame Variance         │
        │  (Standard Deviation / Mean)      │
        └───────┬───────────────────────────┘
                │
        ┌───────┴───────┐
        │               │
        ↓               ↓
┌───────────────┐  ┌────────────────┐
│ Variance >15% │  │ Variance <7.5% │
│               │  │                │
│ REDUCE FPS    │  │ INCREASE FPS   │
│ (System Load) │  │ (Good Perf)    │
└───────┬───────┘  └────────┬───────┘
        │                   │
        ↓                   ↓
    FPS × 0.9           FPS × 1.1
    (max: 5)            (max: 30)
        │                   │
        └────────┬──────────┘
                 ↓
        ┌─────────────────┐
        │ Update Target    │
        │ FPS Display      │
        └─────────────────┘
                 │
                 ↓
        ┌─────────────────┐
        │ Adjust Frame     │
        │ Throttle Interval│
        └─────────────────┘
```

---

## WebSocket Stability Architecture

### Reconnection State Machine

```
                    ┌─────────────┐
                    │ Application │
                    │   Start     │
                    └──────┬──────┘
                           │
                           ↓
                    ┌─────────────┐
              ┌────→│ Connecting  │←────┐
              │     └──────┬──────┘     │
              │            │            │
              │        Success         │
              │            │          Retry
              │            ↓            │
              │     ┌─────────────┐    │
              │     │  Connected  │    │
              │     └──────┬──────┘    │
              │            │            │
              │    ┌───────┴────────┐  │
              │    │                │  │
              │    ↓                ↓  │
         Heartbeat OK          Heartbeat
              │           ┌──→  Failed   │
              │           │      (3x)    │
              │           │              │
              │           │              │
          Continue   ┌────┴────┐    ┌───┴──────┐
              │      │ Missed  │    │Connection│
              │      │Heartbeat│    │  Error   │
              │      └────┬────┘    └────┬─────┘
              │           │              │
              └───────────┴──────────────┘
                           │
                           ↓
                    ┌─────────────┐
                    │Disconnected │
                    └──────┬──────┘
                           │
                           ↓
                 ┌──────────────────┐
                 │ Exponential      │
                 │ Backoff Timer    │
                 │                  │
                 │ 1s→2s→4s→8s→16s  │
                 │ →30s (max)       │
                 └────────┬─────────┘
                          │
                          └───────┐
                                  │
```

### Message Queue Processing

```
WebSocket.onmessage(event)
         │
         ↓
┌────────────────────┐
│ Add to Queue       │
│ with timestamp     │
└─────────┬──────────┘
          │
          ↓
┌────────────────────┐      ┌──────────────────┐
│ Queue.length > 10? │─YES─→│ Drop Oldest Msg  │
└─────────┬──────────┘      └──────────────────┘
          │NO
          ↓
┌────────────────────┐
│ Processing Queue?  │─YES─→ Return (already processing)
└─────────┬──────────┘
          │NO
          ↓
┌────────────────────────────────┐
│ Start Queue Processing         │
│                                │
│ Loop:                          │
│   1. Dequeue message           │
│   2. Calculate latency         │
│   3. Parse JSON                │
│   4. Handle message            │
│   5. Update queue display      │
│   6. requestAnimationFrame()   │
│   7. Process next              │
│                                │
│ Until: Queue empty             │
└────────────────────────────────┘
```

---

## Performance Metrics Calculation

### Frame Variance Calculation

```
Frame Timestamps: [t₁, t₂, t₃, ..., t₃₀]

Step 1: Calculate intervals
  intervals = [t₂-t₁, t₃-t₂, ..., t₃₀-t₂₉]

Step 2: Calculate mean interval
  μ = Σ(intervals) / n

Step 3: Calculate variance
  σ² = Σ((interval - μ)²) / n

Step 4: Calculate standard deviation
  σ = √(σ²)

Step 5: Calculate variance percentage
  variance% = (σ / μ) × 100

Example:
  If μ = 66.67ms (15 FPS ideal)
  And σ = 5ms
  Then variance% = (5 / 66.67) × 100 = 7.5%

  Result: GREEN (healthy, <10%)
```

### Actual FPS Calculation

```
Frame Timestamps: [oldest, ..., newest]

Time Difference = newest - oldest
Frame Count = timestamps.length - 1

Actual FPS = (Frame Count / Time Difference) × 1000

Example:
  30 frames over 2000ms
  FPS = (29 / 2000) × 1000 = 14.5 FPS

  Target: 15 FPS
  Deviation: 3.3%
  Result: GREEN (within 10% of target)
```

### WebSocket Latency Calculation

```
Message Receipt Time: t_receive
Message Process Time: t_process

Latency = t_process - t_receive

Example:
  Message received: 1000ms
  Message processed: 1028ms
  Latency = 28ms

  Result: GREEN (<50ms)
```

---

## Color-Coded Health Thresholds

```
┌─────────────────┬──────────┬──────────┬──────────┐
│     Metric      │  GREEN   │  YELLOW  │   RED    │
├─────────────────┼──────────┼──────────┼──────────┤
│ Actual FPS      │  ≥90%    │  70-90%  │  <70%    │
│ Frame Variance  │  <10%    │  10-15%  │  >15%    │
│ WS Latency      │  <50ms   │  50-100  │  >100ms  │
│ Message Queue   │  <3      │  3-7     │  ≥7      │
│ Dropped Frames  │  <10     │  10-50   │  >50     │
└─────────────────┴──────────┴──────────┴──────────┘

WebSocket Health Indicator:
  🟢 GREEN  = All metrics green OR variance <10% AND queue <3 AND latency <50ms
  🟡 YELLOW = Any metric yellow OR variance 10-20% OR queue 3-7 OR latency 50-150ms
  🔴 RED    = Disconnected OR any metric red OR variance >20% OR queue ≥7 OR latency >150ms
```

---

## Module Interaction Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    DashboardState                        │
│  (Central State Management)                             │
│                                                          │
│  • performanceMonitor { }                               │
│  • adaptiveFrameRate { }                                │
│  • dashboardWs, visionWs                                │
│  • detectionStats { }                                   │
└────────┬────────────────────────────────────────────────┘
         │
    ┌────┴────┬────────────┬────────────┬──────────────┐
    │         │            │            │              │
    ↓         ↓            ↓            ↓              ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐ ┌───────────────┐
│WebSocket│ │Vision  │ │Message │ │Character│ │UI Manager     │
│Manager │ │Manager │ │Handler │ │Manager  │ │               │
└────┬───┘ └───┬────┘ └───┬────┘ └────┬────┘ └───────┬───────┘
     │         │           │           │              │
     │         │           │           │              │
     └─────────┴───────────┴───────────┴──────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │Performance    │
                    │Monitor        │
                    │               │
                    │ • recordFrame │
                    │ • updateMetrics│
                    │ • adjustFPS   │
                    │ • updateUI    │
                    └───────────────┘
```

---

## Data Flow: Frame Reception to Display

```
1. Backend sends frame via WebSocket
           ↓
2. WebSocket.onmessage() triggered
           ↓
3. Add to message queue with timestamp
           ↓
4. Queue processor activated (requestAnimationFrame)
           ↓
5. Dequeue message, calculate latency
           ↓
6. MessageHandler.handleVisionMessage()
           ↓
7. VisionManager.updateVisionDisplay()
           ↓
8. Check adaptive frame rate throttle
           ↓
   ┌───────┴────────┐
   │                │
   ↓                ↓
 SKIP          PROCESS
(Drop)         Frame
   │                │
   │                ↓
   │     PerformanceMonitor.recordFrameTimestamp()
   │                │
   │                ↓
   │     Calculate FPS, variance
   │                │
   │                ↓
   │     Adjust target FPS if needed
   │                │
   │                ↓
   │     VisionManager.updateVideoFrame()
   │                │
   │                ↓
   │     requestAnimationFrame() → Update <img> src
   │                │
   │                ↓
   │     PerformanceMonitor.updateUI()
   │                │
   └────────────────┴────→ Display updated metrics
```

---

## Performance Optimization Decision Tree

```
                    ┌─────────────────┐
                    │ Frame Received  │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
            ┌───────▼──────┐   ┌─────▼─────┐
            │Pending Update│   │Time Since │
            │ = true?      │   │Last < Thr?│
            └───────┬──────┘   └─────┬─────┘
                    │                │
                   YES              YES
                    │                │
                    └────────┬───────┘
                             │
                             ↓
                    ┌─────────────────┐
                    │  DROP FRAME     │
                    │  droppedFrames++│
                    └─────────────────┘

                            NO
                             │
                    ┌────────▼────────┐
                    │  PROCESS FRAME  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │Record Timestamp │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │Calculate Metrics│
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
            ┌───────▼──────┐   ┌─────▼─────┐
            │Variance >15% │   │Variance    │
            │              │   │<7.5%       │
            └───────┬──────┘   └─────┬─────┘
                    │                │
                   YES              YES
                    │                │
            ┌───────▼──────┐   ┌─────▼─────┐
            │Reduce FPS    │   │Increase FPS│
            │Target × 0.9  │   │Target × 1.1│
            └───────┬──────┘   └─────┬─────┘
                    │                │
                    └────────┬───────┘
                             │
                    ┌────────▼────────┐
                    │  Update Display │
                    └─────────────────┘
```

---

**Architecture Version**: 1.0
**Date**: 2025-10-04
**Status**: Implemented and Ready for Testing
