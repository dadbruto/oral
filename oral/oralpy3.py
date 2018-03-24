import pyglet
from pyglet.window import key
#from copy import copy
from numpy.random import rand, choice, shuffle
import os
import codecs
from gtts import gTTS
import time
from tempfile import TemporaryFile



global update_interval,qit
global interrogator

update_interval = .1


#describe cycling parameters via global variables
# t_welcome = 2.0
# time_allowed_for_question = 3
# time_allowed_for_answer = 2
# # set initial state via global variables
# t = 0
# stage_duration = 0
# question_number = 0
# question = "Are you ready?'"
# paused = True
# stage = 'just_started'

def beep():
    print('\a')

def invert_dict(d):
    return dict(zip(d.values( ), d.keys( )))

# def quiterator(s):
    # # iterate over characters in a string
    # i = 0
    # n = len(s)
    # while i < n:
        # yield s[i]
        # i += 1

def get_options():
    from optparse import OptionParser       
    parser = OptionParser()
    parser.add_option("-f", "--phrasebookfile", dest="phrasebook_file_root",default='phrasebook',
                      help="base name of phrasebook file (must have extension '.pbk'), default='phrasebook'", metavar="FILE")
    parser.add_option("-s", "--section",
                      dest="selected_section", default=None,
                      help="sections to concentrate on, if any, default None")
    parts_of_speech_help_string = \
    '''parts_of_speech to concentrate on, if any, specified by a string of characters from `anvigcqp#`, default None. The characters signify:  
                            n: nouns, v: verbs, i: irregular constructions, 
                            g: greetings and phrases of general use, 
                            c: conjunctions, 
                            q: questions, 
                            #: numbers, 
                            p: pronouns and prepositions
    '''
    parser.add_option("-p", "--parts",
                      dest="selected_parts_of_speech", default=None,
                      help=parts_of_speech_help_string)
    parser.add_option("-v", "--verbosity",
                      dest="verbosity", default='0',
                      help='Level of print and error output to console')
    parser.add_option("-c", "--choice",
                      dest="choice_criterion",
                      help="select questions from o(riginal) list, s(huffled) list, u(nweighted random)or w(eighted random); both o and s options terminate after exhausting list, default 'o'",default='w',)
    parser.add_option("-q", "--quiet",
                      action = "store_true",
                      dest="quiet",
                      help="Turn off spoken testing, default False")
    parser.add_option("-d", "--direction",
                      dest="qdirection", default='r',
                      help="Direction of questions: f(orward),b(ackward), r(andom) default 'r'")
    parser.add_option("-t", "--timedelay",
                      dest="waittime", default=4.0,
                      help="Time delay before giving answer default 4 (seconds)")

    (options, args) = parser.parse_args()
    # post processing
    options.verbosity = int(options.verbosity)
    if not options.choice_criterion in 'osuw':
        beep()
        print("Unrecognized choice criterion '"+str(choice_criterion)+"'; see the help.")
        exit()
    options.choice_criterion = {'o':'original','s':'shuffle','u':'unweighted_random','w':'weighted_random'}[options.choice_criterion]
    options.waittime = float(options.waittime)
    if not options.qdirection in 'fbr':
        beep()
        print("Unrecognized questioning direction '"+str(qdirection)+"'; see the help.")
        exit()
    if options.selected_parts_of_speech is None: # make this a set
        options.selected_parts_of_speech = []
    else:
        options.selected_parts_of_speech = set(list(options.selected_parts_of_speech))

    return options


def say(phrase,lang):
    tts = gTTS(text=phrase, lang=lang)
    tmpfileroot = 'oral_tempfile'
    #tmpfile = tmpfileroot+str(time.time())+".mp3"
    tmpfile = tmpfileroot+".mp3"
    tts.save(tmpfile)
    #print("Playing",phrase)
    music = pyglet.resource.media(tmpfile, streaming=False)
    #music = pyglet.resource.media(tmpfile, streaming=True)
    music.play()
    while os.path.exists(tmpfile):
        try:
            os.remove(tmpfile) #remove temporary file
        except: pass
    #os.remove(tmpfile) #remove temporary file
    
    return music.duration


