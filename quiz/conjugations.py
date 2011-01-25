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

ENG_SUBJ_PRO = conjdic('I','you','he/she/it','We','you guys','they')

eng_irregular_present = {
    'be': conjdic('am','are','is','are'),
    }

eng_irregular_past = {
    'be' : conjdic('was','were','was','were'),
    }
eng_irregular_past_simple = {
    'give':'gave','have':'had','write':'wrote','go':'went','feel':'felt',
    'eat':'ate','know':'knew','spit':'spit (past)','put':'put (past)',
    'come':'came','can':'could','see':'saw',
    }

# ENGLISH CONVENIENCE FUNCTS

def make_eng_form_from_stem (inf, ending):
    if inf[-1] in ['sz'] and ending=='s':
        return inf+'e'+ending
    if inf.endswith('e') and inf.lower()!='be':
        return inf[:-1]+ending
    else:
        # double consonants for short vowels...
        if inf[-1] in 'dgmnpt' and inf[-2] in 'aeiou' and not inf[-3] in 'aeiou':
            return inf + inf[-1] + ending
        else:
            return inf+ending

# ENGLISH CONJUGATIONS

def make_eng_present (inf, person):
    if eng_irregular_present.has_key(inf):
        return eng_irregular_present[inf][person]
    if person != TPS:
        return ENG_SUBJ_PRO[person] + ' ' + inf
    else:
        return ENG_SUBJ_PRO[person] + ' ' + inf + 's'

def make_eng_pret (inf, person):
    if eng_irregular_past.has_key(inf):
        return ENG_SUBJ_PRO[person] + ' ' + eng_irregular_past[inf][person]
    elif eng_irregular_past_simple.has_key(inf):
        return ENG_SUBJ_PRO[person] + ' ' + eng_irregular_past_simple[inf]
    else:
        return ENG_SUBJ_PRO[person] + ' ' +  make_eng_form_from_stem(inf,'ed')

def make_eng_past_progr (inf, person):
    return ENG_SUBJ_PRO[person] + ' ' + eng_irregular_past['be'][person] + ' ' + make_eng_form_from_stem(inf,'ing')

def make_eng_subj (inf, person):
    return make_eng_pret('be',person) + " to " + inf

def make_eng_cond (inf, person):
    return ENG_SUBJ_PRO[person] + ' would ' + inf

### SPANISH DATA ###

FUT_ROOT = {
    'poder':'podr',
    'tener':'tendr',
    'saber':'sabr',
    'venir':'vendr',
    'poner':'pondr',
    }

consonants = 'bcdfghjklmnñpqrstvxyz'

preterit_irregular = {
    'ser':conjdic('fui','fuiste','fue','fuimos','fuisteis','fueron'),
    'ver':conjdic('vi','viste','vio','vimos','visteis','vieron'),
    'dar':conjdic('di','diste','dio','dimos','disteis','dieron'),
    }
preterit_irregular['ir']=preterit_irregular['ser']

preterit_irregular_stems = {
    'tener':'tuv',
    'saber':'sup',
    'poner':'pus',
    'traer':'traj',
    'poder':'pud',
    'venir':'vin',
    'querer':'quis',
    }

present_irregular = {
    'ser':conjdic('soy','eres','es','somos','sois','son'),
    'ir':conjdic('voy','vas','va','vamos','vais','van'),
    'ver':conjdic('veo','ves','ve','vemos','veis','ven'),
    }

present_irregular_yo = {
    'dar':'doy',
    'poner':'pongo',
    'conocer':'conozco'
    }

stem_change = {
    'jugar':'juega',
    'sentir':'siente',
    'sentar':'sienta',
    }

