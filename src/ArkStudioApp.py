# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import customtkinter as ctk
from src.pages.ResourceManagerPage import ResourceManagerPage
from src.pages.ABResolverPage import ABResolverPage
from src.utils.UIStyles import style, load_font_asset, load_ttk_style
from src.utils import UIComponents as uic


ctk.set_appearance_mode("light")
ctk.ThemeManager.load_theme("assets/theme.json")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Init
        load_font_asset()
        load_ttk_style(self)

        # Window
        self.title("ArkStudio Dev")
        w = 1280
        h = 720
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Grid
        self.grid_rowconfigure((0), weight=1)
        self.grid_columnconfigure((1), weight=1)

        # Pages
        self.p_rm = ResourceManagerPage(self, 0, 1)
        self.p_ar = ABResolverPage(self, 0, 1)
        self.p_ic = uic.InfoLabelGroup(self, 0, 0, "WIP", "此页面正在开发中")
        self.p_fd = uic.InfoLabelGroup(self, 0, 0, "WIP", "此页面正在开发中")

        # Sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky='nsew')


class Sidebar(ctk.CTkFrame):
    def __init__(self, app:App):
        super().__init__(app, width=150, corner_radius=0)
        self.app = app
        self.configure(**style('menu'))
        self.brand = ctk.CTkLabel(self, text="ArkStudio", **style('banner'))
        self.brand.grid(row=0, column=0, padx=20, pady=20)
        self.menu_buttons:"dict[int,ctk.CTkButton]" = {}
        self.pages:"dict[int,uic.HidableGridWidget]" = {}
        self._add_menu_button(1, "资源库管理", app.p_rm)
        self._add_menu_button(2, "AB文件解包", app.p_ar)
        self._add_menu_button(3, "RGB-A图片合并", app.p_ic)
        self._add_menu_button(4, "FlatBuffers数据解码", app.p_fd)
        self.activate_menu_button(1)

    def _add_menu_button(self, row_index:int, text:str, bind_page:uic.HidableGridWidget):
        btn = ctk.CTkButton(self,
                            text=text,
                            command=lambda: self.activate_menu_button(row_index),
                            **style('menu_btn'))
        btn.grid(row=row_index, column=0, padx=15, pady=10)
        self.menu_buttons[row_index] = btn
        self.pages[row_index] = bind_page

    def activate_menu_button(self, row_index:int):
        for i, b in self.menu_buttons.items():
            b.configure(**style('menu_btn_active' if i == row_index else 'menu_btn_regular'))
        for i, p in self.pages.items():
            p.set_visible(i == row_index)
