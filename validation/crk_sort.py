# Referencing: https://towardsdatascience.com/how-to-implement-merge-sort-algorithm-in-python-4662a89ae48c


def custom_sort(words):
    list_len = len(words)
    if list_len <= 1:
        return words

    mid_point = list_len // 2

    left_side = custom_sort(words[:mid_point])
    right_side = custom_sort(words[mid_point:])
    return merge(left_side, right_side)


def merge(left, right):
    output = []
    i = j = 0
    while i < len(left) and j < len(right):
        if custom_less_than(left[i], right[j]):
            output.append(left[i])
            i += 1
        else:
            output.append(right[j])
            j += 1

    output.extend(left[i:])
    output.extend(right[j:])
    return output


def custom_less_than(l, r):
    """
    Determines if l(eft) is less than r(ight)
    Returns True if l < r
    Returns False otherwise
    Needs the custom priority list so the sorting happens according to the crk dictionary

        Cree alphabet: (space) -  a  â  A Â c  C ê Ê h H i î I Î
        k K m M n N o  ô O Ô p P s S t T w W y Y
        bB dD fF gG jJ lL qQ rR uU vV zZ
    """

    l = l.transcription
    r = r.transcription

    priority_list = [
        " ",
        "-",
        "a",
        "A",
        "â",
        "ā",
        "Â",
        "Ā",
        "b",
        "B",
        "c",
        "C",
        "d",
        "D",
        "e",
        "E",
        "ê",
        "ē",
        "Ê",
        "Ē",
        "f",
        "F",
        "g",
        "G",
        "h",
        "H",
        "i",
        "I",
        "î",
        "ī",
        "Î",
        "Ī",
        "j",
        "J",
        "k",
        "K",
        "l",
        "L",
        "m",
        "M",
        "n",
        "ń",
        "N",
        "Ń",
        "o",
        "O",
        "ô",
        "ō",
        "Ô",
        "Ō",
        "p",
        "P",
        "q",
        "Q",
        "r",
        "R",
        "s",
        "š",
        "S",
        "Š",
        "t",
        "T",
        "u",
        "U",
        "v",
        "V",
        "w",
        "W",
        "x",
        "X",
        "y",
        "ý",
        "Y",
        "Ý",
        "z",
        "Z",
    ]

    i = min(len(l), len(r))
    j = 0
    while j < i:
        l_char = l[j]
        r_char = r[j]
        if not l_char in priority_list:
            l_char_pos = len(priority_list) + 1
        else:
            l_char_pos = priority_list.index(l_char)

        if not r_char in priority_list:
            r_char_pos = len(priority_list) + 1
        else:
            r_char_pos = priority_list.index(r_char)
        if l_char_pos < r_char_pos:
            return True
        elif l_char_pos > r_char_pos:
            return False
        j += 1
    return False
