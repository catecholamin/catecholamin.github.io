// Search overlay controller — clean rewrite
(function () {
    var overlay  = document.getElementById('search-overlay');
    var toggle   = document.getElementById('search-toggle');
    var closeBtn = document.getElementById('search-close');
    var input    = document.getElementById('search-input');
    var resultBox = document.getElementById('search-result');
    var hint     = document.getElementById('search-hint');

    // Guard: elements must exist
    if (!overlay || !toggle) {
        console.warn('Search: required DOM elements not found');
        return;
    }

    function openOverlay() {
        overlay.classList.add('active');
        if (input) {
            setTimeout(function () { input.focus(); }, 50);
        }
    }

    function closeOverlay() {
        overlay.classList.remove('active');
        if (input) input.value = '';
        if (resultBox) resultBox.innerHTML = '';
        if (hint) hint.style.display = '';
    }

    // Toggle button
    toggle.addEventListener('click', function (e) {
        e.preventDefault();
        if (overlay.classList.contains('active')) {
            closeOverlay();
        } else {
            openOverlay();
        }
    });

    // Close button
    if (closeBtn) {
        closeBtn.addEventListener('click', function (e) {
            e.preventDefault();
            closeOverlay();
        });
    }

    // Click outside closes
    overlay.addEventListener('click', function (e) {
        if (e.target === overlay) closeOverlay();
    });

    // ESC closes
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && overlay.classList.contains('active')) closeOverlay();
    });

    // Search with debounce
    var lastQuery = '';
    var searchTimeout = null;

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
            searchTimeout = setTimeout(function () { doSearch(q); }, 200);
        });
    }

    function doSearch(query) {
        if (query === lastQuery) return;
        lastQuery = query;

        // Determine correct path to search.json based on current URL
        var jsonPath = '../../search.json';
        if (/<\/page\d+\//.test(window.location.pathname)) {
            jsonPath = '../search.json';
        }

        $.getJSON(jsonPath).done(function (data) {
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
        }).fail(function () {
            if (resultBox) resultBox.innerHTML = '<div class="search-no-results">搜索加载失败</div>';
        });
    }
})();
