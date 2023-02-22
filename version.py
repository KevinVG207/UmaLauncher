from loguru import logger
import dmm

VERSION = "1.0.0"

def parse_version(version_string: str):
    """Convert version string to tuple."""
    if not version_string:
        return (0,0,0)
    return tuple(int(num) for num in version_string.split("."))

def vstr(version_tuple: tuple):
    """Convert version tuple to string."""
    return ".".join([str(num) for num in version_tuple])


def upgrade(umasettings: dict):
    """Upgrades old versions."""
    script_version = parse_version(VERSION)
    settings_version = parse_version(umasettings.get("_version", None))
    logger.info(f"Script version: {vstr(script_version)}, Settings version: {vstr(settings_version)}")

    if script_version < settings_version:
        logger.warning("Umasettings are for a newer version. Skipping upgrade.")
        return umasettings

    if settings_version < (0,9,1):
        # Remove DMM patch
        logger.info("Found settings before 0.9.1 - Attempting to unpatch DMM.")
        # Unpatch DMM if needed.
        if "dmm_path" in umasettings:
            dmm.unpatch_dmm(umasettings['dmm_path'])
            del umasettings['dmm_path']
        if 'Patch DMM' in umasettings['tray_items']:
            del umasettings['tray_items']['Patch DMM']
        logger.info("Completed upgrade to version 0.9.1")

    # Upgrade settings version no.
    if '_version' in umasettings:
        del umasettings['_version']
    umasettings = {'_version': vstr(script_version), **umasettings}
    return umasettings