### SPANISH CONVENIENCE FUNC
def make_form_from_stem (infinitive, ending):
    SOFT_VOWELS = 'éíei'
    ACCENTS = 'áéóíú'
    accented_ending = False
    for a in ACCENTS:
        if a in ending: accented_ending = True
    if not (len(ending) > 2 or accented_ending):
        # Check for stem-change
        if stem_change.has_key(infinitive):
            infinitive = stem_change[infinitive] + 'r'
    if infinitive.endswith('zar') and ending[0] in SOFT_VOWELS:
        return infinitive[:3]+'c'+ending
    elif infinitive.endswith('car') and ending[0] in SOFT_VOWELS:
        return infinitive[:3]+'qu'+ending
    elif infinitive.endswith('gar') and ending[0] in SOFT_VOWELS:
        return infinitive[:3]+'gu'+ending
    else:
        return infinitive[:-2]+ending

def make_verb (inf, person, ar_stems, er_stems=None, ir_stems=None):
    if not er_stems: er_stems = ar_stems
    if not ir_stems: ir_stems = er_stems
    if inf.endswith('ar'):
        return make_form_from_stem(inf,ar_stems[person])
    elif inf.endswith('er'):
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
                         conjdic('o','as','a','amos','áis','an'),
                         conjdic('o','es','e','emos','éis','en'),
                         conjdic('o','es','e','imos','ís','en')
                         )


def make_imperfect (inf, person):
    ir_conj = conjdic('iba','ibas','iba','íbamos','íbais','iban')
    ser_conj = conjdic('era','eras','era','éramos','érais','eran')
    if inf == 'ver': inf = 'veer'
    if inf == 'ir': return ir_conj[person]
    if inf == 'ser': return ser_conj[person]
    return make_verb(inf,person,
                     conjdic('aba','abas','aba','ábamos','abais','aban'),
                     conjdic('ía','ías','ía','íamos','íais','ían'),
                     )
                         
def make_preterit (inf, person):
    if preterit_irregular.has_key(inf):
        return preterit_irregular[inf][person]
    elif preterit_irregular_stems.has_key(inf):
        endings = {FPS:'e',SPS:'iste',TPS:'o',
                   FPP:'imos',SPP:'isteis',TPP:'ieron'}
        return (preterit_irregular_stems[inf] + endings[person]).replace('jie','je')
    elif inf.endswith('ir'):
        root = inf[:-2]
        syllables = filter(lambda x:x, re.split('[%s]+'%consonants,root))
        if syllables[-1] == 'e':
            root = root.replace('e','i')
        inf = root + 'ir'
    return make_verb(inf,person,
                     ar_stems = {FPS:'é',SPS:'aste',TPS:'ó',
                                 FPP:'amos',SPP:'asteis',TPP:'aron'},
                     er_stems = {FPS:'í',SPS:'iste',TPS:'ió',
                                 FPP:'imos',SPP:'isteis',TPP:'ieron'})

def make_present_subjunctive (inf, person):
    if inf == 'ser': inf = 'seer'
    elif inf == 'ver': inf = 'veer'
    elif inf == 'ir': inf = 'vayer'
    elif present_irregular_yo.has_key(inf):
        stems = conjdic('a','as','a','amos','áis','an')
        return make_present(inf,FPS)[:-1] + stems[person]
    else:
        return make_verb(inf,person,
                         ar_stems=conjdic('e','es','e','emos','éis','en'),
                         er_stems=conjdic('a','as','a','amos','áis','an')
                         )

def make_past_subjunctive (inf, person):
    root = make_preterit(inf,TPP)[:-2]
    stems = conjdic('a','as','a','amos','an')
    form = root + stems[person]
    form = form.replace('aramos','áramos')
    form = form.replace('ieramos','iéramos')
    return form

def make_conditional (inf, person):
    pass

def make_verb_quiz (infinitives, spanish_func, english_func):
    quiz = []
    for span,eng in infinitives:
        for person in FPS,SPS,TPS,FPP,SPP,TPP:
            quiz.append((spanish_func(span,person),english_func(eng,person)))
    return quiz

#print make_verb_quiz([('hablar','talk'),('ser','be'),('comer','eat'),('saber','know')],
#                     make_imperfect,make_eng_past_progr)
#print make_verb_quiz([('hablar','talk'),('ser','be'),('comer','eat'),('saber','know')],
#                     make_preterit,make_eng_pret)
        
