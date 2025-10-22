class InMemoryDB:
    """Very small placeholder for a database connection/store.

    This keeps the structure clear and can be replaced with SQLAlchemy or other
    database clients later.
    """

    def __init__(self):
        self.store = {}

    def get(self, key, default=None):
        return self.store.get(key, default)

    def set(self, key, value):
        self.store[key] = value

    def delete(self, key):
        if key in self.store:
            del self.store[key]

db = InMemoryDB()
