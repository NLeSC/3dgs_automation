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

parser = argparse.ArgumentParser(description="Compute camera parameters using Structure from Motion.")
parser.add_argument("config", help="Config file path.", type=Path)
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(args.config)

gs_dir = Path(config["software"].get("gaussian_splatting_root_dir"))

data = config["data"]
data_dir = Path(data.get("root_dir"))
video_path = Path(data.get("video_path", data_dir / "raw"))
frames_dir = Path(data.get("frames_dir", data_dir / "input"))
images_dir = Path(data.get("images_dir", data_dir / "images"))
sparse_dir = Path(data.get("sparse_dir", data_dir / "sparse" / "0"))

slice = config["slice"]
slice_fps = slice.getfloat("fps", 1.0)
slice_force = slice.getboolean("force", False)

sfm = config["sfm"]
sfm_resize = sfm.getboolean("resize", False)
sfm_force = sfm.getboolean("force", False)


if not frames_dir.exists():
    frames_dir.mkdir(parents=True)
if not frames_dir.is_dir():
    print(f"Input frames directory {frames_dir} is not a directory.")
    sys.exit()

# If the frames directory is empty, try to extract frames from a video file.
frames_empty = True
for image in frames_dir.rglob("*.jpg"):
    frames_empty = False
    break
if slice_force or frames_empty:
    videos = []
    if video_path.is_file():
        videos.append(video_path)
    elif video_path.is_dir():
        for video in video_path.glob("*.mpeg"):
            videos.append(video)
        for video in video_path.glob("*.mpg"):
            videos.append(video)
        for video in video_path.glob("*.mp4"):
            videos.append(video)
    if len(videos) == 0:
        print("Neither input frames or video file found...")
        sys.exit()

    video_str = f"video {videos[0]}" if len(videos) == 1 else f"{len(videos)} videos"
    print(f"Extracting frames from {video_str} using FFMPEG...")
    for i in range(len(videos)):
        frames_pattern = frames_dir
        if len(videos) > 1:
            frames_pattern = frames_pattern / f"{i}"
            frames_pattern.mkdir(parents=True)
        frames_pattern = frames_pattern / "%04d.jpg"
        process = ["ffmpeg", "-i", f"{videos[i]}", "-qscale:v", "1", "-qmin", "1", "-vf", f"fps={slice_fps}", f"{frames_pattern}"]
        process_str = " ".join(process)
        print(f"Calling: {process_str}")
        subprocess.run(process)
        print("")


# If the SfM output does not exist, compute it.
images_empty = True
for image in images_dir.rglob("*.jpg"):
    images_empty = False
    break
if sfm_force or images_empty or \
        not (sparse_dir / "cameras.bin").exists() or \
        not (sparse_dir / "images.bin").exists() or \
        not (sparse_dir / "points3D.bin").exists():
    print("Computing camera parameters using COLMAP...")
    multi_camera = False
    for frame in frames_dir.rglob("*.jpg"):
        multi_camera = True
        break
    for frame in frames_dir.glob("*.jpg"):
        multi_camera = False
        break
    convert = "convert_multi.py" if multi_camera else "convert.py"
    if not gs_dir or not (gs_dir / convert).exists():
        print(f"Missing path to Gaussian Splatting {convert} script.")
        sys.exit()

    process = ["python", f"{(gs_dir / convert).resolve()}", "--source_path", f"{data_dir}"]
    if sfm_resize:
        process.append("--resize")
    process_str = " ".join(process)
    print(f"Calling: {process_str}")
    subprocess.run(process)
    print("")

print("SfM DONE")
print("")
