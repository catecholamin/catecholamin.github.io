---
layout: post
title: 解决GO和KEGG作图的问题
tags: R语言 GO KEGG 生物信息学
---
1. 代码里没有创建文件夹的语句，于是死活都没法生成文件，因为生成的图片是要放在当前目录的figure文件夹下的，但当前目录并没有figure文件夹，于是死循环。新建一个figure文件夹后，问题解决。
2. 通过notepad++打开tsv文件来删除最后一行无数据的废行解决了这个报错： Removed 1 rows containing missing values  
3. 不需要转换成TSV，可以直接处理CSV。另外xlsx另存为CSV就好了，不需要再用什么别的工具。
4. 转换好的文本用notepad++打开看看，可以找到一些问题的解决方法。
5. 参考了这篇文章：[#基因组干货#之烂大街的GO、KEGG分析作图](https://www.jianshu.com/p/462423702851)

