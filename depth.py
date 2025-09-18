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
from contextlib import chdir
from pathlib import Path
import subprocess
import sys

# Note, the executables have dependencies in the depth_anything conda environment.

parser = argparse.ArgumentParser(description="Compute depth images using Depth-Anything-V2.")
parser.add_argument("data", help="Data root path.", type=Path)
parser.add_argument("--da2", help="Depth-Anything-V2 root path.", type=Path)
parser.add_argument("--images", "-i", help="Input images directory path (default: <data>\\images).", type=Path)
parser.add_argument("--depths", "-d", help="Output depth images directory path (default: <data>\\depths).", type=Path)
parser.add_argument("--force", help="Force recomputing the depth images.", action='store_true')

args = parser.parse_args()

if not args.images:
    args.images = args.data / "images"
if not args.depths:
    args.depths = args.data / "depths"
if not args.images.exists() or not args.images.is_dir():
    print(f"Input directory {args.images} is not a directory.")
    sys.exit()

# If the depths directory is empty, compute the depth images.
depths_empty = True
for image in (args.depths).glob("*.png"):
    depths_empty = False
    break
if args.force or depths_empty:
    print("Computing depth images using Depth-Anything-V2...")
    if not args.da2 or not (args.da2 / "run.py").exists():
        print("Missing path to Depth-Anything-V2 run.py script.")
        sys.exit()

    process = [ "python", "run.py", "--encoder", "vitl", "--pred-only", "--grayscale", "--img-path", f"{args.images}", "--outdir", f"{args.depths}"]
    print(f"Calling: {process}")
    print(f"from {args.da2}")
    with chdir(args.da2):
        subprocess.run(process)
        print("")

print("depths DONE")
print("")
