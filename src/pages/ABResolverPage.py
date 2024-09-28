# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os
import tkinter.filedialog as fd
import customtkinter as ctk

from src.backend import ArkClientPayload as acp
from src.backend import ABHandler as abh
from src.utils import UIComponents as uic
from src.utils.UIStyles import file_icon, icon, style
from src.utils.UIConcurrent import GUITaskBase
from .ArkStudioAppInterface import App


class ABResolverPage(ctk.CTkFrame, uic.HidableGridWidget):
    def __init__(self, app:App, grid_row:int, grid_column:int):
        ctk.CTkFrame.__init__(self, app, corner_radius=0)
        uic.HidableGridWidget.__init__(self, grid_row, grid_column, init_visible=False, sticky='nsew')
        self.app = app
        self.grid_rowconfigure((0, 2), weight=0)
        self.grid_rowconfigure((1), weight=1)
        self.grid_columnconfigure((0, 1), weight=1, uniform='column')
        self.abstract = _AbstractPanel(self)
        self.abstract.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky='nsew')
        self.explorer = _ExplorerPanel(self)
        self.explorer.grid(row=1, column=0, rowspan=2, padx=(10, 5), pady=(5, 10), sticky='nsew')
        self.inspector = _InspectorPanel(self)
        self.inspector.grid(row=1, column=1, padx=(5, 10), pady=5, sticky='nsew')
        self.operation = _OperationPanel(self)
        self.operation.grid(row=2, column=1, padx=(5, 10), pady=(5, 10), sticky='nsew')
        self.cur_ab = None
        self.cur_path = None

    def invoke_load_tree(self, ab:abh.ABHandler):
        self.cur_ab = ab
        self.explorer.load_tree(self.cur_ab)

    def invoke_inspect(self, obj:abh.ObjectInfo):
        self.inspector.inspect(obj)
        self.operation.inspect(obj)


class _FileReloadTask(GUITaskBase):
    def __init__(self, manager:ABResolverPage):
        super().__init__("正在读取对象列表...")
        self._manager = manager

    def _run(self):
        self._manager.abstract.set_loading(True)
        self.update(0.25, "正在读取对象列表")
        t = self._manager.after(500, lambda:self.update(0.5))
        if self._manager.cur_path:
            ab = abh.ABHandler(self._manager.cur_path)
            self._manager.after_cancel(t)
            self.update(0.75, "正在加载浏览视图")
            self._manager.invoke_load_tree(ab)

    def _on_complete(self):
        self._manager.abstract.set_loading(False)
        self._manager.abstract.show_file_info()

class _FileExtractTask(GUITaskBase):
    def __init__(self, manager:ABResolverPage):
        super().__init__("正在提取全部对象...")
        self._manager = manager

    def _run(self):
        self._manager.abstract.set_loading(True)
        # TODO WIP: Extract object

    def _on_complete(self):
        self._manager.abstract.set_loading(False)


class _AbstractPanel(ctk.CTkFrame):
    master:ABResolverPage

    def __init__(self, master:ABResolverPage):
        super().__init__(master)
        self.title = ctk.CTkLabel(self, text="资源文件概要", image=icon('abstract'), **style('panel_title'))
        self.title.grid(row=0, column=0, **style('panel_title_grid'))
        self.info_file_name = uic.InfoLabelGroup(self, 1, 0, "文件名称", tight=True)
        self.info_file_name.show("<未知>")
        self.info_file_path = uic.InfoLabelGroup(self, 2, 0, "文件路径", tight=True)
        self.info_file_path.show("<未知>")
        self.btn_open = uic.OperationButton(self, 1, 1, "打开", icon('file_open'),
                                            command=self.cmd_open)
        self.btn_reload = uic.OperationButton(self, 2, 1, "刷新", icon('file_reload'),
                                              command=self.cmd_reload, **style('operation_button_info'))
        self.btn_extract = uic.OperationButton(self, 1, 2, "提取全部对象", icon('file_extract'),
                                               command=self.cmd_extract_all)
        self.progress = uic.ProgressBarGroup(self, 0, 0, grid_columnspan=1, init_visible=False)
        self.btn_list = (self.btn_open, self.btn_reload, self.btn_extract)
        self.grid_columnconfigure((0), weight=1)
        self.grid_columnconfigure((1, 2, 3, 4), weight=0)

    def set_loading(self, loading:bool):
        for i in self.btn_list:
            i.configure(state='disabled' if loading else 'normal')
        self.progress.set_visible(loading)

    def show_file_info(self):
        ab = self.master.cur_ab
        if ab:
            self.info_file_name.show(os.path.basename(ab.filepath))
            self.info_file_path.show(ab.filepath)

    def cmd_open(self):
        new_file = fd.askopenfilename(filetypes=[('Asset Bundle', '*.ab'), ('Any File', '*')])
        if new_file and os.path.isfile(new_file):
            self.cmd_reload()
            self.master.cur_path = new_file

    def cmd_reload(self):
        task = _FileReloadTask(self.master)
        self.progress.bind_task(task)
        task.start()

    def cmd_extract_all(self):
        task = _FileExtractTask(self.master)
        self.progress.bind_task(task)
        task.start()


