::@echo off
:: バッチファイルが置かれているディレクトリに移動
cd /d %~dp0
cd

:: 仮想環境をアクティベート
call .venv\Scripts\activate.bat

:: Pythonw.exeでスクリプトを実行（コンソールウィンドウなし）
start "" .venv\Scripts\pythonw.exe goro-launcher.py

exit
