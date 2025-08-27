import os
import environ


# Print when settings file is loaded
print("Loading config.settings.__init__.py")

# Initialize django-environ
env = environ.Env(
    ENVIRONMENT=(str, "development"),
    OTEL_ENABLED=(bool, False),
)

# Read .env file if it exists
# Look for .env file in the project root directory
env_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)
if os.path.exists(env_file_path):
    environ.Env.read_env(env_file_path)
else:
    # Try the default location as fallback
    environ.Env.read_env()


# Determine which settings to load based on ENVIRONMENT variable
if env("ENVIRONMENT") == "production":
    print("Loading production settings")
    from .production import *  # noqa: F403
elif env("ENVIRONMENT") == "test":
    print("Loading test settings")
    from .test import *  # noqa: F403
else:
    print("Loading development settings")
    from .dev import *  # noqa: F403
