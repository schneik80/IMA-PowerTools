import adsk.core, adsk.fusion
import os, time, traceback
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface
folderSet = 1

CMD_NAME = "Add Default Project Folders"
CMD_ID = "PT-defaultfolders"
CMD_Description = "Create default project folders if they do not exist"


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

    # Add a new button to the end of the file menu.
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
    futil.log(f"{CMD_NAME} Command Created Event")

    # Connect to the events that are needed by this command.
    futil.add_handler(
        args.command.execute, command_execute, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.destroy, command_destroy, local_handlers=local_handlers
    )


def command_execute(args: adsk.core.CommandCreatedEventArgs):
    # this handles the document close and reopen
    ui = None

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        project = app.data.activeProject
        root = project.rootFolder
        folders = root.dataFolders

        folder_names = [folder.name.casefold() for folder in folders]

        if folderSet == 1:

            # Check if 'Documents' folder already exists
            if "documents" not in folder_names:
                folders.add("Documents")

            # Check if 'Archive' folder already exists
            if "archive" not in folder_names:
                folders.add("Archive")

            # Check if 'Obit' folder already exists
            if "obit" not in folder_names:
                folders.add("Obit")

        elif folderSet == 2:
            # Check if '00 - products' folder already exists
            if "00 - products" not in folder_names:
                folders.add("00 - Products")

            # Check if '01 - Sub Assemblies' folder already exists
            if "01 - sub assemblies" not in folder_names:
                folders.add("01 - Sub Assemblies")

            # Check if '02 - ECAD' folder already exists
            if "02 - ecad" not in folder_names:
                folders.add("02 - ECAD")

            # Check if '03 - Parts' folder already exists
            if "03 - parts" not in folder_names:
                folders.add("03 - Parts")

            # Check if '04 - Purchased Parts' folder already exists
            if "04 - parts purchased" not in folder_names:
                folders.add("04 - Purchased Parts")

            # Check if '05 - 3DPCB Parts' folder already exists
            if "05 - 3dpcb parts" not in folder_names:
                folders.add("05 - 3DPCB Parts")

            # Check if '06 - Drawings' folder already exists
            if "06 - drawings" not in folder_names:
                folders.add("06 - Drawings")

            # Check if '07 - Documents' folder already exists
            if "07 - documents" not in folder_names:
                folders.add("07 - Documents")

            # Check if '08 - Render' folder already exists
            if "08 - render" not in folder_names:
                folders.add("08 - Render")

            # Check if '09 - Manufacture' folder already exists
            if "09 - manufacture" not in folder_names:
                folders.add("09 - Manufacture")

            # Check if '10 - Archive' folder already exists
            if "10 - archive" not in folder_names:
                folders.add("10 - Archive")

            # Check if 'XX - Obit' folder already exists
            if "XX - obit" not in folder_names:
                folders.add("XX - Obit")

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


# This function will be called when the user completes the command.
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f"{CMD_NAME} Command Destroy Event")
