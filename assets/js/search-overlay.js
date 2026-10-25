/* ==========================================================================
   站内搜索 · 弹层控制器
   --------------------------------------------------------------------------
   旧版有几个问题，导致搜索完全不可用：

   1. 第 10 行 if (!overlay || !toggle) —— 找的是 #search-toggle，
      而 header.html 里根本没有这个 id，函数直接 return，
      后面所有逻辑（包括搜索本身）从未执行。
   2. 即使在跑，整个文件里也没有给输入框绑过 input 事件，
      doSearch() 定义了却没有任何地方调用。
   3. 数据源写的是 search.json，构建产物实际叫 search-index.json。
   4. 依赖 jQuery 的 $.getJSON，而 jQuery 只在部分布局里加载。

   这一版：
   - 触发点是 .nav-search a，与 header.html 的实际 DOM 一致
   - 数据源固定为 /search-index.json 绝对路径，不猜相对层级
   - 打开后主动 focus，让移动端键盘弹出来
   - 输入加 120ms 防抖，中文输入法不会每敲一下跑一次全量匹配
   - 回车直接进第一条结果
   - 不依赖 jQuery
   ========================================================================== */
(function () {
    'use strict';

    var overlay = document.getElementById('search-overlay');
    var input = document.getElementById('search-input');
    var resultBox = document.getElementById('search-result');
    var hint = document.getElementById('search-hint');
    var closeBtn = document.getElementById('search-close');

    if (!overlay || !input) return;

    var DATA_URL = '/search-index.json';
    var data = null;
    var loading = false;
    var pending = null;

    /* ---------- 开关 ---------- */

    function openOverlay(e) {
        if (e) e.preventDefault();
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        loadData();
        // 移动端要等弹层真正可见之后再 focus，否则键盘不弹
        setTimeout(function () { input.focus(); }, 80);
    }

    function closeOverlay() {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
        input.value = '';
        if (resultBox) resultBox.innerHTML = '';
        if (hint) hint.style.display = '';
    }

    /* ---------- 数据 ---------- */

    function loadData(cb) {
        if (data) { if (cb) cb(); return; }
        if (loading) { if (cb) pending = cb; return; }
        loading = true;
        var xhr = new XMLHttpRequest();
        xhr.open('GET', DATA_URL, true);
        xhr.onload = function () {
            loading = false;
            if (xhr.status === 200) {
                try { data = JSON.parse(xhr.responseText); }
                catch (err) { data = []; }
            } else {
                data = [];
            }
            if (cb) cb();
            if (pending) { var f = pending; pending = null; f(); }
        };
        xhr.onerror = function () {
            loading = false;
            data = [];
            if (cb) cb();
        };
        xhr.send();
    }

    /* ---------- 检索 ---------- */

    function ctxOf(text, needle) {
        var i = text.toLowerCase().indexOf(needle);
        if (i < 0) return '';
        var s = Math.max(0, i - 30);
        var e = Math.min(text.length, i + needle.length + 70);
        return (s > 0 ? '…' : '') + text.substring(s, e) + (e < text.length ? '…' : '');
    }

    function escapeHtml(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function render(matches, q) {
        if (!resultBox) return;
        if (!matches.length) {
            resultBox.innerHTML = '<div class="search-no-results">没有找到相关文章</div>';
            return;
        }
        resultBox.innerHTML = matches.map(function (post) {
            var ex = post.excerpt || '';
            if (!ex && post.content) ex = ctxOf(post.content, q);
            return '<a class="search-result-item" href="' + post.url + '">' +
                   '<span class="result-title">' + escapeHtml(post.title) + '</span>' +
                   (post.date ? '<span class="result-date">' + escapeHtml(post.date) + '</span>' : '') +
                   (ex ? '<span class="result-excerpt">' + escapeHtml(ex) + '</span>' : '') +
                   '</a>';
        }).join('');
    }

    function search(q) {
        q = (q || '').trim();
        if (!q) {
            if (resultBox) resultBox.innerHTML = '';
            if (hint) hint.style.display = '';
            return;
        }
        if (hint) hint.style.display = 'none';

        loadData(function () {
            var q2 = q.toLowerCase();
            var list = data || [];
            var matches = [];
            for (var i = 0; i < list.length && matches.length < 30; i++) {
                var post = list[i];
                if ((post.title || '').toLowerCase().indexOf(q2) >= 0 ||
                    (post.excerpt || '').toLowerCase().indexOf(q2) >= 0 ||
                    (post.tags || '').toLowerCase().indexOf(q2) >= 0 ||
                    (post.content || '').toLowerCase().indexOf(q2) >= 0) {
                    matches.push(post);
                }
            }
            render(matches, q2);
        });
    }

    /* ---------- 事件 ---------- */

    var triggers = document.querySelectorAll('.nav-search a, #mobile-search');
    for (var i = 0; i < triggers.length; i++) {
        triggers[i].addEventListener('click', openOverlay);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', function (e) {
            e.preventDefault();
            closeOverlay();
        });
    }

    overlay.addEventListener('click', function (e) {
        if (e.target === overlay) closeOverlay();
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && overlay.classList.contains('active')) closeOverlay();
    });

    var timer = null;
    input.addEventListener('input', function () {
        var v = this.value;
        clearTimeout(timer);
        timer = setTimeout(function () { search(v); }, 120);
    });

    input.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        var first = resultBox && resultBox.querySelector('.search-result-item');
        if (first) window.location.href = first.getAttribute('href');
    });
})();
