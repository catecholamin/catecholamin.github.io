// Search overlay controller — robust version
(function () {
    var overlay  = document.getElementById('search-overlay');
    var toggle   = document.getElementById('search-toggle');
    var closeBtn = document.getElementById('search-close');
    var input    = document.getElementById('search-input');
    var resultBox = document.getElementById('search-result');
    var hint     = document.getElementById('search-hint');

    if (!overlay || !toggle) {
        console.warn('Search: DOM elements missing');
        return;
    }

    function openOverlay() {
        overlay.classList.add('active');
        if (input) setTimeout(function () { input.focus(); }, 50);
    }

    function closeOverlay() {
        overlay.classList.remove('active');
        if (input) input.value = '';
        if (resultBox) resultBox.innerHTML = '';
        if (hint) hint.style.display = '';
    }

    toggle.addEventListener('click', function (e) {
        e.preventDefault();
        overlay.classList.contains('active') ? closeOverlay() : openOverlay();
    });

    if (closeBtn) closeBtn.addEventListener('click', function (e) { e.preventDefault(); closeOverlay(); });
    overlay.addEventListener('click', function (e) { if (e.target === overlay) closeOverlay(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && overlay.classList.contains('active')) closeOverlay(); });

    var lastQuery = '';
    var searchTimeout = null;

    function getSearchPaths() {
        var p = window.location.pathname;
        // Try multiple possible paths
        if (/page\d+\//.test(p)) return ['../search.json', '../../search.json'];
        if (/\d{4}\/\d{2}\/\d{2}\//.test(p)) return ['../../search.json', '../search.json', '/search.json'];
        return ['../../search.json', '../search.json', '/search.json'];
    }

    function doSearch(query) {
        var paths = getSearchPaths();
        var idx = 0;

        function tryNext() {
            if (idx >= paths.length) {
                if (resultBox) resultBox.innerHTML = '<div class="search-no-results">未找到文章</div>';
                return;
            }
            var jsonPath = paths[idx++];
            console.log('Search: trying', jsonPath);
            $.getJSON(jsonPath)
                .done(function (data) {
                    if (!data || data.length === 0) {
                        if (resultBox) resultBox.innerHTML = '<div class="search-no-results">没有文章数据</div>';
                        return;
                    }
                    var q = query.toLowerCase();
                    var results = [];
                    for (var i = 0; i < data.length; i++) {
                        var post = data[i];
                        if (
                            post.title.toLowerCase().indexOf(q) >= 0 ||
                            (post.excerpt && post.excerpt.toLowerCase().indexOf(q) >= 0) ||
                            (post.tags && post.tags.toLowerCase().indexOf(q) >= 0)
                        ) {
                            var excerpt = (post.excerpt || '').substring(0, 120);
                            results.push(
                                '<a class="search-result-item" href="' + post.url + '">' +
                                '<span class="result-title">' + post.title + '</span>' +
                                (post.date ? '<span class="result-date">' + post.date + '</span>' : '') +
                                (excerpt ? '<span class="result-excerpt">' + excerpt + '...</span>' : '') +
                                '</a>'
                            );
                        }
                    }
                    if (resultBox) {
                        resultBox.innerHTML = results.length === 0
                            ? '<div class="search-no-results">没有找到相关文章</div>'
                            : results.join('');
                    }
                })
                .fail(function () {
                    console.log('Search: path', jsonPath, 'failed, trying next...');
                    tryNext();
                });
        }

        tryNext();
    }

    if (input) {
        input.addEventListener('input', function () {
            var q = this.value.trim();
            clearTimeout(searchTimeout);
            if (!q) {
                if (resultBox) resultBox.innerHTML = '';
                if (hint) hint.style.display = '';
                lastQuery = '';
                return;
            }
            if (hint) hint.style.display = 'none';
            if (q === lastQuery) return;
            lastQuery = q;
            searchTimeout = setTimeout(function () { doSearch(q); }, 300);
        });
    }
})();
