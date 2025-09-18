@echo off
:: Copyright 2025 Netherlands eScience Center
:: 
:: Licensed under the Apache License, Version 2.0 (the "License");
:: you may not use this file except in compliance with the License.
:: You may obtain a copy of the License at
:: 
::     http://www.apache.org/licenses/LICENSE-2.0
:: 
:: Unless required by applicable law or agreed to in writing, software
:: distributed under the License is distributed on an "AS IS" BASIS,
:: WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
:: See the License for the specific language governing permissions and
:: limitations under the License.

:: The arguments must include the data directory; all are passed verbatim to each script.
set args=%*

set env_gs=gaussian_splatting
set gs=D:\gaussian-splatting\

set env_da=depth_anything
set da2=D:\Depth-Anything-V2\

set fps=2.5


set command=python sfm.py --gs %gs% --fps %fps% %args%
echo Calling: "%command%"
call conda activate %env_gs% & %command%

set command=python depth.py --da2 %da2% %args%
echo Calling: "%command%"
call conda activate %env_da% & %command%

set command=python splat.py --gs %gs% --train_exposure %args%
echo Calling: "%command%"
call conda activate %env_gs% & %command%