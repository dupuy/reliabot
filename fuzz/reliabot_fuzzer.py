#!/usr/bin/env python3.12
"""Atheris fuzzing harness for Reliabot.

Requires Python 3.11—3.12
"""

import sys
import atheris


# Import Reliabot modules
import os

# Make sure the parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with atheris.instrument_imports():
    from ruamel.yaml import YAML
    from reliabot import reliabot

from ruamel.yaml.reader import ReaderError
from ruamel.yaml.error import YAMLError


def test_one_input(data: bytes) -> None:
    """Fuzz One Input."""
    fdp = atheris.FuzzedDataProvider(data)

    # 1. Test YAML parsing and validation
    remaining_bytes = fdp.ConsumeBytes(sys.maxsize)

    yaml = YAML(pure=reliabot.PURE)
    try:
        # We stick to the pure python parser as used in reliabot
        config = yaml.load(remaining_bytes)
    except (ReaderError, YAMLError):
        # Expected errors for invalid YAML
        return
    except ValueError:
        # Expected error for invalid numerics ('.')
        return
    except (AssertionError, IndexError, RecursionError, TypeError):
        # "Unexpected" errors due to ruamel.yaml bugs, now handled
        return
    except NotImplementedError:
        # Expected errors due to ruamel.yaml "limitations", now handled
        return
    except Exception:
        # Unexpected errors in YAML parsing
        raise

    # 2. Test Dependabot configuration validation
    if isinstance(config, (dict, reliabot.CommentedMap)):
        try:
            reliabot.validate_dependabot_config(config)
        except ValueError:
            # Expected validation errors
            return
        except Exception:
            raise

        # 3. Test Dependabot configuration update
        try:
            ecos = {"/": {"npm"}}
            reliabot.update_dependabot_config(config, ecos, keep_all)
        except Exception:
            raise


def keep_all(_: str) -> bool:
    """Keep all configuration."""
    return True


if __name__ == "__main__":
    atheris.Setup(sys.argv, test_one_input)
    sys.argv.append("--re")  # disable RE2
    atheris.Fuzz()
