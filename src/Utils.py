def array_string_to_list(array_string, item_type):
    """
    Function to return list stored as string back into a list.
    :param str array_string: string in form of '[A1,A2,A3,A4]'
    :param item_type: type of item to cast each object in array to
    :returns []
    """

    if item_type is None:
        item_type = str

    trimmed = array_string[1:len(array_string) - 1]
    items = trimmed.split(",")
    out = []
    for item in items:
        if not (item == '' or item is None):
            out.append(item_type(item))
    return out
