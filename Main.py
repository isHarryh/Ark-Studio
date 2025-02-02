# -*- coding: utf-8 -*-
# Copyright (c) 2024-2025, Harry Huang
# @ BSD 3-Clause License
from src.ArkStudioApp import App
from src.utils.AnalyUtils import TestRT


app = App()
app.mainloop()
print(TestRT.get_avg_time_all())
