# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os
import tkinter.filedialog as fd
import customtkinter as ctk

from src.backend import ArkClient as ac
from src.backend import ArkClientPayload as acp
from src.utils import UIComponents as uic
from src.utils.AnalyUtils import TestRT
from src.utils.Config import Config
from src.utils.OSUtils import FileSystem
from src.utils.UIStyles import file_icon, icon, style
from src.utils.UIConcurrent import GUITaskBase
from .ArkStudioAppInterface import App


class ResourceManagerPage(ctk.CTkFrame, uic.HidableGridWidget):
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

        self.local_root = Config.get('local_repo_root')
        self.client = ac.ArkClient()
        self.repo = None
        if not self.local_root or not os.path.isdir(self.local_root):
            self.local_root = None
        else:
            self.abstract.cmd_reload()

    def invoke_inspect(self, info:acp.FileInfoBase):
        self.inspector.inspect(info)
        self.operation.inspect(info)
        self.explorer.treeview.refresh([info])

    def invoke_inspect_alt(self, info:acp.FileInfoBase):
        self.inspector.inspect(info)
        self.operation.inspect(info)
        if self.operation.btn_view.is_visible():
            self.operation.btn_view.invoke()

    def invoke_view_file(self, path:str):
        self.app.p_ar.cur_path = path
        self.app.p_ar.abstract.cmd_reload()
        self.app.sidebar.activate_menu_button(2)

    def invoke_load_tree(self, repo:acp.AssetRepoBase):
        self.repo = repo
        self.explorer.load_tree(self.repo)


class _ResourceReloadTask(GUITaskBase):
    def __init__(self, manager:ResourceManagerPage):
        super().__init__("正在重载本地资源库...")
        self._manager = manager

    def _run(self):
        self._manager.abstract.set_loading(True)
        self.update(0.25, "正在读取本地仓库")
        t = self._manager.after(500, lambda:self.update(0.5))
        self._manager.local_root = Config.get('local_repo_root')
        if self._manager.local_root:
            repo = acp.ArkLocalAssetsRepo(self._manager.local_root)
            self._manager.after_cancel(t)
            self.update(0.75, "正在加载浏览视图")
            self._manager.invoke_load_tree(repo)

    def _on_complete(self):
        self._manager.abstract.set_loading(False)
        self._manager.abstract.show_repo_res_version(self._manager.repo)

class _ResourceSwitchLatestTask(GUITaskBase):
    def __init__(self, manager:ResourceManagerPage):
        super().__init__("正在切换到最新版本...")
        self._manager = manager

    def _run(self):
        self._manager.abstract.set_loading(True)
        if isinstance(self._manager.repo, (acp.ArkIntegratedAssetRepo, acp.ArkLocalAssetsRepo)):
            self.update(0.1, "正在获取网路配置")
            self._manager.client.set_current_network_config()
            self.update(0.3, "正在查询最新版本")
            self._manager.client.set_current_version()
            self.update(0.5, "正在获取资源列表")
            remote = self._manager.client.get_repo()
            self.update(0.8, "正在加载浏览视图")
            if isinstance(self._manager.repo, acp.ArkIntegratedAssetRepo):
                self._manager.repo = acp.ArkIntegratedAssetRepo(self._manager.repo.local, remote)
            else:
                self._manager.repo = acp.ArkIntegratedAssetRepo(self._manager.repo, remote)
            self.update(0.9)
            self._manager.explorer.load_tree(self._manager.repo)

    def _on_complete(self):
        self._manager.abstract.set_loading(False)
        self._manager.abstract.show_repo_res_version(self._manager.repo)


