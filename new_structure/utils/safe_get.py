from ..extensions import db


def safe_get(model_cls, pk):
    """Wrapper around db.session.get(model_cls, pk).
    Returns None if pk is falsy. Simplifies future migration / instrumentation.
    """
    if pk is None:
        return None
    return db.session.get(model_cls, pk)
