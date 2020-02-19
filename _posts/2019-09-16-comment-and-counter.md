---
layout: post
title: 添加评论和网站计数功能
author: Sunfly
catalog: false
header-img: "https://api.dujin.org/bing/1920.php"
tags: blog 评论 网站计数
---
博客模版的网站计数不能用，网上搜索了一下，找到了[不蒜子](http://busuanzi.ibruce.info/)，提供方便的网页计数功能，按照作者提供的教程[两行代码 搞定计数](http://ibruce.info/2015/04/04/busuanzi/) 在page和post中添加了如下代码，搞定。真是简单易用，感谢作者。

```
 <script async src="//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js"></script>
 <span id="busuanzi_container_site_pv"><span id="busuanzi_value_site_pv"></span></span>
```

博客的评论系统经历了一番折腾，之前用gitalk一直不成功，不知道问题出在哪里，然后又搜到了[Vssue](https://vssue.js.org/zh/),发现是一个简单易用的评论系统。根据[说明文档](<https://vssue.js.org/zh/guide/getting-started.html>)在post中添加了如下代码，简单易用，顺利搞定。title后面要改成: location.pathname，不然就只有一个issue，不是每篇文章生成一个issue了。

```
<head>
  <!-- Vssue 的样式文件 -->
  <link rel="stylesheet" href="https://unpkg.com/vssue/dist/vssue.min.css">
</head>
<body>
  <div id="vssue"></div>
<script src="https://unpkg.com/vue/dist/vue.min.js"></script>
<script src="https://unpkg.com/vssue/dist/vssue.github.min.js"></script>	
  <script>
    new Vue({
      el: '#vssue',

      data: {
        title: location.pathname,

        options: {
          owner: ' ',
          repo: '  ',
          clientId: ' ',
          clientSecret: ' ', 
        },
      },

      template: `<vssue :title="title" :options="options"></vssue>`,
    })
  </script>
</body>
```


