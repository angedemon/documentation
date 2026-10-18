class _Field:
    def __init__(self, *a, **kw): self.args, self.kw = a, kw
Char = Boolean = Selection = Many2one = Integer = _Field
