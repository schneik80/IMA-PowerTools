import adsk.core, adsk.fusion
import os, traceback
from urllib.parse import quote
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

# Specify the command identity information.
CMD_ID = "cmd_shareOpenDesktop"
CMD_NAME = "Get Open on Desktop Link"
CMD_Description = "Get a link on the clipboard for the active document that can be shared with your team to directly open the document for edit in their Fusion desktop client."

# Specify that the command will be promoted to the panel.
IS_PROMOTED = False

# Global variables by referencing values from /config.py
WORKSPACE_ID = config.design_workspace
TAB_ID = config.tools_tab_id
TAB_NAME = config.my_tab_name

PANEL_ID = config.my_panel_id
PANEL_NAME = config.my_panel_name
PANEL_AFTER = config.my_panel_after

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "")

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # ******************************** Create Command Definition ********************************
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
    )

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # **************** Add a button into the UI so the user can run the command. ****************
    # Get the target workspace the button will be created in.

    qat = ui.toolbars.itemById("QATRight")

    if qat.controls.itemById("shareDropMenu") is None:
        dropDown = qat.controls.addDropDown(
            "Share Menu", ICON_FOLDER, "shareDropMenu", "FeaturePacksCommand", True
        )
    else:
        dropDown = qat.controls.itemById("shareDropMenu")

    # Add a button to toggle the visibility to the end of the panel.
    control = dropDown.controls.addCommand(cmd_def, "cmd_shareSettings", True)
    # control.isPromoted = True


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    qat = ui.toolbars.itemById("QATRight")
    command_control = qat.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    dropDown = qat.controls.itemById("shareMenu")

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    if dropDown:
        dropDown.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Created Event")

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # Connect to the events that are needed by this command.
    futil.add_handler(
        args.command.execute, command_execute, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.destroy, command_destroy, local_handlers=local_handlers
    )


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Execute Event")

    if not app.activeDocument.isSaved:
        ui.messageBox(
            "Can not get <b>Open on Desktop</b> link for an unsaved document\nPlease Save the Document.",
            "Get Open on Desktop Link",
            0,
            2,
        )
        return

    try:
        # show a progress bar
        progressBar = ui.progressBar
        progressBar.showBusy("Generating Share Link"),

        # Generate the share link
        shareLink = f"fusion360://lineageUrn="
        shareLink += quote(app.activeDocument.dataFile.id)

        shareLink += "&hubUrl="
        galilleoUrl = app.activeDocument.dataFile.parentProject.parentHub.fusionWebURL
        stripGalilleo = galilleoUrl.replace(" ", "").rstrip(galilleoUrl[-3:]).upper()
        shareLink += quote(stripGalilleo)

        shareLink += "&documentName="
        shareLink += quote(app.activeDocument.name)

        # output the URL to the text commands
        futil.log(
            f"{CMD_NAME} Open on Desktop Document Link: {shareLink} was added to the clipboard."
        )

        # Copy the shared link to the clipboard
        futil.clipText(shareLink)

        resultString = f"An <b>Open on Desktop</b> link for {app.activeDocument.name} was added to the clipboard."

        if app.activeProduct.productType == "DesignProductType":
            rootComp = app.activeProduct.rootComponent

            if has_external_child_reference(rootComp):
                futil.log(f"{CMD_NAME} Document has external references")
                resultString += f"<br><br>Note:<br>This design has external references. Sharing this design will may share the referenced designs depending on the team member's permissions."
            else:
                futil.log(f"{CMD_NAME} Document has no external references")

        # Hide the progress bar
        progressBar.hide()

        # Display the message to the user
        ui.messageBox(
            resultString,
            "Share Document",
            0,
            2,
        )

    except:
        # Write the error message to the TEXT COMMANDS window.
        app.log(f"Failed:\n{traceback.format_exc()}")


def has_external_child_reference(component: adsk.fusion.Component) -> bool:
    for occurrence in component.occurrences:
        if occurrence.isReferencedComponent:
            return True
        # Recursively check child components
        if has_external_child_reference(occurrence.component):
            return True
    return False


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Destroy Event")

    global local_handlers
    local_handlers = []
