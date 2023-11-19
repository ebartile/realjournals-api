from .service import register_timeline_implementation
from . import service


@register_timeline_implementation("accounts.account", "create")
@register_timeline_implementation("accounts.account", "change")
@register_timeline_implementation("accounts.account", "delete")
def account_timeline(instance, extra_data={}):
    result = {
        "account": service.extract_account_info(instance),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("journals.journal", "create")
@register_timeline_implementation("journals.journal", "change")
@register_timeline_implementation("journals.journal", "delete")
def journal_timeline(instance, extra_data={}):
    result = {
        "journal": service.extract_journal_info(instance),
        "account": service.extract_account_info(instance.account),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("accounts.membership", "create")
@register_timeline_implementation("accounts.membership", "delete")
def membership_timeline(instance, extra_data={}):
    result = {
        "user": service.extract_user_info(instance.user),
        "account": service.extract_account_info(instance.account),
        "role": service.extract_role_info(instance.role),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("users.user", "create")
def user_timeline(instance, extra_data={}):
    result = {
        "user": service.extract_user_info(instance),
    }
    result.update(extra_data)
    return result
