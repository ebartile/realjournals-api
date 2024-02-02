
def attach_members(queryset, as_field="members_attr"):
    """Attach a json members representation to each object of the queryset.

    :param queryset: A Django accounts queryset object.
    :param as_field: Attach the members as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """
             SELECT json_agg(row_to_json(t))
              FROM  (
                        SELECT users_user.id,
                               users_user.username,
                               users_user.first_name,
                               users_user.last_name,
                               users_user.email,
                               concat(first_name, last_name) complete_user_name,
                               users_user.photo,
                               users_user.is_active,
                               accounts_accountrole.id "role",
                               accounts_accountrole.name role_name
                          from accounts_membership
                     LEFT JOIN users_user ON accounts_membership.user_id = users_user.id
                     LEFT JOIN accounts_accountrole ON accounts_accountrole.id = accounts_membership.role_id
                         WHERE accounts_membership.account_id = {tbl}.id
                      ORDER BY complete_user_name
                    ) t
          """

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_notify_policies(queryset, as_field="notify_policies_attr"):
    """Attach a json notification policies representation to each object of the queryset.

    :param queryset: A Django accounts queryset object.
    :param as_field: Attach the notification policies as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """
             SELECT json_agg(row_to_json(notifications_notifypolicy))
               from notifications_notifypolicy
              WHERE notifications_notifypolicy.account_id = {tbl}.id
          """

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset

def attach_my_role_permissions(queryset, user, as_field="my_role_permissions_attr"):
    """Attach a permission array to each object of the queryset.

    :param queryset: A Django accounts queryset object.
    :param as_field: Attach the permissions as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    if user is None or user.is_anonymous:
        sql = "SELECT '{}'"
    else:
        sql = """
                 SELECT accounts_accountrole.permissions
                   from accounts_membership
              LEFT JOIN users_user ON accounts_membership.user_id = users_user.id
              LEFT JOIN accounts_accountrole ON accounts_accountrole.id = accounts_membership.role_id
                  WHERE accounts_membership.account_id = {tbl}.id AND
                        users_user.id = {user_id}"""

        sql = sql.format(tbl=model._meta.db_table, user_id=user.id)

    queryset = queryset.extra(select={as_field: sql})
    return queryset

def attach_private_accounts_same_owner(queryset, user, as_field="private_accounts_same_owner_attr"):
    """Attach a private accounts counter to each object of the queryset.

    :param queryset: A Django accounts queryset object.
    :param as_field: Attach the counter as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    if user is None or user.is_anonymous:
        sql = "SELECT 0"
    else:
        sql = """
                 SELECT COUNT(id)
                   from accounts_account p_aux
                  WHERE p_aux.is_private = True AND
                        p_aux.owner_id = {tbl}.owner_id
              """

        sql = sql.format(tbl=model._meta.db_table, user_id=user.id)

    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_public_accounts_same_owner(queryset, user, as_field="public_accounts_same_owner_attr"):
    """Attach a public accounts counter to each object of the queryset.

    :param queryset: A Django accounts queryset object.
    :param as_field: Attach the counter as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    if user is None or user.is_anonymous:
        sql = "SELECT 0"
    else:
        sql = """
                 SELECT COUNT(id)
                   from accounts_account p_aux
                  WHERE p_aux.is_private = False AND
                        p_aux.owner_id = {tbl}.owner_id
              """

        sql = sql.format(tbl=model._meta.db_table, user_id=user.id)

    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_roles(queryset, as_field="roles_attr"):
    """Attach a json roles representation to each object of the queryset.

    :param queryset: A Django accounts queryset object.
    :param as_field: Attach the roles as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """
             SELECT json_agg(
                        row_to_json(accounts_accountrole)
                        ORDER BY accounts_accountrole.order
                    )
               from accounts_accountrole
              WHERE accounts_accountrole.account_id = {tbl}.id
          """

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset

def attach_extra_info(queryset, user=None):
    queryset = attach_members(queryset)
    queryset = attach_notify_policies(queryset)
    queryset = attach_roles(queryset)
    queryset = attach_my_role_permissions(queryset, user)
    queryset = attach_private_accounts_same_owner(queryset, user)
    queryset = attach_public_accounts_same_owner(queryset, user)
    queryset = attach_is_fan(queryset, user)

    return queryset

def attach_basic_info(queryset, user=None):
    """Attach basic information to each object of the queryset. It's a conservative approach,
    could be reduced in future versions.

    :param queryset: A Django projects queryset object.

    :return: Queryset
    """
    queryset = attach_members(queryset)
    queryset = attach_notify_policies(queryset)
    queryset = attach_my_role_permissions(queryset, user)
    queryset = attach_private_accounts_same_owner(queryset, user)
    queryset = attach_public_accounts_same_owner(queryset, user)
    queryset = attach_is_fan(queryset, user)

    return queryset

def attach_is_fan(queryset, user, as_field="is_fan_attr"):
    """Attach a is fan boolean to each object of the queryset.

    :param queryset: A Django projects queryset object.
    :param as_field: Attach the boolean as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    if user is None or user.is_anonymous:
        sql = "SELECT false"
    else:
        sql = """
                 SELECT COUNT(likes_like.id) > 0
                   from likes_like
             INNER JOIN django_content_type ON likes_like.content_type_id = django_content_type.id
                  WHERE django_content_type.model = 'account' AND
                        django_content_type.app_label = 'accounts' AND
                        likes_like.user_id = {user_id} AND
                        likes_like.object_id = {tbl}.id
              """

        sql = sql.format(tbl=model._meta.db_table, user_id=user.id)

    queryset = queryset.extra(select={as_field: sql})
    return queryset
