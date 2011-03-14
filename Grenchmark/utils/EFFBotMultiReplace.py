
#------------------------------------------------
# from http://effbot.org/zone/python-replace.htm
# Replace multiple string pairs in one go 

import re, string

class MultiReplace:

    def __init__(self, repl_dict):
        # "compile" replacement dictionary

        # assume char to char mapping
        charmap = map(chr, range(256))
        for k, v in repl_dict.items():
            if len(k) != 1 or len(v) != 1:
                self.charmap = None
                break
            charmap[ord(k)] = v
        else:
            self.charmap = string.join(charmap, "")
            return

        # string to string mapping; use a regular expression
        keys = repl_dict.keys()
        keys.sort() # lexical order
        pattern = string.join(map(re.escape, keys), "|")
        self.pattern = re.compile(pattern)
        self.dict = repl_dict

    def replace(self, str):
        # apply replacement dictionary to string
        if self.charmap:
            return string.translate(str, self.charmap)
        def repl(match, get=self.dict.get):
            item = match.group(0)
            return get(item, item)
        return self.pattern.sub(repl, str)

if __name__ == '__main__':
    r = MultiReplace({"spam": "eggs", "eggs": "spam"})
    print r.replace("spam&eggs")

    r = MultiReplace({"a": "b", "b": "a"})
    print r.replace("keaba")

    r = MultiReplace({". ": "\n", "!": "exclamation", "?": "question"})
    print repr(r.replace("look. an albatross !"))

