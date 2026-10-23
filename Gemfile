source "https://rubygems.org"

# 用官方推荐的 github-pages gem，而不是自己去列 jekyll 4.x。
# 它把 Jekyll 3.9.x 和 GitHub Pages 内置的全部插件版本一起锁死，
# 迁移到 Cloudflare Pages 后构建结果与本站在 GitHub Pages 上的表现一致，
# 避免 Jekyll 3 与 4 之间的行为差异（分页、Liquid、Sass 都有差别）。
gem "github-pages", group: :jekyll_plugins

# Ruby 3.0 起不再自带 webrick，jekyll serve 需要
gem "webrick", "~> 1.8"
