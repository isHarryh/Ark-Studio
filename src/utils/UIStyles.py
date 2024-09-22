# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk
from PIL import Image, ImageTk
from ..backend import ArkClient as ac


def icon(icon_key:str):
    if icon_key not in _IconHub.DATA:
        raise KeyError(f"Icon ID not found: {icon_key}")
    rst = _IconHub.DATA[icon_key]
    if isinstance(rst, tuple):
        return tuple(i.get() for i in rst)
    elif isinstance(rst, _DefImage):
        return rst.get()
    else:
        raise TypeError(f"Not recognized value: {rst}")

def file_icon(file_status:int):
    if file_status not in _FileIconHub.DATA:
        raise KeyError(f"File status icon not found: {file_status}")
    return _FileIconHub.DATA[file_status].get()

def style(class_key:str):
    if class_key not in _StyleHub.DATA:
        raise KeyError(f"Style class not found: {class_key}")
    rst = _StyleHub.DATA[class_key].copy()
    lazy_cls = (_DefFont, _DefImage)
    for k, v in rst.items():
        if isinstance(v, lazy_cls):
            rst[k] = v.get()
        elif isinstance(v, tuple):
            new_v = tuple(i.get() if isinstance(i, lazy_cls) else i for i in v)
            rst[k] = new_v
        elif not isinstance(v, (str, int, float)):
            raise TypeError(f"Not recognized style value: {v}")
    return rst

def load_font_asset():
    ctk.FontManager.load_font("assets/fonts/SourceHanSansCN-Medium.otf")

def load_ttk_style(master:tk.Misc):
    _TTkStyleHub.load_style_to(master)

class _KwDict:
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def __getitem__(self, key:str):
        return self._kwargs[key]

    def __eq__(self, other:object):
        if isinstance(other, _KwDict):
            return hash(self) == hash(other)
        return False

    def __hash__(self):
        return hash(tuple(self._kwargs.items()))

class _DefFont:
    """Lazy load ctk font definition record."""
    _CACHE:"dict[int,ctk.CTkFont]" = {}
    _DEFAULT_FONT_FAMILY = 'Source Han Sans CN Medium'
    _DEFAULT_FONT_SIZE = 13

    def __init__(self,
                 family:str=_DEFAULT_FONT_FAMILY,
                 size:int=_DEFAULT_FONT_SIZE,
                 bold:bool=False,
                 italic:bool=False):
        self._data = _KwDict(family=family,
                             size=size,
                             weight='bold' if bold else 'normal',
                             slant='italic' if italic else 'roman')

    def get(self):
        if self._data not in _DefFont._CACHE:
            _DefFont._CACHE[self._data] = ctk.CTkFont(**self._data._kwargs)
        return _DefFont._CACHE[self._data]

    def as_tuple(self):
        return (self._data['family'], self._data['size'], self._data['weight'])

    def dispose(self):
        _DefFont._CACHE.pop(self, None)

class _DefImage:
    """Lazy load ctk image definition record."""
    _CACHE:"dict[int,ctk.CTkImage|ImageTk.PhotoImage]" = {}

    def __init__(self, path:str, size:"tuple[int,int]|int", repaint:str=None, use_ctk:bool=True):
        self._data = _KwDict(path=path,
                              size=size if isinstance(size, tuple) else (size, size),
                              repaint=repaint,
                              use_ctk=use_ctk)
        self._image = None

    def get(self):
        if self._data not in _DefImage._CACHE:
            if self._image is None:
                self._image = Image.open(self._data['path'])
            image = self._image.copy()
            if self._data['repaint'] is not None:
                grayscale = image.convert('L')
                image = Image.new('RGBA', image.size, self._data['repaint'])
                image.putalpha(grayscale)
            if self._data['use_ctk']:
                rst = ctk.CTkImage(image, size=self._data['size'])
            else:
                image = image.resize(self._data['size'], resample=Image.BILINEAR)
                rst = ImageTk.PhotoImage(image)
            self._CACHE[self._data] = rst
        return self._CACHE[self._data]

    def dispose(self):
        _DefImage._CACHE.pop(self._data, None)

