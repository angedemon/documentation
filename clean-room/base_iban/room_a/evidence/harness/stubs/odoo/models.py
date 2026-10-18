class _BaseBank:
    """Stand-in for the base res.partner.bank parent (not available in SOURCE)."""
    def _get_supported_account_types(self):
        return [('bank', 'Normal')]
    def retrieve_acc_type(self, acc_number):
        return 'bank'   # STUB: base implementation not in SOURCE
    def create(self, vals_list):
        return vals_list
    def write(self, vals):
        return vals
class Model(_BaseBank):
    pass
