# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os
import platform
import subprocess


class UserFileSeeing:
    @staticmethod
    def see_file(path):
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