window = pyglet.window.Window(resizable=True,caption='Oral')

@window.event
def on_resize(width, height):
    global display
    #print('The window was resized to %dx%d' % (width, height))
    #window_width, window_height = width,height
    display.question_label.x, display.question_label.y = int(0.5*width),int(0.67*height)
    display.answer_label.x, display.answer_label.y = int(0.5*width),int(0.33*height)
    display.count_label.x, display.count_label.y = int(0.02*width),int(0.9*height)
    display.paused_label.x, display.paused_label.y = int(0.5*width),int(0.5*height)
    display.time_left_label.x, display.time_left_label.y = int(0.95*width),int(0.9*height)
    display.help_label.x, display.help_label.y = int(0.02*width),int(0.05*height)
    display.question_pool_description_label.x, display.question_pool_description_label.y = int(0.02*width),int(0.98*height)

@window.event
def on_key_press(symbol, modifiers):
    global interrogator
    if symbol == key.Q:
        #print('The "Q" key was pressed.')
        pyglet.app.exit()
    elif symbol == key.SPACE:
        #print('The "pause" key was pressed.')
        interrogator.paused = not interrogator.paused
        #print("interrogator.paused",interrogator.paused)
        if interrogator.paused:
            interrogator.display.paused_label.text = 'Paused'
        else:
            interrogator.display.paused_label.text = ''

@window.event
def update(dt):
    global interrogator
    #print("Entered pyglet update with stage",interrogator.stage,"and t = ",t)
    list_is_finished = interrogator.update(dt)
    #print("after interrogator.update, t = ",interrogator.t)
    if list_is_finished: pyglet.app.exit()

@window.event
def on_draw():
    global display
    window.clear()
    display.question_label.draw()
    display.answer_label.draw()
    display.count_label.draw()
    display.paused_label.draw()
    display.time_left_label.draw()
    display.help_label.draw()
    display.question_pool_description_label.draw()


class InterrogatorDisplay(object):
    def __init__(self):
        #self.x = 1
        self.question_number = 0
        self.time_left_label_text = ''
        self.paused = True
        self.question_label = pyglet.text.Label('Welcome to oral exam!',
                                  color = (200,250,0,255),
                                  font_name='Times New Roman',
                                  font_size=36,
                                  x=window.width//2, y=2*window.height//3,
                                  anchor_x='center', anchor_y='center')
        self.answer_label= pyglet.text.Label('',
                                  color = (0,200,0,255),
                                  font_name='Times New Roman',
                                  font_size=36,
                                  x=window.width//2, y=window.height//3,
                                  anchor_x='center', anchor_y='center')
        self.question_pool_description_label = pyglet.text.Label(' ',
                                  font_name='Times New Roman',
                                  font_size=16,
                                  x=int(0.05*window.width), y=int(0.85*window.height),
                                  anchor_x='left', anchor_y='top')
        self.count_label= pyglet.text.Label('Question #'+str(self.question_number),
                                  font_name='Times New Roman',
                                  font_size=16,
                                  x=(0.1*window.width), y=int(0.90*window.height),
                                  anchor_x='left', anchor_y='top')
        self.time_left_label= pyglet.text.Label('',
                                  font_name='Times New Roman',
                                  font_size=16,
                                  x=int(0.1*window.width), y=int(0.90*window.height),
                                  anchor_x='right', anchor_y='top')
        self.paused_label= pyglet.text.Label('Paused',
                                  font_name='Times New Roman',
                                  font_size=24,
                                  x=int(0.5*window.width), y=window.height//2,
                                  anchor_x='center', anchor_y='center')
        self.help_label= pyglet.text.Label("Spacebar to toggle pause, 'q' to quit:",
                                  font_name='Times New Roman',
                                  font_size=16,
                                  x=int(0.05*window.width), y=int(0.01*window.height),
                                  anchor_x='left', anchor_y='bottom')

