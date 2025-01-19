import adsk.core, adsk.fusion
import os, traceback
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = "PT-exportmermaid"
CMD_NAME = "Export Mermaid Diagram..."
CMD_Description = "Export Active Document as Mermaid mmd diagram"
IS_PROMOTED = False

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description
    )

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
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


def command_execute(args: adsk.core.CommandCreatedEventArgs):
    # this handles the relationship export
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox("A Design Must be Active.", "Mermaid Export")
            return

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Create the title for the output.
        parentOcc = design.parentDocument.name
        resultString = "%%{\ninit: {\n'theme':'base',\n'themeVariables': {\n'primaryColor': '#f0f0f0',\n'primaryBorderColor': '#454F61',\n'lineColor': '#59cff0',\n'tertiaryColor': '#e1ecf5',\n'fontSize': '14px'\n}\n}\n}%%\n"
        resultString += "graph LR\n"
        # resultString += sParentOcc + '\n'

        # Call the recursive function to traverse the assembly and build the output string.
        resultString = traverseAssembly(
            parentOcc, rootComp.occurrences.asList, 1, resultString
        )

        msg = ""
        # Set styles of file dialog.
        folderDlg = ui.createFolderDialog()
        folderDlg.title = "Choose Folder to save Mermaid Graph"

        # Show file save dialog
        dlgResult = folderDlg.showDialog()
        if dlgResult == adsk.core.DialogResults.DialogOK:
            filepath = os.path.join(folderDlg.folder, parentOcc + ".mmd")
            # Write the results to the file
            with open(filepath, "w") as f:
                f.write(resultString)
            ui.messageBox("Graph saved at: " + filepath, parentOcc, 0, 2)
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


def traverseAssembly(sParent, occurrences, currentLevel, inputString):
    for i in range(0, occurrences.count):
        occ = occurrences.item(i)

        sItem = occ.name
        sItem = sItem.replace("-", "_")
        sItem = sItem.replace('"', "")
        sItem = sItem.replace("=", "")
        sItem = sItem.replace("(", "")
        sItem = sItem.replace(")", "")
        sItem = sItem.replace("<", "_")
        sItem = sItem.replace(">", "_")

        sParent = sParent.replace("-", "_")
        sParent = sParent.replace("-", "_")
        sParent = sParent.replace('"', "")
        sParent = sParent.replace("=", "")
        sParent = sParent.replace("(", "")
        sParent = sParent.replace(")", "")
        sParent = sParent.replace("<", "_")
        sParent = sParent.replace(">", "_")

        sRelationship = sParent + " --> " + sItem + "\n"
        sRelationship = sRelationship.replace(" ", "")

        inputString += sRelationship

        if occ.childOccurrences:
            inputString = traverseAssembly(
                occ.name, occ.childOccurrences, currentLevel + 1, inputString
            )
    return inputString
