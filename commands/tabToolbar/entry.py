import adsk.core, adsk.fusion
import os, traceback, pathlib, zipfile, sys, json
import urllib.request
from sys import platform
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = "PT-TabToolbar"
CMD_NAME = "Install Assembly Tab"
CMD_Description = "Add a new Assembly Tab to the Fusion Design toolbar. Reorders and modifies default toolbar for more efficient design workflows"


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

    # Add a new button before the end of the file menu.
    control = fileDropDown.controls.addCommand(cmd_def)


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
    futil.log(f"{CMD_NAME} Command start event")

    app = adsk.core.Application.get()
    ui = app.userInterface

    ui.messageBox(
        "Ready to install a new Design document Toolbar with a new Assembly Tab? ",
        "Install Assembly Tab",
        3,
        1,
    )

    try:

        if platform == "win32":
            futil.log(f"{CMD_NAME} Windows platform detected")
            winassytb()
            return

        elif platform == "darwin":
            futil.log(f"{CMD_NAME} Mac platform detected")
            macassytb()
            return

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def close():
    ui.messageBox(
        "New Design toolbar with Assembly Tab is installed. Please save and close or close all open documents then restart Fusion",
        "Install Assembly Tab",
        0,
        2,
    )
    futil.log(f"{CMD_NAME} Command close event")


def macassytb():
    try:
        PATHS_DICT = json.loads(app.executeTextCommand("paths.get"))
        code_path = pathlib.Path(PATHS_DICT.get("appDirectory"))
        print(f"MACOS {code_path}")

        tb_path = os.path.join(
            code_path,
            "Fusion",
            "Fusion",
            "UI",
            "FusionUI",
            "Resources",
            "Toolbar",
            "TabToolbars.xml",
        )

        tb_zip = os.path.join(
            code_path,
            "Fusion",
            "Fusion",
            "UI",
            "FusionUI",
            "Resources",
            "Toolbar",
            "TabToolbars.zip",
        )

        if os.path.exists(tb_path):
            zipfile.ZipFile(tb_zip, mode="w").write(tb_path)
            futil.log(f"{CMD_NAME} Zip file created")
        else:
            futil.log(f"{CMD_NAME} File not found. No Zip file created")
            return

        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/schneik80/Fusion-Assembly-Tab/main/TabToolbars.xml",
            tb_path,
        )
        futil.log(f"{CMD_NAME} New toolbar.xml downloaded")

        close()

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def winassytb():
    try:
        PATHS_DICT = json.loads(app.executeTextCommand("paths.get"))
        code_path = pathlib.Path(PATHS_DICT.get("appDirectory"))
        tb_path = os.path.join(
            code_path.parent,
            "Fusion",
            "UI",
            "FusionUI",
            "Resources",
            "Toolbar",
            "TabToolbars.xml",
        )

        tb_zip = os.path.join(
            code_path.parent,
            "Fusion",
            "UI",
            "FusionUI",
            "Resources",
            "Toolbar",
            "TabToolbars.zip",
        )

        if os.path.exists(tb_path):
            zipfile.ZipFile(tb_zip, mode="w").write(tb_path)
            futil.log(f"{CMD_NAME} Zip file created")
        else:
            futil.log(f"{CMD_NAME} File not found. No Zip file created")
            return

        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/schneik80/Fusion-Assembly-Tab/main/TabToolbars.xml",
            tb_path,
        )
        futil.log(f"{CMD_NAME} New toolbar.xml downloaded")

        close()
        # call to open the path in os file manager
        # os.startfile(tb_path)

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Destroy Event")

    global local_handlers
    local_handlers = []
