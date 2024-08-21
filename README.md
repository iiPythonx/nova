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
🚀 Nova 0.8.1 | Project Initialization
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

##### Plugins

See [PLUGINS.md](./docs/PLUGINS.md).


### Troubleshooting

Ensure you have uvloop installed:
```sh
pacman -S libuv
dnf install libuv
apt install libuv1
