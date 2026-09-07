source "https://rubygems.org"

# Use GitHub Pages-compatible Jekyll and the plugins this site actually enables.
gem "jekyll", "~> 3.10.0"
gem "jekyll-sitemap", "~> 1.4.0"

# Ruby 3 no longer ships WEBrick, which powers the local preview server.
gem "webrick", "~> 1.8"

# Windows does not provide the IANA time zone database used by the site.
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end
