class LazyTranslate:
    """Stub: returns the source string, %-formatted with args (no translation)."""
    def __init__(self, module): pass
    def __call__(self, source, *args, **kwargs):
        if args:
            return source % args
        if kwargs:
            return source % kwargs
        return source
