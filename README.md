<div align = "center">

![Nova Loga](docs/nova.png)

A site building framework for people who like to keep it simple.

</div>

### Installation

```sh
pip install nova-framework
```

For the latest development version:
```sh
pip install git+https://github.com/iiPythonx/nova
```

### Usage

> [!WARNING]
> Nova 0.11 introduces some experimental features, you might experience bugs.

To initialize a Nova project, just run `nova init` and follow the instructions:
```sh
🚀 Nova 0.13.0 | Project Initialization
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

# optional
after_build_command = "bash /etc/somescript.sh"
```

##### Plugins

See [PLUGINS.md](./docs/PLUGINS.md).

### Built-in Jinja variables

- `GIT_HASH` - The full Git SHA of the current repo, updated once per build.
    - If git is not installed, or no `.git` folder is found, `GIT_HASH` will be a blank string.

### Troubleshooting

Ensure you have uvloop installed:
```sh
pacman -S libuv
dnf install libuv
apt install libuv1
```
