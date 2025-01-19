import adsk.core
import os, os.path
import json
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface
dropDownCommandInput = adsk.core.DropDownCommandInput.cast(None)
boolvalueInput = adsk.core.BoolValueCommandInput.cast(None)
stringDocname = adsk.core.StringValueCommandInput.cast(None)
my_hub = app.data.activeHub

# create doc name values
docSeed = ""
docTitle = ""
docSeed = ""
my_DocsDictSorted = ()

# command identity information.
CMD_ID = f"{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog"
CMD_NAME = "Create Related Data"
CMD_Description = (
    "Create a new related document of the active document using a template"
)

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# Define the location where the command button will be created.
WORKSPACE_ID = "FusionSolidEnvironment"
PANEL_ID = "SolidCreatePanel"

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "")

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Load project and folder from json
def loadProject(__file__):
    global app, data, my_DocsDictSorted

    my_addin_path = os.path.dirname(os.path.realpath(__file__))
    my_projectfolder_json_path = os.path.join(my_addin_path, "data.json")
    my_docs_json_path = os.path.join(my_addin_path, "docs.json")

    # check if the documents json has been created
    docsExist = os.path.isfile(my_docs_json_path)
    futil.log(f"{CMD_NAME} Doc Json Exists: {docsExist}")

    if docsExist == False:

        with open(my_projectfolder_json_path) as json_file:
            data = json.load(json_file)

        app = adsk.core.Application.get()
        # ui = app.userInterface
        my_hub = app.data.activeHub
        my_project = my_hub.dataProjects.itemById(data["PROJECT_ID"])
        if my_project is None:
            ui.messageBox(
                f"Project with id:{data['PROJECT_ID']} not found, review the readme file for instructions on how to set up the add-in."
            )
            return data
        my_folder = my_project.rootFolder.dataFolders.itemById(data["FOLDER_ID"])
        if my_folder is None:
            ui.messageBox(
                f"Folder with id:{data['FOLDER_ID']} not found, review the readme file for instructions on how to set up the add-in."
            )
            return data

        my_DocsDictUnsorted = {}
        for data_file in my_folder.dataFiles:
            if data_file.fileExtension == "f3d":
                name_Dict = data_file.name + "dict"
                my_DocsDictUnsorted.update(
                    {
                        name_Dict: {
                            "name": data_file.name,
                            "urn": data_file.id,
                        }
                    }
                )

        my_DocsDictSorted = dict(sorted(my_DocsDictUnsorted.items()))
        futil.log(f"{CMD_NAME} Doc Data Created: {my_DocsDictSorted}")
        ...

        my_DocsJson = json.dumps(my_DocsDictSorted)
        with open(my_docs_json_path, "w") as f:
            f.write(my_DocsJson)
            futil.log(f"{CMD_NAME} Doc Json Saved")
    else:

        with open(my_docs_json_path) as json_file:
            my_DocsDictSorted = json.load(json_file)
            futil.log(f"{CMD_NAME} Doc Data Loaded: {my_DocsDictSorted}")

        return


data = loadProject(__file__)


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
    )

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)
    

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI at the end of the menu.
    control = panel.controls.addCommand(cmd_def)

    # Specify if the command is promoted to the main toolbar.
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Created Event")
    futil.log(f"Hub Configured: {config.COMPANY_HUB}")

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs
    global app, docSeed, docURN

    #hub check
    hub = app.data.activeHub
    if hub.id != config.COMPANY_HUB:
        futil.log(f'active hub is {hub.id}.\n{config.COMPANY_HUB} was expected')
        ui.messageBox(
            "The active hub is not configured for this command.\nPlease switch to the correct hub and try again.",
            "Incorrect Hub",
            0,
            3,
        )
        return

    returnValue = 1
    if app.activeDocument.isSaved == False:
        returnValue = ui.messageBox(
            "Related Documents can only be created from saved Documents.\nPlease save this document and try again",
            "Document Not Saved",
            0,
            3,
        )

    if returnValue == 0:
        return

    # Define the dialog for command
    dropDownCommandInput = inputs.addDropDownCommandInput(
        "dropDownCommandInput",
        "Type",
        adsk.core.DropDownStyles.LabeledIconDropDownStyle,
    )

    dropDownItems_ = dropDownCommandInput.listItems
    for key, val in my_DocsDictSorted.items():
        if isinstance(val, dict):
            dropDownItems_.add(val.get("name"), True),
            docActive = app.activeDocument
            docWithVersion = docActive.name
            docSeed = docWithVersion.rsplit(" ", 1)[0]  # trim version
            docTitle = docSeed + " ‹+› " + (val.get("name"))
            docURN = val.get("urn")

    boolCommandInput = inputs.addBoolValueInput("boolvalueInput_", "Auto-Name", True)
    boolCommandInput.value = True

    stringDocName = inputs.addStringValueInput("stringValueInput_", "Name", docTitle)
    stringDocName.isEnabled = False

    # Connect to the events
    futil.add_handler(
        args.command.execute, command_execute, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.inputChanged, command_input_changed, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.destroy, command_destroy, local_handlers=local_handlers
    )


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Execute Event")

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    global docURN, docSeed, docTitle

    docActiveUrn = app.data.findFileById(docURN)

    docActive = app.activeDocument
    docWithVersion = docActive.name
    docSeed = docWithVersion.rsplit(" ", 1)[0]  # trim version
    docTitleinput: adsk.core.StringValueCommandInput = inputs.itemById(
        "stringValueInput_"
    )
    docTitle = docTitleinput.value
    docNew = app.documents.open(docActiveUrn)
    docNew.saveAs(
        docTitle,
        docActive.dataFile.parentFolder,
        "Auto created by related data add-in",
        "",
    )
    transform = adsk.core.Matrix3D.create()
    seedDoc = adsk.fusion.Design.cast(
        docNew.products.itemByProductType("DesignProductType")
    )
    seedDoc.rootComponent.occurrences.addByInsert(docActive.dataFile, transform, True)

    docNew.save(
        "Auto saved by related data add-in"
    )  # Save new doc and add boiler plate comment


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    global docURN, docTitle, docSeed
    stringDocname = args.inputs.itemById("stringValueInput_")

    # handle the combobox change event
    if changed_input.id == "dropDownCommandInput":
        searchDict = changed_input.selectedItem.name

        # find the right dictionary based on the combo box value
        listOfKeys = ""
        for i in my_DocsDictSorted.keys():
            for j in my_DocsDictSorted[i].values():
                if searchDict in j:
                    if i not in listOfKeys:
                        listOfKeys = i

        docURN = (my_DocsDictSorted).get(listOfKeys).get("urn")  # set the urn
        doctempname = (my_DocsDictSorted).get(listOfKeys).get("name")
        docTitle = docSeed + " ‹+› " + doctempname
        stringDocname.value = docTitle

    # Auto name or user name input
    if changed_input.id == "boolvalueInput_":
        if changed_input.value == True:
            stringDocname.isEnabled = False
        else:
            stringDocname.isEnabled = True

    # General logging for debug.
    futil.log(
        f"{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}"
    )


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Destroy Event")

    global local_handlers
    local_handlers = []
