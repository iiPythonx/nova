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

### Configuration and usage

To initialize a Nova project, just run `nova init` and follow the instructions:
```sh
🚀 Nova 0.3.0 | Project Initialization
Source location (default: src): src/
Destination location (default: dist): dist/
```

Afterwards, put your [Jinja2](https://jinja.palletsprojects.com/) and other assets inside your configured source folder.  
To launch a development server, you can run `nova serve --reload` to get a hot-reloading capable web server.  

---

To build your app for production, just run `nova build`. It will spit out a static site in your configured destination path.
