
import urllib.request as request
from html.parser import HTMLParser


class LCLParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.tags = None
        self.callback = []

    def error(self, message):
        pass

    def handle_starttag(self, tag, attrs):
        if not self.tags:
            self.tags = (tag, attrs, [])
            self.callback.append(self.tags[2])
        else:
            self.callback[-1].append((tag, attrs, []))
            self.callback.append(self.callback[-1][-1][2])

    def handle_endtag(self, tag):
        self.callback.pop()

    def handle_data(self, data):
        if not self.callback:
            return
        self.callback[-1].append(data)

    def handle_comment(self, data):
        pass

    def handle_charref(self, name):
        pass

    def handle_decl(self, data):
        pass



def beautify(tags, tabs=0):
    print('\t' * tabs, end="")
    if type(tags) is tuple:
        print(f"{tags[0]}    {tags[1]}")
        for part in tags[2]:
            beautify(part, tabs+1)
    else:
        print(tags)


def to_lcl(tags):
    if type(tags) == tuple:
        tag_type, attrs, children = tags
        lcl_attrs = []

        for attr in attrs:
            lcl_attrs.append(f"attr({attr[0]},\"{attr[1]}\")")
        lcl_children = []

        for child in children:
            lcl_children.append(to_lcl(child))

        lcl_attrs = ",".join(lcl_attrs)
        lcl_children = ",".join(lcl_children)

        return f"tag({tag_type},[{lcl_attrs}],[{lcl_children}])"
    else:
        return '"' + tags.replace('"', "'") + '"'


def is_valid(string):
    paren = []
    in_q = False
    for c in string:
        if c == '"':
            in_q = not in_q
        if c == "(":
            paren.append(")")
        if c == "[":
            paren.append("]")
        if c in ")]":
            if len(paren) == 0 or paren[-1] != c:
                return False
            paren.pop()
    return True


def url_opener(url):
    text = request.urlopen(url).read().decode('utf-8')
    Parser = LCLParser()
    Parser.feed(text)
    if not Parser.tags:
        text = text.replace('"', "'")
        return f"\"{text}\""
    t = to_lcl(Parser.tags)
    if is_valid(t):
        return t
    else:
        return None


if __name__ == "__main__":
    x = url_opener("http://www.randomnumberapi.com/api/v1.0/random?min=1&max=10&count=1")
    print(is_valid(x))
