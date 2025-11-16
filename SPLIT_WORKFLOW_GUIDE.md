# Split Workflow Guide

## Overview

The system is now split into two separate steps:
1. **GLB Generation** - Convert 2D images to 3D models (using `generate_glb_files.py`)
2. **Claude Reasoning** - Solve puzzles using the 3D models (using `claude_spatial_reasoning_improved.py`)

This separation allows you to:
- ✅ Generate all GLB files at once (can run overnight)
- ✅ Experiment with different prompts without regenerating GLBs
- ✅ Resume interrupted processes more easily
- ✅ Save API costs by reusing GLB files

## Two Workflow Options

### Option 1: Two-Step Workflow (Recommended)

**Step 1: Generate all GLB files first**
```bash
python3 generate_glb_files.py
```
This will:
- Process problems 1-29 by default
- Create GLB files: `tmp/preview_model_problem_1.glb`, etc.
- Skip files that already exist
- Take ~30-90 minutes depending on Meshy API speed

**Step 2: Run Claude reasoning with existing GLBs**
```bash
python3 claude_spatial_reasoning_improved.py --skip-glb
```
This will:
- Use the pre-generated GLB files
- Only call Claude API (no Meshy API calls)
- Much faster since GLB generation is skipped

**Benefits:**
- Can regenerate GLB files independently if needed
- Can rerun reasoning with different prompts without waiting for Meshy
- Can interrupt and resume more easily

### Option 2: All-in-One Workflow (Original)

```bash
python3 claude_spatial_reasoning_improved.py
```
This will:
- Generate GLB files on-the-fly as needed
- Immediately proceed to Claude reasoning
- Works like the original script

**When to use:**
- First-time run with no existing GLB files
- Processing a small subset of problems
- Don't want to manage two separate scripts

## generate_glb_files.py - Detailed Usage

### Basic Commands

```bash
# Generate all GLB files (problems 1-29)
python3 generate_glb_files.py

# Generate specific range
python3 generate_glb_files.py --start 1 --end 10

# Generate single problem
python3 generate_glb_files.py --start 5 --end 5

# Force regeneration (delete and recreate existing files)
python3 generate_glb_files.py --force

# Custom input/output directories
python3 generate_glb_files.py --input ./my_images --output ./my_models
```

### Features

**1. Smart Skip Logic**
- Automatically skips problems that already have GLB files
- Shows file size for existing files
- Deletes and regenerates if `--force` is used

**2. Progress Tracking**
```
[1/29] Problem 1
------------------------------------------------------------
Processing: ./screenshots/cropped/1.png -> ./tmp/preview_model_problem_1.glb
  Submitting to Meshy API...
  Task ID: 019a8b34-cde6-733b-85b0-6f98c695408d
  Status: PROCESSING | Progress: 45% | Waiting 5 seconds...
  ✓ Preview task finished.
  ✓ Saved: ./tmp/preview_model_problem_1.glb (1247.3 KB)

[2/29] Problem 2
------------------------------------------------------------
  ⊙ Already exists: ./tmp/preview_model_problem_2.glb (1523.8 KB)
  Skipping (delete file to regenerate)
```

**3. Error Handling**
- Continues processing on errors
- Shows summary of failed problems at the end
- Useful error messages for HTTP errors

**4. Summary Report**
```
================================================================================
Generation Complete!
================================================================================
Successful: 27/29
Failed: 2/29

Failed problems:
  Problem 15: HTTP 402: Payment Required
  Problem 23: HTTP 402: Payment Required

GLB files saved to: ./tmp/
================================================================================
```

### Common Use Cases

**Generate all files overnight:**
```bash
# Run in background
nohup python3 generate_glb_files.py > glb_generation.log 2>&1 &

# Check progress
tail -f glb_generation.log
```

**Regenerate specific problem:**
```bash
# Delete the GLB file
rm tmp/preview_model_problem_15.glb

# Regenerate just that one
python3 generate_glb_files.py --start 15 --end 15
```

**Check what's already generated:**
```bash
# Count existing GLB files
ls tmp/preview_model_problem_*.glb | wc -l

# See which ones are missing
for i in {1..29}; do
  if [ ! -f "tmp/preview_model_problem_$i.glb" ]; then
    echo "Missing: Problem $i"
  fi
done
```

## claude_spatial_reasoning_improved.py - Updated Usage

### With Pre-Generated GLB Files (Faster)

```bash
# Use existing GLB files (no Meshy API calls)
python3 claude_spatial_reasoning_improved.py --skip-glb

# With different modes
python3 claude_spatial_reasoning_improved.py --skip-glb --mode single
python3 claude_spatial_reasoning_improved.py --skip-glb --mode two-stage

# Process specific range
python3 claude_spatial_reasoning_improved.py --skip-glb --start 1 --end 10
```

### Without Pre-Generated GLB Files (Original Behavior)

```bash
# Generate GLBs on-the-fly
python3 claude_spatial_reasoning_improved.py

# Same as above, more explicit
python3 claude_spatial_reasoning_improved.py --start 1 --end 29
```

### Error Handling

If you use `--skip-glb` but GLB files don't exist:
```
ERROR: GLB file not found: ./tmp/preview_model_problem_5.glb
Run generate_glb_files.py first or remove --skip-glb flag.
```

**Solution:** Either generate the GLB file or remove `--skip-glb` flag.

