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
import configparser
from pathlib import Path
import subprocess
import sys

# Note, the executables have dependencies in the gaussian_splatting conda environment.

parser = argparse.ArgumentParser(description="Compute Gaussian splats using 3DGS.")
parser.add_argument("config", help="Config file path.", type=Path)
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(args.config)

gs_dir = Path(config["software"].get("gaussian_splatting_root_dir"))

data = config["data"]
data_dir = Path(data.get("root_dir"))
sparse_dir = Path(data.get("sparse_dir", data_dir / "sparse" / "0"))
depths_dir = Path(data.get("depths_dir", data_dir / "depths"))
splats_dir = Path(data.get("splats_dir", data_dir / "splats"))

depths = config["depths"]
depths_force = depths.getboolean("force", False)

splats = config["splats"]
train_exposure = splats.getboolean("train_exposure", False)
splats_force = splats.getboolean("force", False)


if not splats_dir.exists():
    splats_dir.mkdir(parents=True)
if not sparse_dir.is_dir():
    print(f"Input SfM directory {sparse_dir} not found.")
    sys.exit()
if not (sparse_dir / "cameras.bin").exists() or \
        not (sparse_dir / "images.bin").exists() or \
        not (sparse_dir / "points3D.bin").exists():
    print(f"Input SfM files not found in {sparse_dir}.")
    sys.exit()

# If there are depth images without a params file, compute it.
depths_empty = True
for image in depths_dir.rglob("*.png"):
    depths_empty = False
    break
if not depths_empty and (depths_force or not (sparse_dir / "depth_params.json").exists()):
    print(f"Depth images found in {depths_dir}: computing params file...")

    process = ["python", f"{(gs_dir / 'utils' / 'make_depth_scale.py').resolve()}", "--base_dir", f"{data_dir}", "--depths_dir", f"{depths_dir}"]
    process_str = " ".join(process)
    print(f"Calling: {process_str}")
    subprocess.run(process)
    print("")

# If no 3D Gaussian splats exist, compute them.
if splats_force or not (splats_dir / "point_cloud" / "iteration_30000" / "point_cloud.ply").exists():
    print("Computing Gaussian splats using 3DGS...")
    if not gs_dir or not (gs_dir / "train.py").exists():
        print("Missing path to Gaussian Splatting convert.py script.")
        sys.exit()

    process = ["python", f"{(gs_dir / 'train.py').resolve()}", "--optimizer_type", "sparse_adam", "--source_path", f"{data_dir}", "--model_path", f"{splats_dir}"]
    if train_exposure:
        process.extend(["--exposure_lr_init", "0.001", "--exposure_lr_final", "0.0001", "--exposure_lr_delay_steps", "5000", "--exposure_lr_delay_mult", "0.001", "--train_test_exp"])
    if not depths_empty and (sparse_dir / "depth_params.json").exists():
        process.extend(["--depths", f"{depths_dir}"])
    process_str = " ".join(process)
    print(f"Calling: {process_str}")
    subprocess.run(process)
    print("")

print("splats DONE")
print("")
