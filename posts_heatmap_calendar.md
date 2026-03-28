---
title: 文章热图与日历
layout: default
header-img: /assets/img/hero.jpg
---

{% include header.html %}

<div class="g-banner heatmap-banner {{ site.postPatterns | prepend: 'post-pattern-' }} {{ site.theme-color | prepend: 'bgcolor-' }}" data-theme="{{ site.theme-color }}">
    <h2>文章热图与日历</h2>
    <h3>记录每一篇文字的温度</h3>
</div>

<main class="g-container heatmap-content">

    <!-- Heatmap Section -->
    <section class="heatmap-section">
        <h3 class="section-title">
            <i class="iconfont icon-calendar"></i> 年度热图
            <span class="heatmap-legend">
                <span class="legend-label">少</span>
                <span class="legend-cell level-0"></span>
                <span class="legend-cell level-1"></span>
                <span class="legend-cell level-2"></span>
                <span class="legend-cell level-3"></span>
                <span class="legend-cell level-4"></span>
                <span class="legend-label">多</span>
            </span>
        </h3>
        <div id="heatmap-container" class="heatmap-container"></div>
        <div id="heatmap-tooltip" class="heatmap-tooltip"></div>
    </section>

    <!-- Calendar Section -->
    <section class="calendar-section">
        <h3 class="section-title">
            <i class="iconfont icon-date"></i> 月度日历
            <div class="calendar-nav">
                <button id="cal-prev" class="cal-btn">&lt;</button>
                <span id="cal-month-label"></span>
                <button id="cal-next" class="cal-btn">&gt;</button>
            </div>
        </h3>
        <div class="calendar-grid" id="calendar-grid"></div>
        <div id="calendar-post-list" class="calendar-post-list"></div>
    </section>

</main>

{% include footer.html %}

<script>
// Embedded post data from Jekyll
var POSTS_DATA = [
    {% for post in site.posts %}
    {
        title: "{{ post.title | escape }}",
        url: "{{ post.url | relative_url }}",
        date: "{{ post.date | date: '%Y-%m-%d' }}",
        tags: "{% for tag in post.tags %}{{ tag }}{% if forloop.last == false %}, {% endif %}{% endfor %}",
        year: {{ post.date | date: '%Y' }},
        month: {{ post.date | date: '%m' }},
        day: {{ post.date | date: '%d' }}
    }{% unless forloop.last %},{% endunless %}
    {% endfor %}
];

// Build date -> posts map
var dateMap = {};
POSTS_DATA.forEach(function(p) {
    if (!dateMap[p.date]) dateMap[p.date] = [];
    dateMap[p.date].push(p);
});

// ==================
// HEATMAP
// ==================
function buildHeatmap() {
    var container = document.getElementById('heatmap-container');
    var tooltip = document.getElementById('heatmap-tooltip');
    var now = new Date();
    var currentYear = now.getFullYear();

    // Find first Sunday of the year
    var firstDay = new Date(currentYear, 0, 1);
    var startOffset = firstDay.getDay(); // 0=Sun

    // Count posts per date
    var postCount = {};
    POSTS_DATA.forEach(function(p) {
        var d = new Date(p.date);
        if (d.getFullYear() === currentYear) {
            var key = p.date;
            postCount[key] = (postCount[key] || 0) + 1;
        }
    });

    // Build SVG grid
    var weeks = [];
    var currentDate = new Date(firstDay);
    currentDate.setDate(currentDate.getDate() - startOffset);

    for (var w = 0; w < 53; w++) {
        var week = [];
        for (var d = 0; d < 7; d++) {
            var dateStr = currentDate.toISOString().slice(0, 10);
            var count = postCount[dateStr] || 0;
            var inYear = currentDate.getFullYear() === currentYear;
            week.push({
                date: dateStr,
                count: count,
                inYear: inYear,
                future: currentDate > now
            });
            currentDate.setDate(currentDate.getDate() + 1);
        }
        weeks.push(week);
    }

    // Month labels
    var monthNames = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];
    var monthLabelRow = '<div class="heatmap-months">';
    var prevMonth = -1;
    weeks.forEach(function(week, wi) {
        var m = week[0].date ? new Date(week[0].date).getMonth() : -1;
        if (m !== prevMonth && week[0].inYear) {
            monthLabelRow += '<span class="month-label" style="left:' + (wi * 14) + 'px">' + monthNames[m] + '</span>';
            prevMonth = m;
        }
    });
    monthLabelRow += '</div>';

    // Day labels
    var dayLabels = ['', '一', '', '三', '', '五', ''];

    // Grid
    var gridHtml = '<div class="heatmap-grid">';
    dayLabels.forEach(function(label, di) {
        gridHtml += '<div class="heatmap-day-label">' + label + '</div>';
        for (var wi = 0; wi < weeks.length; wi++) {
            var cell = weeks[wi][di];
            if (!cell) { gridHtml += '<div class="heatmap-cell empty"></div>'; continue; }
            var level = cell.count === 0 ? 0 : cell.count >= 4 ? 4 : cell.count >= 2 ? 3 : cell.count >= 1 ? 2 : 1;
            var cls = ['level-0','level-1','level-2','level-3','level-4'][level];
            var extra = !cell.inYear || cell.future ? 'future' : '';
            gridHtml += '<div class="heatmap-cell ' + cls + ' ' + extra + '" data-date="' + cell.date + '" data-count="' + cell.count + '"></div>';
        }
        gridHtml += '\n';
    });
    gridHtml += '</div>';

    container.innerHTML = monthLabelRow + '<div class="heatmap-scroll"><div class="heatmap-inner">' + gridHtml + '</div></div>';

    // Tooltip
    container.querySelectorAll('.heatmap-cell:not(.empty):not(.future)').forEach(function(cell) {
        cell.addEventListener('mouseenter', function(e) {
            var date = this.getAttribute('data-date');
            var count = parseInt(this.getAttribute('data-count'));
            var posts = dateMap[date] || [];
            var label = date + ' · ' + count + '篇';
            var list = posts.map(function(p) {
                return '<a href="' + p.url + '">' + p.title + '</a>';
            }).join('');
            tooltip.innerHTML = '<div class="tt-date">' + date + '</div>' +
                '<div class="tt-count">' + count + ' 篇文章</div>' +
                (list ? '<div class="tt-list">' + list + '</div>' : '');
            tooltip.style.display = 'block';
            tooltip.style.left = (e.clientX + 10) + 'px';
            tooltip.style.top = (e.clientY - 60) + 'px';
        });
        cell.addEventListener('mouseleave', function() {
            tooltip.style.display = 'none';
        });
    });
}

