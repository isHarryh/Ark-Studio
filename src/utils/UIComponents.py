# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk
from PIL import Image, ImageTk
from typing import Callable, Any, TypeVar, Generic

from .UIStyles import style, icon
from .UIConcurrent import GUITaskBase
from ..utils.AnalyUtils import DurationFormatter
from ..utils.BiMap import BiMap
from .AudioComposer import AudioComposer, AudioTrack


################
# Base Classes #
################

class HidableGridWidget(tk.Grid):
    """Hidable widget base class for gird layout."""

    def __init__(self,
                 grid_row:int,
                 grid_column:int,
                 grid_rowspan:int=1,
                 grid_columnspan:int=1,
                 init_visible:bool=True,
                 **grid_addition:Any):
        self.__grid_kwargs = grid_addition
        self.__grid_kwargs.update({'row': grid_row,
                                   'column': grid_column,
                                   'rowspan': grid_rowspan,
                                   'columnspan': grid_columnspan})
        self.set_visible(init_visible)

    def set_visible(self, value:bool):
        """Sets the visibility of the widget."""
        if value:
            self.grid(**self.__grid_kwargs)
        else:
            self.grid_remove()
        self.__visible = value

    def is_visible(self):
        """Gets the visibility of the widget."""
        return self.__visible

##########################
# Frequent Used Controls #
##########################

class OperationButton(ctk.CTkButton, HidableGridWidget):
    """Operation button widget."""

    def __init__(self,
                 master:ctk.CTkFrame,
                 grid_row:int,
                 grid_column:int,
                 text:str,
                 image:ctk.CTkImage=None,
                 command:"Callable[[],Any]"=None,
                 **kwargs):
        ctk.CTkButton.__init__(self, master, text=text, image=image, command=command,
                               **style('operation_button'), **kwargs)
        HidableGridWidget.__init__(self, grid_row, grid_column, init_visible=True, **style('operation_button_grid'))

    def set_command(self, command:"Callable[[], Any]"):
        """Sets the active command of the button, `None` for disable the command."""
        self.configure(command=command)

class InfoLabelGroup(ctk.CTkFrame, HidableGridWidget):
    """Information label group widget."""

    def __init__(self,
                 master:ctk.CTkFrame,
                 grid_row:int,
                 grid_column:int,
                 head_text:str,
                 body_text:str="",
                 tight:bool=False,
                 init_visible:bool=True):
        ctk.CTkFrame.__init__(self, master, fg_color='transparent')
        HidableGridWidget.__init__(self, grid_row, grid_column, init_visible=init_visible,
                                    **style('info_label_grid'))
        self._head = ctk.CTkLabel(self, text=head_text, **style('info_label_head'))
        self._head.grid(row=0, column=0, **style('info_label_head_grid'))
        self._body = ctk.CTkLabel(self, text=body_text, **style('info_label_body'))
        self._body.grid(row=0 if tight else 1, column=1 if tight else 0, **style('info_label_body_grid'))
        self.set_body_text(body_text)

    def show(self, value:str="", placeholder:str=""):
        """Shows a new text, `None` for hiding this label."""
        if value is None:
            self.set_visible(False)
        else:
            self.set_visible(True)
            self.set_body_text(value, placeholder)

    def set_body_text(self, value:str="", placeholder:str=""):
        """Sets a new body text;"""
        if value:
            self._body.configure(text=value)
        else:
            self._body.configure(text=placeholder)
        self._text = value

class ProgressBarGroup(ctk.CTkFrame, HidableGridWidget):
    """Progress bar group widget."""

    def __init__(self,
                 master:ctk.CTkFrame,
                 grid_row:int,
                 grid_column:int,
                 grid_rowspan:int=1,
                 grid_columnspan:int=1,
                 head_text:str="",
                 body_text:str="",
                 init_visible:bool=True):
        ctk.CTkFrame.__init__(self, master)
        HidableGridWidget.__init__(self, grid_row, grid_column, grid_rowspan, grid_columnspan, init_visible,
                                    **style('progress_bar_grid'))
        self._head = ctk.CTkLabel(self, text=head_text, image=icon('progress'), compound='left',
                                  **style('progress_bar_head'))
        self._head.grid(row=0, column=0, **style('progress_bar_head_grid'))
        self._head.configure(text=head_text)
        self._body = ctk.CTkLabel(self, text=body_text, **style('progress_bar_body'))
        self._body.grid(row=0, column=2, **style('progress_bar_body_grid'))
        self._body.configure(text=body_text)
        self._prog = ctk.CTkProgressBar(self)
        self._prog.grid(row=0, column=1)

    def set_head_text(self, value:str):
        """Sets a new head text."""
        self._head.configure(text=value)

    def bind_task(self, task:GUITaskBase):
        """Binds the progress bar to a task."""
        self._prog.configure(variable=task.observable_progress)
        self._body.configure(textvariable=task.observable_message)

