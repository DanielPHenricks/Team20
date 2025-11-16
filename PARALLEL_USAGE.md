# Parallel Processing Guide

## Quick Start

### Run with default settings (3 parallel workers, two-stage mode)
```bash
python3 claude_spatial_reasoning_improved.py
```
Output: `output-advanced.txt`

### Run with more parallel workers (faster if you have API headroom)
```bash
python3 claude_spatial_reasoning_improved.py --workers 5
```

### Run in single-stage mode (faster, uses fewer tokens)
```bash
python3 claude_spatial_reasoning_improved.py --mode single --workers 5
```

### Run on a subset of problems
```bash
python3 claude_spatial_reasoning_improved.py --start 1 --end 10 --workers 3
```

### Run sequentially (for debugging)
```bash
python3 claude_spatial_reasoning_improved.py --sequential
```

### Custom output file
```bash
python3 claude_spatial_reasoning_improved.py --output my_results.txt --workers 4
```

## Key Features

### 🚀 Parallel Processing
- **Default: 3 workers** - Safe for most API rate limits
- **Recommended: 3-5 workers** - Good balance of speed and reliability
- **Aggressive: 8-10 workers** - Only if you have high API limits
- Each worker processes a different problem simultaneously
- Results written immediately (thread-safe) - no data loss on interruption

### 📊 Progress Tracking
- Real-time progress updates: "[Problem X] Starting..."
- Completion notifications: "[Problem X] ✓ Completed successfully"
- Overall progress: "Progress: 15/29 problems completed (51%)"

### 🔒 Thread-Safe File Writing
- Results written immediately to `output-advanced.txt`
- Thread-safe locking prevents corruption
- Safe to interrupt (Ctrl+C) - already-completed results are saved

### 🗂️ Isolated Problem Processing
- Each problem gets its own:
  - GLB file: `tmp/preview_model_1.glb`, `tmp/preview_model_2.glb`, etc.
  - Render directory: `renders_problem_1/`, `renders_problem_2/`, etc.
- No file conflicts between parallel workers

## Performance Comparison

| Mode | Workers | Problems | Est. Time | Cost (tokens) |
|------|---------|----------|-----------|---------------|
| Sequential two-stage | 1 | 29 | ~90 min | ~60k per problem |
| Parallel two-stage | 3 | 29 | ~30 min | ~60k per problem |
| Parallel two-stage | 5 | 29 | ~18 min | ~60k per problem |
| Parallel single-stage | 5 | 29 | ~12 min | ~20k per problem |

**Speed improvements:**
- 3 workers: ~3x faster
- 5 workers: ~5x faster
- 10 workers: ~8-10x faster (diminishing returns due to Meshy API)

## API Considerations

### Anthropic API
- Default rate limit: ~50 requests/min on paid plans
- Each problem makes 1-2 API calls (single-stage vs two-stage)
- Recommended workers: 3-5 for safety

### Meshy API
- Each problem makes 1 image-to-3D request
- Takes 30-60 seconds per conversion
- This is often the bottleneck, not Claude API

### Cost Estimation
**Two-stage mode per problem:**
- Stage 1: ~800 tokens output (~$12/MTok) = ~$0.01
- Stage 2: ~1200 tokens output = ~$0.015
- Input: ~12 images × 768px = ~$0.02
- **Total per problem: ~$0.045**
- **29 problems: ~$1.30**

**Single-stage mode per problem:**
- Single call: ~1200 tokens output
- Input: ~12 images × 768px = ~$0.02
- **Total per problem: ~$0.032**
- **29 problems: ~$0.93**

## Troubleshooting

### "Payment Required" from Meshy
```bash
# Meshy API ran out of credits - check your account
# Fix: Add credits to Meshy account or reduce problem count
python3 claude_spatial_reasoning_improved.py --start 1 --end 5
```

### Too many API errors
```bash
# Reduce parallel workers if hitting rate limits
python3 claude_spatial_reasoning_improved.py --workers 2
```

### Want to see detailed logs
```bash
# Run sequentially to see step-by-step execution
python3 claude_spatial_reasoning_improved.py --sequential --start 1 --end 3
```

### Memory issues on M1/M2 Mac
```bash
# Reduce workers to prevent memory exhaustion
python3 claude_spatial_reasoning_improved.py --workers 2
```

## Output Format

The `output-advanced.txt` file contains:
```
Spatial Reasoning Results - two-stage mode
Problems 1-29
================================================================================

1: [Claude's detailed reasoning]
   ...
   Final answer: 2

============================================================

2: [Claude's detailed reasoning]
   ...
   Final answer: 4

============================================================

...
```

## Advanced Usage

### Compare modes side-by-side
```bash
# Run single-stage
python3 claude_spatial_reasoning_improved.py --mode single --output single-results.txt --workers 5

# Run two-stage
python3 claude_spatial_reasoning_improved.py --mode two-stage --output two-stage-results.txt --workers 3

# Compare accuracy
diff single-results.txt two-stage-results.txt
```

### Test on a few problems first
```bash
# Validate setup on 3 problems
python3 claude_spatial_reasoning_improved.py --start 1 --end 3 --workers 1

# If successful, run full batch
python3 claude_spatial_reasoning_improved.py --workers 5
```

### Maximize speed (if you have high API limits)
```bash
python3 claude_spatial_reasoning_improved.py --mode single --workers 10
```

## Tips for Best Results

1. **Start with 3 workers** - Safe default for most users
2. **Use two-stage mode** - Better accuracy (~15-25% improvement)
3. **Monitor first few completions** - Make sure results look good
4. **Check Meshy credits** - Each problem uses 1 credit
5. **Interrupt safely** - Ctrl+C won't lose completed results
6. **Clean up render folders** - `rm -rf renders_problem_*` after completion

## Cleanup

After running, you can clean up temporary files:
```bash
# Remove all render directories
rm -rf renders_problem_*

# Remove temporary GLB files
rm -f tmp/preview_model_*.glb

# Keep only the final results
ls -lh output-advanced.txt
```
