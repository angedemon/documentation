def check_company_domain_parent_of(*a, **kw): return []
class Model:
    """Plain recorder standing in for the ORM root. Not base behaviour."""
    def create(self, vals_list): return vals_list
    def write(self, vals): return vals
    def _condition_to_sql(self, alias, fname, operator, value, query):
        return ('CONDITION', fname, operator, value)