###############################
# Specialized Preview Widgets #
###############################

_ITEM_TYPE = TypeVar('_ITEM_TYPE')

class TreeviewFrame(ctk.CTkFrame, HidableGridWidget, Generic[_ITEM_TYPE]):
    """Treeview frame widget."""

    def __init__(self, master:ctk.CTkFrame, grid_row:int, grid_column:int, columns:int=1, tree_mode:bool=True, empty_tip:str=""):
        ctk.CTkFrame.__init__(self, master, fg_color='transparent')
        HidableGridWidget.__init__(self, grid_row, grid_column, init_visible=True, sticky='nsew')
        self._inited = False
        # Init settings
        self._tree_mode = tree_mode
        self._columns = tuple(range(1, columns)) if columns > 1 else ()
        self._columns_settings = {}
        self.grid_rowconfigure((0), weight=1)
        self.grid_columnconfigure((0), weight=1)
        # Post settings
        self._text_of:"Callable[[_ITEM_TYPE],str]" = lambda _:''
        self._icon_of:"Callable[[_ITEM_TYPE],ImageTk.PhotoImage]" = lambda _:None
        self._value_of:"Callable[[_ITEM_TYPE],tuple]" = lambda _:()
        self._parent_of:"Callable[[_ITEM_TYPE],_ITEM_TYPE]" = lambda _:None
        self._children_of:"Callable[[_ITEM_TYPE],list[_ITEM_TYPE]]" = lambda _:None
        self._on_item_selected:"Callable[[_ITEM_TYPE],None]" = lambda _:None
        self._on_item_double_click:"Callable[[_ITEM_TYPE],None]" = lambda _:None
        self._insert_sorter:"Callable[[list[_ITEM_TYPE]],list[_ITEM_TYPE]]" = lambda x:x
        # Runtime variables
        self.treeview:ttk.Treeview = None
        self.iid2item:"BiMap[int,_ITEM_TYPE]" = None
        self._scroll_bar = None
        self._sort_reverse = False
        # Show empty tip
        self._empty_tip_label = ctk.CTkLabel(self, text=empty_tip, **style('treeview_empty_tip'))
        self._empty_tip_label.grid(row=0, column=0)

    def set_column(self, column_index:int, pref_width:int, head_text:str, anchor:str='nw'):
        """Sets the detailed config of the specified column. Index starts from `0`."""
        column = f'#{column_index}'
        self._columns_settings[column_index] = lambda: (
            self.treeview.heading(column,
                                  text=head_text,
                                  anchor='nw',
                                  command=lambda:self._sort_by_column(column)),
            self.treeview.column(column,
                                 width=pref_width,
                                 minwidth=pref_width // 2, anchor=anchor)
        )

    def set_text_extractor(self, consumer:"Callable[[_ITEM_TYPE],str]"):
        """Sets the item text string extractor."""
        self._text_of = consumer

    def set_icon_extractor(self, consumer:"Callable[[_ITEM_TYPE],ImageTk.PhotoImage]"):
        """Sets the item icon image extractor."""
        self._icon_of = consumer

    def set_value_extractor(self, consumer:"Callable[[_ITEM_TYPE],tuple]"):
        """Sets the item value extractor."""
        self._value_of = consumer

    def set_parent_extractor(self, consumer:"Callable[[_ITEM_TYPE],_ITEM_TYPE]"):
        """Sets the item parent extractor. Valid only in tree mode."""
        if not self._tree_mode:
            raise RuntimeError("Only supported in tree mode")
        self._parent_of = consumer

    def set_children_extractor(self, consumer:"Callable[[_ITEM_TYPE],list[_ITEM_TYPE]]"):
        """Sets the item children extractor. Valid only in tree mode."""
        if not self._tree_mode:
            raise RuntimeError("Only supported in tree mode")
        self._children_of = consumer

    def set_on_item_selected(self, consumer:"Callable[[_ITEM_TYPE],None]"):
        """Sets a callback that will be called when an item is selected."""
        self._on_item_selected = consumer

    def set_on_item_double_click(self, consumer:"Callable[[_ITEM_TYPE],None]"):
        """Sets a callback that will be called when an item has been double clicked."""
        self._on_item_double_click = consumer

    def set_insert_order(self, sorter:"Callable[[list[_ITEM_TYPE]],list[_ITEM_TYPE]]"):
        """Sets a sorter that sorts the item list to be inserted."""
        self._insert_sorter = sorter

    def clear(self):
        """Clears the whole treeview and resets all data. Must be invoked before any `insert` action."""
        # Treeview reset
        if self.treeview:
            self.treeview.destroy()
        self.treeview = ttk.Treeview(self, columns=self._columns, height=20)
        for i in self._columns_settings.values():
            i()
        self.treeview.grid(row=0, column=0, padx=(5, 0), pady=(0, 5), sticky='nsew')
        self.treeview.tag_bind('general_tag', '<<TreeviewOpen>>', self._item_opened)
        self.treeview.tag_bind('general_tag', '<<TreeviewSelect>>', self._item_selected)
        self.treeview.bind('<Double-1>', self._item_double_click)
        # Scroll bar reset
        self._scroll_bar = ctk.CTkScrollbar(self, orientation='vertical', command=self.treeview.yview)
        self._scroll_bar.grid(row=0, column=1, sticky='ns')
        self.treeview.configure(yscrollcommand=self._scroll_bar.set)
        # IID map reset
        self.iid2item = BiMap()
        self._inited = True

    def insert(self, items:"list[_ITEM_TYPE]"):
        """Inserts an item list."""
        for i in self._insert_sorter(items):
            self._insert_one(i)

    def _insert_one(self, item:_ITEM_TYPE):
        if not self._inited:
            raise RuntimeError("Treeview not initialized")
        if item not in self.iid2item.values():
            # Insert parent items first
            parent = self._parent_of(item)
            if parent and parent not in self.iid2item.values():
                self.insert(parent)
            # Insert this item
            iid = self.treeview.insert(
                self.iid2item.get_key(parent, '') if parent else '',
                tk.END,
                text=self._text_of(item),
                image=self._icon_of(item),
                values=self._value_of(item),
                tags=('general_tag')
                )
            self.iid2item[iid] = item
            # Insert a pre-contained item into this item if it it has children
            if self._children_of(item):
                self.treeview.insert(iid, tk.END, text="")

    def _delete_one(self, *iid:int):
        if not self._inited:
            raise RuntimeError("Treeview not initialized")
        for i in iid:
            # Delete the descendants items first
            self._delete_one(*self.treeview.get_children(i))
            # Delete this item
            self.treeview.delete(i)
            if i in self.iid2item.keys():
                del self.iid2item[i]

    def _sort_by_column(self, column:str):
        if not self._inited:
            raise RuntimeError("Treeview not initialized")
        if self._tree_mode:
            return # Sorting is not supported in tree mode
        # Sort the items
        if column == '#0':
            # For the display column, just sort by the raw insert order
            l = [self.iid2item.get_value(iid) for iid in self.treeview.get_children('')]
            l = self._insert_sorter(l)
            for i, item in enumerate(reversed(l) if self._sort_reverse else l):
                self.treeview.move(self.iid2item.get_key(item), '', i)
        else:
            # For value columns, sort by the cell value
            l = [(self.treeview.set(iid, column), iid) for iid in self.treeview.get_children('')]
            l.sort(reverse=self._sort_reverse)
            for i, (_, iid) in enumerate(l):
                self.treeview.move(iid, '', i)
        self._sort_reverse = not self._sort_reverse

    def _item_opened(self, _:tk.Event):
        iid = self.treeview.selection()[0]
        item = self.iid2item.get_value(iid)
        # Clear the current descendants of this item
        self._delete_one(*self.treeview.get_children(iid))
        # Insert the children of this item
        children = self._children_of(item)
        if children:
            self.insert(children)

    def _item_selected(self, _:tk.Event):
        iid = self.treeview.selection()[0]
        self._on_item_selected(self.iid2item.get_value(iid))

    def _item_double_click(self, event:tk.Event):
        iid = self.treeview.identify('item', event.x, event.y)
        self._on_item_double_click(self.iid2item.get_value(iid))


class TextPreviewer(ctk.CTkFrame, HidableGridWidget):
    _START = 0.0
    _END = 'end'

    def __init__(self, master:ctk.CTkFrame, grid_row:int, grid_column:int, empty_tip:str=""):
        ctk.CTkFrame.__init__(self, master, fg_color='transparent')
        HidableGridWidget.__init__(self, grid_row, grid_column, init_visible=True, sticky='nsew')
        self.display = ctk.CTkTextbox(self, state='disabled', wrap='none')
        self.display.grid(row=0, column=0, sticky='nsew')
        self.grid_rowconfigure((0), weight=1)
        self.grid_columnconfigure((0), weight=1)
        self._empty_tip = empty_tip
        self.show(None)

    def show(self, value:"bytes|None"):
        # TODO Perf of large text (>5MB)
        self.display.configure(state='normal')
        self.display.delete(TextPreviewer._START, TextPreviewer._END)
        if value:
            decoded = value.decode(errors='replace')
            self.display.insert(TextPreviewer._START, decoded)
        else:
            self.display.insert(TextPreviewer._START, self._empty_tip)
        self.display.configure(state='disabled')


class ImagePreviewer(ctk.CTkFrame, HidableGridWidget):
    _FILL = 0.66667

    def __init__(self, master:ctk.CTkFrame, grid_row:int, grid_column:int, empty_tip:str=""):
        ctk.CTkFrame.__init__(self, master, fg_color='transparent')
        HidableGridWidget.__init__(self, grid_row, grid_column, init_visible=True, sticky='nsew')
        self.display = ctk.CTkLabel(self, compound='bottom')
        self.display.grid(row=0, column=0, pady=5, sticky='ew')
        self.info = ctk.CTkLabel(self, anchor='center')
        self.info.grid(row=1, column=0, sticky='ew')
        self.grid_rowconfigure((0), weight=1)
        self.grid_rowconfigure((1), weight=0)
        self.grid_columnconfigure((0), weight=1)
        master.bind('<Configure>', self._on_resize)
        self._empty_tip = empty_tip
        self._tk_image = None
        self._size_request = (self.display.winfo_width(), self.display.winfo_height())
        self._size_current = (-1, -1)
        self._aspect_ratio = 1
        self.show(None)

    def show(self, value:"Image.Image|None"):
        # TODO Pref of large image (>2000px*2000px)
        if value:
            self._tk_image = ctk.CTkImage(value, size=value.size)
            self._size_current = value.size
            self._aspect_ratio = value.width / value.height
            self.display.configure(text="")
            self.info.configure(text=f"{value.width} * {value.height}")
        else:
            self._tk_image = ctk.CTkImage(Image.new('RGBA', (1, 1)))
            self._size_current = (1, 1)
            self._aspect_ratio = 1.0
            self.display.configure(text=self._empty_tip)
            self.info.configure(text="")
        self.display.configure(image=self._tk_image)
        self._fit()

    def _fit(self):
        if self._tk_image and self._size_request != self._size_current:
            w, h = self._size_request
            ratio = w / h
            if ratio > self._aspect_ratio:
                w = h * self._aspect_ratio
            else:
                h = w / self._aspect_ratio
            size_real = (int(w * ImagePreviewer._FILL), int(h * ImagePreviewer._FILL))
            self._tk_image.configure(size=size_real)
            self._size_current = self._size_request

    def _on_resize(self, event:tk.Event):
        self._size_request = (event.width, event.height)
        self._fit()


class AudioController(ctk.CTkFrame, HidableGridWidget):
    def __init__(self, master:"AudioPreviewer", grid_row:int, grid_column:int, audio_name:str, audio_data:bytes):
        ctk.CTkFrame.__init__(self, master, fg_color='transparent')
        HidableGridWidget.__init__(self, grid_row, grid_column, init_visible=True, sticky='ew')
        self.track = AudioTrack(audio_data)
        self.name = ctk.CTkLabel(self, **style('audio_ctrl_name'))
        self.name.grid(row=0, column=0, columnspan=3)
        self.name.configure(text=audio_name)
        self.info = ctk.CTkLabel(self, **style('audio_ctrl_info'))
        self.info.grid(row=1, column=0, columnspan=3)
        self.info.configure(text=f"{self.track.duration} s | " + \
                            f"{self.track.channels} Chs | " + \
                            f"{self.track.bytes_per_sample * 8} bits | " + \
                            f"{self.track.sample_rate} Hz")
        self.var_duration = tk.DoubleVar(self, value=0.0)
        self.time_cur = ctk.CTkLabel(self, text=DurationFormatter.apply(0.0), **style('audio_ctrl_info'))
        self.time_cur.grid(row=2, column=0, sticky='w', **style('audio_ctrl_operation_grid'))
        self.time_end = ctk.CTkLabel(self, text=DurationFormatter.apply(self.track.duration), **style('audio_ctrl_info'))
        self.time_end.grid(row=2, column=2, sticky='e', **style('audio_ctrl_operation_grid'))
        self.slider = ctk.CTkSlider(self, from_=0.0, to=self.track.duration, command=self._slider_action, variable=self.var_duration)
        self.slider.grid(row=3, column=0, columnspan=3, sticky='ew', **style('audio_ctrl_operation_grid'))
        self.btn_play = ctk.CTkButton(self, text='播放', image=icon('audio_play'), command=self._btn_play_action)
        self.btn_play.grid(row=4, column=1, **style('audio_ctrl_operation_grid'))
        self.btn_play_is_playing_cache = False
        self.after_id = None
        self.grid_columnconfigure((0, 1, 2), weight=1)

    def _slider_action(self, value:float):
        self.time_cur.configure(text=DurationFormatter.apply(value))
        flag = self.track.is_playing()
        self.push_status(False)
        self.push_status(flag)

    def _btn_play_action(self):
        self.push_status(not self.track.is_playing())

    def pull_status(self):
        # Sync duration
        new_duration = self.track.get_playing_duration()
        self.var_duration.set(new_duration)
        self.time_cur.configure(text=DurationFormatter.apply(min(new_duration, self.track.duration)))
        # Sync playing status
        self.push_status(self.track.is_playing())
        # Register the next run
        if self.after_id is not None:
            self.after_id = self.after(1, self.pull_status)

    def push_status(self, status:bool):
        if status != self.btn_play_is_playing_cache:
            self.btn_play_is_playing_cache = status
            if status:
                # Switch to playing mode
                # Reset duration to zero if previous playing has completed
                if self.var_duration.get() >= self.track.duration:
                    self.var_duration.set(0.0)
                # Reload track and start to play
                AudioComposer.load(self.track)
                self.track.play(self.var_duration.get())
                # Enable scheduled refreshing task
                self.after_id = self.after(1, self.pull_status)
                # Toggle button status
                self.btn_play.configure(text='暂停', image=icon('audio_pause'))
            else:
                # Switch to paused mode
                # Disable scheduled refreshing task
                if self.after_id:
                    self.after_cancel(self.after_id)
                    self.after_id = None
                # Stop playing
                self.track.stop()
                # Toggle button status
                self.btn_play.configure(text='播放', image=icon('audio_play'))

    def dispose(self):
        self.push_status(False)
        self.track.dispose()


class AudioPreviewer(ctk.CTkFrame, HidableGridWidget):
    def __init__(self, master:ctk.CTkFrame, grid_row:int, grid_column:int, empty_tip:str=""):
        ctk.CTkFrame.__init__(self, master, fg_color='transparent')
        HidableGridWidget.__init__(self, grid_row, grid_column, init_visible=True, sticky='nsew')
        self.info = ctk.CTkLabel(self, anchor='center')
        self.info.grid(row=0, column=0, sticky='ew')
        self.controllers:"list[AudioController]" = []
        self.grid_columnconfigure((0), weight=1)
        self._empty_tip = empty_tip
        self.show(None)

    def show(self, value:"dict[str,bytes]|None"):
        # Clear previous audios
        for i in self.controllers:
            i.dispose()
            i.set_visible(False)
        self.controllers.clear()
        if isinstance(value, dict):
            # Add current audios
            for i, (k, v) in enumerate(value.items()):
                self.controllers.append(AudioController(self, i + 1, 0, k, v))
            self.info.configure(text="")
        else:
            self.info.configure(text=self._empty_tip)
