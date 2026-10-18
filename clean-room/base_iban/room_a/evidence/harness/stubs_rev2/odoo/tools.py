def _(source, *args, **kwargs):
    """Stub translation: returns the source string, %-formatted (no translation)."""
    if args: return source % args
    if kwargs: return source % kwargs
    return source
class LazyTranslate:
    def __init__(self, module): pass
    def __call__(self, source, *args, **kwargs): return _(source, *args, **kwargs)
class SQL: pass
def clean_context(ctx): return ctx
