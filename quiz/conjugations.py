# -*- coding: utf-8

import re

FPS = 0 # First person singular
SPS = 1
TPS = 2
FPP = 3
SPP = 4
TPP = 5

### CONVENIENCE FUNCTIONS ###
def conjdic (*lst):
    lst = list(lst)
    while len(lst) < 6:
        lst.append(lst[-1])
    return {FPS:lst[0],SPS:lst[1],TPS:lst[2],
            FPP:lst[3],SPP:lst[4],TPP:lst[5]}

# ENGLISH DATA

ENG_SUBJ_PRO = conjdic(u'I',u'you',u'he/she/it',u'We',u'you guys',u'they')

eng_irregular_present = {
    'be': conjdic(u'am',u'are',u'is',u'are'),
    u'be (condition)': conjdic(u'am (condition)',u'are (condition)',u'is (condition)',u'are (condition)'),
    u'be (identity)': conjdic(u'am (identity)',u'are (identity)',u'is (identity)',u'are (identity)'),
    u'can':conjdic(u'can'),
    u'have':conjdic(u'have',u'have',u'has',u'have')
    }

eng_irregular_past = {
    u'be' : conjdic(u'was',u'were',u'was',u'were'),
    u'be (condition)': conjdic(u'was (condition)',u'were (condition)',u'was (condition)',u'were (condition)'),
    u'be (identity)': conjdic(u'was (identity)',u'were (identity)',u'was (identity)',u'were (identity)'),    
    
    }
eng_irregular_past_simple = {
    u'give':u'gave',u'have':u'had',u'write':u'wrote',u'go':u'went',u'feel':u'felt',
    u'eat':u'ate',u'know':u'knew',u'spit':u'spit (past)',u'put':u'put (past)',
    u'come':u'came',u'can':u'could',u'see':u'saw',u'think':u'thought',u'say':u'said',
    }

eng_irregular_pp = {
    u'see':u'seen',
    u'write':u'written',
    u'be':u'been',
    u'be (condition)': u'been (condition)',
    u'be (identity)': u'been (identity)',        
    u'go':u'gone',
    u'has':u'had',
    u'come':u'come',
    u'put':u'put',
    u'know':u'known',
    u'smite':u'smitten',
    u'can':u'been able',
    u'think':u'thought',
    u'say':u'said'
    }

# ENGLISH CONVENIENCE FUNCTS

def make_eng_form_from_stem (inf, ending):
    suffix = u''
    suffix_match = re.search(u'\s-*\([^)]*\)$',inf)
    if suffix_match:
        suffix = inf[suffix_match.start():suffix_match.end()]
        inf = inf[:suffix_match.start()]
    if inf[-1] in ['sz'] and ending==u's':
        return inf+u'e'+ending+suffix
    if inf.endswith(u'e') and inf.lower()!=u'be':
        return inf[:-1]+ending+suffix
    else:
        # double consonants for short vowels...
        if inf[-1] in u'dgmnpt' and inf[-2] in u'aeiou' and not inf[-3] in u'aeiou':
            return inf + inf[-1] + ending + suffix
        else:
            return inf+ending+suffix

# ENGLISH CONJUGATIONS

def make_eng_present (inf, person):
    if eng_irregular_present.has_key(inf):
        return ENG_SUBJ_PRO[person] + u' ' + eng_irregular_present[inf][person]
    if person != TPS:
        return ENG_SUBJ_PRO[person] + u' ' + inf
    else:
        return ENG_SUBJ_PRO[person] + u' ' + inf + u's'

def make_eng_present_subjunctive (inf, person):
    return make_eng_present(inf, person) + u' (subjunctive)'

def make_eng_pret (inf, person):
    if eng_irregular_past.has_key(inf):
        return ENG_SUBJ_PRO[person] + u' ' + eng_irregular_past[inf][person]
    elif eng_irregular_past_simple.has_key(inf):
        return ENG_SUBJ_PRO[person] + u' ' + eng_irregular_past_simple[inf]
    else:
        return ENG_SUBJ_PRO[person] + u' ' +  make_eng_form_from_stem(inf,u'ed')

def make_eng_past_progr (inf, person):
    return ENG_SUBJ_PRO[person] + u' ' + eng_irregular_past['be'][person] + u' ' + make_eng_form_from_stem(inf,u'ing')

def make_eng_past_subj (inf, person):
    return ENG_SUBJ_PRO[person] + " were to " + inf

def make_eng_cond (inf, person):
    return ENG_SUBJ_PRO[person] + u' would ' + inf

def make_eng_past_participle (inf):
    if eng_irregular_pp.has_key(inf): return eng_irregular_pp[inf]
    else: return make_eng_form_from_stem(inf,u'ed')

def make_eng_present_perfect (inf, person):
    return make_eng_present(u'have',person) + u' ' + make_eng_past_participle(inf)

def make_eng_pluperfect (inf, person):
    return make_eng_pret(u'have',person) + u' ' + make_eng_past_participle(inf)

