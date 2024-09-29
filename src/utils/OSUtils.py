# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os
import platform
import shutil
import subprocess


class FileSystem:
    @staticmethod
    def rm(path:str):
        """**DANGEROUS**: Deletes a file or a directory."""
        if os.path.isfile(path):
            os.unlink(path)
        elif os.path.isdir(path):
            if path.strip().rstrip() in ['', '/', '\\']:
                raise OSError("Dangerous action")
            shutil.rmtree(path, ignore_errors=True)

    @staticmethod
    def mkdir(dirpath:str):
        """Makes a directory."""
        os.makedirs(dirpath, exist_ok=True)

    @staticmethod
    def mkdir_for(filepath:str):
        """Makes the parent directory of the given file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    @staticmethod
    def see_file(path:str):
        """Uses the platform explorer to see the file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"The specified path does not exist: {path}")

        os_name = platform.system()

        if os_name == 'Windows':
            subprocess.run(f'explorer /select,"{os.path.abspath(path)}"', check=False)
        elif os_name == "Darwin":
            subprocess.run(['open', '-R', path], check=False)
        elif os_name == "Linux":
            try:
                subprocess.run(['nautilus', '--select', path], check=False)
            except FileNotFoundError:
                try:
                    subprocess.run(['xdg-open', path], check=False)
                except FileNotFoundError:
                    raise OSError("No supported file manager found on this Linux system.")
        else:
            raise OSError(f"Unsupported operating system: {os_name}")
