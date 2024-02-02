class DatabaseRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'journals':
            return 'mongodb'  # Route specific app's models to MongoDB
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'journals':
            return 'mongodb'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations if both objects are in the same database
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'journals':
            return db == 'mongodb'
        return db == 'default'
