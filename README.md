# Nova

A site building framework for people who like to keep it simple.

---

### Installation

```sh
pip install nova-framework
```

For the latest development version:
```sh
pip install git+https://github.com/iiPythonx/nova
```

### Usage

To initialize a Nova project, just run `nova init` and follow the instructions:
```sh
🚀 Nova 0.7.2 | Project Initialization
Source location (default: src): src/
Destination location (default: dist): dist/
```

Afterwards, put your [Jinja2](https://jinja.palletsprojects.com/) and other assets inside your configured source folder.  

Run `nova build` to get a static site built for production in your destination path.  
Run `nova serve` to serve a static build of your site.  
Run `nova serve --reload` to get a hot-reloading capable web server.  

### Configuration

All project configuration should be put inside of `nova.toml` in your working directory.

##### Project

```toml
[project]
mapping = "source_path:destination_path"
```

##### Plugins / Single Page App

```toml
[plugins.spa]
title = "My Website"
title_sep = "-"

# Target element the JS will swap out
target = ".any_css_selector" 

# These are relative to your configured paths
# ie. source_path/relative_source and destination_path/relative_destination
mapping = "relative_source:relative_destination"

# Skip embedding the JS into the file and just add a script-src?
external = true
```

##### Plugins / Minification

```toml
[plugins.minify]

# Available options are .js, .css, and .html
suffixes = [".html", ".js"]

[plugins.minify.options]

# See https://docs.rs/minify-html/latest/minify_html/struct.Cfg.html
# This section only applies to HTML minification
keep_comments = true
keep_closing_tags = false
```

##### Plugins / Nonce

```toml
[plugins.nonce]

# This nonce will be added to every link, script, and style tag
nonce = "Z2TFyOVC69nS8fvS/tC/Lw=="
```

##### Plugins / Typescript

```toml
[plugins.typescript]

# These are relative to your configured paths
# ie. source_path/ts and destination_path/js
mapping = "ts:js"
