<!-- 欢迎阅读 Ark-Studio 说明文档 -->
<!-- 仓库：https://github.com/isHarryh/Ark-Studio -->

<!--suppress HtmlDeprecatedAttribute -->
<div align="center" style="text-align:center">
   <h1> Ark-Unpacker </h1>
   <p>
      Arknights Assets Studio | 明日方舟游戏资源集成式管理平台 <br>
      <code><b> WIP </b></code>
   </p>
   <p>
      <img alt="GitHub Top Language" src="https://img.shields.io/github/languages/top/isHarryh/Ark-Studio?label=Python">
      <img alt="GitHub License" src="https://img.shields.io/github/license/isHarryh/Ark-Studio?label=License"/>
   </p>
   <sub>
      <i> This project only supports Chinese docs. If you are an English user, feel free to contact us. </i>
   </sub>
</div>

## 介绍 <sub>Intro</sub>

**正在开发中（This Project is Now Working in Progress...）**

**ArkStudio** 是为游戏《明日方舟》开发的，能够一体化管理游戏资源的非官方项目。

#### 背景
本项目的前身是 [ArkUnpacker](https://github.com/isHarryh/Ark-Unpacker) 解包器。由于后者拷贝所需游戏资源的方法繁琐、不能实现对整个游戏资源库的浏览、不能预览单个游戏文件的内容，因此特地开发此项目，旨在实现对游戏资源库的查看、下载和单向版本控制，以及对游戏资源文件的解包、预览和提取。

#### 实现的功能
1. **资源库管理**
    - [x] 浏览本地资源库
    - [x] 比较并显示本地资源库和官方资源库的差异
    - [ ] 从官方资源库下载或同步文件到本地
    - [ ] 按关键词搜索指定的文件
    - [ ] 切换到指定的资源库版本
2. **AB 文件解包**
    - [x] 浏览 AB 文件的对象列表
    - [x] 预览文本和二进制文件
    - [x] 预览图片文件
    - [ ] 预览音频文件
    - [ ] 区分显示不可提取对象和可提取对象
    - [ ] 提取和批量提取资源文件到本地
    - [ ] 按关键词或类型搜索指定的对象
3. **RGB-A 图片合并**
    - [ ] 选择并显示指定的 RGB 图和 Alpha 图
    - [ ] 导出合并后的图片到本地
    - [ ] 在文件夹中批量实现上述功能
4. **FlatBuffers 数据解码**
    - [ ] 选择指定的二进制文件并显示预测的 Schema
    - [ ] 导出解码后的数据到本地
    - [ ] 在文件夹中批量实现上述功能
5. **其他**
    - [ ] 提供设置选项
    - [ ] 提供教程组件

#### 支持的类型
| Unity类型 | 描述 | 导出格式 |
|:---|:---|:---|
| Sprite | 精灵图 | PNG图片 |
| Texture2D | 二维纹理图 | PNG图片 |
| AudioClip | 音频剪辑 | WAV音频 |
| TextAsset | 文本或字节数据 | 未指定 |

## 注意事项 <sub>Notice</sub>
用户应当在合理的范围内使用本项目。严禁将本项目的软件所提取的游戏资源内容用于商业用途或损害版权方（上海鹰角网络有限公司）的相关利益。

## 使用方法 <sub>Usage</sub>
本项目的 GUI 基于 tkinter 和 customtkinter 开发，采用 Poetry 作为依赖管理系统。

当前项目正处于开发阶段，功能尚不完整，请静候佳音。

## 许可证 <sub>Licensing</sub>
本项目基于 **BSD-3 开源协议**。任何人都可以自由地使用和修改项目内的源代码，前提是要在源代码或版权声明中保留作者说明和原有协议，且不可以使用本项目名称或作者名称进行宣传推广。
