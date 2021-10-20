import os
import toml

def get_pat(key_name='admin'):
    home = os.path.expanduser("~")
    config_file_name = ".gh_pat.toml"
    if os.path.exists(config_file_name):
        config_file = config_file_name
    elif os.path.exists(os.path.join(home, config_file_name)):
        config_file = os.path.join(home, config_file_name)
    else:
      return None

    try:
      toml_blob = toml.load(config_file)
      pat = toml_blob[key_name]
      return pat
    except Exception:
      return None

