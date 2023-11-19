from django.dispatch import Signal

# Define a signal without providing_args
user_registered = Signal()
user_change_email = Signal()
user_verify_email = Signal()
user_cancel_account = Signal()
