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


def extract_frames(video_path : Path, frames_dir : Path, slice_fps : float, slice_force : bool, slice_skip : bool):
    # If the frames directory is empty, try to extract frames from a video file.
    # Note, this function has dependencies in the gaussian_splatting conda environment.
    if slice_skip: return

    frames_empty = True
    for _ in frames_dir.rglob("*.jpg"):
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


def compute_sfm(gs_dir : Path, data_dir : Path, frames_dir : Path, images_dir : Path, sparse_dir : Path, sfm_resize : bool, sfm_force : bool, sfm_skip : bool):
    # If the SfM output does not exist, compute it.
    # Note, this function has dependencies in the gaussian_splatting conda environment.
    if sfm_skip: return

    images_empty = True
    for _ in images_dir.rglob("*.jpg"):
        images_empty = False
        break
    if sfm_force or images_empty or \
            not (sparse_dir / "cameras.bin").exists() or \
            not (sparse_dir / "images.bin").exists() or \
            not (sparse_dir / "points3D.bin").exists():
        print("Computing camera parameters using COLMAP...")
        multi_camera = False
        for _ in frames_dir.rglob("*.jpg"):
            multi_camera = True
            break
        for _ in frames_dir.glob("*.jpg"):
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


def compute_depths(da_dir : Path, images_dir : Path, depths_dir : Path, depths_enable : bool, depths_force : bool, depths_skip : bool):
    # If the depths directory is empty, compute the depth images.
    # Note, this function has dependencies in the depth_anything conda environment.
    if depths_skip: return

    depths_empty = True
    for _ in depths_dir.rglob("*.png"):
        depths_empty = False
        break
    if depths_enable and (depths_force or depths_empty):
        print("Computing depth images using Depth-Anything-V2...")
        if not da_dir or not (da_dir / "run.py").exists():
            print("Missing path to Depth-Anything-V2 run.py script.")
            sys.exit()
            
        from contextlib import chdir

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


def scale_depths(gs_dir : Path, data_dir : Path, sparse_dir : Path, depths_dir : Path, depths_force : bool, depths_skip : bool):
    if depths_skip: return

    # If there are depth images without a params file, compute it.
    # Note, this function has dependencies in the gaussian_splatting conda environment.
    depths_empty = True
    for _ in depths_dir.rglob("*.png"):
        depths_empty = False
        break
    if not depths_empty and (depths_force or not (sparse_dir / "depth_params.json").exists()):
        print(f"Depth images found in {depths_dir}: computing params file...")

        process = ["python", f"{(gs_dir / 'utils' / 'make_depth_scale.py').resolve()}", "--base_dir", f"{data_dir}", "--depths_dir", f"{depths_dir}"]
        process_str = " ".join(process)
        print(f"Calling: {process_str}")
        subprocess.run(process)
        print("")


def train_splats(gs_dir : Path, data_dir : Path, sparse_dir : Path, depths_dir : Path, splats_dir : Path, train_exposure : bool, splats_force : bool):
    # If no 3D Gaussian splats exist, compute them.
    # Note, this function has dependencies in the gaussian_splatting conda environment.
    depths_empty = True
    for _ in depths_dir.rglob("*.png"):
        depths_empty = False
        break
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


def main():
    parser = argparse.ArgumentParser(description="Process 3D Gaussian Splatting.")
    parser.add_argument("mode", help="Processing mode.", choices=["sfm", "depth", "splat", "all"], nargs='?', default="all")
    parser.add_argument("config", help="Config file path.", type=Path)
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    data = config["data"]
    data_dir = Path(data.get("root_dir"))


    if args.mode in ["sfm", "all"]:
        frames_dir = Path(data.get("frames_dir", data_dir / "input"))

        if not frames_dir.exists():
            frames_dir.mkdir(parents=True)
        if not frames_dir.is_dir():
            print(f"Input frames directory {frames_dir} is not a directory.")
            sys.exit()

        extract_frames(
            video_path = Path(data.get("video_path", data_dir / "raw")),
            frames_dir=frames_dir,
            slice_fps = config["slice"].getfloat("fps", 1.0),
            slice_force = config["slice"].getboolean("force", False),
            slice_skip = config["slice"].getboolean("skip", False)
        )

        compute_sfm(
            gs_dir = Path(config["software"].get("gaussian_splatting_root_dir")),
            data_dir = data_dir,
            frames_dir = frames_dir,
            images_dir = Path(data.get("images_dir", data_dir / "images")),
            sparse_dir = Path(data.get("sparse_dir", data_dir / "sparse" / "0")),
            sfm_resize = config["sfm"].getboolean("resize", False),
            sfm_force = config["sfm"].getboolean("force", False),
            sfm_skip = config["sfm"].getboolean("skip", False)
        )

        print("SfM DONE")
        print("")


    if args.mode in ["depth", "all"]:
        images_dir = Path(data.get("images_dir", data_dir / "images"))

        if not images_dir.is_dir():
            print(f"Input directory {images_dir} is not a directory.")
            sys.exit()

        compute_depths(
            da_dir = Path(config["software"].get("depth_anything_root_dir")),
            images_dir = images_dir,
            depths_dir = Path(data.get("depths_dir", data_dir / "depths")),
            depths_enable = config["depths"].getboolean("enable", False),
            depths_force = config["depths"].getboolean("force", False),
            depths_skip = config["depths"].getboolean("skip", False)
        )

        print("depths DONE")
        print("")


    if args.mode in ["splat", "all"]:
        sparse_dir = Path(data.get("sparse_dir", data_dir / "sparse" / "0"))
        splats_dir = Path(data.get("splats_dir", data_dir / "splats"))

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

        scale_depths(
            gs_dir = Path(config["software"].get("gaussian_splatting_root_dir")),
            data_dir = data_dir,
            sparse_dir = sparse_dir,
            depths_dir = Path(data.get("depths_dir", data_dir / "depths")),
            depths_force = config["depths"].getboolean("force", False),
            depths_skip = config["depths"].getboolean("skip", False)
        )

        train_splats(
            gs_dir = Path(config["software"].get("gaussian_splatting_root_dir")),
            data_dir = data_dir,
            sparse_dir = sparse_dir,
            depths_dir = Path(data.get("depths_dir", data_dir / "depths")),
            splats_dir = splats_dir,
            train_exposure = config["splats"].getboolean("train_exposure", False),
            splats_force = config["splats"].getboolean("force", False)
        )
                
        print("splats DONE")
        print("")

if __name__ == "__main__":
    main()