def make_eng_pluperfect_subj (inf, person):
    return make_eng_past_subj(u'have',person) + u' ' + make_eng_past_participle(inf)

def make_eng_present_perfect_subj (inf, person):
    return make_eng_present_perfect(inf,person) + u' (subjunctive)'


### SPANISH DATA ###

FUT_ROOT = {
    u'decir':u'dir',
    u'hacer':u'har',
    u'poder':u'podr',
    u'poner':u'pondr',
    u'querer':u'querr',
    u'saber':u'sabr',
    u'salir':u'saldr',
    u'tener':u'tendr',
    u'venir':u'vendr',
    }

consonants = u'bcdfghjklmnñpqrstvxyz'

preterit_irregular = {
    u'ser':conjdic(u'(de ser) fui',u'(de ser) fuiste',u'(de ser) fue',u'(de ser) fuimos',u'(de ser) fuisteis',u'(de ser) fueron'),
    u'ir':conjdic(u'(de ir) fui',u'(de ir) fuiste',u'(de ir) fue',u'(de ir) fuimos',u'(de ir) fuisteis',u'(de ir) fueron'),    
    u'ver':conjdic(u'vi',u'viste',u'vio',u'vimos',u'visteis',u'vieron'),
    u'dar':conjdic(u'di',u'diste',u'dio',u'dimos',u'disteis',u'dieron'),
    }

preterit_irregular_stems = {
    u'decir':u'dij',
    u'estar':u'estuv',
    u'haber':u'hub',
    u'hacer':u'hic',
    u'poder':u'pud',
    u'poner':u'pus',
    u'querer':u'quis',
    u'saber':u'sup',
    u'tener':u'tuv',
    u'traer':u'traj',
    u'venir':u'vin',
    }

present_irregular = {
    u'ser':conjdic(u'soy',u'eres',u'es',u'somos',u'sois',u'son'),
    u'ir':conjdic(u'voy',u'vas',u'va',u'vamos',u'vais',u'van'),
    u'ver':conjdic(u'veo',u'ves',u've',u'vemos',u'veis',u'ven'),
    u'haber':conjdic(u'he',u'has',u'ha',u'hemos',u'habeis',u'han'),
    u'estar':conjdic(u'estoy',u'estás',u'está',u'estamos',u'estáis',u'están')
    }

present_irregular_yo = {
    u'dar':u'doy',
    u'poner':u'pongo',
    u'saber':u'sé',
    u'venir':u'vengo',
    u'decir':u'digo',
    u'valer':u'valgo',
    u'salir':u'salgo',
    u'conocer':u'conozco',
    u'parecer':u'parezco',
    }

irregular_participle = {
    u'escribir':u'escrito',
    u'hacer':u'hecho',
    u'poner':u'puesto',
    u'ver':u'visto',
    u'volver':u'vuelto',
    u'hacer':u'hecho',
    u'decir':u'dicho',
    }

stem_change = {
    u'decir':u'dice',
    u'pedir':u'pide',
    u'jugar':u'juega',
    u'sentir':u'siente',
    u'sentar':u'sienta',
    u'poder':u'puede',
    u'querer':u'quiere',
    u'venir':u'viene',
    u'tener':u'tiene',
    }

### SPANISH CONVENIENCE FUNC
def make_form_from_stem (infinitive, ending):
    SOFT_VOWELS = u'éíei'
    ACCENTS = u'áéóíú'
    accented_ending = False
    for a in ACCENTS:
        if a in ending: accented_ending = True
    if not (len(ending) > 2 or accented_ending):
        # Check for stem-change
        if stem_change.has_key(infinitive):
            infinitive = stem_change[infinitive] + u'r'
    if infinitive.endswith(u'zar') and ending[0] in SOFT_VOWELS:
        return infinitive[:-3]+u'c'+ending
    elif infinitive.endswith(u'car') and ending[0] in SOFT_VOWELS:
        return infinitive[:-3]+u'qu'+ending
    elif infinitive.endswith(u'gar') and ending[0] in SOFT_VOWELS:
        print ending[0],u'is a soft vowel',ending
        return infinitive[:-3]+u'gu'+ending
    else:
        return infinitive[:-2]+ending

def make_verb (inf, person, ar_stems, er_stems=None, ir_stems=None):
    if not er_stems: er_stems = ar_stems
    if not ir_stems: ir_stems = er_stems
    if inf.endswith(u'ar'):
        return make_form_from_stem(inf,ar_stems[person])
    elif inf.endswith(u'er'):
        return make_form_from_stem(inf,er_stems[person])
    else:
        return make_form_from_stem(inf,ir_stems[person])

# SPANISH CONJS

def make_present (inf, person):
    if present_irregular.has_key(inf):
        return present_irregular[inf][person]
    elif person==FPS and present_irregular_yo.has_key(inf):
        return present_irregular_yo[inf]
    else:
        return make_verb(inf,
                         person,
                         conjdic(u'o',u'as',u'a',u'amos',u'áis',u'an'),
                         conjdic(u'o',u'es',u'e',u'emos',u'éis',u'en'),
                         conjdic(u'o',u'es',u'e',u'imos',u'ís',u'en')
                         )


