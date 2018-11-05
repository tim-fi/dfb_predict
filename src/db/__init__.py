from .models import *
from .core import *

__all__ = models.__all__ + core.__all__


DB.create_tables()
