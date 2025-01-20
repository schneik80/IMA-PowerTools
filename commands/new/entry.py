import adsk.core, adsk.fusion, adsk.cam, adsk.drawing
import os, traceback, json
from ...lib import fusionAddInUtils as futil
from ... import config
from datetime import datetime

CMD_NAME = "New Document"
CMD_ID = "PT-new"
CMD_Description = "Create new Document"
IS_PROMOTED = False

# Global variables by referencing values from /config.py
WORKSPACE_ID = config.design_workspace
TAB_ID = config.tools_tab_id
TAB_NAME = config.my_tab_name

PANEL_ID = config.my_panel_id
PANEL_NAME = config.my_panel_name
PANEL_AFTER = config.my_panel_after

# Pallet
PALETTE_NAME = CMD_NAME
PALETTE_ID = f"{config.COMPANY_NAME}_{config.ADDIN_NAME}_palette_id"
PALETTE_URL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "resources", "index.html"
)
PALETTE_URL = PALETTE_URL.replace(
    "\\", "/"
)  # The path function builds a valid OS path. This fixes it to be a valid local URL.
PALETTE_DOCKING = (
    adsk.core.PaletteDockingStates.PaletteDockStateRight
)  # Set a default docking behavior for the palette

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "")

# Holds references to event handlers
local_handlers = []
app = adsk.core.Application.get()
ui = app.userInterface


# Executed when add-in is run.
def start():
    # ******************************** Create Command Definition ********************************
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
    )

    # Add command created handler. The function passed here will be executed when the command is executed.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******************************** Create Command Control ********************************
    # Get target workspace for the command.
    qat = ui.toolbars.itemById("QAT")

    # Create the command control, i.e. a button in the UI.
    control = qat.controls.addCommand(cmd_def, "FileSubMenuCommand", False)


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    qat = ui.toolbars.itemById("QAT")
    command_control = qat.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    palette = ui.palettes.itemById(PALETTE_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

    # Delete the Palette
    if palette:
        palette.deleteMe()


# Event handler that is called when the user clicks the command button in the UI.
# To have a dialog, you create the desired command inputs here. If you don't need
# a dialog, don't create any inputs and the execute event will be immediately fired.
# You also need to connect to any command related events here.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME}: Command created event.")
    futil.log(f"Hub Configured: {config.COMPANY_HUB}")

    # Create the event handlers you will need for this instance of the command
    futil.add_handler(
        args.command.execute, command_execute, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.destroy, command_destroy, local_handlers=local_handlers
    )


# Because no command inputs are being added in the command created event, the execute
# event is immediately fired.
def command_execute(args: adsk.core.CommandEventArgs):
    global palette
    # General logging for debug.
    futil.log(f"{CMD_NAME}: Command execute event.")

    palettes = ui.palettes

    palette = palettes.itemById(PALETTE_ID)
    if palette is None:
        palette = palettes.add(
            id=PALETTE_ID,
            name=PALETTE_NAME,
            htmlFileURL=PALETTE_URL,
            isVisible=False,
            showCloseButton=True,
            isResizable=True,
            width=450,
            height=600,
            useNewWebBrowser=True,
        )
        futil.add_handler(palette.closed, palette_closed)
        futil.add_handler(palette.navigatingURL, palette_navigating)
        futil.add_handler(palette.incomingFromHTML, palette_incoming)
        futil.log(
            f"{CMD_NAME}: Created a new palette: ID = {palette.id}, Name = {palette.name}"
        )

    if palette.dockingState == adsk.core.PaletteDockingStates.PaletteDockStateFloating:
        palette.dockingState = PALETTE_DOCKING

        # hub check
    hub = app.data.activeHub
    if hub.id != config.COMPANY_HUB:
        futil.log(f"active hub is {hub.id}.\n{config.COMPANY_HUB} was expected")
        ui.messageBox(
            "The active hub is not configured for this command.\nPlease switch to the correct hub and try again.",
            "Incorrect Hub",
            0,
            3,
        )
        palette.isVisible = False
    else:
        palette.isVisible = True


# Use this to handle a user closing your palette.
def palette_closed(args: adsk.core.UserInterfaceGeneralEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME}: Palette was closed.")


# Use this to handle a user navigating to a new page in your palette.
def palette_navigating(args: adsk.core.NavigationEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME}: Palette navigating event.")

    # Get the URL the user is navigating to:
    url = args.navigationURL

    log_msg = f"User is attempting to navigate to {url}\n"
    futil.log(log_msg, adsk.core.LogLevels.InfoLogLevel)

    # Check if url is an external site and open in user's default browser.
    if url.startswith("http"):
        args.launchExternally = True


# Use this to handle events sent from javascript in your palette.
def palette_incoming(html_args: adsk.core.HTMLEventArgs):
    global palette

    # General logging for debug.
    futil.log(f"{CMD_NAME}: Palette incoming event.")

    message_data: dict = json.loads(html_args.data)
    message_action = html_args.action

    log_msg = f"Event received from {html_args.firingEvent.sender.name}\n"
    log_msg += f"Action: {message_action}\n"
    log_msg += f"Data: {message_data}"
    futil.log(log_msg, adsk.core.LogLevels.InfoLogLevel)

    palette.isVisible = False
    ui.progressBar.showBusy("Creating new document...")

    docTitle = create_unique_Filename()
    docActive = app.data.activeFolder
    docCopyURN = message_data["link"]
    docActiveURN = app.data.findFileById(docCopyURN)
    docNew = app.documents.open(docActiveURN)
    docNew.saveAs(
        docTitle,
        docActive,
        "Auto created by new add-in",
        "",
    )

    ui.progressBar.hide()


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME}: Command destroy event.")

    global local_handlers
    local_handlers = []


def create_unique_Filename(prefix="new"):
    # get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}"

    return filename