class Interrogator(object):
                
    def __init__(self,display,phrasebook,selected_keys,usage,choice_criterion='original',direction='f',t_welcome=2,time_allowed_for_question=4,time_allowed_for_answer=3,quiet=False):
        #print("Init Interrogator with choice_criterion, direction",choice_criterion,direction)
        self.display = display
        self.phrasebook = phrasebook
        self.quiet = quiet
        self.stage = 'just_started'
        self.t = 0.0 # elapsed time in current stage
        self.answer = 'Are you ready?'
        self.question = 'Welcome!'
        self.answer_language = 'en'
        self.question_language = 'en'
        self.usage = usage
        self.paused = True
        self.display.paused = self.paused 
        #describe cycling parameters via global variables
        self.t_welcome = 2.0
        self.time_allowed_for_question = 3
        self.time_allowed_for_answer = 2
        self.stage_duration = 0
        self.question_number = 0
        self.display.question_number = self.question_number
        self.fade_time = 1.0
        self.calls = 0
        self.display_time_left = False
        self.qdirection = direction
        def QuestionKeyGenerator(entrykeys,uses,method='original'):
            #print("method=",method)
            #print("entrykeys=",entrykeys)
            n = len(entrykeys)
            sL = entrykeys # range(n)        
            if method in ('shuffle','original'):
                i = 0;
            if method == 'shuffle':
                shuffle(sL)
            if method == 'unweighted_random' and uses is not None:
                while True: 
                        yield choice(sL)
            elif method == 'weighted_random' or(method == 'unweighted_random' and uses is None):
                #print("Here",0)
                if uses is not None: # weight selection in favour of unused questions
                    #print("uses",uses)
                    #print("entrykeys",entrykeys)
                    selected_uses = {k:uses[k] for k in entrykeys}
                    #print("selected_uses",selected_uses)
                    max_uses = max(selected_uses.values())
                    probability_distribution = [max_uses+1 - v for v in selected_uses.values()]
                    s = sum(probability_distribution)
                    probability_distribution = [p/(1.0*s) for p in probability_distribution]
                    #k = choice(range(working_nphrases), 1, p=probability_distribution)[0]    
                    while True: 
                        #print("Here",1)
                        #print("sL",sL)
                        #print("probability_distribution",probability_distribution)
                        yield choice(sL, 1, p=probability_distribution)[0]    
            else:
                while i < n:
                    yield sL[i]
                    i = i + 1
        self.qkeygen = QuestionKeyGenerator(selected_keys,usage,method=choice_criterion)  # Instantiate the question iterator

    def define_question_from_key(self,key,qdirection):
        #print("key",key)
        if qdirection == 'r': 
            question_direction = choice(('f','b'))
        else:
            question_direction = qdirection
        if question_direction == 'f': 
            self.question_language = 'es'
            self.answer_language = 'en'
            self.question = key
            self.answer = phrasebook.es2en[key]
        elif question_direction == 'b': 
            self.question_language = 'en'
            self.answer_language = 'es'
            self.question = phrasebook.es2en[key]
            self.answer = key
        else:
            myfail('Unrecogized question direction'+str(qdirection))
        #return question, answer, question_language, answer_language

    def update(self,update_interval):
        #print("Interrogator entrance status: stage",self.stage,"t",self.t,"duration",self.stage_duration,"calls",self.calls)
        #print("Entered interrogator update with stage",self.stage,"and t = ",self.t)
        
        list_is_finished = False
        if not self.paused:
            self.t = self.t+update_interval
            #print("Updating t to",self.t)
            if self.display_time_left: self.display.time_left_label.text = 'Time left '+str(int(self.stage_duration - self.t))
        if self.stage == 'just_started':
            #print("Discovered expired stage",self.stage)
            self.stage = 'welcoming'
            self.stage_duration = self.t_welcome
            self.t = 0.0
        elif self.stage == 'welcoming' and self.t >= self.stage_duration:
            #print("Discovered expired stage",self.stage)
            # play and print question, and let the user look for t = time_allowed_for_question
            self.display_time_left = True
            self.question_number = self.question_number + 1
            self.display.question_number = self.question_number
            display.count_label.text = 'Question #'+str(self.question_number)
            try:
                self.key = str(self.qkeygen.__next__())
                self.define_question_from_key(self.key,self.qdirection)
            except StopIteration:
                list_is_finished = True
                self.question ='The question list is finished'
            #print("iter key=",self.question)
            display.answer_label.text = ''
            display.question_label.text = self.question
            self.stage = 'question_was_posted'
            self.stage_duration = self.time_allowed_for_question
            if not self.quiet and not list_is_finished: self.stage_duration = say(self.question,self.question_language) + self.stage_duration 
            self.t = 0.0
        elif self.stage == 'question_was_posted'  and self.t >= self.stage_duration and not list_is_finished:
            #print("Descovered expired stage",stage)
            # play and print answer, and let the user look for t = time_allowed_for_answer
            self.display_time_left = False
            display.time_left_label.text = 'Time left '+str(int(self.stage_duration - self.t))
            if not list_is_finished:
                display.answer_label.text = str(self.answer)
                self.stage = 'answer_was_posted'
                self.stage_duration = self.time_allowed_for_answer
                if not self.quiet: self.stage_duration = say(self.answer,self.answer_language) + self.stage_duration 
                self.t = 0.0
        elif self.stage == 'answer_was_posted' and self.t > self.stage_duration and not list_is_finished:
            #print("Descovered expired stage",stage)
            self.usage[self.key] = self.usage[self.key] + 1
            self.display_time_left = False
            if self.t >= self.stage_duration:
                self.stage = 'fading'
                self.stage_duration = self.fade_time
                self.t = 0.0
                display.time_left_label.text = ''
        elif self.stage == 'fading' and self.t >= self.stage_duration and not list_is_finished:
            #print("Descovered expired stage",stage)
            self.stage = 'welcoming'
            self.stage_duration = 0.0
            self.t = 0.0
        else:
            #print("No action in interrogator update")
            pass
        
        self.calls = self.calls+1
        
        return list_is_finished    

    

