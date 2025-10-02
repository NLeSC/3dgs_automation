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

call run_sfm.bat   %args%
call run_depth.bat %args%
call run_splat.bat %args%