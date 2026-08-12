
"""
E.V.I.E. - Computer & Device Control
Phase 13A-13L
"""

from .models import DeviceCapability, DeviceDescriptor, DeviceKind, DeviceRisk
from .filesystem_models import FilesystemActionResult, PathInfo, PathRisk
from .windows_models import MonitorInfo, WindowInfo
from .process_models import ApplicationLaunchResult, ProcessInfo
from .notification_models import NotificationResult
from .media_models import AudioDeviceInfo, CameraDeviceInfo, CaptureResult
from .accessibility_models import UIActionResult, UIElementInfo
from .browser_models import BrowserPageInfo, DOMActionResult, DOMElementInfo
from .vision_models import ScreenCaptureInfo, VisualTarget
from .control_models import (
    AttemptStatus,
    ComputerControlRequest,
    ComputerControlResult,
    ControlAttempt,
    ControlMethod,
)
from .remote_models import (
    RemoteActionRequest,
    RemoteActionResult,
    RemoteDeviceDescriptor,
)
from .integration_models import ComputerToolPlan

from .controller import *
from .media_controller import *
from .accessibility_controller import *
from .browser_controller import *
from .vision_controller import *
from .control_controller import control_local_computer
from .remote_controller import (
    execute_remote_device_action,
    list_local_remote_devices,
    probe_remote_device,
    register_local_remote_device,
    remove_local_remote_device,
)
from .integration import handle_computer_message
