source "https://rubygems.org"

# Cloudflare Pages / GitHub Pages 构建 Jekyll 用。
# 仓库原本没有 Gemfile，GitHub Pages 是平台内置环境，
# 换到 Cloudflare Pages 后必须显式声明依赖，否则构建会失败。
gem "jekyll", "~> 4.3"

# _config.yml 里 plugins 声明的三个插件
gem "jekyll-paginate", "~> 1.1"
gem "jekyll-sitemap", "~> 1.4"
gem "jekyll-feed", "~> 0.17"

# kramdown 解析器（_config.yml 里 markdown: kramdown）
gem "kramdown-parser-gfm", "~> 1.1"

# Ruby 3.0+ 不再自带 webrick，jekyll serve 需要它
gem "webrick", "~> 1.8"
