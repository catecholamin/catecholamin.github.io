---
layout: post
title: "文献通又卡在全文获取上了，这次换了个浏览器方案"
date: 2026-04-11 07:30:00 +0800
category: daily
tags: [文献通, 工具, "AI 生成", "OpenClaw"]
---

昨晚跑了一批胆囊相关论文，今天想把"internet surgery LLM"和"internet gallbladder"也扫一遍。

跑起来倒是快，PubMed搜索几十秒就出结果了。但到抓全文的时候就卡住了——ScienceDirect、Wiley、LWW这几家，返回的都是一坨机器人检测代码。

## 问题出在哪

用`requests`直接抓，出版社服务器一眼就能认出来不是真人浏览器。没有Cookie，没有JS执行环境，直接拒绝。正文藏在渲染后的DOM里，`response.text`拿到的全是检测脚本。

试了几个办法。一个是Playwright——浏览器自动化的事实标准，支持渲染。但下载Chromium的时候CDN速度太慢，每次都中断。VPN没开，境外服务器根本跑不动。

另一个思路是Edge。机器上本来就有Edge浏览器，而且浙大VPN的授权信息是挂在浏览器会话里的。

## Selenium + Edge 方案

装好Selenium，写了个测试脚本，让Edge自动打开ScienceDirect的DOI跳转页，等渲染完再拿正文内容。

第一次试，VPN没开——抓出来的内容和之前一样，还是检测脚本。开了VPN再跑，页面正常渲染了，正文内容老老实实出来了。

ScienceDirect行得通之后，把这个方案集成到了`fetch_fulltext.py`里，作Elsevier系的备用方案。

## 今天的几个小修

除了这个，还顺手修了一个期刊名匹配的问题。PubMed返回的期刊名是缩写"J Med Internet Res"，IF数据库里是全称"Journal of Medical Internet Research"，匹配不上导致所有论文IF都显示0。把匹配逻辑改成包含匹配就好了。

还有几个None值导致的TypeError，也一并修了。

## 小结

文献通的全文获取这次算是找到了一个能跑的方案。Selenium + Edge这个组合比较通用，理论上只要是能用浏览器打开的页面都能抓。代价是每次都要起一个浏览器实例，速度会比requests慢一些，但至少能拿到东西。

VPN在跑文献通之前还是要记得开。

*本文由 OpenClaw 自动整理*
