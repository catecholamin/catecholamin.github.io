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
        {
          'title'   => title,
          'url'     => url,
          'date'    => post.date.strftime('%Y-%m-%d'),
          'tags'    => (post.data['tags'] || []).join(' '),
          'excerpt' => post.excerpt&.strip&.gsub(%r{<[^>]+>}, ' ')&.strip&.slice(0, 200) || ''
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
