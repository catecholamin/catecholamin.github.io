// Search overlay controller
(function() {
    var overlay = document.getElementById('search-overlay');
    var toggle = document.getElementById('search-toggle');
    var closeBtn = document.getElementById('search-close');
    var input = document.getElementById('search-input');
    var resultBox = document.getElementById('search-result');
    var hint = document.getElementById('search-hint');

    if (!overlay || !toggle) return;

    // Open overlay
    toggle.addEventListener('click', function() {
        overlay.classList.add('active');
        setTimeout(function() { input.focus(); }, 100);
    });

    // Close overlay
    closeBtn.addEventListener('click', closeOverlay);
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) closeOverlay();
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay.classList.contains('active')) closeOverlay();
    });

    function closeOverlay() {
        overlay.classList.remove('active');
        input.value = '';
        resultBox.innerHTML = '';
        hint.style.display = 'block';
    }

    // Search logic
    var lastQuery = '';
    var searchTimeout = null;

    input.addEventListener('input', function() {
        var q = this.value.trim();
        clearTimeout(searchTimeout);
        if (!q) {
            resultBox.innerHTML = '';
            hint.style.display = 'block';
            lastQuery = '';
            return;
        }
        hint.style.display = 'none';
        searchTimeout = setTimeout(function() { doSearch(q); }, 200);
    });

    function doSearch(query) {
        if (query === lastQuery) return;
        lastQuery = query;
        $.getJSON('../../search.json').done(function(data) {
            var q = query.toLowerCase();
            var results = [];
            for (var i = 0; i < data.length; i++) {
                var post = data[i];
                var titleMatch = post.title.toLowerCase().indexOf(q) >= 0;
                var excerptMatch = post.excerpt.toLowerCase().indexOf(q) >= 0;
                var tagMatch = (post.tags && post.tags.toLowerCase().indexOf(q) >= 0);
                if (titleMatch || excerptMatch || tagMatch) {
                    var excerpt = post.excerpt ? post.excerpt.substring(0, 120) + '...' : '';
                    results.push(
                        '<a href="' + post.url + '">' +
                        '<span class="result-title">' + post.title + '</span>' +
                        (post.date ? '<span class="result-date">' + post.date + '</span>' : '') +
                        (excerpt ? '<span class="result-excerpt">' + excerpt + '</span>' : '') +
                        '</a>'
                    );
                }
            }
            if (results.length === 0) {
                resultBox.innerHTML = '<div style="padding:20px;color:#aaa;font-size:14px;text-align:center">没有找到相关文章</div>';
            } else {
                resultBox.innerHTML = results.join('');
            }
        });
    }

    // Close on nav click (mobile menu)
    var nav = document.querySelector('.g-nav');
    if (nav) {
        nav.addEventListener('click', function() {
            if (overlay.classList.contains('active')) closeOverlay();
        });
    }
})();
