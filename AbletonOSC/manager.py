# Standard library imports
import importlib
import logging
import os

# Third-party imports
from ableton.v2.control_surface import ControlSurface

# Local application/library specific imports
from . import abletonosc

logger = logging.getLogger("abletonosc")

class Manager(ControlSurface):
    """Manager class for AbletonOSC."""

    def __init__(self, c_instance):
        """Initialize the Manager class.

        Args:
            c_instance: Instance of the ControlSurface class.
        """
        ControlSurface.__init__(self, c_instance)

        self.log_level = "info"
        self.start_logging()

        self.handlers = []
        self.show_message("AbletonOSC: Listening for OSC on port %d" % abletonosc.OSC_LISTEN_PORT)

        self.osc_server = abletonosc.OSCServer()
        self.schedule_message(0, self.tick)

        self.init_api()

        class LiveOSCErrorLogHandler(logging.StreamHandler):
            def emit(handler, record):
                message = record.getMessage()
                message = message[message.index(":") + 2:]
                try:
                    self.osc_server.send("/live/error", (message,))
                except OSError:
                    # If the connection is dead, silently ignore errors as there's not much more we can do
                    pass
        self.live_osc_error_handler = LiveOSCErrorLogHandler()
        self.live_osc_error_handler.setLevel(logging.ERROR)
        logger.addHandler(self.live_osc_error_handler)

    def start_logging(self):
        """Start logging."""
        module_path = os.path.dirname(os.path.realpath(__file__))
        log_dir = os.path.join(module_path, "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir, 0o755)
        log_path = os.path.join(log_dir, "abletonosc.log")
        self.log_file_handler = logging.FileHandler(log_path)
        self.log_file_handler.setLevel(self.log_level.upper())
        formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
        self.log_file_handler.setFormatter(formatter)
        logger.addHandler(self.log_file_handler)

    def init_api(self):
        """Initialize the API."""
        def test_callback(params):
            self.show_message("Received OSC OK")
            self.osc_server.send("/live/test", ("ok",))
        def reload_callback(params):
            self.reload_imports()
        def get_log_level_callback(params):
            return (self.log_level,)
        def set_log_level_callback(params):
            log_level = params[0]
            if log_level not in ("debug", "info", "warning", "error", "critical"):
                raise ValueError(f"Invalid log level: {log_level}")
            self.log_level = log_level
            self.log_file_handler.setLevel(self.log_level.upper())

        self.osc_server.add_handler("/live/test", test_callback)
        self.osc_server.add_handler("/live/api/reload", reload_callback)
        self.osc_server.add_handler("/live/api/get/log_level", get_log_level_callback)
        self.osc_server.add_handler("/live/api/set/log_level", set_log_level_callback)

        with self.component_guard():
            self.handlers = [
                abletonosc.SongHandler(self),
                abletonosc.ApplicationHandler(self),
                abletonosc.ClipHandler(self),
                abletonosc.ClipSlotHandler(self),
                abletonosc.TrackHandler(self),
                abletonosc.DeviceHandler(self),
                abletonosc.ViewHandler(self)
            ]

    def clear_api(self):
        """Clear the API."""
        self.osc_server.clear_handlers()
        for handler in self.handlers:
            handler.clear_api()

    def tick(self):
        """
        Called once per 100ms "tick". This method allows long-running
        processes such as the OSC server to perform operations without
        threading, which is not supported in Live's embedded Python.
        """
        logger.debug("Tick...")
        self.osc_server.process()
        self.schedule_message(1, self.tick)

    def reload_imports(self):
        """Reload imports."""
        try:
            importlib.reload(abletonosc.application)
            importlib.reload(abletonosc.clip)
            importlib.reload(abletonosc.clip_slot)
            importlib.reload(abletonosc.device)
            importlib.reload(abletonosc.handler)
            importlib.reload(abletonosc.osc_server)
            importlib.reload(abletonosc.song)
            importlib.reload(abletonosc.track)
            importlib.reload(abletonosc.view)
            importlib.reload(abletonosc)
        except Exception as e:
            exc = traceback.format_exc()
            logging.warning(exc)

        if self.handlers:
            self.clear_api()
            self.init_api()
        logger.info("Reloaded code")

    def disconnect(self):
        """Disconnect the OSC server."""
        self.show_message("Disconnecting...")
        logger.info("Disconnecting...")
        self.osc_server.shutdown()
        super().disconnect()
