---
layout: post
title: "从 github.io 到 996196.xyz：一个没什么人看的博客的搬家档案"
subtitle: 七年的博客，两个晚上，和一堆看起来都对的错
date: 2026-10-24
categories: 技术
cover: /img/cover-20261024-migration.jpg
tags: [Cloudflare Pages, 域名, DNS, 评论系统, Twikoo, MongoDB, Jekyll, AI 生成, Hermes]
---

这个博客在 GitHub Pages 上放了七年。一直能用，但国内打开越来越慢，有时候干脆打不开。数据也不好看：我拿 Cloudflare 的统计测了一下，同一个页面在国内访问，首字节偶尔要三四秒。

于是决定搬。

这篇不写心路历程，只记技术细节和踩过的坑，算是给自己留一份施工档案。如果你也要搬，能省点时间。

## 一、为什么选 Cloudflare Pages

GitHub Pages 的问题是它在中国大陆没有节点，访问要绕出去。我试过的替代方案：

| 平台 | 国内实测 | 结论 |
|---|---|---|
| GitHub Pages | 1/3 次成功 | 时通时断，不能用 |
| Vercel | 慢，偶发无法访问 | 排除 |
| Netlify | 0.86–2.28s，稳定 | 可用，但只做后端 |
| **Cloudflare Pages** | **0.70–2.05s，10/10** | **选它** |

Cloudflare 的节点在香港、台湾、新加坡都有，国内走的是最近的边缘节点，比我预想的好。

搬家过程本身没什么技术含量：新建 Pages 项目，连 GitHub 仓库，填构建命令。

```bash
export LANG=C.UTF-8 && export LC_ALL=C.UTF-8 && export RUBYOPT=-EUTF-8 && bundle install && jekyll build
```

输出目录填 `_site`。

**这里有个坑**：我的仓库里有 62 个中文文件名，如果不设 `LANG` 和 `RUBYOPT=-EUTF-8`，Jekyll 构建会报 `Encoding::UndefinedConversionError` 直接失败。这四个环境变量不是可有可无的装饰。

构建第一次跑通之后，`catecholamin.pages.dev` 就可以访问了，国内测了十次全通。

![迁移前后的访问路径对比](/img/blog-migration-1-path.svg)

左边是原来的样子：请求绕出去再绕回来，实测三次只有一次能成。右边是现在，直接落到最近的边缘节点。同一台机器、同一网络环境下连续测的。

![机房里的一捆网线](/images/2026-10-24-1.jpg){: width="1200" height="800"}
<p class="image-credit">Photo by Scott Rodgerson on Unsplash</p>

## 二、买了个域名

有了稳定站点，剩下一个问题：`catecholamin.pages.dev` 这个地址太长，念不出来。

我对域名的要求很奇怪，只有一条：**要好记，而且好记的理由得是我自己的**。所以没去抢什么 `sunfly.com`，那玩意儿 1996 年就被人注册了，现在挂在 Sedo 上议价。

`.xyz` 这个后缀有个特殊政策，叫 **1.111B Class**：所有 6 到 9 位纯数字的域名，注册、续费、转移统统 99 美分一年。因为数字组合有 11.11 亿个，注册局干脆打包做低价。

于是我开始找号。过程挺有意思，记一下思路：

**第一层：按键盘字母编码**

`sunfly` 在手机九宫格上对应 786359（s=7 u=8 n=6 f=3 l=5 y=9）。这个号当时还可注册。

**第二层：按字母形状**

`s` 像 5，`u` 像 0，`n` 像 2，`f` 像 3，`l` 像 1 —— 拼出 502314。这个号很漂亮，但查下来 2026 年 5 月被人抢了。

**第三层：老手机按几下**

功能机时代打字母要连按。`sunfly` 每个字母的按键次数是 4-2-2-1-3-3，得 422133。

**第四层：字母序号**

`s` 是第 19 个字母，`f` 是第 6 个，拼成 **196**。

最后我选了 **996196.xyz**。

前半段 **996** 是那个我们都懂的工作时长，后半段 **196** 是我名字首字母在字母表里的位置。念出来是"九九六，一九六"，两组三字，停顿清楚。

价格方面有个重要发现：**不是所有注册商都执行 99 美分政策**。