# Read in progressbook
def read_progressbook(phrasebook_file_root,es2uses):
    progress_file_name = phrasebook_file_root + '.prg'
    progress_file_bad_entries = 0
    if os.path.exists(progress_file_name):
        with codecs.open(progress_file_name, 'r',encoding='utf-8') as f:
            for line in f:
                if line[0] != '#':  # not a comment
                    try:
                        tokens = line.rstrip().split('/')
                        en = tokens[1].rstrip().lstrip()
                        es = tokens[0].rstrip().lstrip()
                    except:
                        progress_file_bad_entries = progress_file_bad_entries + 1
                        break
                    if not (es in phrasebook.es2en):
                        beep()
                        print("Progress file entry",es,"not in phrasebook.")
                        #exit()
                    if len(tokens)>2: 
                        es2uses[es] = int(tokens[2].rstrip().lstrip())
                    else:
                        es2uses[es] = 0
        f.close()
        return es2uses
    else:
        return None

#global section
def safe_exec(s):
    allowed_global_settable_variable_names = 'rumpelstiltskin,section' # a comma separated list
    exec('global '+allowed_global_settable_variable_names+";"+s,globals(),{})
    return

class Testbook(object):   
    def __init__(self,filename_root=None,verbosity=1,en2es={},es2en={},\
    es2uses={},es2section={},parts_of_speech={},index_of_es={}):
        number = list(set([len(en2es),len(es2en),len(es2uses),len(es2section),len(index_of_es)]))
        #print("Entering t with ",filename_root)
        if len(number)>1:
            beep()
            print("Testbook input dictionaries have different lengths:",number)
            exit()
        else:
            self.number = number[0]
        if self.number > 0 and filename_root is not None: myfail("Testbook instantiation cannot have both filename and dictionary values specified:")
        if filename_root is None:
            self.en2es = en2es
            self.es2en = es2en
            self.es2uses = es2uses
            self.es2section = es2section
            self.index_of_es = index_of_es
            self.parts_of_speech = parts_of_speech
        else:
            self.filename_root = filename_root
            phrasebook_file_name = filename_root + '.pbk'
            index = 0
            phrasebook_file_bad_entries = 0
            current_section = None
            parts_of_speech={}
            en2es = {}
            es2en = {}
            es2uses = {}
            index_of_es = {}
            es2section = {}
            line_number = 0
            if os.path.exists(phrasebook_file_name):
                with codecs.open(phrasebook_file_name, 'r',encoding='utf-8') as f:
                    for line in f:
                        line_number = line_number + 1
                        #print("line",line)
                        line = line.rstrip()
                        if len(line) > 0 and line[0] !='#': 
                            try:
                                tokens = line.split('/')
                                en = tokens[1].rstrip().lstrip()
                                es = tokens[0].rstrip().lstrip()
                            except:
                                if verbosity: print('Bad entry in phrasebook at line '+str(line_number)+': '+line+"'")              
                                phrasebook_file_bad_entries = phrasebook_file_bad_entries + 1
                                break
                            if en in en2es: myfail("Duplicate entry in phrasebook at line "+str(line_number)+":"+str(en))
                            if es in es2en: myfail("Duplicate entry in phrasebook at line "+str(line_number)+":"+str(es))
                            # This is a valid entry, in the right section.  Is it a selected part of speech?
                            if len(tokens) > 2:
                                this_part_of_speech = tokens[2].rstrip().lstrip()
                            else:
                                this_part_of_speech = None
                            #print("this_part_of_speech",this_part_of_speech)
                            # We need to track all entries in the phrasebook, because we have to write out a complete progress file at the end.
                            parts_of_speech[es] = this_part_of_speech
                            index_of_es[es] = index
                            index = index + 1
                            en2es[en] = es
                            es2en[es] = en
                            es2uses[es] = 0  # to be overwritten by progress entries
                            es2section[es] = current_section
                            #print("current_section",current_section)
                            # # Which entries do we keep in our working set?
                            # # If selected_parts_of_speech is None, 
                            # # automatically include this entry, but if we are selecting :
                            # # by parts of speech, check and discard if it is None
                            # is_selected_section = (selected_section is None) \
                            # or ((current_section is not None) and (current_section == selected_section))
                            # is_selected_part_of_speech = (selected_parts_of_speech is None) \
                            # or ((this_part_of_speech is not None and (set(this_part_of_speech) & selected_parts_of_speech_as_set)))
                            # if is_selected_section and is_selected_part_of_speech:
                                # working_set_eskeys.append(es) 
                        # May be a python instruction, e.g. to set the section ID
                        elif len(line) > 2 and line[0:2] == '#!':
                            try:
                                global section
                                safe_exec(line[2:])
                                current_section = section
                            except Exception as e:
                                if verbosity >0: 
                                    mywarn("Undecipherable directive at line",line_number,"'"+str(line[2:])+"'");
                                    print('Error is',e)
                            
                f.close()
                if verbosity > 0: print("Found",len(en2es),'entries in phrasebook',"'"+filename_root+"'") 
                self.en2es = en2es
                self.es2en = es2en
                self.es2uses = es2uses
                self.es2section = es2section
                self.index_of_es = index_of_es
                self.parts_of_speech = parts_of_speech
                self.number = len(es2en)
            else: myfail("No phrasebook file exists: aborting.")

    def __repr__(self):
        #print(self.en2es,self.es2en,self.es2uses,self.es2section,self.index_of_es,self.parts_of_speech)
        s = 'Index\t-key\t-values\t-section\t-parts_of_speech\t-uses\n'
        for k in self.es2en.keys():
            s = s+' '+str(self.index_of_es[k])+'\t-'+str(k)+'\t-'+str(self.es2en[k])+'\t-'+str(self.es2section[k])+'\t-'+str(self.parts_of_speech[k])+'\t-'+str(self.es2uses[k])+'\n'
        return s
    def selectkeys(self, sections, categories):
        #select the 'es' keys corresponding to specified sections and categories
        #print("categories",categories)
        if sections is not None and  type(sections) not in (list,tuple):  # may be a single item and not a list or set
            sections_set = [sections]
        else:
            sections_set = None
        categories_set = set(categories)
        #print("sections_set",sections_set)
        selected_keys = list(self.es2en.keys())
        if len(categories_set) > 0:
            selected_keys =  [k  for k in selected_keys \
            if self.parts_of_speech[k] is None or categories_set.intersection(self.parts_of_speech[k])]
        # print("selected_keys so far",selected_keys)
        # print("sections set",sections_set)
        # print("sections_set is not None set",sections_set is not None)
        if sections_set is not None and len(sections_set) > 0: 
            selected_keys =  [k for k in selected_keys \
            if self.es2section[k] in sections_set]
        return selected_keys
        
