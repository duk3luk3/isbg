def truncate(inp, length):
    if len(inp) > length:
        return repr(inp)[:length-3] + '...'
    else:
        return inp

def shorten(inp, length):
    if isinstance(inp, dict):
        return dict([(k, shorten(v, length)) for k,v in inp.items()])
    elif isinstance(inp, list) or isinstance(inp, tuple):
        return [ shorten(x, length) for x in inp]
    else:
        return truncate(inp, length)