```
OnlyDomains   首年 $1.04，续费 $14.49    ← 陷阱
Namecheap     首年 €0.75，续费 €0.75     ← 真便宜
Cloudflare    $12.30 一年                ← 不参与
```

OnlyDomains 的页面上写得很直白：6 位数字域名按"标准注册费"收。如果你只看到首年价就下单，第二年账单会让你清醒。

**判断一个域名贵不贵，看续费价，别看首年价。** 首年是招徕，续费才是成本。

![桌上摊开的笔记本](/images/2026-10-24-2.jpg){: width="1200" height="800"}
<p class="image-credit">Photo by Kelly Sikkema on Unsplash</p>

## 三、DNS 配置踩的两个坑

买完域名要把它接到 Cloudflare。

**坑一：界面文案变了**

网上教程都说点「Add a site」，但我找遍整个后台也没这个按钮。现在是 **Add a domain**，功能完全一样。

**坑二：Connect 和 Transfer 是两回事**

进到添加域名页面，有两个选项：

- **Connect a domain** —— 把 DNS 托管交给 Cloudflare，域名留在原注册商
- **Transfer a domain** —— 把域名注册商转到 Cloudflare

**选前者。** 后者要把域名迁到 Cloudflare Registrar，而它对 `.xyz` 收 12.30 美元一年——你辛辛苦苦找到的 0.75 欧元当场作废。

选对之后，给两个 nameserver：

```
arely.ns.cloudflare.com
marty.ns.cloudflare.com
```

回 Namecheap 后台，Domain List → Manage → NAMESERVERS 改成 Custom DNS，把这两个填进去。

**注意**：填完整域名，别加结尾的点，别加 `https://`。

## 四、等 NS 生效时学到的

改完 NS 之后，我等了将近一个小时，Cloudflare 一直显示 pending。

查下来发现一件事：**WHOIS 更新不等于 DNS 生效**。

```
注册局 WHOIS    ARELY.NS.CLOUDFLARE.COM    ← 立刻变了
公共 DNS 查询   dns1.registrar-servers.com  ← 还是旧的
```

这是两个系统。Namecheap 提交变更后，注册局的 WHOIS 数据库马上更新，但顶级域服务器（`.xyz` 的权威 DNS）的委派记录要等 TTL 过期才刷新。DNS 查询走的是后者。

所以那一个小时里，WHOIS 看起来一切正常，实际解析还是指向 Namecheap。

![路口的指示牌](/images/2026-10-24-3.jpg){: width="1200" height="800"}
<p class="image-credit">Photo by Prince Adufah on Unsplash</p>

**判断 NS 有没有真正生效，别看 WHOIS，要查 DNS**：

```bash
curl -s -H "accept: application/dns-json" \
  "https://doh.pub/dns-query?name=996196.xyz&type=NS"
```

返回 `arely.ns.cloudflare.com` 才算通。

## 五、访问统计：siteTag 和 token 不是一回事

站点跑起来之后，我想知道有没有人看。

Cloudflare Web Analytics 免费，支持非代理站点。但有个限制：**它的自动注入只对 `*.pages.dev` 生效**，自定义域名和 GitHub Pages 都得手动埋点。

于是我做了个按域名分发的脚本：

```javascript
var token;
if (/^996196\.xyz$/i.test(h)) {
  token = "主站 token";
} else if (/github\.io$/i.test(h)) {
  token = "GitHub token";
} else {
  token = "pages.dev token";
}
```

三个域名，三个统计站点，数据分开。

**这里有个认知误区要澄清**：

页面上 `data-cf-beacon` 里的 **token**，和 GraphQL 查询要用的 **siteTag**，**是两个不同的值**。

我一开始以为它们是同一个东西，拿 token 去查数据，永远是 0 次。后来去后台对比才发现：

```
996196.xyz              → siteTag: 3ef33b12...   token: f8b62b6f...
catecholamin.github.io  → siteTag: 6eeecc7a...   token: 71bbf061...
```

**埋点用 token，查询用 siteTag。** 混用查不到任何数据。

还有一点：Cloudflare 的 `rumPageloadEventsAdaptiveGroups` 是**自适应采样**的。7 天内的数据是精确的（`sampleInterval=1`），超过之后按 1/10 采样再四舍五入，数字会失真——而且是跳着走的那种失真，比如 30 天窗口显示 20 次，7 天窗口反而显示 28 次。

