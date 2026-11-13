#!/usr/bin/env python3
"""Reproduces Tables II-IV and Fig. 1 of
"The Request Amplification Floor in Object-Store-Backed IPFS".

Inputs are the block counts measured with measure_blocks.sh (kubo v0.30.0)
and published list prices. Everything else is arithmetic.
"""
from math import ceil, comb

MIB_PER_GIB = 1024
GB_PER_GIB = 1.0   # both tariffs define 1 GB as 2**30 bytes (binary gigabyte)
PUT_PER_OP = 0.005 / 1000           # S3 PUT and GCS Class A, USD
S3_STORE_GB = 0.023                 # USD per GB-month
GCS_STORE_GB = 0.020

# Measured with measure_blocks.sh: chunk label -> total blocks
MEASURED = {"64 KiB": 1611, "128 KiB": 806, "256 KiB": 404,
            "512 KiB": 203, "1 MiB": 101}                 # 100 MiB file
MEASURED_GIB = {"64 KiB": 16480, "128 KiB": 8241, "256 KiB": 4121,
                "512 KiB": 2061, "1 MiB": 1031}           # 1 GiB file

def table2():
    s3 = S3_STORE_GB * GB_PER_GIB
    gcs = GCS_STORE_GB * GB_PER_GIB
    print("Table II  (store $/GiB-month: S3 %.4f, GCS %.4f)" % (s3, gcs))
    for k, n in MEASURED_GIB.items():
        w = n * PUT_PER_OP
        print(f"  {k:8s} {n:6d}  write ${w:.4f}  S3 {100*w/s3:6.1f}%  GCS {100*w/gcs:6.1f}%")

N = 404                              # blocks, 100 MiB at 256 KiB
def objects(K):                      # block count of each packed object
    full, rem = divmod(N, K)
    return [K] * full + ([rem] if rem else [])

def read_amp(K, R):
    """Expected blocks fetched / blocks required, for a uniformly random
    R-block subset, whole-object requests, blocks treated as equal size."""
    fetched = sum(n * (1 - comb(N - n, R) / comb(N, R)) for n in objects(K))
    return fetched / R

def table3():
    s3 = S3_STORE_GB * GB_PER_GIB
    base = MEASURED_GIB["256 KiB"]
    print("Table III")
    for K in (1, 4, 16, 32, 128):
        ops = ceil(base / K); w = ops * PUT_PER_OP
        print(f"  K={K:3d} ops/GiB {ops:5d}  write ${w:.4f}  {100*w/s3:5.1f}% of S3 month"
              f"  reduction {base/ops:5.1f}x  read amp {read_amp(K,1):6.1f}x")

def table4():
    print("Table IV")
    for K in (1, 4, 16, 32, 128):
        row = [read_amp(K, R) for R in (1, 4, 40, 202, 404)]
        print(f"  K={K:3d} " + "  ".join(f"{v:6.1f}x" for v in row))

def figure(path="fig_tradeoff.pdf"):
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42      # TrueType, never Type 3
    matplotlib.rcParams["ps.fonttype"] = 42
    matplotlib.rcParams["font.family"] = "DejaVu Serif"
    import matplotlib.pyplot as plt
    base = MEASURED_GIB["256 KiB"]
    Ks = [1, 4, 16, 32, 128]
    x = [ceil(base / K) for K in Ks]
    y = [read_amp(K, 1) for K in Ks]
    fig, ax = plt.subplots(figsize=(3.45, 2.6))
    floor = MEASURED_GIB["1 MiB"]
    ax.axvspan(10, floor, color="0.9", zorder=0)
    ax.axvline(floor, ls="--", color="0.3", lw=0.9)
    ax.plot(x, y, "o-", color="k", ms=4, lw=1.1)
    off = {1: (6, -10), 4: (6, 2), 16: (6, 2), 32: (6, 2), 128: (6, -3)}
    for K, xi, yi in zip(Ks, x, y):
        ax.annotate(f"K={K}", (xi, yi), textcoords="offset points",
                    xytext=off[K], fontsize=7,
                    ha="left")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.invert_xaxis()
    ax.set_xlim(8000, 20); ax.set_ylim(0.7, 300)
    ax.set_xlabel("Write operations per GiB (cheaper →)", fontsize=8)
    ax.set_ylabel("Read amplification\n(single block, no range)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.text(7000, 120, "chunk-size\nfloor\n(1 MiB cap)", fontsize=6.5,
            ha="left", va="center")
    ax.text(150, 1.1, "reachable only\nby packing", fontsize=6.5, ha="center")
    fig.tight_layout(pad=0.3)
    fig.savefig(path)

if __name__ == "__main__":
    table2(); table3(); table4(); figure()
    # Composition check (Section VI-B)
    b = MEASURED_GIB["256 KiB"]; print("compose:", b + ceil(b / 32), "vs", b)
    print("index: %.3f%% at 256 KiB, %.3f%% at 64 KiB" % (100*52/(262144+14), 100*52/(65536+14)))
