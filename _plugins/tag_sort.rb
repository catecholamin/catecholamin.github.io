module Jekyll
  # Generates sorted tag data for use in tags.html
  # Creates site.data['sorted_tags'] = [{name: 'tag', count: n}, ...] sorted by count desc
  class TagSortGenerator < Generator
    safe true

    def generate(site)
      tags = site.tags
      sorted = tags.sort_by { |_name, posts| -posts.size }
      site.data['sorted_tags'] = sorted.map { |name, posts| { 'name' => name, 'count' => posts.size } }
    end
  end
end