所以想看准确数字，**窗口不要超过 7 天**。

## 六、评论系统：整个项目最折腾的部分

原来用的是 Utterances，靠 GitHub Issues 存评论。问题很明显：**读者必须有 GitHub 账号**，而且登录要跳 `github.com`，这个域名在国内经常超时。

测了一下：

```
api.github.com    200  1.53s      ← 能读评论
github.com/login  超时三次        ← 发不了
```

所以是"能看不能发"。换。

最后选了 **Twikoo**，后端部署在 Netlify Functions，数据库用 MongoDB Atlas 免费版（M0，512MB）。

![评论系统的三层结构](/img/blog-migration-2-stack.svg)

结构不复杂，但每一层都有各自的脾气。下面五个坑，两个在中间那层，一个在数据库那层，还有两个根本不在层里——在接口约定上。

![亮着背光的键盘](/images/2026-10-24-4.jpg){: width="1200" height="800"}
<p class="image-credit">Photo by Paul Zoetemeijer on Unsplash</p>

### 坑 1：环境变量填了占位符

MongoDB 给的连接串长这样：

```
mongodb+srv://sunfly:<password>@cluster0.xxxxx.mongodb.net/
```

尖括号是文档里的占位语法，要替换成真实密码。

我把它填进 Netlify 之后，后端一直返回：

```json
{"code":1000,"message":"bad auth : authentication failed"}
```

排查了半天才发现，填进去的是带尖括号的版本，甚至一度填成了三个星号 `***`——因为从文档复制时，密码显示为星号，直接复制就把星号当成了密码。

**认证失败 = 密码真的不对，不是网络问题。** 如果是 IP 白名单没开，报的会是 timeout 而不是 auth failed。

### 坑 2：Node 版本不够

后端能启动，`GET_CONFIG` 也能读配置，但查评论时报 `请更新 Twikoo 云函数至最新版本`。

这个错误信息很误导，前后端版本其实是完全一致的（都是 2.0.17）。

真正的线索是**执行时长**：

```
正常查库    1.4 – 5.1 秒
失败那次     245 毫秒
```

MongoDB 在新加坡，光 TLS 握手就要 100-300ms。**245 毫秒连网络都没发出去**，说明代码在碰数据库之前就崩了。

查 `twikoo-netlify` 的依赖：

```json
"dependencies": {
  "mongodb": "^7.6.0"
},
"engines": {
  "node": ">=22.12.0"
}
```

MongoDB 的 Node 驱动 7.x 需要 Node 20 以上。Netlify 默认给的可能不是 22。

解决：在环境变量里加一条 `NODE_VERSION=22`，然后**清缓存重建**（普通部署不会重建已有的函数实例）。

![245 毫秒说明了一切](/img/blog-migration-4-245ms.svg)

这张图是整篇里我最想留下的一张。**报错信息撒谎，但耗时不撒谎。**

### 坑 3：数据库名没指定，数据写进了 test 库

连接串结尾是这样的：

```
mongodb+srv://sunfly:****@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

注意 `.net/` 后面直接就是问号，**没有数据库名**。

MongoDB 驱动遇到这种情况会用默认库 `test`。结果我在页面上发的评论全部进了 `test.comment`，而我去 `twikoo` 库里查，当然一条都没有。

改法很简单，在斜杠后面加上库名：

```
mongodb+srv://sunfly:****@cluster0.xxxxx.mongodb.net/twikoo?retryWrites=true&w=majority
                                                                 ↑