class _ResourceSyncAllFileTask(GUITaskBase):
    def __init__(self, manager:ResourceManagerPage):
        super().__init__("正在同步文件...")
        self._manager = manager

    def _run(self):
        self._manager.abstract.set_loading(True)
        if isinstance(self._manager.repo, acp.ArkIntegratedAssetRepo):
            STEP1_WEIGHT = 0.2
            STEP2_WEIGHT = 0.8
            # Step1
            self.update(0.0, "正在初始化...")
            NEED_DELETE = (acp.FileStatus.DELETE,)
            NEED_DOWNLOAD = (acp.FileStatus.ADD, acp.FileStatus.MODIFY)
            NEED_SYNC = NEED_DELETE + NEED_DOWNLOAD
            infos = self._manager.repo.infos
            infos_len = len(infos)
            filtered_infos = []
            for i, info in enumerate(infos):
                self.update(STEP1_WEIGHT * i / infos_len, f"正在计算变更 {i / infos_len:.1%}")
                if info.status in NEED_SYNC:
                    filtered_infos.append(info)
            # Step2
            filtered_infos_len = len(filtered_infos)
            for i, info in enumerate(filtered_infos):
                self.update(STEP1_WEIGHT + STEP2_WEIGHT * i / filtered_infos_len, f"已完成 {i}/{filtered_infos_len}")
                if info.status in NEED_DELETE:
                    print('D', info)
                    FileSystem.rm(info.local.path)
                elif info.status in NEED_DOWNLOAD:
                    print(info)
                    d = self._manager.client.get_asset(info.remote.data_name, unzip=True)
                    FileSystem.mkdir_for(info.local.path)
                    with open(info.local.path, 'wb') as f:
                        f.write(d)

    def _on_complete(self):
        self._manager.abstract.set_loading(False)
        self._manager.abstract.cmd_switch_latest()


class _AbstractPanel(ctk.CTkFrame):
    master:ResourceManagerPage

    def __init__(self, master:ResourceManagerPage):
        super().__init__(master)
        self.title = ctk.CTkLabel(self, text="资源库概要", image=icon('abstract'), **style('panel_title'))
        self.title.grid(row=0, column=0, **style('panel_title_grid'))
        self.info_local_ver = uic.InfoLabelGroup(self, 1, 0, "当前资源版本号", tight=True)
        self.info_local_ver.show("<未知>")
        self.info_remote_ver = uic.InfoLabelGroup(self, 2, 0, "目标资源版本号", tight=True)
        self.info_remote_ver.show("<未知>")
        self.btn_open = uic.OperationButton(self, 1, 1, "浏览", icon('repo_open'),
                                            command=self.cmd_open)
        self.btn_reload = uic.OperationButton(self, 2, 1, "重载", icon('repo_reload'),
                                              command=self.cmd_reload, **style('operation_button_info'))
        self.btn_switch_latest = uic.OperationButton(self, 1, 2, "切换最新版本", icon('switch_latest'),
                                                     command=self.cmd_switch_latest)
        self.btn_switch_manual = uic.OperationButton(self, 2, 2, "WIP：切换其他版本", icon('switch_manual'),
                                                     **style('operation_button_info'))
        self.btn_sync = uic.OperationButton(self, 1, 3, "同步所有变更", icon('repo_sync'),
                                            command=self.cmd_sync_all_file)
        self.progress = uic.ProgressBarGroup(self, 0, 0, grid_columnspan=1, init_visible=False)
        self.btn_list = (self.btn_open, self.btn_reload, self.btn_switch_latest, self.btn_switch_manual, self.btn_sync)
        self.grid_columnconfigure((0), weight=1)
        self.grid_columnconfigure((1, 2, 3, 4), weight=0)

    def set_loading(self, loading:bool):
        for i in self.btn_list:
            i.configure(state='disabled' if loading else 'normal')
        self.progress.set_visible(loading)

    def show_repo_res_version(self, repo:acp.AssetRepoBase):
        self.info_local_ver.show("<未知>")
        self.info_remote_ver.show("<未知>")
        local_ver = ""
        if isinstance(repo, acp.ArkLocalAssetsRepo):
            local_ver = repo.detect_res_version()
        elif isinstance(repo, acp.ArkIntegratedAssetRepo):
            local_ver = repo.local.detect_res_version()
            self.info_remote_ver.show(repo.remote.version.res, "<未知>")
        self.info_local_ver.show(local_ver, "<未知>")

    def cmd_open(self):
        new_root = fd.askdirectory(mustexist=True)
        if new_root and os.path.isdir(new_root):
            self.cmd_reload()
            Config.set('local_repo_root', new_root)

    def cmd_reload(self):
        task = _ResourceReloadTask(self.master)
        self.progress.bind_task(task)
        task.start()

    def cmd_switch_latest(self):
        task = _ResourceSwitchLatestTask(self.master)
        self.progress.bind_task(task)
        task.start()

    def cmd_sync_all_file(self):
        task = _ResourceSyncAllFileTask(self.master)
        self.progress.bind_task(task)
        task.start()