def write_progressbook(interrogator):   
    progress_file_name = interrogator.phrasebook.filename_root + '.prg'   
    with codecs.open(progress_file_name, 'w',encoding='utf-8') as f:
        es_of_index = invert_dict(interrogator.phrasebook.index_of_es)
        indices = list(es_of_index.keys())
        #print("indices",indices)
        indices.sort()

        for k in range(len(indices)):
            es = es_of_index[k]
            f.write(es+" / "+interrogator.phrasebook.es2en[es]+" / "+str(interrogator.usage[es])+" \n")
    f.close()

def mywarn(message):
    beep()
    print(message)  
def myfail(message): mywarn(message); exit()
            
#######################################################################
# Main program starts here


o = get_options()

#read phrasebook
phrasebook = Testbook(filename_root=o.phrasebook_file_root, verbosity=1)
if phrasebook is None:  myfail("Cannot find phrasebook file.")      

# Select question pool
selected_keys = phrasebook.selectkeys(o.selected_section,o.selected_parts_of_speech) # working subset of phrasebook
#print("wsk",selected_keys)
working_set_size = len(selected_keys)

# And create a description string for it.
question_pool_description = 'Question pool: '+':  '+str(working_set_size)+' items from '+o.phrasebook_file_root 
if o.selected_section is not None: 
    question_pool_description = question_pool_description + ' section '+str(o.selected_section)
if len(o.selected_parts_of_speech) > 0: 
    desc = ', '.join(o.selected_parts_of_speech)
    question_pool_description = question_pool_description + ' of type(s) '+str(desc)
if o.verbosity > 1:   print(question_pool_description)
if len(selected_keys) == 0: myfail("No phrasebook entries satisfy criteria!")

# Read the progressbook
es2uses = read_progressbook(o.phrasebook_file_root,phrasebook.es2uses)
if es2uses is None and o.verbosity > 0: mywarn("No progress file exists: initializing a new one.")

# Instantiations of required objects
display = InterrogatorDisplay() # Instantiate the window to use
display.question_pool_description_label.text = question_pool_description
interrogator = Interrogator(display,phrasebook,selected_keys,es2uses,quiet = o.quiet,choice_criterion=o.choice_criterion,direction=o.qdirection) # 

# Start the clock
pyglet.clock.schedule_interval(update, update_interval)


#window.push_handlers(pyglet.window.event.WindowEventLogger())

#Start the event loop
pyglet.app.run()

# Perform exit
write_progressbook(interrogator)
print('\nGoodbye!')
if not o.quiet: wait_time = say('Hasta la vista!','es')
time.sleep(wait_time)