```

**连接串结尾少一个库名，数据就会悄悄地跑到别的地方去。** 而且不会报错，功能完全正常，只是你找不到数据。

### 坑 4：接口名被废弃了

我以为在测后端，用 curl 发：

```bash
curl -X POST .../twikoo -d '{"event":"GET_COMMENTS","url":"/","page":1}'
```

一直报错。后来看 Twikoo 2.0 的代码才发现，这个接口改名了：

```
1.x 版本    GET_COMMENTS
2.0 版本    GET_COMMENTS_COUNT
```

换成新接口立刻返回：

```json
{"data":[{"url":"/","count":0}],"accessToken":"..."}
```

**不要拿旧版本文档的接口去测新版本。**

### 坑 5：path 用标题还是用路径

Utterances 原来用的是 `issue-term="title"`，靠文章标题做匹配。这种做法的问题是：**你在后台把标题改一个字，历史评论就全断了**。

Twikoo 里我改用路径：

```javascript
twikoo.init({
  envId: 'https://xxx.netlify.app/.netlify/functions/twikoo',
  el: '#tcomment',
  path: location.pathname,
  lang: 'zh-CN'
});
```

有个细节值得记：Jekyll 会把 `/2026/10/18/week.html` **308 重定向**到 `/2026/10/18/week`，所以 `location.pathname` 拿到的是无扩展名的版本。这不是 bug——好处是读者不管从哪个链接进来，看到的都是同一份评论，不会分裂。

## 七、目录被正文遮住的问题

最后一个 bug 比较有意思。

现象：文章右侧的目录只在页面上方和下方能看见，滚到正文中间就消失了。

查 CSS 发现 `.post-content` 是这么写的：

```css
.post-content {
    position: relative;
    width: 100%;
    background-color: #fff;
    overflow: hidden;
}
```

而目录是：

```css
.post-toc.has-toc {
    position: fixed;
    left: calc(50% + 388px);
}
```

**两个都是定位元素，都没设 z-index。**

CSS 层叠规则里，`z-index: auto` 的定位元素按 DOM 顺序层叠，**后出现的盖住先出现的**。目录写在 `<div class="post-content">` 前面，所以那块铺满全宽的白色背景把目录整个盖住了。

至于为什么上下两头能看见——因为那两处不在 `post-content` 的高度范围内（上面是文章头图，下面是作者卡片）。

修法就一行：

```css
.post-toc.has-toc {
    z-index: 100;
}
```

选 100 而不是更大，是为了不挡住顶部导航栏（`z-index: 1000`）。

![目录被正文遮挡的层叠问题](/img/blog-migration-3-zindex.svg)

左边是原来的样子，目录被压在最底下，只有正文上下两头的空白处能露出来。右边抬高之后就一直在最上面了。

![桌上的放大镜](/images/2026-10-24-5.jpg){: width="1200" height="800"}
<p class="image-credit">Photo by Markus Winkler on Unsplash</p>

## 八、侧边标签栏为什么一直不变

首页右侧有一列标签，我从来没管过它。直到我自己某天盯着它看了一眼：这玩意儿好像一直是那十几个，几年都没换过。

一看还真是——`backup`、`github`、`blog`、`R语言`、`生物信息学`……全是早期那批文章打的标签，跟最近写的东西一点关系都没有。

模块长这样：

```liquid
{% raw %}{% for tag in site.tags %}
    {% if forloop.index > site.recommend-condition-size %}{% break %}{% endif %}
    <a href="tags.html#{{ tag[0] }}" class="tag">{{ tag[0] }}</a>
{% endfor %}{% endraw %}
```

看起来没毛病：遍历所有标签，取前 18 个。`recommend-condition-size` 在 `_config.yml` 里配成 18。

问题出在**"遍历的顺序"**上。

`site.tags` 是个 Ruby Hash，Liquid 拿到的遍历顺序是**这个 Hash 的插入顺序**——而它又是文章按时间正序处理时逐个累积出来的。所以 2011 年那几篇的标签最先插进去，就永远排在最前面。

**取前 18 个，就是取最早那 18 个。** 后面新增的标签不管写多少篇，只要排在 19 位之后，就永远进不来。

这跟"排序"没关系，是从来没排过。它只是一直按插入顺序截断。

### 想按热度排，但没有插件可用

在 Jekyll 里这本来是个插件能解决的活，写一个 `sort_by` 就完了。但 Cloudflare Pages 不执行 `_plugins/` 目录，只能用 Liquid 硬做。

Liquid 没有"按某个属性排序"这种能力，`sort` 只能对字符串和数字排序。于是想了个绕路的办法：

**把"文章数"补零成固定长度的字符串，和标签名拼在一起，靠字符串字典序排出数字大小。**

`0027::AI 生成` 排在 `0013::周记` 前面，因为 `0027` > `0013`。补零是必须的——不补的话 `"27"` 会排在 `"4"` 后面。

### 第一版写错了

我第一版是这么写的：

```liquid
{% raw %}{{ tag[1].size | prepend: "0000" | slice: -4 }}::{{ tag[0] }}{% endraw %}
```

跑起来，标签栏变成了：

```
鸡娃、飞书、风险、靶向治疗、阳过、阳康、门诊、镜像、跑步……
```

全是 1 篇的标签，按中文名倒序排。

**Liquid 的 `slice` 签名是 `slice: start, length`。** 我只给了 `-4` 一个参数，它的意思是「从倒数第 4 位开始、取 **1 个**字符」。

对 `"000027"` 取 `slice: -4`，得到的是那个位置的单个字符 `"0"`。**所有标签的 key 都变成了 `"0"`**，排序当场退化，变成了按标签名排序。

正确的写法是 `slice: -4, 4`。不过最后我干脆没用 slice，改成显式的位数判断：

```liquid
{% raw %}{%- assign tn = tag[1].size -%}
{%- if tn < 10 -%}000{{ tn }}
{%- elsif tn < 100 -%}00{{ tn }}
{%- elsif tn < 1000 -%}0{{ tn }}
{%- else -%}{{ tn }}{%- endif -%}{% endraw %}
```

啰嗦，但不用猜 filter 的行为。

### 现在的顺序

```
AI 生成      27 篇
Hermes       23 篇
论文         16 篇
周记         13 篇
临床         13 篇
OpenClaw     12 篇
小红书        9 篇
手术          8 篇
```

和实际的写作分布对上了。

**这个坑和前面那个 245 毫秒很像**：代码没报错，功能也在跑，输出的东西看着像模像样——只是内容全是错的。如果不是我多看了它一眼，它大概会一直错下去。

---

## 九、搜索框在手机上是坏的

我在手机上试了一下，点搜索按钮直接跳走了，到了页面又搜不了。

先用无头浏览器在桌面尺寸下测，一切正常：点了弹层出现，输入有结果。**但换成 390×844 的 iPhone 视口重测，问题就出来了。**

### 先看 JS，它第一行就死了

```javascript
var toggle = document.getElementById('search-toggle');
if (!overlay || !toggle) return;      // ← 这里
```

`header.html` 里**根本没有** `search-toggle` 这个 id。整个 IIFE 到这里就 `return` 了，后面全部逻辑——包括搜索本身——从来没跑过。

翻下去还有三个问题：

1. **输入框从来没绑过 `input` 事件**。`doSearch()` 定义了，但没有任何地方调用它。
2. **数据源写的是 `search.json`**，而构建产物叫 `search-index.json`。
3. **依赖 jQuery 的 `$.getJSON`**，而 jQuery 只在部分布局里加载。

### 两份实现互相打脸

`header.html` 里还藏着一份内联脚本，做几乎一样的事。它用：

```javascript
document.querySelector('.nav-search a')
```

**`querySelector` 只抓第一个匹配。**

桌面端导航是静态渲染的，抓得到。但手机上的菜单是折叠的、由 JS 后插入的节点——`querySelector` 抓到的是那个不可见的桌面版本，真正的移动端菜单项没被拦截，于是走默认的 `href`：

```html
<a href="/search.html">   ← 拦住就没跳转，没拦住就跳到这
```

这就是"点了按钮直接跳走"的来源。

### 还有一个更根本的问题

`.g-nav` 在手机上本来就是 `display: none`：

```css
@media screen and (max-width: 695px) {
    .g-header .g-nav { display: none; }
}
```

**搜索图标藏在这个折叠菜单里。** 用户得先点汉堡展开菜单、再点搜索——中间任何一步出岔子，就表现为"点了没反应"或者"跳走了"。

而且父元素 `display: none` 时，子元素用 CSS 是救不回来的。必须在 DOM 层面单独放一个入口。

### 改法

**一、合并成一份实现**

删掉 `header.html` 里的内联脚本，交互全部交给 `search-overlay.js`。触发点改成抓全部：

```javascript
var triggers = document.querySelectorAll('.nav-search a, #mobile-search');
triggers.forEach(function (el) {
    el.addEventListener('click', openOverlay);
});
```

**二、移动端给一个常驻按钮**

```html
<a href="/search.html" class="mobile-search" id="mobile-search">
    <i class="iconfont icon-search"></i>
