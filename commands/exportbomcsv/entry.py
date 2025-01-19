import adsk.core, adsk.fusion
import os, traceback
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

showversion = True  # show versions in xref component names, default is on
showsubs = False  # show the subassemblies in list, for flat BOM default is off. Children are still displayed this only affects the sub itself
docname = ""  # a default name

CMD_NAME = "Export BOM as CSV"
CMD_ID = "PT-exportbom"
CMD_Description = "Export active assembly structure and quantities as a CSV file"
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
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        global docname
        global showversion
        global showsubs

        command = args.firingEvent.sender
        inputs = command.commandInputs

        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox("A Design Must be Active.", "BOM Export")
            return

        # Get all occurrences in the rootComp component of the active design
        rootComp = design.rootComponent
        occs = rootComp.allOccurrences

        for input in inputs:
            if input.id == "docname_":
                docname = input.value
            elif input.id == "showversion_":
                showversion = input.value
            elif input.id == "showsubs_":
                showsubs = input.value

        # Gather information about each unique component
        bom = []
        for occ in occs:
            comp = occ.component
            refocc = occ.isReferencedComponent
            occtype = occ.childOccurrences.count
            # print (occtype)
            jj = 0
            for bomI in bom:
                if bomI["component"] == comp:
                    # Increment the instance count of the existing row.
                    bomI["instances"] += 1
                    break
                jj += 1

            if jj == len(bom):
                # Modify the name if versions are OFF and an occurrence is an xref
                if showversion == False and refocc == True:
                    longname = comp.name
                    shortname = " v".join(longname.split(" v")[:-1])
                else:
                    shortname = comp.name

                mat = ""
                bodies = comp.bRepBodies
                for bodyK in bodies:
                    if bodyK.isSolid:
                        mat += bodyK.material.name

                # Add this component to the BOM
                bom.append(
                    {
                        "component": comp,
                        "name": shortname,
                        "pn": comp.partNumber,
                        "material": mat,
                        "instances": 1,
                        "sub": occtype,
                    }
                )

        # collect BOM data
        parentOcc = design.parentDocument.name
        resultString = parentOcc + " BOM\n"
        resultString += "Display Name," + "Part Number," + "Material," + "Count\n"
        resultString += traverseAssembly(bom)

        # Display the BOM in the console
        print(resultString)

        # Set styles of file dialog.
        folderDlg = ui.createFolderDialog()
        folderDlg.title = "Choose Folder to save BOM CSV"

        # Show file save dialog
        dlgResult = folderDlg.showDialog()
        if dlgResult == adsk.core.DialogResults.DialogOK:
            filepath = os.path.join(folderDlg.folder, parentOcc + ".csv")
            # Write the results to the file
            with open(filepath, "w") as f:
                f.write(resultString)
            ui.messageBox("BOM saved at: " + filepath, parentOcc, 0, 2)
            futil.log(f"BOM Saved at {filepath}")
        else:
            return

    except:
        if ui:
            ui.messageBox(
                ("command executed failed: {}").format(traceback.format_exc())
            )


# This function will be called when the user completes the command.
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f"{CMD_NAME} Command Destroy Event")


# walk thru the assembly
def traverseAssembly(bom):
    mStr = ""
    if showsubs == False:
        for item in bom:
            if item["sub"] < 1:
                mStr += (
                    '"'
                    + item["name"]
                    + '","'
                    + str(item["pn"])
                    + '","'
                    + str(item["material"])
                    + '",'
                    + str(item["instances"])
                    + ",EA"
                    + "\n"
                )
        return mStr
    if showsubs == True:
        for item in bom:
            mStr += (
                '"'
                + item["name"]
                + '","'
                + str(item["pn"])
                + '","'
                + str(item["material"])
                + '",'
                + str(item["instances"])
                + ",EA"
                + "\n"
            )
        return mStr
