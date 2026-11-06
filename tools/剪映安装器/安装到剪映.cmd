@echo off
setlocal
pushd "%~dp0" || exit /b 1
python -X utf8 -c "import runpy; runpy.run_path('\u5b89\u88c5\u5230\u526a\u6620.py', run_name='__main__')" %*
set "install_status=%errorlevel%"
popd
if "%~1"=="" pause
exit /b %install_status%