def make_imperfect (inf, person):
    ir_conj = conjdic(u'iba',u'ibas',u'iba',u'íbamos',u'íbais',u'iban')
    ser_conj = conjdic(u'era',u'eras',u'era',u'éramos',u'érais',u'eran')
    if inf == u'ver': inf = u'veer'
    if inf == u'ir': return ir_conj[person]
    if inf == u'ser': return ser_conj[person]
    return make_verb(inf,person,
                     conjdic(u'aba',u'abas',u'aba',u'ábamos',u'abais',u'aban'),
                     conjdic(u'ía',u'ías',u'ía',u'íamos',u'íais',u'ían'),
                     )
                         
def make_preterit (inf, person):
    if preterit_irregular.has_key(inf):
        return preterit_irregular[inf][person]
    elif preterit_irregular_stems.has_key(inf):
        endings = {FPS:u'e',SPS:u'iste',TPS:u'o',
                   FPP:u'imos',SPP:u'isteis',TPP:u'ieron'}
        return (preterit_irregular_stems[inf] + endings[person]).replace(u'jie',u'je')
    elif inf.endswith(u'ir'):
        root = inf[:-2]
        syllables = filter(lambda x:x, re.split(u'[%s]+u'%consonants,root))
        if syllables[-1] == u'e':
            root = root.replace(u'e',u'i')
        inf = root + u'ir'
    return make_verb(inf,person,
                     ar_stems = {FPS:u'é',SPS:u'aste',TPS:u'ó',
                                 FPP:u'amos',SPP:u'asteis',TPP:u'aron'},
                     er_stems = {FPS:u'í',SPS:u'iste',TPS:u'ió',
                                 FPP:u'imos',SPP:u'isteis',TPP:u'ieron'})

def make_present_subjunctive (inf, person):
    if inf == u'ser': inf = u'seer'
    elif inf == u'ver': inf = u'veer'
    elif inf == u'ir': inf = u'vayer'
    elif inf == u'haber': inf = u'hayer'
    elif inf == u'estar':
        return conjdic(u'esté',u'estés',u'esté',u'estemos',u'estéis',u'estén')[person]
    elif present_irregular_yo.has_key(inf):
        stems = conjdic(u'a',u'as',u'a',u'amos',u'áis',u'an')
        return make_present(inf,FPS)[:-1] + stems[person]
    return make_verb(inf,person,
                     ar_stems=conjdic(u'e',u'es',u'e',u'emos',u'éis',u'en'),
                     er_stems=conjdic(u'a',u'as',u'a',u'amos',u'áis',u'an')
                     )

def make_past_subjunctive (inf, person):
    root = make_preterit(inf,TPP)[:-2]
    stems = conjdic(u'a',u'as',u'a',u'amos',u'ais',u'an')
    form = root + stems[person]
    form = form.replace(u'aramos',u'áramos')
    form = form.replace(u'ieramos',u'iéramos')
    form = form.replace(u'eramos',u'éramos')    
    return form

def make_future (inf, person):
    endings = conjdic(u'é',u'ás',u'á',u'emos',u'éis',u'án')
    root = FUT_ROOT.get(inf,inf)
    return root + endings[person]

def make_conditional (inf, person):
    endings = conjdic(u'ía',u'ías',u'ía',u'íamos',u'íais',u'ían')
    root = FUT_ROOT.get(inf,inf)
    return root + endings[person]

def make_past_participle (inf):
    if irregular_participle.has_key(inf):
        return irregular_participle[inf]
    elif inf[-2:]==u'ar':
        return inf[:-1]+u'do'
    else:
        return inf[:-2]+u'ido'

def make_antepresente (inf, person):
    return make_present(u'haber',person) + u' ' + make_past_participle(inf)

def make_antepasado (inf, person):
    return make_imperfect(u'haber',person) + u' ' + make_past_participle(inf)

def make_antepasado_subjuntivo (inf, person):
    return make_past_subjunctive(u'haber',person) + u' ' + make_past_participle(inf)

def make_antepresente_subjuntivo (inf, person):
    return make_present_subjunctive(u'haber',person) + u' ' + make_past_participle(inf)

def make_verb_quiz (infinitives, spanish_func, english_func):
    quiz = []
    for span,eng in infinitives:
        for person in FPS,SPS,TPS,FPP,SPP,TPP:
            quiz.append((spanish_func(span,person),english_func(eng,person)))
    return quiz

#print make_verb_quiz([(u'hablar',u'talk'),(u'ser',u'be'),(u'comer',u'eat'),(u'saber',u'know')],
#                     make_imperfect,make_eng_past_progr)
#print make_verb_quiz([(u'hablar',u'talk'),(u'ser',u'be'),(u'comer',u'eat'),(u'saber',u'know')],
#                     make_preterit,make_eng_pret)
        
