from django.apps import apps


def get_instance_by_ref(account_id, obj_ref):
    model_cls = apps.get_model("references", "Reference")
    try:
        instance = model_cls.objects.get(account_id=account_id, ref=obj_ref)
    except model_cls.DoesNotExist:
        instance = None

    return instance
