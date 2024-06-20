# Nova / Structure

The basic Nova project structure should look something like this:
```
src/
├── template.jinja2
├── example.jinja2
└── static/
    ├── robots.txt
    └── main.js
```

The `src` folder will change depending on your configuration inside `nova.toml`.  
The `static` folder will be copied 1:1 to your output folder on build via the static plugin.
