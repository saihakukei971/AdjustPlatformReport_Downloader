@echo off
REM ====================================================
REM Adjust Platform Report Downloader �������s�X�N���v�g
REM ====================================================
REM �쐬��: 2025/05/05
REM 
REM ���̃o�b�`�t�@�C���́A�l�b�g���[�N�h���C�u���Adjust Platform
REM �o�b�`�������������s���邽�߂̂��̂ł��B
REM �^�X�N�X�P�W���[������Ăяo�����Ƃ�z�肵�Ă��܂��B
REM ====================================================

REM ���O�o�͂̐ݒ�
set LOGFILE=%~dp0log\batch_execution_%date:~0,4%%date:~5,2%%date:~8,2%.log
set TIMESTAMP=%date% %time%

REM ���O�t�H���_�̍쐬�i���݂��Ȃ��ꍇ�j
if not exist "%~dp0log" mkdir "%~dp0log"

REM ���O�t�@�C���̏������b�Z�[�W
echo %TIMESTAMP% - �o�b�`�������J�n���܂��B > "%LOGFILE%"

REM ============================================
REM �l�b�g���[�N�h���C�u�ւ̃A�N�Z�X
REM ============================================
echo %TIMESTAMP% - �l�b�g���[�N�h���C�u�ւ̐ڑ������݂܂�... >> "%LOGFILE%"

REM �l�b�g���[�N�h���C�u�����ɐڑ�����Ă��邩�`�F�b�N
net use Z: 2>nul
if %ERRORLEVEL% EQU 0 (
    echo %TIMESTAMP% - ���Ƀl�b�g���[�N�h���C�uZ:���ڑ�����Ă��܂��B�ؒf���܂�... >> "%LOGFILE%"
    net use Z: /delete /y
    if %ERRORLEVEL% NEQ 0 (
        echo %TIMESTAMP% - �G���[: �l�b�g���[�N�h���C�uZ:�̐ؒf�Ɏ��s���܂����B >> "%LOGFILE%"
        goto ERROR_EXIT
    )
)

REM �l�b�g���[�N�h���C�u�ɐڑ�
net use Z: \\server\share /user:domain\username password
if %ERRORLEVEL% NEQ 0 (
    echo %TIMESTAMP% - �G���[: �l�b�g���[�N�h���C�u�ւ̐ڑ��Ɏ��s���܂����B(�G���[�R�[�h: %ERRORLEVEL%) >> "%LOGFILE%"
    goto ERROR_EXIT
)
echo %TIMESTAMP% - �l�b�g���[�N�h���C�u�ւ̐ڑ��ɐ������܂����B >> "%LOGFILE%"

REM ============================================
REM Python�̃p�X�m�F
REM ============================================
echo %TIMESTAMP% - Python�̃p�X���m�F���Ă��܂�... >> "%LOGFILE%"
set PYTHON_PATH=C:\Path\to\Python\python.exe

REM Python�̑��݊m�F
if not exist "%PYTHON_PATH%" (
    echo %TIMESTAMP% - �G���[: Python���s�t�@�C����������܂���B�p�X���m�F���Ă�������: %PYTHON_PATH% >> "%LOGFILE%"
    goto CLEANUP
)
echo %TIMESTAMP% - Python���s�t�@�C����������܂���: %PYTHON_PATH% >> "%LOGFILE%"

REM ============================================
REM ���s���̏���
REM ============================================
REM �J�����g�f�B���N�g����ύX
cd /d Z:\path\to\adjust_batch
if %ERRORLEVEL% NEQ 0 (
    echo %TIMESTAMP% - �G���[: ��ƃf�B���N�g���ւ̈ړ��Ɏ��s���܂����B�p�X���m�F���Ă��������B >> "%LOGFILE%"
    goto CLEANUP
)
echo %TIMESTAMP% - ��ƃf�B���N�g���ւ̈ړ��ɐ������܂���: %CD% >> "%LOGFILE%"

REM �ݒ�t�@�C���̑��݊m�F
if not exist "config.ini" (
    echo %TIMESTAMP% - �G���[: config.ini�t�@�C����������܂���B >> "%LOGFILE%"
    goto CLEANUP
)

REM Excel�t�@�C���̑��݊m�F
if not exist "GAC_adjust�Ǘ���ʏ��.xlsx" (
    echo %TIMESTAMP% - �G���[: GAC_adjust�Ǘ���ʏ��.xlsx�t�@�C����������܂���B >> "%LOGFILE%"
    goto CLEANUP
)

REM �o�̓f�B���N�g���̍쐬�i���݂��Ȃ��ꍇ�j
set OUTPUT_DIR=output
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo %TIMESTAMP% - ���s���̏������������܂����B >> "%LOGFILE%"

REM ============================================
REM �X�N���v�g�̎��s
REM ============================================
echo %TIMESTAMP% - Adjust Platform Report Downloader�̎��s���J�n���܂�... >> "%LOGFILE%"
echo %TIMESTAMP% - �R�}���h: %PYTHON_PATH% adjust_playwright_batch.py --headless --date %date:~0,4%%date:~5,2%%date:~8,2% >> "%LOGFILE%"

REM �X�N���v�g�̎��s
%PYTHON_PATH% adjust_playwright_batch.py --headless --date %date:~0,4%%date:~5,2%%date:~8,2%

REM ���s���ʂ̊m�F
set EXIT_CODE=%ERRORLEVEL%
if %EXIT_CODE% EQU 0 (
    echo %TIMESTAMP% - �X�N���v�g�̎��s���������܂����B >> "%LOGFILE%"
) else (
    echo %TIMESTAMP% - �G���[: �X�N���v�g�̎��s�Ɏ��s���܂����B(�G���[�R�[�h: %EXIT_CODE%) >> "%LOGFILE%"
)

REM ���ʂ̊m�F
echo %TIMESTAMP% - �I���R�[�h: %EXIT_CODE% >> "%LOGFILE%"

REM �������ʂ̊m�F�F������CSV�t�@�C������������Ă��邩
set TODAY=%date:~0,4%%date:~5,2%%date:~8,2%
set CSV_COUNT=0
for %%F in ("%OUTPUT_DIR%\%TODAY%\*.csv") do set /a CSV_COUNT+=1

echo %TIMESTAMP% - �{��(%TODAY%)�������ꂽCSV�t�@�C����: %CSV_COUNT% >> "%LOGFILE%"

REM ============================================
REM �N���[���A�b�v����
REM ============================================
:CLEANUP
echo %TIMESTAMP% - �N���[���A�b�v���������s���܂�... >> "%LOGFILE%"

REM �l�b�g���[�N�h���C�u��ؒf
echo %TIMESTAMP% - �l�b�g���[�N�h���C�u�̐ؒf�����݂܂�... >> "%LOGFILE%"
net use Z: /delete /y
if %ERRORLEVEL% NEQ 0 (
    echo %TIMESTAMP% - �x��: �l�b�g���[�N�h���C�u�̐ؒf�Ɏ��s���܂����B(�G���[�R�[�h: %ERRORLEVEL%) >> "%LOGFILE%"
) else (
    echo %TIMESTAMP% - �l�b�g���[�N�h���C�u�̐ؒf�ɐ������܂����B >> "%LOGFILE%"
)

REM ����I��
echo %TIMESTAMP% - �o�b�`�������������܂����B >> "%LOGFILE%"
exit /b %EXIT_CODE%

REM ============================================
REM �G���[�I������
REM ============================================
:ERROR_EXIT
echo %TIMESTAMP% - �G���[�������������߁A�����𒆒f���܂��B >> "%LOGFILE%"
exit /b 1