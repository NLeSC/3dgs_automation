#Copyright 2025 Netherlands eScience Center
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.


import argparse
from pathlib import Path
import subprocess
import sys

# Note, the executables have dependencies in the gaussian_splatting conda environment.

parser = argparse.ArgumentParser(description="Compute Gaussian splats using 3DGS.")
parser.add_argument("data", help="Data root path.", type=Path)
parser.add_argument("--gs", help="Gaussian Splatting root path.", type=Path)
parser.add_argument("--depths", "-d", help="Input depth images directory path (default: <data>\\depths).", type=Path)
parser.add_argument("--splats", "-s", help="Output Gaussian splats directory path (default: <data>\\splats).", type=Path)
parser.add_argument("--train_exposure", help="Train exposure settings.", action='store_true')
parser.add_argument("--force", help="Force recomputing the camera parameters.", action='store_true')

args = parser.parse_args()

if not args.depths:
    args.depths = args.data / "depths"
if not args.splats:
    args.splats = args.data / "splats"
if not args.splats.exists():
    args.splats.mkdir(parents=True)
sparse_dir = args.data / "sparse" / "0"
if not sparse_dir.exists() or not sparse_dir.is_dir():
    print(f"Input SfM directory {sparse_dir} not found.")
    sys.exit()
if not (sparse_dir / "cameras.bin").exists() or not (sparse_dir / "images.bin").exists() or not (sparse_dir / "points3D.bin").exists():
    print(f"Input SfM files not found in {sparse_dir}.")
    sys.exit()

# If there are depth images without a params file, compute it.
depths_empty = True
for image in args.depths.glob("*.png"):
    depths_empty = False
    break
if not depths_empty and (args.force or not (sparse_dir / "depth_params.json").exists()):
    print(f"Depth images found in {args.depths}: computing params file...")

    process = ["python", f"{(args.gs / 'utils' / 'make_depth_scale.py').resolve()}", "--base_dir", f"{args.data}", "--depths_dir", f"{args.depths}"]
    print(f"Calling: {process}")
    subprocess.run(process)
    print("")

# If no 3D Gaussian splats exist, compute them.
if args.force or not (args.splats / "point_cloud" / "iteration_30000" / "point_cloud.ply").exists():
    print("Computing Gaussian splats using 3DGS...")
    if not args.gs or not (args.gs / "train.py").exists():
        print("Missing path to Gaussian Splatting convert.py script.")
        sys.exit()

    process = ["python", f"{(args.gs / 'train.py').resolve()}", "--optimizer_type", "sparse_adam", "--source_path", f"{args.data}", "--model_path", f"{args.splats}"]
    if args.train_exposure:
        process.extend(["--exposure_lr_init", "0.001", "--exposure_lr_final", "0.0001", "--exposure_lr_delay_steps", "5000", "--exposure_lr_delay_mult", "0.001", "--train_test_exp"])
    if not depths_empty and (sparse_dir / "depth_params.json").exists():
        process.extend(["--depths", f"{args.depths}"])
    print(f"Calling: {process}")
    subprocess.run(process)
    print("")

print ("DONE")
