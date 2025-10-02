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
from contextlib import chdir
from pathlib import Path
import subprocess
import sys

# Note, the executables have dependencies in the depth_anything conda environment.

parser = argparse.ArgumentParser(description="Compute depth images using Depth-Anything-V2.")
parser.add_argument("config", help="Config file path.", type=Path)
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(args.config)

da_dir = Path(config["software"].get("depth_anything_root_dir"))

data = config["data"]
data_dir = Path(data.get("root_dir"))
images_dir = Path(data.get("images_dir", data_dir / "images"))
depths_dir = Path(data.get("depths_dir", data_dir / "depths"))

depths = config["depths"]
depths_force = depths.getboolean("force", False)


if not images_dir.is_dir():
    print(f"Input directory {images_dir} is not a directory.")
    sys.exit()

# If the depths directory is empty, compute the depth images.
depths_empty = True
for image in depths_dir.rglob("*.png"):
    depths_empty = False
    break
if depths_force or depths_empty:
    print("Computing depth images using Depth-Anything-V2...")
    if not da_dir or not (da_dir / "run.py").exists():
        print("Missing path to Depth-Anything-V2 run.py script.")
        sys.exit()

    image_dirs = set()
    for image in images_dir.rglob("*.jpg"):
        image_dirs.add(image.parent)
    for image_dir in image_dirs:
        outdir = depths_dir
        if len(image_dirs) > 1:
            outdir = outdir / image_dir.name
        process = [ "python", "run.py", "--encoder", "vitl", "--pred-only", "--grayscale", "--img-path", f"{image_dir}", "--outdir", f"{outdir}"]
        process_str = " ".join(process)
        print(f"Calling: {process_str}")
        print(f"from {da_dir}")
        with chdir(da_dir):
            subprocess.run(process)
            print("")

print("depths DONE")
print("")