class _StyleHub:
    COLOR_WHITE = '#FFF'
    COLOR_BLACK = '#000'
    FONT_XXS = _DefFont(size=10)
    FONT_XS = _DefFont(size=11)
    FONT_S = _DefFont(size=12)
    FONT_M = _DefFont(size=13)
    FONT_MB = _DefFont(size=13)
    FONT_L = _DefFont(size=14)
    FONT_LB = _DefFont(size=14, bold=True)
    FONT_XLB = _DefFont(size=20, bold=True)
    THEME = [
        "#f4f6f9", #[0]
        "#cbd5e3", #[1]
        "#a3b4cd", #[2]
        "#7a93b7", #[3]
        "#5272a1", #[4]
        "#2A528C", #[5]
        "#214170", #[6]
        "#193154", #[7]
        "#102038", #[8]
        "#08101b", #[9]
    ]
    DATA:"dict[str,dict]" = {
        # Banner
        'banner': {'font': FONT_XLB},
        # Menu
        'menu': {'fg_color': THEME[3]},
        'menu_btn': {'font': FONT_LB,
                     'width': 150,
                     'height': 35},
        'menu_btn_regular': {'fg_color': THEME[0],
                             'hover_color': THEME[1],
                             'text_color': THEME[9]},
        'menu_btn_active': {'fg_color': THEME[5],
                            'hover_color': THEME[6],
                            'text_color': THEME[0]},
        # Panel
        'panel_title': {'font': FONT_MB,
                        'text_color': THEME[3],
                        'anchor': 'w',
                        'compound': 'left'},
        'panel_title_grid': {'padx': 10,
                             'pady': 10,
                             'sticky': 'nw'},
        # Button
        'operation_button': {'font': FONT_S},
        'operation_button_info': {'fg_color': (THEME[1], THEME[8]),
                                  'hover_color': (THEME[2], THEME[7]),
                                  'text_color': (THEME[7], THEME[2]),
                                  'border_color': (THEME[5], THEME[5]),
                                  'border_width': 1},
        'operation_button_grid': {'padx': (5, 10),
                                  'pady': (5, 10),
                                  },
        # Label
        'info_label_head': {'font': FONT_MB,
                            'corner_radius': 10,
                            'fg_color': THEME[1],
                            'text_color': THEME[5],
                            'anchor': 'e'},
        'info_label_body': {'font': FONT_S,
                            'anchor': 'nw'},
        'info_label_head_grid': {'padx': 5,
                                 'pady': 0,
                                 'sticky': 'nw'},
        'info_label_body_grid': {'padx': (10, 5),
                                 'pady': 0,
                                 'sticky': 'nw'},
        'info_label_grid': {'padx': 5,
                            'pady': 5,
                            'sticky': 'ew'},
        # Progress bar
        'progress_bar_head': {'font': FONT_M,
                              'text_color': THEME[5],
                              'anchor': 'w'},
        'progress_bar_body': {'font': FONT_S,
                              'text_color': (THEME[3], THEME[6]),
                              'anchor': 'e'},
        'progress_bar_head_grid': {'padx': 5,
                                   'pady': 0,
                                   'sticky': 'nw'},
        'progress_bar_body_grid': {'padx': 5,
                                   'pady': 0,
                                   'sticky': 'ne'},
        'progress_bar_grid': {'padx': 10,
                              'pady': 5,
                              'sticky': 'ew'},
        # Treeview
        'treeview_empty_tip': {'font': FONT_L},
        # Audio Controller
        'audio_ctrl_name': {'font': FONT_M,
                            'anchor': 'center'},
        'audio_ctrl_info': {'font': FONT_S,
                            'anchor': 'center'},
        'audio_ctrl_operation_grid': {'padx': 10,
                                      'pady': (0, 5)},
    }