</a>
```

```css
.mobile-search { display: none; }
@media screen and (max-width: 695px) {
    .mobile-search {
        display: flex;
        position: absolute;
        top: 28px;
        right: 56px;
    }
}
```

桌面隐藏，手机上固定在右上角、汉堡左边。不用展开菜单就能点到。

**三、focus 要延迟**

```javascript
setTimeout(function () { input.focus(); }, 80);
```

弹层刚 `display: flex` 就立刻 `focus()`，移动端键盘经常不弹。等一帧以上再调。

**四、静态资源加版本号**

```html
<script src="/assets/js/search-overlay.js?v=2"></script>
```

因为 `cache-control: public, max-age=14400`——**四小时缓存**。我改完推上去，手机上很可能还在跑几小时前的旧文件，改了也看不见效果。带个 `?v=2` 是全新 URL，浏览器必须重新拉。

### 验证

用 CDP 驱动无头 Chrome，设成 iPhone 视口真点一遍：

```
=== 手机首屏（不点任何菜单）===
  搜索按钮可见  true      位置 302,28  32×32
  点击后 active true
  URL 未跳转    true
  输入框聚焦    search-input
  输入「胰腺」  3 条结果
```

四项全过：元素可见、点击生效、URL 没误跳、focus 到位。

**这次教训是"只测一个端不够"**。桌面 headless 全绿的时候，手机上完全是另一回事——折叠菜单、触摸事件、键盘唤起，每一层都有自己的脾气。

---

## 十、样式改了四遍，一点反应都没有

首页每张文章卡片右下角有个日期。有一篇的日期跑到框外面去了。

是 2026 年 8 月 2 日那篇周记，标签多，八个。标签区一行放不下就换行，第二行连同日期一起溢出卡片的边框。

我以为是十分钟能修好的事，改了四次才发现不对。

![一整面玻璃幕墙](/images/2026-10-24-6.jpg){: width="1200" height="800"}
<p class="image-credit">Photo by Adrian Siaril on Unsplash</p>

### 四次都失败了

**第一次**，看到 `.post-meta` 写着 `height: 22px`，改成 `auto`。

推上去，等四分钟，刷新——没变。

**第二次**，怀疑是浮动的问题。`.post-tags` 用了 `float: left`，浮动元素不参与父元素的高度计算。改成 flex 布局。

没变。

**第三次**，加 `overflow: hidden`，想把溢出的部分裁掉。

裁掉了，但标签也被裁掉半截，更难看。

**第四次**，终于发现卡片是 CSS Grid：

```css
.article-item {
    grid-template-rows: auto 1fr;
}
```

第二行的 `1fr` 把标签区锁死成"剩余空间"，标签再多也撑不开它。

改成 `auto auto`。

——还是没变。

### 让浏览器自己说出来

到这一步才想起来，可以用 Chrome DevTools Protocol 的 `CSS.getMatchedStylesForNode`，直接问浏览器这个元素到底匹配了哪些规则、哪条赢了。

一看就明白了：

```
[.article-list .article-item .post-meta .post-tags]   float:left; display:inline-block
[.article-item .post-tags]                            float:none; display:flex
```

两条规则，我写的在下面，是后加载的——但它**没赢**。

因为 CSS 不是"谁在后面谁说话"，是**先比权重**：

```
.article-list .article-item .post-meta .post-tags     四个类   (0,4,0)
.article-item .post-tags                              两个类   (0,2,0)
```

四个类压倒两个类。我改的每一行，浏览器从头到尾都没用过。

改成同样四层：

```css
.article-list .article-item .post-meta .post-tags {
    float: none;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}
