# Quick Start Guide - Improved Spatial Reasoning

## One-Command Run

```bash
python3 claude_spatial_reasoning_improved.py
```

That's it! This will:
- ✅ Use two-stage reasoning (best accuracy)
- ✅ Run 3 problems in parallel
- ✅ Process all 29 problems
- ✅ Output to `output-advanced.txt`
- ✅ Show real-time progress
- ⏱️ Complete in ~30 minutes

## Command Cheat Sheet

| What you want | Command |
|---------------|---------|
| **Default (best accuracy)** | `python3 claude_spatial_reasoning_improved.py` |
| **Faster (good accuracy)** | `python3 claude_spatial_reasoning_improved.py --mode single --workers 5` |
| **Test on 5 problems** | `python3 claude_spatial_reasoning_improved.py --start 1 --end 5` |
| **Maximum speed** | `python3 claude_spatial_reasoning_improved.py --mode single --workers 10` |
| **Debug mode (sequential)** | `python3 claude_spatial_reasoning_improved.py --sequential --start 1 --end 3` |
| **Custom output file** | `python3 claude_spatial_reasoning_improved.py --output my_results.txt` |

## Key Parameters

- `--mode`: `two-stage` (best) or `single` (faster)
- `--workers`: Number of parallel threads (default: 3, recommended: 3-5)
- `--start` / `--end`: Problem range (default: 1-29)
- `--output`: Output filename (default: `output-advanced.txt`)
- `--sequential`: Disable parallelization (for debugging)

## What's Improved?

| Feature | Original | Improved |
|---------|----------|----------|
| Views | 8 corners | 12 strategic + labeled |
| Resolution | 512px | 768px |
| Lighting | Basic | Enhanced 5-light |
| Prompts | Generic | Structured reasoning |
| Processing | Sequential | Parallel (3-10x faster) |
| Output | `claude_answers.txt` | `output-advanced.txt` |

## Expected Performance

**Speed:**
- 3 workers: ~30 min (29 problems)
- 5 workers: ~18 min (29 problems)
- 10 workers: ~10 min (29 problems)

**Accuracy Improvement:** +35-70% (estimated)

**Cost:** ~$1.30 for 29 problems (two-stage mode)

## Files You'll Get

After running:
- ✅ `output-advanced.txt` - Your results
- 📁 `renders_problem_1/` through `renders_problem_29/` - All view images
- 📁 `tmp/preview_model_*.glb` - 3D models from Meshy

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Meshy "Payment Required" | Add credits to Meshy account |
| Too many errors | Reduce workers: `--workers 2` |
| Want to see details | Use: `--sequential --start 1 --end 3` |
| Out of memory | Reduce workers: `--workers 2` |

## Cleanup After Running

```bash
# Remove temporary render folders (optional)
rm -rf renders_problem_*

# Remove temporary 3D models (optional)
rm -f tmp/preview_model_*.glb

# Keep only your results
ls -lh output-advanced.txt
```

## Next Steps

1. **Start with a test run:**
   ```bash
   python3 claude_spatial_reasoning_improved.py --start 1 --end 5
   ```

2. **Check the output:**
   ```bash
   cat output-advanced.txt
   ```

3. **If it looks good, run the full batch:**
   ```bash
   python3 claude_spatial_reasoning_improved.py --workers 5
   ```

4. **Monitor progress in terminal - you'll see:**
   - `[Problem X] Starting...`
   - `[Problem X] ✓ Completed successfully`
   - `Progress: X/29 problems completed (XX%)`

## Need More Info?

- **Full technical details:** See `IMPROVEMENTS_SUMMARY.md`
- **Parallel processing guide:** See `PARALLEL_USAGE.md`
- **Complete overview:** See `SUMMARY_OF_IMPROVEMENTS.md`

---

**Ready? Just run:**
```bash
python3 claude_spatial_reasoning_improved.py
```