class _IconHub:
    DATA:"dict[str,_DefImage|tuple[_DefImage]]" = {
        'progress': _DefImage('assets/icons_ui/i_rhombus.png', 18, repaint=_StyleHub.THEME[5]),
        'explorer': _DefImage('assets/icons_ui/i_sitemap.png', 18, repaint=_StyleHub.THEME[3]),
        'inspector': _DefImage('assets/icons_ui/i_file.png', 18, repaint=_StyleHub.THEME[3]),
        'abstract': _DefImage('assets/icons_ui/i_archive.png', 18, repaint=_StyleHub.THEME[3]),
        'operation': _DefImage('assets/icons_ui/i_tools.png', 18, repaint=_StyleHub.THEME[3]),
        'repo_open': _DefImage('assets/icons_ui/i_binoculars.png', 18, repaint=_StyleHub.THEME[0]),
        'repo_reload': _DefImage('assets/icons_ui/i_synchronization.png', 18, repaint=_StyleHub.THEME[7]),
        'switch_latest': _DefImage('assets/icons_ui/i_arrow_up.png', 18, repaint=_StyleHub.THEME[0]),
        'switch_manual': _DefImage('assets/icons_ui/i_arrow_right.png', 18, repaint=_StyleHub.THEME[7]),
        'repo_sync': _DefImage('assets/icons_ui/i_download.png', 18, repaint=_StyleHub.THEME[0]),
        'file_view': _DefImage('assets/icons_ui/i_paste.png', 18, repaint=_StyleHub.THEME[0]),
        'file_sync': _DefImage('assets/icons_ui/i_download.png', 18, repaint=_StyleHub.THEME[0]),
        'file_goto': _DefImage('assets/icons_ui/i_browser.png', 18, repaint=_StyleHub.THEME[7]),
        'file_open': _DefImage('assets/icons_ui/i_paste.png', 18, repaint=_StyleHub.THEME[0]),
        'file_reload': _DefImage('assets/icons_ui/i_synchronization.png', 18, repaint=_StyleHub.THEME[7]),
        'file_extract': _DefImage('assets/icons_ui/i_upload.png', 18, repaint=_StyleHub.THEME[0]),
    }

class _FileIconHub:
    DATA:"dict[int,_DefImage]" = {
        ac.FileStatus.DIRECTORY: _DefImage('assets/icons_file/i_folder.png', 18, use_ctk=False),
        ac.FileStatus.UNCHECKED: _DefImage('assets/icons_file/i_unchecked.png', 18, use_ctk=False),
        ac.FileStatus.OKAY: _DefImage('assets/icons_file/i_file.png', 18, use_ctk=False),
        ac.FileStatus.ADD: _DefImage('assets/icons_file/i_add.png', 18, use_ctk=False),
        ac.FileStatus.ADDED: _DefImage('assets/icons_file/i_added.png', 18, use_ctk=False),
        ac.FileStatus.MODIFY: _DefImage('assets/icons_file/i_modify.png', 18, use_ctk=False),
        ac.FileStatus.MODIFIED: _DefImage('assets/icons_file/i_modified.png', 18, use_ctk=False),
        ac.FileStatus.DELETE: _DefImage('assets/icons_file/i_delete.png', 18, use_ctk=False),
        ac.FileStatus.DELETED: _DefImage('assets/icons_file/i_deleted.png', 18, use_ctk=False),
    }

class _TTkStyleHub:
    @staticmethod
    def load_style_to(master:tk.Misc):
        ttk_style = ttk.Style(master)
        ttk_style.theme_use('default')
        # https://www.tcl-lang.org/man/tcl8.6/TkCmd/ttk_treeview.htm
        ttk_style.configure('Treeview',
                            font=_StyleHub.FONT_XXS.as_tuple(),
                            padding=2,
                            foreground=_StyleHub.COLOR_WHITE,
                            background=_StyleHub.COLOR_WHITE,
                            fieldbackground='transparent')
        ttk_style.map('Treeview', background=[('selected', _StyleHub.THEME[4])])
        ttk_style.configure('Treeview.Heading',
                            font=_StyleHub.FONT_XS.as_tuple(),
                            padding=4,
                            foreground=_StyleHub.THEME[6],
                            background=_StyleHub.THEME[0],
                            relief='none')
        ttk_style.map('Treeview.Heading',
                      background=[('active', _StyleHub.THEME[1])],)
        # https://www.tcl-lang.org/man/tcl8.6/TkCmd/ttk_scrollbar.htm
        ttk_style.configure('TScrollbar', relief='none')
