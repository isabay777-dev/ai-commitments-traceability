import re, html
from html.parser import HTMLParser

class _T(HTMLParser):
    def __init__(self):
        super().__init__(); self.out=[]; self.skip=0
    def handle_starttag(self,t,a):
        if t in ('script','style'): self.skip+=1
        if t in ('p','div','br','tr','li','h1','h2','h3','h4','td'): self.out.append('\n')
    def handle_endtag(self,t):
        if t in ('script','style'): self.skip-=1
    def handle_data(self,d):
        if not self.skip: self.out.append(d)

def xhtml_to_text(s):
    p=_T(); p.feed(s); t=''.join(p.out)
    t=re.sub(r'[ \t\xa0]+',' ',t); t=re.sub(r'\n\s*\n+','\n',t)
    return t.strip()

# Narrow AI dictionary (EN/PL/NL/RU/KZ); generic digitalisation terms deliberately excluded
AI_PATTERNS = [
 r'artificial intelligence', r'\bA\.?I\.?\b(?=[\s\-]*(?:model|tool|solution|system|based|driven|powered|agent|technolog|application|use|adoption|capabilit|act|governance|strategy|platform|assistant))',
 r'machine learning', r'deep learning', r'neural network', r'generative ai', r'\bgenai\b', r'large language model', r'\bLLMs?\b', r'natural language processing', r'computer vision', r'chatgpt', r'\bcopilot\b',
 r'sztuczn\w* inteligencj\w*', r'uczeni\w* maszynow\w*', r'sieci\w* neuronow\w*',
 r'kunstmatige intelligentie', r'machinaal leren',
 r'искусственн\w* интеллект\w*', r'машинн\w* обучени\w*', r'нейросет\w*', r'нейронн\w* сет\w*', r'генеративн\w*',
 r'жасанды интеллект\w*',
 r'\bИИ\b', r'\bSI\b(?=\s+(?:w|do|jest|oraz|i)\b)',
]
AI_RE = re.compile('|'.join(AI_PATTERNS), re.I)

def ai_hits(text):
    sents = re.split(r'(?<=[\.\!\?])\s+|\n', text)
    return [s.strip() for s in sents if AI_RE.search(s)]