```

这次才真的生效。

### 三个问题叠在一起

回头看，"日期跑出框"是三层原因同时起作用：

**一、权重。** 四层选择器压着两层，改什么都不生效。

**二、Grid 的 1fr。** 标签区被锁成固定的剩余空间，内容撑不开容器。

**三、float。** 浮动元素不撑开父元素，标签的高度从来没被算进去。

只修一个，另外两个还在。所以每次都是"看起来改了，又好像没改"。

**样式不生效的时候，第一反应应该是查权重，不是反复改值。** 我改了四次，前三次都在改那些根本没被采纳的属性。

### 热图根本不在那个框里

修完日期，接着看侧边栏。

首页右边是一列：上面作者介绍，中间标签云，下面本该是文章热图。但热图看着是独立的一块，跟上面那个白框对不上——像是悬在外面。

第一反应还是样式：背景色不对、边框不对、圆角不对。调了半天没效果。

最后去查 DOM 结构：

```html
<aside class="g-sidebar-wrapper">
    <div class="g-sidebar">          <!-- 白框从这开始 -->
        <section class="author-card">...</section>
        <section class="tags-card">...</section>
    </div>                            <!-- 白框到这结束 -->
    <div class="sidebar-widget">      <!-- 热图在外面 -->
        文章热图
    </div>