class _ExplorerPanel(ctk.CTkFrame):
    master:ResourceManagerPage

    def __init__(self, master:ResourceManagerPage):
        super().__init__(master)
        self.title = ctk.CTkLabel(self, text="资源浏览器", image=icon('explorer'), **style('panel_title'))
        self.title.grid(row=0, column=0, **style('panel_title_grid'))
        self.children_map:"dict[acp.FileInfoBase,set[acp.FileInfoBase]]" = None
        self.treeview:"uic.TreeviewFrame[acp.FileInfoBase]" = uic.TreeviewFrame(self, 1, 0, columns=3, empty_tip="列表为空")
        self.treeview.set_column(0, 300, "资源名称")
        self.treeview.set_column(1, 100, "状态")
        self.treeview.set_column(2, 100, "大小")
        self.treeview.set_text_extractor(lambda x:x.basename)
        self.treeview.set_icon_extractor(lambda x:file_icon(x.status))
        self.treeview.set_value_extractor(lambda x:(acp.FileStatus.to_str(x.status), x.get_file_size_str()))
        self.treeview.set_parent_extractor(lambda x:x.parent if x.parent and x.parent.name else None)
        self.treeview.set_children_extractor(lambda x:self.children_map.get(x, None))
        self.treeview.set_on_item_selected(self.master.invoke_inspect)
        self.treeview.set_on_item_double_click(self.master.invoke_inspect_alt)
        self.treeview.set_insert_order(lambda x:sorted(x, key=lambda y:(not isinstance(y, acp.DirFileInfo), y.name)))
        self.grid_rowconfigure((0), weight=0)
        self.grid_rowconfigure((1), weight=1)
        self.grid_columnconfigure((0), weight=1)

    def load_tree(self, repo:acp.AssetRepoBase):
        with TestRT('repo_load_tree'):
            # Clear the current items
            self.treeview.clear()
            # Load the new items
            if repo is not None:
                self.children_map = self.master.repo.get_children_map()
                self.treeview.insert(list(self.children_map[acp.DirFileInfo('')]))


class _InspectorPanel(ctk.CTkFrame):
    master:ResourceManagerPage

    def __init__(self, master:ResourceManagerPage):
        super().__init__(master)
        self.title = ctk.CTkLabel(self, text="资源检视器", image=icon('inspector'), **style('panel_title'))
        self.title.grid(row=0, column=0, **style('panel_title_grid'))
        self.info_name = uic.InfoLabelGroup(self, 1, 0, "名称", tight=True)
        self.info_location = uic.InfoLabelGroup(self, 2, 0, "位置", tight=True)
        self.info_status = uic.InfoLabelGroup(self, 3, 0, "状态", tight=True)
        self.info_size_local = uic.InfoLabelGroup(self, 4, 0, "本地文件大小", tight=True)
        self.info_size_remote = uic.InfoLabelGroup(self, 5, 0, "远程文件大小", tight=True)
        self.info_digest_local = uic.InfoLabelGroup(self, 6, 0, "本地文件哈希", tight=True)
        self.info_digest_remote = uic.InfoLabelGroup(self, 7, 0, "远程文件哈希", tight=True)
        self.grid_columnconfigure((0), weight=1)

    def inspect(self, info:acp.FileInfoBase):
        self.info_name.show(info.basename, "<空>")
        self.info_location.show(info.parent.name, "<根>")
        if isinstance(info, acp.ArkIntegratedFileInfo):
            self.info_status.show(acp.FileStatus.to_str(info.status), "<未知>")
            self.info_size_local.show(f"{info.local.file_size} B", "0 B")
            self.info_size_remote.show(f"{info.remote.file_size if info.remote else 0} B", "0 B")
            self.info_digest_local.show(info.local.md5, "<未知>")
            self.info_digest_remote.show(info.remote.md5 if info.remote else "", "<未知>")
        elif isinstance(info, acp.ArkLocalFileInfo):
            self.info_status.show("尚未检查更新")
            self.info_size_local.show(f"{info.file_size} B", "0 B")
            self.info_size_remote.show(None)
            self.info_digest_local.show(info.md5, "<未知>")
            self.info_digest_remote.show(None)
        elif isinstance(info, acp.DirFileInfo):
            self.info_status.show("文件夹")
            self.info_size_local.show(None)
            self.info_size_remote.show(None)
            self.info_digest_local.show(None)
            self.info_digest_remote.show(None)