// ==================
// CALENDAR
// ==================
var calYear, calMonth;
var dayNames = ['日','一','二','三','四','五','六'];

function buildCalendar(year, month) {
    var container = document.getElementById('calendar-grid');
    var label = document.getElementById('cal-month-label');
    var postList = document.getElementById('calendar-post-list');

    label.textContent = year + '年' + (month + 1) + '月';

    var firstDay = new Date(year, month, 1);
    var lastDay = new Date(year, month + 1, 0);
    var startDow = firstDay.getDay();
    var daysInMonth = lastDay.getDate();

    var html = '<div class="cal-week-header">';
    dayNames.forEach(function(d) { html += '<div class="cal-week-day">' + d + '</div>'; });
    html += '</div><div class="cal-days">';

    // Empty cells before first day
    for (var i = 0; i < startDow; i++) {
        html += '<div class="cal-day empty"></div>';
    }

    // Days
    var now = new Date();
    for (var d = 1; d <= daysInMonth; d++) {
        var dateStr = year + '-' + String(month + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0');
        var posts = dateMap[dateStr] || [];
        var hasPosts = posts.length > 0;
        var isToday = year === now.getFullYear() && month === now.getMonth() && d === now.getDate();
        var dotHtml = hasPosts ? '<div class="cal-day-dots"><span class="cal-day-dot"></span>' +
            (posts.length > 1 ? '<span class="cal-day-count">' + posts.length + '</span>' : '') + '</div>' : '';
        html += '<div class="cal-day' + (hasPosts ? ' has-posts' : '') + (isToday ? ' today' : '') + '" data-date="' + dateStr + '">' +
            '<span class="cal-day-num">' + d + '</span>' + dotHtml + '</div>';
    }

    // Fill remaining cells
    var totalCells = startDow + daysInMonth;
    var remaining = (7 - (totalCells % 7)) % 7;
    for (var i = 0; i < remaining; i++) {
        html += '<div class="cal-day empty"></div>';
    }

    html += '</div>';
    container.innerHTML = html;

    // Click day to show posts
    container.querySelectorAll('.cal-day.has-posts').forEach(function(day) {
        day.addEventListener('click', function() {
            var date = this.getAttribute('data-date');
            var posts = dateMap[date] || [];
            if (posts.length === 0) return;
            var listHtml = '<div class="cal-post-list-title">' + date + ' 共 ' + posts.length + ' 篇</div>';
            listHtml += '<ul class="cal-post-list">';
            listHtml += posts.map(function(p) {
                return '<li><a href="' + p.url + '">' + p.title + '</a>' +
                    (p.tags ? '<span class="cal-post-tags">' + p.tags + '</span>' : '') + '</li>';
            }).join('');
            listHtml += '</ul>';
            postList.innerHTML = listHtml;
            postList.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });
    });
}

// Init calendar to current month
var now = new Date();
calYear = now.getFullYear();
calMonth = now.getMonth();
buildCalendar(calYear, calMonth);

document.getElementById('cal-prev').addEventListener('click', function() {
    calMonth--;
    if (calMonth < 0) { calMonth = 11; calYear--; }
    buildCalendar(calYear, calMonth);
});
document.getElementById('cal-next').addEventListener('click', function() {
    calMonth++;
    if (calMonth > 11) { calMonth = 0; calYear++; }
    buildCalendar(calYear, calMonth);
});

// Init heatmap
buildHeatmap();
</script>
