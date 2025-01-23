import adsk.core, adsk.fusion
import html, os, traceback
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_NAME = "Document References"
CMD_ID = "PT-docrefs"
CMD_Description = "List Active Document References"
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

    # ******************************** Create Command Control ********************************
    # Get target workspace for the command.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get target toolbar tab for the command and create the tab if necessary.
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    if toolbar_tab is None:
        toolbar_tab = workspace.toolbarTabs.add(TAB_ID, TAB_NAME)

    # Get target panel for the command and and create the panel if necessary.
    panel = toolbar_tab.toolbarPanels.itemById(PANEL_ID)
    if panel is None:
        panel = toolbar_tab.toolbarPanels.add(PANEL_ID, PANEL_NAME, PANEL_AFTER, False)

    # Create the command control, i.e. a button in the UI.
    control = panel.controls.addCommand(cmd_def)

    # Now you can set various options on the control such as promoting it to always be shown.
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

    # Delete the panel if it is empty
    if panel.controls.count == 0:
        panel.deleteMe()

    # Delete the tab if it is empty
    if toolbar_tab.toolbarPanels.count == 0:
        toolbar_tab.deleteMe()


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
        design = app.activeProduct

        if not design:
            ui.messageBox("No active Fusion design")
            return

        activeDoc = app.activeDocument
        parentDataFiles = activeDoc.designDataFile.parentReferences
        childDataFiles = activeDoc.designDataFile.childReferences
        docParents = []
        docChildren = []
        docDrawings = []
        docRelated = []
        subString = " ‹+› "

        # Process parent and related data files
        if parentDataFiles:
            for file in parentDataFiles:

                if subString in file.name:
                    target_list = docRelated

                elif file.fileExtension == "f2d":
                    target_list = docDrawings

                else:
                    target_list = docParents

        # Process child data files
        if childDataFiles:
            docChildren = [
                {"name": file.name, "id": file.id} for file in childDataFiles
            ]

        # Links String to report references
        links = f"<h1>Source document: {html.escape(activeDoc.name)}</h1>"
        links += f"<h3>Parents ({len(docParents)}):</h3>"

        if docParents:
            for item in docParents:
                links += f'{(item["name"])}<br>'
        else:
            links += f"No Parent Relationships"

        links += f"<h3>Children ({len(docChildren)}):</h3>"

        if docChildren:
            for item in docChildren:
                links += f'{(item["name"])}<br>'
        else:
            links += f"No Child Relationships<br>"

        links += f"<h3>Drawings ({len(docDrawings)}):</h3>"

        if docDrawings:
            for item in docDrawings:
                links += f'{(item["name"])}<br>'
        else:
            links += f"No Drawings<br>"

        links += f"<h3>Related Data ({len(docRelated)}):</h3>"

        if docRelated:
            for item in docRelated:
                links += f'{(item["name"])}<br>'
        else:
            links += f"No Related Data Relationships"

        relationshipCount = (
            len(docParents) + len(docChildren) + len(docDrawings) + len(docRelated)
        )
        relationsTitle = f"References ({relationshipCount})"

        ui.messageBox(links, relationsTitle)

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


# This function will be called when the user completes the command.
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f"{CMD_NAME} Command Destroy Event")
