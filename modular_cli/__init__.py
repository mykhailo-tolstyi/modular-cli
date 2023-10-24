import pkg_resources


def get_entry_point() -> str:
    default_name = 'modular-cli'
    for item in pkg_resources.working_set:
        if isinstance(item, pkg_resources.EggInfoDistribution):
            default_name = item.key
            break

    return default_name


ENTRY_POINT = get_entry_point()
