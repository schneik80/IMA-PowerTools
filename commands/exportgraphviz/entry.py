import adsk.core, adsk.fusion
import os, traceback, subprocess
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_NAME = "Export Graphiz Diagram..."
CMD_ID = "PT-Exportgraphviz"
CMD_Description = "Export Active Document as Graphviz dot diagram"

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # ******************************** Create Command Definition ********************************
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description
    )

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # **************** Add a button into the UI so the user can run the command. ****************
    # Get the target workspace the button will be created in.

    qat = ui.toolbars.itemById("QAT")

    # Get the drop-down that contains the file related commands.
    fileDropDown = qat.controls.itemById("FileSubMenuCommand")

    # Add a new button after the Export control.
    control = fileDropDown.controls.addCommand(cmd_def, "ExportCommand", True)


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    qat = ui.toolbars.itemById("QAT")
    fileDropDown = qat.controls.itemById("FileSubMenuCommand")
    command_control = fileDropDown.controls.itemById(CMD_ID)
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
    # Connect to the events that are needed by this command.
    futil.add_handler(
        args.command.execute, command_execute, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.destroy, command_destroy, local_handlers=local_handlers
    )
    futil.log(f"{CMD_NAME} Command Creation Event")


def command_execute(args: adsk.core.CommandCreatedEventArgs):
    # this handles the export
    futil.log(f"{CMD_NAME} Command Execute Event")
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox(
                "Active document is not a Fusion design document",
                "Incorrect Document Type",
            )
            return

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Create the title for the output.
        parentOcc = design.parentDocument.name
        parentOccTrimmed = parentOcc.rsplit(" ", 1)[0]  # trim version

        resultString = (
            'digraph "' + parentOcc + '" {' + '\n'
        )  # Change layout engine here
        resultString += 'layout="twopi";' + '\n'  # default is "dot"
        resultString += (
            'node[width=.75; height=.5; fontsize=8; fontname=helvetica; shape=box; style=rounded;];' + '\n'
        )
        # resultString += "nodesep=.2" + "\n"
        resultString += 'ranksep = 2;' + '\n'
        resultString += (
            'concentrate=true;' + '\n'
        )  # true will show only one edge, falls shows edge for each reference
        # resultString += 'mode="ipsep;"' + '\n' # neato only
        # resultString += 'diredgeconstraints=true;' + '\n' # neato only
        resultString += 'overlap="false;"' + '\n'
        resultString += 'splines=curved;' + '\n'
        resultString += (
            '"' + parentOccTrimmed + '" [style = filled; fillcolor = lightskyblue;];'
        )

        # Call the recursive function to traverse the assembly and build the output string.
        resultString = traverseAssembly(
            parentOcc, rootComp.occurrences.asList, 1, resultString
        )

        resultString += "}"

        # Set styles of file dialog.
        folderDlg = ui.createFolderDialog()
        folderDlg.title = "Choose Folder to save Graphviz Graph"

        # Show file save dialog
        dlgResult = folderDlg.showDialog()
        if dlgResult == adsk.core.DialogResults.DialogOK:
            filepath = os.path.join(folderDlg.folder, parentOcc + ".dot")
            # Write the results to the file
            with open(filepath, "w") as f:
                f.write(resultString)
            ui.messageBox("Graph dot file saved at: " + filepath)
            writestring = "open -a /Applications/Graphviz.app" + ' "' + filepath + '"'
            futil.log(writestring)
            os.system(writestring)

        else:
            return

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


# This function will be called when the user completes the command.
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f"{CMD_NAME} Command Destroy Event")


def traverseAssembly(parent, occurrences, currentLevel, inputString):
    for i in range(0, occurrences.count):
        occ = occurrences.item(i)

        foo1 = occ.name
        foo2 = foo1.rsplit(" ", 1)[0]  # trim version

        parent1 = parent.rsplit(" ", 1)[0]  # trim version

        foo = '"' + parent1 + '"->"' + foo2 + '"' + " ;" + "\n"

        inputString += foo

        if occ.childOccurrences:
            inputString = traverseAssembly(
                occ.name, occ.childOccurrences, currentLevel + 1, inputString
            )
    return inputString
