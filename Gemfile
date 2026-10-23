source "https://rubygems.org"

# Cloudflare Pages 的构建镜像当前是 Ruby 3.4，github-pages gem 锁定的
# Jekyll 3.9.x 依赖在 3.4 下装不上，所以改用 Jekyll 4。
# 站点已提交编译好的 CSS（assets/css/app.min.css），不依赖 Sass 编译，
# 因此 Jekyll 4 与 3 的差异对本站只落在分页和 Liquid 上，这两处行为一致。
gem "jekyll", "~> 4.3"

# _config.yml 的 plugins 需要。注意：这里都不要写 group: :jekyll_plugins，
# Cloudflare 构建镜像默认设置了 BUNDLE_WITHOUT，带该分组的 gem 会被跳过，
# 表现为构建时找不到插件。
gem "jekyll-paginate", "~> 1.1"
gem "jekyll-sitemap", "~> 1.4"
gem "jekyll-feed", "~> 0.17"

# _config.yml 里 markdown: kramdown
gem "kramdown-parser-gfm", "~> 1.1"

# Ruby 3.0 起不再自带 webrick
gem "webrick", "~> 1.8"
