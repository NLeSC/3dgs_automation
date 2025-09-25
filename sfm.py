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

parser = argparse.ArgumentParser(description="Compute camera parameters using Structure from Motion.")
parser.add_argument("data", help="Data root path.", type=Path)
parser.add_argument("--gs", help="Gaussian Splatting root path.", type=Path)
parser.add_argument("--frames", "-f", help="Input frames directory path (default: <data>\\input).", type=Path)
parser.add_argument("--resize", help="Resize the images during SfM.", action='store_true')
parser.add_argument("--force", help="Force recomputing the camera parameters.", action='store_true')
parser.add_argument("--video", "-v", help="Input video file path.", type=Path)
parser.add_argument("--fps", help="Frames per second to extract from video (default: %(default)s).", type=float, default=5) # TODO(tvl): default temp at 5 for testing

args = parser.parse_args()

if not args.frames:
    args.frames = args.data / "input"
if not args.frames.exists():
    args.frames.mkdir(parents=True)
if not args.frames.is_dir():
    print(f"Input frames directory {args.frames} is not a directory.")
    sys.exit()

# If the frames directory is empty, try to extract frames from a video file.
frames_empty = True
for image in args.frames.rglob("*.jpg"):
    frames_empty = False
    break
if frames_empty:
    print("Input frames not found: locating input video...")
    videos = []
    if args.video:
        videos.append(args.video)
    else:
        video_dir = args.data / "raw"
        if video_dir.exists() and video_dir.is_dir():
            for video in video_dir.glob("*.mpeg"):
                videos.append(video)
            for video in video_dir.glob("*.mpg"):
                videos.append(video)
            for video in video_dir.glob("*.mp4"):
                videos.append(video)
    if len(videos) == 0:
        print("Neither input frames or video file found...")
        sys.exit()

    video_str = f"video {videos[0]}" if len(videos) == 1 else f"{len(videos)} videos"
    print(f"Extracting frames from {video_str} using FFMPEG...")
    for i in range(len(videos)):
        frames = args.frames
        if len(videos) > 1:
            frames = frames / f"{i}"
            frames.mkdir(parents=True)
        frames = frames / "%04d.jpg"
        process = ["ffmpeg", "-i", f"{videos[i]}", "-qscale:v", "1", "-qmin", "1", "-vf", f"fps={args.fps}", f"{frames}"]
        process_str = " ".join(process)
        print(f"Calling: {process_str}")
        subprocess.run(process)
        print("")

# If the SfM output does not exist, compute it.
images_empty = True
for image in (args.data / "images").rglob("*.jpg"):
    images_empty = False
    break
sparse_dir = args.data / "sparse" / "0"
if args.force or images_empty or not (sparse_dir / "cameras.bin").exists() or not (sparse_dir / "images.bin").exists() or not (sparse_dir / "points3D.bin").exists():
    print("Computing camera parameters using COLMAP...")
    multi_camera = False
    for frame in args.frames.rglob("*.jpg"):
        multi_camera = True
        break
    for frame in args.frames.glob("*.jpg"):
        multi_camera = False
        break
    convert = "convert_multi.py" if multi_camera else "convert.py"
    if not args.gs or not (args.gs / convert).exists():
        print(f"Missing path to Gaussian Splatting {convert} script.")
        sys.exit()

    process = ["python", f"{(args.gs / convert).resolve()}", "--source_path", f"{args.data}"]
    if args.resize:
        process.append("--resize")
    process_str = " ".join(process)
    print(f"Calling: {process_str}")
    subprocess.run(process)
    print("")

print("SfM DONE")
print("")
