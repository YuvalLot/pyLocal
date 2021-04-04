
from math import ceil, floor, log10, sin, cos, tan, asin, acos, atan


# For Math
def Reader(queryName:str, queryComp:str):
    """
    basic math operations in LCL form.

    :param queryName: str
    :param queryComp: str
    :return: generator
    """

    if queryName == "hE":
        comps = queryComp.split(",")
        if len(comps) != 2:
            return
        if comps[0][0] == "?" or comps[1][0] == "?":
            return
        try:
            if float(comps[0]) == float(comps[1]):
                yield {}
            return
        except ValueError:
            return

    if queryName == 'hAdd':
        comps = queryComp.split(",")
        if len(comps) != 3:
            return
        if comps[0][0] == "?" or comps[1][0] == "?":
            return
        try:
            num1 = float(comps[0])
            num2 = float(comps[1])
            num3 = num1 + num2
            if num3.is_integer():
                num3 = int(num3)
            if comps[2][0] == "?":
                yield {comps[2]:str(num3)}
            elif float(comps[2]) == num3:
                yield {}
            else:
                return
        except ValueError:
            return

    if queryName == 'hSub':
        comps = queryComp.split(",")
        if len(comps) != 3:
            return
        if comps[0][0] == "?" or comps[1][0] == "?":
            return
        try:
            num1 = float(comps[0])
            num2 = float(comps[1])
            num3 = num1 - num2
            if num3.is_integer():
                num3 = int(num3)
            if comps[2][0] == "?":
                yield {comps[2]: str(num3)}
            elif float(comps[2]) == num3:
                yield {}
            else:
                return
        except ValueError:
            return

    if queryName == 'hMul':
        comps = queryComp.split(",")
        if len(comps) != 3:
            return
        if comps[0][0] == "?" or comps[1][0] == "?":
            return
        try:
            num1 = float(comps[0])
            num2 = float(comps[1])
            num3 = num1 * num2
            if num3.is_integer():
                num3 = int(num3)
            if comps[2][0] == "?":
                yield {comps[2]: str(num3)}
            elif float(comps[2]) == num3:
                yield {}
            else:
                return
        except ValueError:
            return

    if queryName == 'hDiv':
        comps = queryComp.split(",")
        if len(comps) != 3:
            return
        if comps[0][0] == "?" or comps[1][0] == "?":
            return
        try:
            num1 = float(comps[0])
            num2 = float(comps[1])
            if num2 == 0:
                return
            num3 = num1 / num2
            if num3.is_integer():
                num3 = int(num3)
            if comps[2][0] == "?":
                yield {comps[2]: str(num3)}
            elif float(comps[2]) == num3:
                yield {}
            else:
                return
        except ValueError:
            return

    if queryName == 'hMod':
        comps = queryComp.split(",")
        if len(comps) != 3:
            return
        if comps[0][0] == "?" or comps[1][0] == "?":
            return
        try:
            num1 = float(comps[0])
            num2 = float(comps[1])
            if num2 == 0:
                return
            num3 = num1 % num2
            if num3.is_integer():
                num3 = int(num3)
            if comps[2][0] == "?":
                yield {comps[2]: str(num3)}
            elif float(comps[2]) == num3:
                yield {}
            else:
                return
        except ValueError:
            return

    if queryName == 'hFloor':
        comps = queryComp.split(",")
        if len(comps) != 2:
            return
        if comps[0][0] == "?":
            return
        try:
            num1 = float(comps[0])
            num2 = int(floor(num1))
            if comps[1][0] == "?":
                yield {comps[1]: str(num2)}
            elif float(comps[1]) == num2:
                yield {}
            else:
                return
        except ValueError:
            return

    if queryName == 'hCeil':
        comps = queryComp.split(",")
        if len(comps) != 2:
            return
        if comps[0][0] == "?":
            return
        try:
            num1 = float(comps[0])
            num2 = int(ceil(num1))
            if comps[1][0] == "?":
                yield {comps[1]: str(num2)}
            elif float(comps[1]) == num2:
                yield {}
            else:
                return
        except ValueError:
            return

    if queryName == 'hPower':
        comps = queryComp.split(",")
        if len(comps) != 3:
            return
        if comps[0][0] == "?" or comps[1][0] == "?":
            return
        try:
            num1 = float(comps[0])
            num2 = float(comps[1])
            num3 = num1 ** num2
            if num3.is_integer():
                num3 = int(num3)
            if comps[2][0] == "?":
                yield {comps[2]: str(num3)}
            elif float(comps[2]) == num3:
                yield {}
            else:
                return
        except ValueError:
            return

    if queryName == 'hLog':
        comps = queryComp.split(",")
        if len(comps) != 2:
            return
        if comps[0][0] == "?":
            return
        try:
            num1 = float(comps[0])
            num2 = log10(num1)
            if num2.is_integer():
                num2 = int(num2)
            if comps[1][0] == "?":
                yield {comps[1]: str(num2)}
            elif float(comps[1]) == num2:
                yield {}
            else:
                return
        except ValueError:
            return

    if queryName == 'hCos':
        comps = queryComp.split(",")
        if len(comps) != 2:
            return

        if comps[1][0] == "?":
            try:
                num1 = float(comps[0])
                num2 = cos(num1)
                if num2.is_integer():
                    num2 = int(num2)
                yield {comps[1]: str(num2)}
            except ValueError:
                return

        elif comps[0][0] == "?":
            try:
                num1 = float(comps[1])
                try:
                    num2 = acos(num1)
                except ValueError:
                    return
                if num2.is_integer():
                    num2 = int(num2)
                yield {comps[0]: str(num2)}
            except ValueError:
                return
        else:
            try:
                num1 = float(comps[1])
                num2 = cos(float(comps[0]))
                if num1 == num2:
                    yield {}
            except ValueError:
                return

    if queryName == 'hSin':
        comps = queryComp.split(",")
        if len(comps) != 2:
            return

        if comps[1][0] == "?":
            try:
                num1 = float(comps[0])
                num2 = sin(num1)
                if num2.is_integer():
                    num2 = int(num2)
                yield {comps[1]: str(num2)}
            except ValueError:
                return

        elif comps[0][0] == "?":
            try:
                num1 = float(comps[1])
                try:
                    num2 = asin(num1)
                except ValueError:
                    return
                if num2.is_integer():
                    num2 = int(num2)
                yield {comps[0]: str(num2)}
            except ValueError:
                return
        else:
            try:
                num1 = float(comps[1])
                num2 = sin(float(comps[0]))
                if num1 == num2:
                    yield {}
            except ValueError:
                return

    if queryName == 'hTan':
        comps = queryComp.split(",")
        if len(comps) != 2:
            return

        if comps[1][0] == "?":
            try:
                num1 = float(comps[0])
                try:
                    num2 = tan(num1)
                except ValueError:
                    return
                if num2.is_integer():
                    num2 = int(num2)
                yield {comps[1]: str(num2)}
            except ValueError:
                return

        elif comps[0][0] == "?":
            try:
                num1 = float(comps[1])
                num2 = atan(num1)
                if num2.is_integer():
                    num2 = int(num2)
                yield {comps[0]: str(num2)}
            except ValueError:
                return
        else:
            try:
                num1 = float(comps[1])
                num2 = tan(float(comps[0]))
                if num1 == num2:
                    yield {}
            except ValueError:
                return

    if queryName == 'hLT':
        comps = queryComp.split(",")
        if len(comps) != 2:
            return
        try:
            num1 = float(comps[0])
            num2 = float(comps[1])
            if num1 < num2:
                yield {}
            else:
                return
        except ValueError:
            return
