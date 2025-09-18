# 3dgs_automation
Pipeline automation of 3D Gaussian Splatting from
`https://github.com/graphdeco-inria/gaussian-splatting`

## Installation
Note that 3D Gaussian Splatting should work on both Windows and Linux operating systems.
However, I was unable to get it working on current linux systems.

These installation instructions are for Windows Server 2019 with CUDA and a good GPU,
because that is the type of Windows system available to us on Research Cloud.

### Dependencies
#### git
Download git from `https://git-scm.com/downloads/win` and install it.

##### GitHub
Create a new ssh key on the workspace.
from `https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key`
```(cmd)
ssh-keygen -t ed25519 -C "<your_email>"
```
Add the public key to your github account.
* the public key should be in `C:\Users\<username>\.ssh\id_ed25519.pub`

#### conda
Download mamba from `https://github.com/conda-forge/miniforge` and install it.
* Preferably on an attached storage drive, because conda takes up a huge amount of space.
  * Note that conda refuses to install on top of an existing version.
    Because of it's size, installing it requires first deleting the old install.
* Update conda (the first time, this must be done in the Miniforge Prompt)
```(cmd)
conda deactivate
conda update --all
conda init
```

#### Visual Studio 2019
Note that gaussian-splating is not compatible with later Visual Studio versions.
Download VS Community from `https://aka.ms/vs/16/release/vs_community.exe` and install it
* Make sure to enable Desktop development with C++

#### CUDA 11.8
Note that a Research Cloud workspace comes with CUDA 12 installed,
but gaussian-splating is not compatible with this version.

Download CUDA toolkit 11.8 from
`https://developer.nvidia.com/cuda-11-8-0-download-archive` and install it.
* Note that the installer may mention that Nsight was not replaced by a newer version
  check that the current version is 11.8
```(cmd)
nvcc --version
```

##### CUDA 12.3.2
The SIBR viewer pre-built binaries may require CUDA 12.
Download CUDA toolkit 12.3.2 (the last version to support Windows Server 2019) from
`https://developer.nvidia.com/cuda-12-3-2-download-archive`

#### COLMAP
Download COLMAP with CUDA from `https://github.com/colmap/colmap/releases`
Extract the zip to `<user>\COLMAP\`
Add `<user>\COLMAP\` to the Local Path (Search 'edit the system environment variables')

#### ImageMagick
Download ImageMagick from `https://imagemagick.org/script/download.php#windows` and
install it.
Verify it's working:
```(cmd)
magick logo: logo.gif
magick identify logo.gif
```

#### 7-zip
Download 7-zip from `https://www.7-zip.org/download.html` and install it.

#### FFMPEG
Download FFMPEG essentials from `https://www.gyan.dev/ffmpeg/builds/`
Extract the 7z file to `<user>\FFMPEG\`
Add `<user>\FFMPEG\bin\` to the Local Path.

#### CMake 3.24
Download `	cmake-3.24.4-windows-x86_64.msi` from `https://cmake.org/files/v3.24/` and
install it.

#### Reboot
At this point, you'll want to restart the machine for several of the changes to take
effect.

#### Depth Anything v2
Note that the repository with weights takes up about 1.35GB and its dependencies about 1.85GB. This is somewhat restrictive on the cloud storage.

Clone repository:
```(cmd)
git clone https://github.com/DepthAnything/Depth-Anything-V2.git
```
Download weights from `https://huggingface.co/depth-anything/Depth-Anything-V2-Large/resolve/main/depth_anything_v2_vitl.pth?download=true` and place them under `Depth-Anything-V2/checkpoints/`

Install dependencies
```(cmd)
conda create -n depth_anything
conda activate depth_anything
conda install python
pip install -r Depth-Anything-V2\requirements.txt
```

### Gaussian Splatting source
Clone the repository.
Note the repository is cloned recusively, because it has several submodules.
```(cmd)
git clone git@github.com:graphdeco-inria/gaussian-splatting.git --recursive
```

Install packages using conda
```(cmd)
conda activate
SET DISTUTILS_USE_SDK=1
cd gaussian-splatting\
conda env create --file environment.yml
conda activate gaussian_splatting
```

Install the accelerated rasterizer to enable increased training speed:
```(cmd)
pip uninstall diff-gaussian-rasterization -y
cd submodules/diff-gaussian-rasterization
rmdir /S build
git checkout 3dgs_accel
pip install .
```

### GaussianSplats3D viewer
#### From source
Either install node.js from `http://nodejs.org/`
or:
```(cmd)
conda activate gaussian_splatting
conda install nodejs
```

Setup nodejs
```(cmd)
conda activate gaussian_splatting
npm install
npm run build-windows
```

Clone repository
```(cmd)
git clone git@github.com:mkkellogg/GaussianSplats3D.git
```

Demo:
download `https://projects.markkellogg.org/downloads/gaussian_splat_data.zip`
move to `<code>\build\demo\assets\data`
```(cmd)
npm run demo
```

#### Online viewer
Open `https://projects.markkellogg.org/threejs/demo_gaussian_splats_3d.php`


## Process dataset
Note that these methods will skip parts for which output already exists,
unless the optional `--force` argument is used.


### Compute Structure from Motion
```(cmd)
conda activate gaussian_splatting
python sfm.py [absolute\path\to\data\root\]
```

or set the directories in `run_sfm.bat` and call
```(cmd)
run_sfm.bat [absolute\path\to\data\root\]
```

### Compute Depths (optional)
```(cmd)
conda activate depth_anything
python depth.py [absolute\path\to\data\root\]
```

or set the directories in `run_depth.bat` and call
```(cmd)
run_depth.bat [absolute\path\to\data\root\]
```

### Compute Splats
```(cmd)
conda activate gaussian_splatting
python splat.py [absolute\path\to\data\root\]
```

or set the directories in `run_splat.bat` and call
```(cmd)
run_splat.bat [absolute\path\to\data\root\]
```

### Compute full pipeline
set the directories in `run_pipeline.bat` and call
```(cmd)
run_pipeline.bat [absolute\path\to\data\root\]
```
