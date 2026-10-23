require 'json'

module Jekyll
  class SearchIndexGenerator < Generator
    safe true
    priority :low

    def generate(site)
      search_dir = File.join(site.source, '')
      index_path = File.join(search_dir, 'search-index.json')

      posts = site.posts.docs.map do |post|
        title = post.data['title']
        title = post.slug if title.nil? || title.to_s.strip.empty?
        url = post.url
        # Fallback: use filename (without .md) as slug when title/url is broken
        # (Jekyll's slugify strips non-ASCII chars, so Chinese titles → empty slug → broken URL)
        if url.nil? || url.strip.empty? || url =~ %r{/\d{4}/\d{2}/\d{2}/\.html$}
          slug = post.name.sub(/\.md$/, '')
          url = "/#{post.date.strftime('%Y/%m/%d')}/#{slug}.html"
        end
        # Jekyll 4 里 post.excerpt 返回 Jekyll::Excerpt 对象而不是字符串，
        # 直接调用 .strip 会抛 NoMethodError 导致整个构建失败。
        # 先 to_s 再处理；Jekyll 3（GitHub Pages）下 to_s 是幂等的，同样安全。
        excerpt = post.excerpt.to_s.strip.gsub(%r{<[^>]+>}, ' ').strip[0, 200].to_s
        {
          'title'   => title,
          'url'     => url,
          'date'    => post.date.strftime('%Y-%m-%d'),
          'tags'    => (post.data['tags'] || []).join(' '),
          'excerpt' => excerpt
        }
      end

      File.open(index_path, 'w', encoding: 'utf-8') do |f|
        f.write(JSON.pretty_generate(posts))
        f.write("\n")
      end

      puts "[search] Generated #{index_path} with #{posts.size} posts"
    end
  end
end
