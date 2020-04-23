def IntToByte4(arg1, arg2, arg3):
    arg2[arg3] = arg1 & 0xFF
    arg2[arg3 + 1] = (arg1 & 0xFF00) >> 8
    arg2[arg3 + 2] = (arg1 & 0xFF0000) >> 16
    arg2[arg3 + 3] = (arg1 & 0xFF000000) >> 24


def Byte4ToInt(arg1, arg2):
    return ((arg1[arg2 + 3] & 255) << 24) | ((arg1[arg2 + 2] & 255) << 16) | ((arg1[arg2 + 1] & 255) << 8) | (
                arg1[arg2] & 255)


def Byte2ToInt(arg1, arg2):
    return ((arg2 & 0xFF) << 8) | (arg1 & 0xFF)


def wmemcpyUni(key, length, uni):
    n = 0
    i = 0
    while i < length:
        uni[n] = key[i]
        uni[n + 1] = key[i + 1]
        n += 2
        i += 2
    return n


def AryByte2ToInt(arg1, arg2):
    return ((arg1[arg2 + 1] & 0xFF) << 8) | ((arg1[arg2]) & 0xFF)
