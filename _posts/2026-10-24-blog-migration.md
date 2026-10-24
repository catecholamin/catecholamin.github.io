---
layout: post
title: 折腾了两天，把博客迁到自己的域名上
subtitle: 一次从 GitHub Pages 到 Cloudflare Pages 的搬迁记录
date: 2026-10-24
categories: 技术
tags: Cloudflare Pages 域名 DNS 评论系统 Twikoo MongoDB Jekyll
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

这一路上踩了五个坑，一个比一个隐蔽。

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

## 八、现在的状态

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

总结三条经验：

**一是看错误信息要结合其他线索。** `请更新云函数至最新版本` 这句话是假的，但 `245 毫秒` 是真的。数据库连接不可能比 200 毫秒还快，这个数字直接指向了真正的问题所在。

**二是"没报错"不等于"对了"。** 连接串少写库名，功能一切正常，评论能发能显示，只是数据写进了另一个库。如果不是我主动去查数据库，这个坑可能永远发现不了。

**三是便宜的域名要看续费价。** 99 美分和 1.04 美元的差别不痛不痒，14.49 美元的续费才是真正的账单。

至于值不值得折腾——说实话，这个博客没什么人看。但每次打开自己拼出来的地址，还是会觉得这两天没白花。

---

*本文记录于 2026 年 10 月 24 日深夜。*
