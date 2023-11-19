from django.apps import apps
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from apps.utils.exceptions import IntegrityError



def create_or_get_dimensions(breakpoint, w, h, x, y, moved=False, static=False, is_resizable=False):
    model_cls = apps.get_model("settings", "Dimensions")
    try:
        dimensions, created = model_cls.objects.get_or_create(
            breakpoint=breakpoint,
            w=w,
            h=h,
            x=x,
            y=y,
            moved=moved,
            static=static,
            isResizable=is_resizable
        )
        return dimensions, created
    except model_cls.MultipleObjectsReturned:
        # Handle the case when there are multiple matching records (if unique constraints are violated)
        return None, False

def account_pages_exists(account) -> bool:
    model_cls = apps.get_model("settings", "Page")
    qs = model_cls.objects.filter(account=account,
                                  )
    return qs.exists()


def create_account_pages(account):
    model_cls = apps.get_model("settings", "Page")
    try:
        return model_cls.objects.create(account=account,
                                        user=user,
                                        homepage=homepage)
    except IntegrityError as e:
        raise IntegrityError(
            _("Notify exists for specified user and account")) from e


