# ipfs-request-amplification

Measurement scripts and data for the paper:

**The Request Amplification Floor in Object-Store-Backed IPFS**
Diyath Sahan Rajapakshe and Shanika Hansani Kithulgodage
8th IEEE International Conference on Advancements in Computing (ICAC 2026), paper 832.

The paper shows that when InterPlanetary File System (IPFS) blocks are stored one per object in a commercial object store, the cost is governed by the number of blocks, not by the number of bytes. This repository contains everything needed to reproduce the block counts, the cost tables, the packing analysis and the figure.

## Contents

| File | Purpose |
|---|---|
| `measure_blocks.sh` | Adds random files to a fresh, offline kubo repository at each chunk size and counts the resulting blocks. |
| `blocks_measured.csv` | The output of `measure_blocks.sh` used in the paper (kubo v0.30.0). |
| `compute_tables.py` | Reproduces Tables III, IV and V and Fig. 1 from the measured counts and published list prices. |
| `fig_tradeoff.pdf` | Fig. 1 as it appears in the paper. |

## Requirements

- kubo v0.30.0 (`ipfs` binary). Download it from https://github.com/ipfs/kubo/releases/tag/v0.30.0
- bash, coreutils, findutils and awk
- Python 3.8 or later with matplotlib (only for `compute_tables.py`)
- About 2.5 GB of free disk space in the temporary directory

No network access, cloud account or running IPFS daemon is needed. Every measurement is offline.

## Reproducing the measurements (Tables I and II)

```bash
IPFS_BIN=/path/to/ipfs ./measure_blocks.sh > blocks.csv
```

The script measures five file sizes (100 KiB, 1 MiB, 10 MiB, 100 MiB, 1 GiB) at five chunk sizes (64 KiB, 128 KiB, 256 KiB, 512 KiB, 1 MiB). It takes about one minute.

For each configuration it:

1. creates an empty repository with `ipfs init -e`;
2. adds a file of random bytes with `ipfs add -Q --offline --pin=false --chunker=size-N`;
3. counts blocks by enumerating the directed acyclic graph with `ipfs refs -r -u` and adding the root;
4. counts block files in the flatfs store as a cross-check.

All other import settings are the kubo defaults (version 0 content identifiers, raw leaves disabled, balanced layout).

Block counts are deterministic for a given file size and chunk size, so your `blocks.csv` should match `blocks_measured.csv` in every column except `total_block_bytes` and `max_block_bytes`, which are also expected to match because they depend only on sizes.

### CSV columns

| Column | Meaning |
|---|---|
| `file_bytes` | Size of the input file |
| `chunk_bytes` | Chunker setting |
| `blocks_refs` | Blocks in the graph, counted with `ipfs refs` plus the root. This is the count used in the paper. |
| `blocks_flatfs` | New block files in the repository after the add |
| `leaves` | Ceiling of `file_bytes / chunk_bytes` |
| `interior` | `blocks_refs` minus `leaves` |
| `max_block_bytes` | Largest block file |
| `total_block_bytes` | Sum of block file sizes written by the add |
| `ok` | 1 if the add succeeded, 0 if kubo rejected it |

### The 1 MiB cap

kubo rejects chunk sizes above 1 MiB. To see this:

```bash
ipfs add --offline --chunker=size-2097152 somefile
# Error: chunker parameters may not exceed the maximum chunk size of 1048576
```

## Reproducing the cost and packing tables (Tables III to V, Fig. 1)

```bash
python3 compute_tables.py
```

This prints the three tables and writes `fig_tradeoff.pdf`. The measured block counts are constants at the top of the script, so edit them there if you repeat the measurement with different sizes.

## Prices used

The monetary figures are modelled from published list prices. They are not billed amounts.

| Item | Price | Source |
|---|---|---|
| Amazon S3 Standard storage | $0.023 per GB-month | https://aws.amazon.com/s3/pricing/ |
| Amazon S3 PUT request | $0.005 per 1,000 | same |
| Google Cloud Storage Standard storage, single region | $0.020 per GB-month | https://cloud.google.com/storage/pricing |
| Google Cloud Storage Class A operation | $0.005 per 1,000 | same |

Both providers define one gigabyte of storage as 2^30 bytes, so these prices apply per gibibyte. Prices were checked on 12 November 2026 and may have changed since.

## Limits

- No latency is measured, and nothing is run against a live object store.
- The packing results are computed from the measured block counts. They do not come from a working packed datastore.
- Files are incompressible random data with fixed-size chunking. Content-defined chunking and directories of many small files are not covered.

## Citation

```bibtex
@inproceedings{rajapakshe2026amplification,
  author    = {Rajapakshe, Diyath Sahan and Kithulgodage, Shanika Hansani},
  title     = {The Request Amplification Floor in Object-Store-Backed {IPFS}},
  booktitle = {Proc. 8th IEEE International Conference on Advancements in Computing (ICAC)},
  year      = {2026}
}
```

Page numbers and the DOI will be added once the proceedings are published.

## Licence

Released under the MIT License. See the `LICENSE` file for the full text.