</aside>
```

热图那一块写在 `</div>` **之后**，成了 `aside` 的第二个子元素。

它当然不在框里——**它物理上就不在**。

把它移进 `</div>` 里面，样式一行都没动，位置立刻对了：

```
g_sidebar    left 953   right 1193
标签栏       left 974   right 1172
热图块       left 974   right 1172
```

左右边界完全重合。

![搭到一半的脚手架](/images/2026-10-24-7.jpg){: width="1200" height="800"}
<p class="image-credit">Photo by Paul Becker on Unsplash</p>

**这个教训比权重更值钱**：看着像样式问题，其实是结构问题。元素在哪儿，决定了它在哪个框里。

### 结构对了，才轮到谈好不好看

三个判断：

**一、两条分隔线在打架。** 标签栏自带一条 `border-bottom`，我又给热图加了 `border-top`。240 像素宽的窄栏里两条横线挨得太近，看着像一条粗线。删掉我加的那条。

**二、标题是多余的。** 我在热图上加了"文章热图"四个字，还配了个 12 像素的日历图标。问题在于：上面那栏标签云根本没有标题，是直接铺开的；这里突然冒出一个标题，本身就不统一。而且热图下面那行 `2026 ← →` 已经把这块是什么说清楚了。

删掉。少一行字，整块安静下来。

**三、标签不该有实心底纹。** 十八个灰底方块铺在白底上，读起来像一排按钮。标签要有轻盈感，不该有按钮的重量感。改成默认透明、只靠间距区分，鼠标移上去才浮出底纹。

**四、日期对齐。** 原来 `align-items: flex-start`，日期贴着第一行标签的顶边。标签换行时日期悬在上半截，右下角空一块。改成 `flex-end`，跟最后一行齐底。

顺带把热图格子从 15 像素放大到 18 像素——原来一行内容只占 146 像素，两边各空 27 像素，太松。放大后填充率从 74% 到 81%。

---

## 十一、现在的状态

```
博客地址     https://996196.xyz          首字节 0.898s
备份入口     https://catecholamin.pages.dev
旧入口       https://catecholamin.github.io
证书         Google Trust Services，自动续期
域名成本     €0.75/年 × 10 年 ≈ 62 元
评论系统     Twikoo 2.0.17 + Netlify + MongoDB Atlas
访问统计     Cloudflare Web Analytics，三域名分开
```

三个域名都能访问，canonical 统一指向新域名。

## 最后

这次迁移花了两个晚上，真正用在配置上的时间不到三分之一，剩下的都在排查那几个坑——尤其是评论系统，五个问题里没有一个会告诉你真正的原因。

总结四条经验：

**一是看错误信息要结合其他线索。** `请更新云函数至最新版本` 这句话是假的，但 `245 毫秒` 是真的。数据库连接不可能比 200 毫秒还快，这个数字直接指向了真正的问题所在。

**二是"没报错"不等于"对了"。** 连接串少写库名，功能一切正常，评论能发能显示，只是数据写进了另一个库。如果不是我主动去查数据库，这个坑可能永远发现不了。

**三是便宜的域名要看续费价。** 99 美分和 1.04 美元的差别不痛不痒，14.49 美元的续费才是真正的账单。

**四是样式不生效先查权重，位置不对先查结构。** 我先是改了四遍 CSS 属性，结果那些属性从头到尾没被浏览器采纳过；后来又想用样式把热图"塞进"那个框，而它其实只是没写在 `</div>` 里面。这两件事加起来浪费的时间，比配 DNS 还多。

至于值不值得折腾——说实话，这个博客没什么人看。但每次打开自己拼出来的地址，还是会觉得这两天没白花。

---

*本文记录于 2026 年 10 月 24 日深夜。*

<p class="image-credit">Cover photo by Winston Chen on Unsplash</p>

*本文由Hermes自动整理*
