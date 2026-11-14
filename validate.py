from html.parser import HTMLParser
import sys

VOID={'meta','link','br','img','input','hr'}
class P(HTMLParser):
    def __init__(s): super().__init__(); s.stack=[]; s.errs=[]
    def handle_starttag(s,t,a):
        if t not in VOID: s.stack.append(t)
    def handle_endtag(s,t):
        if t in VOID: return
        if s.stack and s.stack[-1]==t: s.stack.pop()
        else: s.errs.append(t)
p=P(); p.feed(open(sys.argv[1]).read()); p.close()
print('ERR', p.errs, 'UNCLOSED', p.stack)
sys.exit(1 if p.errs or p.stack else 0)