class _OperationPanel(ctk.CTkFrame):
    master:ResourceManagerPage

    def __init__(self, master:ResourceManagerPage):
        super().__init__(master)
        self.title = ctk.CTkLabel(self, text="操作", image=icon('operation'), **style('panel_title'))
        self.title.grid(row=0, column=0, **style('panel_title_grid'))
        self.btn_view = uic.OperationButton(self, 1, 0, "查看此文件", icon('file_view')
                                            )
        self.btn_sync = uic.OperationButton(self, 2, 0, "同步此文件", icon('file_sync')
                                                     )
        self.btn_goto = uic.OperationButton(self, 3, 0, "在文件夹中显示", icon('file_goto'),
                                              **style('operation_button_info'))
        self.grid_columnconfigure((0), weight=1)

    def inspect(self, info:acp.FileInfoBase):
        if isinstance(info, (acp.ArkIntegratedFileInfo, acp.ArkLocalFileInfo, acp.DirFileInfo)):
            if not isinstance(info, acp.DirFileInfo) and \
                info.status in (acp.FileStatus.ADD, acp.FileStatus.DELETE, acp.FileStatus.MODIFY):
                self.btn_sync.set_visible(True)
                self.btn_sync.set_command(lambda:self.cmd_sync(info))
            else:
                self.btn_sync.set_visible(False)
                self.btn_sync.set_command(None)
            if not isinstance(info, acp.DirFileInfo) and os.path.exists(info.path):
                self.btn_view.set_visible(True)
                self.btn_view.set_command(lambda:self.master.invoke_view_file(info.path))
                self.btn_goto.set_visible(True)
                self.btn_goto.set_command(lambda:FileSystem.see_file(info.path))
            else:
                self.btn_view.set_visible(False)
                self.btn_view.set_command(None)
                self.btn_goto.set_visible(False)
                self.btn_goto.set_command(None)

    def cmd_sync(self, info:acp.FileInfoBase):
        if isinstance(info, acp.ArkIntegratedFileInfo):
            task = _ResourceSyncFileTask(self.master, info)
            self.master.abstract.progress.bind_task(task)
            task.start()


class _ResourceSyncFileTask(GUITaskBase):
    def __init__(self, manager:ResourceManagerPage, info:acp.ArkIntegratedFileInfo):
        super().__init__("正在同步文件...")
        self._manager = manager
        self._info = info

    def _run(self):
        self._manager.abstract.set_loading(True)
        if isinstance(self._manager.repo, acp.ArkIntegratedAssetRepo) and \
            isinstance(self._info, acp.ArkIntegratedFileInfo):
            if self._info.status == acp.FileStatus.DELETE:
                self.update(0.2, "正在删除...")
                FileSystem.rm(self._info.local.path)
            elif self._info.status in [acp.FileStatus.ADD, acp.FileStatus.MODIFY]:
                self.update(0.2, "正在下载...")
                d = self._manager.client.get_asset(self._info.remote.data_name, unzip=True)
                self.update(0.8, "正在写入...")
                FileSystem.mkdir_for(self._info.local.path)
                with open(self._info.local.path, 'wb') as f:
                    f.write(d)
            self.update(0.9, "正在校验...")
            self._manager.invoke_inspect(self._info)

    def _on_complete(self):
        self._manager.abstract.set_loading(False)