## Recommended Workflows

### Workflow 1: Initial Run (All 29 Problems)

```bash
# Step 1: Generate all GLB files (run overnight if needed)
python3 generate_glb_files.py

# Step 2: Run Claude reasoning
python3 claude_spatial_reasoning_improved.py --skip-glb
```

**Time savings:**
- GLB generation: ~30-90 minutes (one time)
- Claude reasoning: ~60-90 minutes
- **Total:** ~90-180 minutes
- **Advantage:** Can regenerate reasoning without waiting for GLBs

### Workflow 2: Test on Small Subset

```bash
# Quick test on 5 problems
python3 generate_glb_files.py --start 1 --end 5
python3 claude_spatial_reasoning_improved.py --skip-glb --start 1 --end 5
```

### Workflow 3: Experiment with Prompts

```bash
# Generate GLBs once
python3 generate_glb_files.py

# Try different prompts/modes (fast, no Meshy API calls)
python3 claude_spatial_reasoning_improved.py --skip-glb --mode single --output results_single.txt
python3 claude_spatial_reasoning_improved.py --skip-glb --mode two-stage --output results_two_stage.txt

# Compare results
diff results_single.txt results_two_stage.txt
```

### Workflow 4: Resume After Interruption

```bash
# Check which GLBs exist
ls tmp/preview_model_problem_*.glb

# Generate missing ones
python3 generate_glb_files.py --start 15 --end 29

# Run reasoning on specific range
python3 claude_spatial_reasoning_improved.py --skip-glb --start 15 --end 29
```

### Workflow 5: Regenerate Single Problem

```bash
# Something went wrong with problem 12, regenerate everything
rm tmp/preview_model_problem_12.glb
rm renders/*_problem_12.png
rm renders/annotated/*_problem_12.png

# Regenerate GLB
python3 generate_glb_files.py --start 12 --end 12

# Rerun reasoning
python3 claude_spatial_reasoning_improved.py --skip-glb --start 12 --end 12
```

## File Organization

```
Team20/
├── generate_glb_files.py          # New: GLB generation script
├── claude_spatial_reasoning_improved.py  # Updated: Now supports --skip-glb
├── render_improved.py              # Unchanged
│
├── tmp/                            # Generated GLB files
│   ├── preview_model_problem_1.glb
│   ├── preview_model_problem_2.glb
│   └── ...
│
├── renders/                        # Generated views
│   ├── view_000_problem_1.png
│   └── ...
│
└── output-advanced.txt             # Final results
```

## Benefits of Split Workflow

### 1. Faster Iteration
- Modify prompts and rerun without waiting for Meshy API
- Test different reasoning modes quickly

### 2. Cost Savings
- Don't regenerate expensive GLB files unnecessarily
- Reuse GLB files across multiple runs

### 3. Better Debugging
- Isolate issues: is it GLB generation or Claude reasoning?
- Can manually inspect GLB files before running reasoning

### 4. Easier Resumption
- If interrupted, just check which GLBs exist
- Resume from where you left off

### 5. Parallel Friendly (Future)
- Can distribute GLB generation across multiple machines
- All reasoning can use the same GLB files

## Cost Analysis

### Option 1: Two-Step Workflow
**First time:**
- GLB generation: 29 problems × Meshy cost
- Claude reasoning: 29 problems × Claude cost
- **Total:** Full cost

**Subsequent runs (with prompt changes):**
- GLB generation: $0 (reuse existing)
- Claude reasoning: 29 problems × Claude cost
- **Total:** Only Claude cost (~50% savings)

### Option 2: All-in-One Workflow
**Every run:**
- GLB generation: 29 problems × Meshy cost
- Claude reasoning: 29 problems × Claude cost
- **Total:** Full cost each time

**Conclusion:** Two-step workflow saves money if you run multiple iterations.

## Troubleshooting

### Problem: "GLB file not found" error
**Solution:**
```bash
# Generate the missing GLB
python3 generate_glb_files.py --start X --end X

# Or run without --skip-glb flag
python3 claude_spatial_reasoning_improved.py --start X --end X
```

### Problem: Meshy API returns 402 Payment Required
**Solution:** Add credits to your Meshy account, then:
```bash
# Regenerate failed GLBs
python3 generate_glb_files.py --force --start X --end Y
```

### Problem: Want to regenerate specific GLB
**Solution:**
```bash
# Delete and regenerate
rm tmp/preview_model_problem_5.glb
python3 generate_glb_files.py --start 5 --end 5
```

### Problem: Want to regenerate ALL GLBs
**Solution:**
```bash
# Force regeneration
python3 generate_glb_files.py --force
```

## Quick Reference

| Task | Command |
|------|---------|
| Generate all GLBs | `python3 generate_glb_files.py` |
| Generate GLBs 1-10 | `python3 generate_glb_files.py --start 1 --end 10` |
| Force regenerate all | `python3 generate_glb_files.py --force` |
| Run reasoning (with existing GLBs) | `python3 claude_spatial_reasoning_improved.py --skip-glb` |
| Run reasoning (generate GLBs too) | `python3 claude_spatial_reasoning_improved.py` |
| Test on 5 problems | See Workflow 2 above |
| Regenerate problem 12 | See Workflow 5 above |

---

**Recommended:** Use the two-step workflow for best flexibility and cost savings! 🚀
