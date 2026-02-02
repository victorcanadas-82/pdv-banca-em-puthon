@echo off
title PDV Banca - Iniciando
echo Iniciando o sistema da banca... aguarde.
python -m streamlit run app.py --server.headless true
pause