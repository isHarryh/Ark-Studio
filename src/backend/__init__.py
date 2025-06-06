# -*- coding: utf-8 -*-
# Copyright (c) 2024-2025, Harry Huang
# @ BSD 3-Clause License


def __add_lz4ak_decompression():
    from UnityPy.helpers import CompressionHelper
    from UnityPy.enums.BundleFile import CompressionFlags
    from .Block import decompress_lz4ak

    # New compression algorithm introduced in Arknights v2.5.04+
    CompressionHelper.DECOMPRESSION_MAP[CompressionFlags.LZHAM] = decompress_lz4ak


__add_lz4ak_decompression()
