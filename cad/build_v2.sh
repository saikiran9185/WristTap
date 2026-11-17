#!/bin/zsh
# WristTap v2 (closed shells): exports every printable part, runs the virtual fit checks, renders pictures.
cd "$(dirname "$0")"
mkdir -p stl/v2 png/v2
fail=0
for p in core_base core_lid hand_base hand_lid pod_piezo pod_fsr fit_test; do
  openscad --backend=manifold -D "part=\"$p\"" --export-format=binstl -o stl/v2/$p.stl band.scad 2>&1 | grep -E "WARNING|ERROR" | sed "s/^/[$p] /"
done
echo "--- virtual fit checks (part vs. components; must be EMPTY) ---"
for c in chk_core chk_core_lid chk_hand chk_hand_lid; do
  out=$(openscad --backend=manifold -D "part=\"$c\"" -o /tmp/wt_$c.stl band.scad 2>&1)
  if echo "$out" | grep -q "top level object is empty"; then echo "PASS $c"; else echo "FAIL $c (parts overlap)"; fail=1; fi
done
for p in core_open core_inside hand_open assembly; do
  openscad --backend=manifold -D "part=\"$p\"" --render --imgsize=1400,1000 --colorscheme=Tomorrow --autocenter --viewall -o png/v2/$p.png band.scad >/dev/null 2>&1 &
done; wait
exit $fail
