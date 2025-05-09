# -*- coding: utf-8 -*-
# Copyright (c) 2024-2025, Harry Huang
# @ BSD 3-Clause License
import re
import customtkinter as ctk
from dataclasses import dataclass

from ..backend import ArkClientPayload as acp
from ..backend import GitHubClient as ghc
from ..pages.ArkStudioAppInterface import App
from ..utils import UIComponents as uic
from ..utils.UIStyles import icon, style


class SelectVersionDialog(ctk.CTkToplevel):
    def __init__(self, master:App):
        super().__init__(master)

        # Window
        self.title("Select")
        w = 640
        h = 640
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Modal
        self.transient(master)
        self.grab_set()
        self.lift()

        # Grid
        self.grid_rowconfigure((0, 1, 3, 4), weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Components
        self.title_label = ctk.CTkLabel(self, text="选择资源版本号",
                                        image=icon('goto'), **style('panel_title'))
        self.title_label.grid(row=0, column=0, pady=10, padx=20, sticky='nw')

        self.tip1_label = ctk.CTkLabel(self, text="从互联网获取到的版本记录：")
        self.tip1_label.grid(row=1, column=0, pady=10, padx=20, sticky='nw')

        self.treeview = uic.TreeviewFrame(self, 0, 0, columns=2, tree_mode=False, empty_tip="暂无数据")
        self.treeview.set_column(0, 200, "资源版本号")
        self.treeview.set_column(1, 150, "对应客户端版本")
        self.treeview.set_text_extractor(lambda v:v.res)
        self.treeview.set_icon_extractor(lambda _:'')
        self.treeview.set_value_extractor(lambda v:(v.client,))
        self.treeview.set_insert_order(lambda l:list(reversed(sorted(l))))
        self.treeview.set_on_item_selected(self._on_item_selected)
        self.treeview.clear()
        self.treeview.grid(row=2, column=0, pady=10, padx=20, sticky='nsew')

        self.entry = ctk.CTkEntry(self, placeholder_text="选择一个版本记录，或者在此手动输入资源版本号...")
        self.entry.grid(row=3, column=0, pady=10, padx=20, sticky='ew')

        self.button_group = ctk.CTkFrame(self)
        self.button_group.grid(row=4, column=0, pady=10, padx=20, sticky='ne')

        self.confirm_button = uic.OperationButton(self.button_group, 0, 0, "确认",
                                               image=icon('dialog_okay'), command=self._on_confirm)

        self.cancel_button = uic.OperationButton(self.button_group, 0, 1, "取消",
                                                 image=icon('dialog_cancel'), command=self.destroy)

        # Data
        self.rst = SelectVersionResult(confirmed=False, version=None)
        self._agd_repo = "Kengxxiao/ArknightsGameData"
        self._agd_branch = "master"
        self._agd_server = "CN"
        self._agd_pp = 25
        self._agd_p = 0
        self._show_next_page_versions()

    def get_result(self):
        return self.rst

    def _on_item_selected(self, ver:acp.ArkVersion):
        self.entry.delete(0, ctk.END)
        self.entry.insert(0, ver.res)

    def _on_confirm(self):
        ver = acp.ArkVersion(res=self.entry.get().strip('\n'), client="")
        self.rst = SelectVersionResult(confirmed=True, version=ver)
        self.destroy()

    def _fetch_next_page_versions_from_agd(self):
        client = ghc.GitHubClient()
        self._agd_p += 1
        commits = client.get_commits(
            self._agd_repo,
            sha=self._agd_branch,
            per_page=self._agd_pp,
            page=self._agd_p
        )
        rst:"list[acp.ArkVersion]" = []
        for c in commits:
            m = re.match(
                r'\[([A-Z]{2}) UPDATE\] Client:([\d\.]+) Data:([a-zA-Z\d\-_]+)',
                c.message
            )
            if m and m.group(1) == self._agd_server:
                ver = acp.ArkVersion(res=m.group(3), client=m.group(2))
                rst.append(ver)
        return rst

    def _show_next_page_versions(self):
        self.treeview.insert(self._fetch_next_page_versions_from_agd())


@dataclass
class SelectVersionResult:
    confirmed: bool
    version: acp.ArkVersion
