import adsk.core, adsk.fusion
import os, traceback
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_NAME = "Sketch Repair"
CMD_ID = "PT-SketchFix"
CMD_Description = "Attempt to repair a sketch with small gaps or disconnected endpoints."
IS_PROMOTED = False

# Global variables by referencing values from /config.py
WORKSPACE_ID = config.design_workspace
TAB_ID = "SketchTab"
PANEL_ID = "SketchModifyPanel"

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

    # Add command created handler. The function passed here will be executed when the command is executed.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******************************** Create Command Control ********************************
    # Get the Sketch tab
    sketchTab = ui.allToolbarTabs.itemById(TAB_ID)
    if not sketchTab:
        ui.messageBox(f"{TAB_ID} tab not found")
        return

        # Get the Modify panel in the Sketch tab
    modifyPanel = sketchTab.toolbarPanels.itemById(PANEL_ID)
    if not modifyPanel:
        ui.messageBox(f"{PANEL_ID} panel not found in {TAB_ID} tab")
        return

    # Create the command control, i.e. a button in the UI.
    control = modifyPanel.controls.addCommand(cmd_def)

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
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        ui = app.userInterface

        # Check a Design document is active.
        if not design:
            ui.messageBox("No active Fusion design", CMD_NAME)
            return

        if design.activeEditObject and isinstance(
            design.activeEditObject, adsk.fusion.Sketch
        ):
            app.executeTextCommand("sketch.repairsketch /3")
            app.executeTextCommand("sketch.repair")

            ui.messageBox("Sketch repaired.", CMD_NAME, 0, 2)
            futil.log(f"{CMD_NAME} Sketch repaired.")

        else:
            ui.messageBox("No sketch is currently active.", CMD_NAME)

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


# This function will be called when the user completes the command.
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f"{CMD_NAME} Command Destroy Event")
