#!/usr/bin/env bash
# Measures UnixFS block counts for fixed-size chunking with kubo.
# Usage: IPFS_BIN=/path/to/ipfs ./measure_blocks.sh > blocks.csv
# One fresh, empty, offline repository per configuration.
set -euo pipefail
IPFS=${IPFS_BIN:-ipfs}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
SIZES="102400 1048576 10485760 104857600 1073741824"      # 100 KiB .. 1 GiB
CHUNKS="65536 131072 262144 524288 1048576"               # 64 KiB .. 1 MiB
echo "file_bytes,chunk_bytes,blocks_refs,blocks_flatfs,leaves,interior,max_block_bytes,total_block_bytes,ok"
for S in $SIZES; do
  head -c "$S" /dev/urandom > "$WORK/f.bin"
  for C in $CHUNKS; do
    export IPFS_PATH="$WORK/repo"; rm -rf "$IPFS_PATH"
    "$IPFS" init -e >/dev/null 2>&1
    base=$(find "$IPFS_PATH/blocks" -name '*.data' | wc -l)
    if CID=$("$IPFS" add -Q --offline --pin=false --chunker=size-$C "$WORK/f.bin" 2>"$WORK/err"); then
      refs=$(( $("$IPFS" refs -r -u --offline "$CID" | wc -l) + 1 ))
      fs=$(( $(find "$IPFS_PATH/blocks" -name '*.data' | wc -l) - base ))
      leaves=$(( (S + C - 1) / C ))
      maxb=$(find "$IPFS_PATH/blocks" -name '*.data' -printf '%s\n' | sort -n | tail -1)
      tot=$(find "$IPFS_PATH/blocks" -name '*.data' -newer "$WORK/f.bin" -printf '%s\n' | awk '{s+=$1} END{print s+0}')
      echo "$S,$C,$refs,$fs,$leaves,$(( refs - leaves )),$maxb,$tot,1"
    else
      echo "$S,$C,,,,,,,0  # $(tr '\n' ' ' < "$WORK/err")"
    fi
  done
done
