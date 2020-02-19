---
layout:     post
title:      “在Win10上安装Ubuntu 18”
subtitle:   “学生信，绕不开linux”
date:       2019-10-12
author:     Sunfly
header-img: "img/ubuntu.desktop.jpeg"
cover:      "img/ubuntu.jpg"
catalog: true
tags: linux 生信 ubuntu win10 镜像 bioconda 安装软件
---

学生物信息学，绕不开linux，学linux，最简单的可能就是在win 10自带的ubuntu子系统了吧。参考这个帖子[如何在Windows10上直接运行Linux？](https://baijiahao.baidu.com/s?id=1607159570058814753)，在windows 应用市场下载安装ubuntu，并完成配置，安装一些软件。简述一下安装配置过程中的要点和遇到的一些坑。

# 修改镜像地址
在目录：C:\Users\用户名\AppData\Local\Packages\CanonicalGroupLimited.UbuntuonWindows_79rhkp1fndgsc
\LocalState\rootfs\etc\apt找到sources.list，然后改成阿里云的源
```
deb http://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse
```
随后运行sudo apt-get update
下载安装软件速度大大提升。

# 使用远程桌面登陆
要使用远程桌面登陆必须：
sudo service xrdp restart(重启xrdp服务）

# 复制黏贴
在windows中复制后，在命令行点右键就是粘帖。
在命令行中选中后，按Ctrl+Shift+C是复制。

# 安装bioconda
https://bioconda.github.io/user/install.html#install-conda
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sh Miniconda3-latest-Linux-x86_64.sh
```
反复提示 Unable to establish SSl connection
网上查了好多网页，最终怀疑是https代理问题，使用https时如果想要忽略服务器端证书的校验，可以使用 -k 参数。https://www.cnblogs.com/frankyou/p/6693256.html
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -k
```
可以下载了，但网速太慢，改成清华镜像。
```
wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh
```
不加-k也秒下好了。果然是网络的问题。
然后```bash Miniconda3-latest-Linux-x86_64.sh```
但是使用默认下载源下载安装软件会很慢，所以需要更换国内下载源：
更换为清华：
```
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --set show_channel_urls yes
```
或者更换为中科大：
```
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/free/
conda config --set show_channel_urls yes
```

# 使用bioconda安装软件
```
conda install -y bwa
conda install -y hisat2
conda install -y hmer2 htseq htslib igvtools
conda install -y gatk4
conda install -c bioconda samtools
conda install -c bioconda fastqc
conda install -y bowtie2
conda install -y tabix
conda install -y vcftools
conda install -y samstat
```
## 安装SRA Toolkit
安装bioconda后其实可以在conda下载安装SRA Toolkit https://anaconda.org/daler/sratoolkit ```conda install -c daler sratoolkit``` 但是可能又是网络连接问题，反复失败。于是只能手工安装吧。参考生信技能树的安装方法：
```
## 在这里找到下载地址 http://www.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?view=software 
##创建sratoolkit文件夹，转到该文件夹目录并将文件下载到此文件夹
mkdir sratoolkit &&  cd sratoolkit
wget http://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/2.10.0/sratoolkit.2.10.0-ubuntu64.tar.gz
## 安装
tar zxvf sratoolkit.2.10.0-ubuntu64.tar.gz
~/biosoft/sratoolkit/sratoolkit.2.10.0-ubuntu64/bin/fastdump -h
```

接下来就是自学linux。