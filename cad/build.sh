#!/bin/zsh
# Builds every printable part, runs the virtual fit checks and renders preview pictures.
cd "$(dirname "$0")"
mkdir -p stl png
fail=0
for p in fit_test pod_top pod_piezo pod_combo hand_plate carrier; do
  openscad --backend=manifold -D "part=\"$p\"" --export-format=binstl -o stl/$p.stl wristtap.scad 2>&1 | grep -E "WARNING|ERROR|CHECK" | sort -u | sed "s/^/[$p] /"
done
echo "--- virtual fit checks (part vs. components; must be EMPTY) ---"
for c in chk_pod_top chk_pod_piezo chk_pod_combo chk_hand chk_carrier; do
  out=$(openscad --backend=manifold -D "part=\"$c\"" -o /tmp/wt_$c.stl wristtap.scad 2>&1)
  if echo "$out" | grep -q "top level object is empty"; then echo "PASS $c"; else echo "FAIL $c (parts overlap)"; fail=1; fi
done
for p in assembly pod_top pod_piezo pod_combo hand_plate carrier fit_test; do
  openscad --backend=manifold -D "part=\"$p\"" --render --imgsize=1200,900 --colorscheme=Tomorrow --autocenter --viewall $( [ $p = assembly ] && echo "--camera=0,-20,0,62,0,215,420" ) -o png/$p.png wristtap.scad >/dev/null 2>&1
done
# pack the STLs into one JS file so the guide's 3D viewer works when opened straight from Finder
python3 - <<'PY'
import base64, json, os
names = ["fit_test","pod_top","pod_piezo","pod_combo","hand_plate","carrier"]
data = {n: base64.b64encode(open(f"stl/{n}.stl","rb").read()).decode() for n in names}
open("models.js","w").write("window.WT_MODELS=" + json.dumps(data) + ";\n")
print("models.js", os.path.getsize("models.js")//1024, "KB")
PY
exit $fail
