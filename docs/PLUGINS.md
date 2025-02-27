# Nova / Plugins

> [!NOTE]
> Any `mapping` options are relative to `project.mapping` unless otherwise stated.

#### Plugins / Single Page App

This plugin implements support for [Single Page Applications](https://en.wikipedia.org/wiki/Single-page_application).  
Place valid Jinja2 inside a pages folder and this plugin will build it to create only the diff of the compiled HTML for serving.  

If you have questions about this plugin, feel free to open a Github discussion.

```toml
[plugins.spa]
title = "My Website"
title_sep = "-"
mapping = "pages:."

# Target element the JS will swap out
target = ".any_css_selector" 

# Skip embedding the JS into the file and just add a script-src? (optional)
external = false

# Skip adding a script altogether, allowing you to make your own? (optional)
noscript = false
```

#### Plugins / Sass

This plugin adds basic Sass compilation support using [Dart Sass](https://sass-lang.com/dart-sass/).

```toml
[plugins.sass]
mapping = "sass:css"
```

#### Plugins / Static

This plugin has no configuration, it will copy Nova's `static` folder to your output folder every build.  
See [the source code](https://github.com/iiPythonx/nova/blob/main/nova/plugins/plugin_static.py) for more details about this process, or see [STRUCTURE.md](./STRUCTURE.md) for example structure.

#### Plugins / Minification

This plugin adds basic HTML, CSS, & JS minification.  
HTML is minified with [minify-html](https://github.com/wilsonzlin/minify-html), JS with [uglifyjs](https://github.com/mishoo/UglifyJS), and CSS with [csso](https://github.com/css/csso).

```toml
[plugins.minify]
suffixes = [".html", ".js"]
```

#### Plugins / Nonce

This plugin adds a static nonce to all link, script, and style tags in your built files. It is meant to be replaced on demand with your per-request nonce by something like a Cloudflare worker.

```toml
[plugins.nonce]
nonce = "Z2TFyOVC69nS8fvS/tC/Lw=="
```

#### Plugins / Typescript

This plugin adds basic Typescript compilation support using [swc](https://github.com/swc-project/swc).

```toml
[plugins.typescript]
mapping = "ts:js"
```
