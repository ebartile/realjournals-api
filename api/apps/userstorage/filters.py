from apps.accounts.filters import FilterBackend


class StorageEntriesFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        queryset = super().filter_queryset(request, queryset, view)
        query_params = {}

        if "keys" in request.query_params:
            field_data = request.query_params["keys"]
            query_params["key__in"] = field_data.split(",")

        if query_params:
            queryset = queryset.filter(**query_params)

        return queryset
