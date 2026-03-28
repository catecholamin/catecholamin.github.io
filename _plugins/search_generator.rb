require 'json'

module Jekyll
  class SearchIndexGenerator < Generator
    safe true
    priority :low

    def generate(site)
      search_dir = File.join(site.source, '')
      index_path = File.join(search_dir, 'search-index.json')

      posts = site.posts.docs.map do |post|
        {
          'title'   => post.data['title'] || post.slug,
          'url'     => post.url,
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
