import os
import sys
import shutil
from pathlib import Path

def build_exe():
    """打包程序为exe文件"""
    print("开始打包...")
    
    # 清理之前的构建文件
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # 使用PyInstaller打包
    os.system("pyinstaller --noconfirm --onefile --windowed --icon=icon.ico --name=FilesHelper gui.py")
    
    print("打包完成！")
    print("可执行文件位于 dist 目录下")

if __name__ == "__main__":
    build_exe() 