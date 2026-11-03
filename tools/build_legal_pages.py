"""Rebuild privacy and terms pages (IT + EN) from the SnapTask app's legal texts.

Usage: python3 tools/build_legal_pages.py <path to SnapTask/SnapTask/Legal>
The pages keep the head, style and nav of the current privacy.html / en/privacy.html.
"""
import sys,re,html,os,textwrap
legal=sys.argv[1]
site=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def swift_text(name):
    src=open(legal+'/LegalTexts.swift',encoding='utf-8').read()
    m=re.search(r'static let '+name+r' = """\n(.*?)\n    """',src,re.S)
    return textwrap.dedent(m.group(1))+'\n'
tmpl={'it':open(site+'/privacy.html',encoding='utf-8').read(),'en':open(site+'/en/privacy.html',encoding='utf-8').read()}
CFG={
 ('it','privacy'):dict(src=legal+'/PrivacyPolicy.it.md',out='privacy.html',title='Informativa sulla Privacy',desc="Informativa sulla privacy per l'app SnapTask.",self='/privacy',other='/en/privacy'),
 ('en','privacy'):dict(text=swift_text('privacyPolicyEN'),out='en/privacy.html',title='Privacy Policy',desc='Privacy policy for the SnapTask app.',self='/en/privacy',other='/privacy'),
 ('it','terms'):dict(src=legal+'/TermsOfService.it.md',out='termini.html',title='Termini di servizio',desc="Termini di servizio dell'app SnapTask.",self='/termini',other='/en/terms'),
 ('en','terms'):dict(text=swift_text('termsOfServiceEN'),out='en/terms.html',title='Terms of Service',desc='Terms of service for the SnapTask app.',self='/en/terms',other='/termini'),
}
L={'it':dict(updated='Ultimo aggiornamento',effective='Data di entrata in vigore',back='Torna a <a href="/">Home</a> o visita le pagine <a href="/supporto">Supporto</a>, <a href="/privacy">Privacy</a> e <a href="/termini">Termini</a>.'),
   'en':dict(updated='Last updated',effective='Effective date',back='Back to <a href="/en/">Home</a>, or see <a href="/en/support">Support</a>, <a href="/en/privacy">Privacy</a> and <a href="/en/terms">Terms</a>.')}
def inline(t):
    t=html.escape(t,quote=False)
    t=re.sub(r'giovannisebastianoamadei@gmail\.com',r'<a href="mailto:giovannisebastianoamadei@gmail.com">giovannisebastianoamadei@gmail.com</a>',t)
    t=re.sub(r'\bgaranteprivacy\.it\b',r'<a href="https://www.garanteprivacy.it">garanteprivacy.it</a>',t)
    return t
def li(t):
    m=re.match(r'^([^:]{1,40}):\s(.*)$',t)
    if m and '(' not in m.group(1) or (m and m.group(1).count('(')==m.group(1).count(')')):
        return f'<li><strong>{inline(m.group(1))}:</strong> {inline(m.group(2))}</li>'
    return f'<li>{inline(t)}</li>'
def body(md):
    lines=md.rstrip('\n').split('\n')
    dates=lines[:2]; rest=lines[2:]
    secs=[]; cur=None
    for l in rest:
        if l.startswith('## '): cur=[l[3:],[]]; secs.append(cur)
        elif cur is not None: cur[1].append(l)
    out=[]
    for i,(title,ls) in enumerate(secs):
        h=[]; ul=None
        def close():
            nonlocal ul
            if ul is not None: h.append('        <ul>\n'+'\n'.join('          '+x for x in ul)+'\n        </ul>'); ul=None
        for l in ls:
            s=l.strip()
            if not s: close(); continue
            if s.startswith('### '): close(); h.append(f'        <h3>{inline(s[4:])}</h3>'); continue
            if s.startswith('- '):
                if ul is None: ul=[]
                ul.append(li(s[2:])); continue
            close(); h.append(f'        <p>{inline(s)}</p>')
        close()
        op=' open' if i==1 and title.split('. ',1)[-1] in ('In breve','In Short') else ''
        out.append(f'    <div class="card">\n      <details{op}>\n        <summary><strong>{inline(title)}</strong></summary>\n'+'\n'.join(h)+'\n      </details>\n    </div>')
    return dates,'\n\n'.join(out)
for (lang,kind),c in CFG.items():
    t=tmpl[lang]
    dates,secs=body(c['text'] if 'text' in c else open(c['src'],encoding='utf-8').read())
    upd=dates[1].split(':',1)[1].strip(); eff=dates[0].split(':',1)[1].strip()
    head,_=t.split('    <h1>',1)
    head=re.sub(r'<title>.*?</title>',f'<title>SnapTask | {c["title"]}</title>',head)
    head=re.sub(r'<meta name="description" content="[^"]*">',f'<meta name="description" content="{html.escape(c["desc"])}">',head)
    # nav language switch points to the same document in the other language
    head=head.replace('href="/en/privacy">EN</a>',f'href="{c["other"]}">EN</a>') if lang=='it' else head.replace('<a href="/privacy" style="color:var(--link)">IT</a>',f'<a href="{c["other"]}" style="color:var(--link)">IT</a>')
    page=(head+f'    <h1>{c["title"]}</h1>\n    <p class="muted">{L[lang]["updated"]}: {upd}</p>\n\n'
          f'    <div class="card">\n      <p><strong>{L[lang]["effective"]}:</strong> {eff}</p>\n    </div>\n\n'
          +secs+f'\n\n    <p class="muted">{L[lang]["back"]}</p>\n  </div>\n</body>\n</html>\n')
    open(site+'/'+c['out'],'w',encoding='utf-8').write(page); print('wrote',c['out'])
