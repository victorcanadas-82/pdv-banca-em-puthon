Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd.exe /c python -m streamlit run app.py --server.headless true", 0
Set WshShell = Nothing