import os
import toml

# pat file format:
#
# admin = "key1"
# read-only = "key2"
# key99 = "key99"
#
def get_pat_from_file(key_name='admin'):
    home = os.path.expanduser("~")
    config_file_name = ".gh_pat.toml"
    if os.path.exists(config_file_name):
        config_file = config_file_name
    elif os.path.exists(os.path.join(home, config_file_name)):
        config_file = os.path.join(home, config_file_name)
    else:
      return None

    # TODO: check that file permissions are 600

    try:
      toml_blob = toml.load(config_file)
      pat = toml_blob[key_name]
      return pat
    except Exception:
      return None
