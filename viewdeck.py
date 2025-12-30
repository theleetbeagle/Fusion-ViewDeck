import adsk.core, adsk.fusion, traceback, math

handlers = []

# === View orientation commands ===
view_commands = [
    ('goHomeViewCommand', 'Go Home View', 'Reorient camera to Home view.', 'home'),
    ('goTopViewCommand', 'Go to Top View', 'Top view.', adsk.core.ViewOrientations.TopViewOrientation),
    ('goBottomViewCommand', 'Go to Bottom View', 'Bottom view.', adsk.core.ViewOrientations.BottomViewOrientation),
    ('goLeftViewCommand', 'Go to Left View', 'Left view.', adsk.core.ViewOrientations.LeftViewOrientation),
    ('goRightViewCommand', 'Go to Right View', 'Right view.', adsk.core.ViewOrientations.RightViewOrientation),
    ('goFrontViewCommand', 'Go to Front View', 'Front view.', adsk.core.ViewOrientations.FrontViewOrientation),
    ('goBackViewCommand', 'Go to Back View', 'Back view.', adsk.core.ViewOrientations.BackViewOrientation),
]

# === Rotate logic ===
def rotate_camera_like_viewcube(view, degrees=90):
    camera = view.camera
    eye = camera.eye
    target = camera.target
    up = camera.upVector

    view_dir = target.vectorTo(eye)
    view_dir.normalize()

    angle_rad = math.radians(degrees)
    rotation = adsk.core.Matrix3D.create()
    rotation.setToRotation(angle_rad, view_dir, target)

    rotated_eye = adsk.core.Point3D.create(eye.x, eye.y, eye.z)
    rotated_eye.transformBy(rotation)

    rotated_up = adsk.core.Vector3D.create(up.x, up.y, up.z)
    rotated_up.transformBy(rotation)

    camera.eye = rotated_eye
    camera.upVector = rotated_up
    view.camera = camera
    view.refresh()

# === Generic view command handler factory ===
def make_view_handler(orientation):
    class ViewExecuteHandler(adsk.core.CommandEventHandler):
        def notify(self, args):
            try:
                view = adsk.core.Application.get().activeViewport
                if orientation == 'home':
                    view.goHome()
                else:
                    cam = view.camera
                    cam.viewOrientation = orientation
                    cam.isSmoothTransition = False
                    view.camera = cam
                    view.refresh()
            except:
                ui = adsk.core.Application.get().userInterface
                ui.messageBox(f'Error switching view:\n{traceback.format_exc()}')
    return ViewExecuteHandler

# === Rotate command handler ===
class RotateViewExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            view = adsk.core.Application.get().activeViewport
            rotate_camera_like_viewcube(view, 90)
        except:
            ui = adsk.core.Application.get().userInterface
            ui.messageBox(f'Error rotating view:\n{traceback.format_exc()}')

# === Command creation wrapper ===
def make_command_created_handler(execute_handler_class):
    class CreatedHandler(adsk.core.CommandCreatedEventHandler):
        def notify(self, args):
            try:
                cmd = args.command
                exec_handler = execute_handler_class()
                cmd.execute.add(exec_handler)
                handlers.append(exec_handler)
            except:
                ui = adsk.core.Application.get().userInterface
                ui.messageBox(f'CommandCreated error:\n{traceback.format_exc()}')
    return CreatedHandler

# === Main entry ===
def run(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')

        # Add Go Home + orientation commands
        for cmd_id, name, desc, orientation in view_commands:
            cmd_def = ui.commandDefinitions.itemById(cmd_id)
            if not cmd_def:
                cmd_def = ui.commandDefinitions.addButtonDefinition(cmd_id, name, desc, '')
                created_handler = make_command_created_handler(make_view_handler(orientation))()
                cmd_def.commandCreated.add(created_handler)
                handlers.append(created_handler)
            if not panel.controls.itemById(cmd_id):
                panel.controls.addCommand(cmd_def)

        # Add rotate command
        rot_cmd_id = 'rotateViewClockwiseCommand'
        rot_cmd_def = ui.commandDefinitions.itemById(rot_cmd_id)
        if not rot_cmd_def:
            rot_cmd_def = ui.commandDefinitions.addButtonDefinition(
                rot_cmd_id,
                'Rotate 90° Clockwise',
                'Rotates view 90° clockwise like ViewCube arrow.',
                ''
            )
            created_handler = make_command_created_handler(RotateViewExecuteHandler)()
            rot_cmd_def.commandCreated.add(created_handler)
            handlers.append(created_handler)
        if not panel.controls.itemById(rot_cmd_id):
            panel.controls.addCommand(rot_cmd_def)

    except:
        adsk.core.Application.get().userInterface.messageBox('Add-in Error:\n{}'.format(traceback.format_exc()))
