# Here you define the commands that will be added to your add-in.

# If you want to add an additional command, duplicate one of the existing directories and import it here.
# You need to use aliases (import "entry" as "my_module") assuming you have the default module named "entry".
from .assemblystats import entry as assemblystats
from .autosave import entry as autosave
from .datatoggle import entry as datatoggle
from .defaultfolders import entry as defaultfolders
from .dochistory import entry as dochistory
from .docinfo import entry as docinfo
from .exportbomcsv import entry as exportbomcsv
from .exportgraphviz import entry as exportgraphviz
from .exportmermaid import entry as exportmermaid
from .getandupdate import entry as getandupdate
from .insertSTEP import entry as insertSTEP
from .new import entry as new
from .refmanager import entry as refmanager
from .refrences import entry as refrences
from .refresh import entry as refresh
from .relateddata import entry as relateddata
from .shareDocument import entry as shareDocument
from .shareSettings import entry as shareSettings
from .shareOpenOnWeb import entry as shareOpenOnWeb
from .sketchfix import entry as sketchfix
from .sketchunderconstrained import entry as sketchunderconstrained
from .tabToolbar import entry as tabToolbar
from .timelinecompute import entry as timelinecompute

# Fusion will automatically call the start() and stop() functions.
commands = [
    assemblystats,
    autosave,
    datatoggle,
    defaultfolders,
    dochistory,
    docinfo,
    exportbomcsv,
    exportgraphviz,
    exportmermaid,
    getandupdate,
    refresh,
    insertSTEP,
    new,
    refmanager,
    refrences,
    relateddata,
    shareDocument,
    shareSettings,
    shareOpenOnWeb
    sketchfix,
    sketchunderconstrained,
    tabToolbar,
    timelinecompute,
]


# Assumes you defined a "start" function in each of your modules.
# The start function will be run when the add-in is started.
def start():
    for command in commands:
        command.start()


# Assumes you defined a "stop" function in each of your modules.
# The stop function will be run when the add-in is stopped.
def stop():
    for command in commands:
        command.stop()
