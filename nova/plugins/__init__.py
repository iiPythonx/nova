from .plugin_sass import SassPlugin
from .plugin_static import StaticPlugin

available_plugins = {
    "sass": SassPlugin,
    "static": StaticPlugin
}
