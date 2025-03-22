mkdir "%APPDATA%\pip" 2>nul & echo [global] > "%APPDATA%\pip\pip.ini" & echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple >> "%APPDATA%\pip\pip.ini"
pip install -r requirements.txt