class _ExplorerPanel(ctk.CTkFrame):
    master:ABResolverPage

    def __init__(self, master:ABResolverPage):
        super().__init__(master)
        self.title = ctk.CTkLabel(self, text="对象浏览器", image=icon('explorer'), **style('panel_title'))
        self.title.grid(row=0, column=0, **style('panel_title_grid'))
        self.children_map:"dict[acp.FileInfoBase,set[abh.ObjectInfo]]" = None
        self.treeview:"uic.TreeviewFrame[abh.ObjectInfo]" = uic.TreeviewFrame(self, 1, 0, columns=3, tree_mode=False, empty_tip="列表为空")
        self.treeview.set_column(0, 350, "对象名称")
        self.treeview.set_column(1, 100, "类型")
        self.treeview.set_column(2, 150, "PathID", anchor='ne')
        self.treeview.set_text_extractor(lambda x:x.name)
        self.treeview.set_icon_extractor(lambda x:file_icon(1))
        self.treeview.set_value_extractor(lambda x:(x.type.name, x.pathid))
        self.treeview.set_on_item_selected(self.master.invoke_inspect)
        self.treeview.set_insert_order(lambda x:sorted(x, key=lambda y:(y.type.name, y.name)))
        self.grid_rowconfigure((0), weight=0)
        self.grid_rowconfigure((1), weight=1)
        self.grid_columnconfigure((0), weight=1)

    def load_tree(self, ab:abh.ABHandler):
        # Clear the current items
        self.treeview.clear()
        # Load the new items
        self.treeview.insert(ab.objects)


class _InspectorPanel(ctk.CTkTabview):
    master:ABResolverPage

    def __init__(self, master:ABResolverPage):
        super().__init__(master)
        self.tab_names = ("对象信息", "文本", "图像", "音频")
        # Tab 1 >>>>> Info
        self.tab1 = self.add(self.tab_names[0])
        self.info_name = uic.InfoLabelGroup(self.tab1, 1, 0, "对象名称", tight=True)
        self.info_type = uic.InfoLabelGroup(self.tab1, 2, 0, "类型", tight=True)
        self.info_pathid = uic.InfoLabelGroup(self.tab1, 3, 0, "PathID", tight=True)
        # Tab 2 >>>>> Script
        self.tab2 = self.add(self.tab_names[1])
        self.text_area = uic.TextPreviewer(self.tab2, 0, 0, "无文本或二进制资源")
        self.tab2.grid_columnconfigure((0), weight=1)
        # Tab 3 >>>>> Image
        self.tab3 = self.add(self.tab_names[2])
        self.image_area = uic.ImagePreviewer(self.tab3, 0, 0, "无图像资源")
        self.tab3.grid_columnconfigure((0), weight=1)
        # Tab 4 >>>>> Audio
        self.tab4 = self.add(self.tab_names[3])
        self.audio_area = uic.AudioPreviewer(self.tab4, 0, 0, "无可解码的音频")
        self.tab4.grid_columnconfigure((0), weight=1)

    def inspect(self, obj:abh.ObjectInfo):
        self.info_name.show(obj.name)
        self.info_type.show(obj.type.name)
        self.info_pathid.show(obj.pathid)
        script = obj.script
        image = obj.image
        audio = obj.audio
        if script:
            self.set(self.tab_names[1])
        self.text_area.show(script)
        if image:
            self.set(self.tab_names[2])
        self.image_area.show(obj.image)
        if audio:
            self.set(self.tab_names[3])
        self.audio_area.show(obj.audio)
        if not any((script, image, audio)):
            self.set(self.tab_names[0])


class _OperationPanel(ctk.CTkFrame):
    master:ABResolverPage

    def __init__(self, master:ABResolverPage):
        super().__init__(master)
        self.title = ctk.CTkLabel(self, text="操作", image=icon('operation'), **style('panel_title'))
        self.title.grid(row=0, column=0, **style('panel_title_grid'))
        self.btn_view = uic.OperationButton(self, 1, 0, "WIP：导出此对象", icon('file_extract')
                                            )
        self.grid_columnconfigure((0), weight=1)

    def inspect(self, obj:abh.ObjectInfo):
        self.btn_view.set_visible(obj.is_extractable())
