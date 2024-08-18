# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
from src.ArkStudioApp import App
from src.utils.AnalyUtils import TestRT


app = App()
app.mainloop()
print(TestRT.get_avg_time_all())
