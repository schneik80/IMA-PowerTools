import adsk.core, adsk.fusion
import os, traceback
from ...lib import fusion360utils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

# TODO *** Specify the command identity information. ***
CMD_ID = "cmd_shareDocument"
CMD_NAME = "Get a Share Link"
CMD_Description = "Share active Document and copy the link to the clipboard."

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
    control = dropDown.controls.addCommand(cmd_def, "", False)
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

    # TODO Connect to the events that are needed by this command.
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

    # TODO ******************************** Your code here ********************************

    shareCmdDef = ui.commandDefinitions.itemById("SimpleSharingPublicLinkCommand")
    isShareAllowed = shareCmdDef.controlDefinition.isEnabled

    if app.activeDocument.isSaved == False:
        ui.messageBox(
            "Can not share an unsaved document\nPlease Save the Document.",
            "Share Document",
            0,
            2,
        )
        return

    if isShareAllowed is False:
        ui.messageBox(
            "Sharing is not allowed.\nPlease check if your Team Hub Administrator has disabled sharing",
            "Share Document",
            0,
            2,
        )
        return

    try:
        shareState = app.activeDocument.dataFile.sharedLink
        progressBar = ui.progressBar

        # Check if the document is shared
        if shareState.isShared == False:
            # creating a link can take a few seconds so show a busy bar
            progressBar.showBusy("Generating Share Link"),

            shareState.isShared = True  # Share the document

            progressBar.hide()

        # Get the shared link
        shareLink = shareState.linkURL

        if shareLink == "":
            app.log(f"Failed to get a link to the document")
            ui.messageBox(
                f"Failed to share the document.",
                "Share Document",
                1,
                2,
            )
            exit(0)

        # Copy the shared link to the clipboard
        clipboardText(shareLink)

        resultString = f"<b>Document is shared.</b> <br> Share link: <a href=''{shareLink}''>{shareLink}</a> was added to clipboard."
        # Display a link to the user
        ui.messageBox(
            resultString,
            "Share Document",
            0,
            2,
        )

    except:
        # Write the error message to the TEXT COMMANDS window.
        app.log(f"Failed:\n{traceback.format_exc()}")


def clipboardText(linkText):

    if os.name == "nt":
        os.system(f"echo {linkText.strip()} | clip")
    else:
        os.system(f'echo "{linkText.strip()}" | pbcopy')
    app.log(f"link: {linkText} was added to clipboard")


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Destroy Event")

    global local_handlers
    local_handlers = []
